"""
ar5iv-to-notion 主程序

将 arXiv 论文导入 Notion，包括完整内容和参考文献子页面

使用方法:
    python main.py <arxiv_id>
    python main.py 1706.03762 --with-refs
    python main.py 2301.08362 --verbose --no-cache
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

from config import AppConfig, NotionConfig, CacheConfig, ReferenceConfig
from models import PaperData, PaperStatus, Reference
from fetch.arxiv_api import ArxivApiClient
from fetch.ar5iv_extractor import Ar5ivExtractor
from process.reference_resolver import ReferenceResolver
from notion.converter import NotionConverter
from notion.creator import NotionCreator
from utils import setup_logging, normalize_arxiv_id, format_exception
from storage.file_manager import FileManager
from process.qwen_annotator import QwenAnnotator


def _detect_category(primary_category: str) -> str:
    """Map an arXiv primary category to a file system category folder."""
    c = primary_category.lower()
    if any(k in c for k in ["cs.ai", "cs.ma", "cs.ro"]):
        return "ai_agent"
    if any(k in c for k in ["cs.cv", "cs.cl", "cs.lg", "stat.ml", "cs.ne"]):
        return "deep_learning"
    if any(k in c for k in ["cs.gt", "cs.sy"]):
        return "reinforcement_learning"
    return "other"


class Ar5ivToNotion:
    """
    ar5iv-to-notion 主处理类
    
    负责协调各模块完成论文导入流程
    """
    
    def __init__(self, config: AppConfig):
        """
        初始化处理器

        Args:
            config: 应用配置
        """
        self.config = config

        self.arxiv_client = ArxivApiClient(config=config.arxiv, cache_config=config.cache)
        self.ar5iv_extractor = Ar5ivExtractor(config=config.arxiv, cache_config=config.cache)
        self.ref_resolver = ReferenceResolver(config=config.reference, arxiv_client=self.arxiv_client)

        # File manager and annotator (new)
        self.file_manager = FileManager(base_dir=Path("."))
        self.annotator = QwenAnnotator(config=config.qwen, file_manager=self.file_manager)

        self.converter = NotionConverter(
            max_text_length=config.content.max_text_length,
            include_equations=config.content.include_equations,
            include_figures=config.content.include_figures,
            include_tables=config.content.include_tables,
            max_sections=config.content.max_sections,
        )
        self.notion_creator = NotionCreator(config=config.notion, converter=self.converter)
    
    async def process_paper(
        self,
        arxiv_id: str,
        category: str = "",
        with_references: bool = True,
        use_cache: bool = True,
        max_ref_pages: int = 20,
        annotate: bool = True,
    ) -> PaperData:
        import time as _time
        arxiv_id = normalize_arxiv_id(arxiv_id)
        logger.info(f"Processing: {arxiv_id}")

        paper = PaperData(arxiv_id=arxiv_id, status=PaperStatus.FETCHING)
        start_ms = int(_time.time() * 1000)

        try:
            # 1. Fetch arXiv metadata
            paper.metadata = await self.arxiv_client.get_paper(arxiv_id, use_cache)
            if not paper.metadata:
                paper.status = PaperStatus.FAILED
                paper.error = "Could not fetch arXiv metadata"
                return paper

            logger.info(f"Title: {paper.metadata.title}")

            # Auto-detect category from arXiv primary category if not provided
            if not category:
                category = _detect_category(paper.metadata.primary_category)

            # 2. Extract ar5iv content
            paper.status = PaperStatus.PARSING
            paper.content = await self.ar5iv_extractor.extract_paper(arxiv_id, use_cache)
            if not paper.content:
                logger.warning("ar5iv extraction failed — using metadata only")

            # 3 + 5 (concurrent). Annotation and reference resolution run at the same time.
            async def _do_annotation() -> list:
                if not (annotate and self.config.qwen.enabled and paper.content):
                    return []
                if not self.config.qwen.api_key:
                    logger.warning("DASHSCOPE_API_KEY not set — skipping annotation")
                    return []
                return await self.annotator.annotate_paper(paper.content, arxiv_id, category)

            async def _do_resolve_refs() -> list:
                if not (with_references and paper.content and paper.content.references):
                    return []
                return await self.ref_resolver.resolve_references(paper.content.references)

            logger.info("Annotating paragraphs and resolving references concurrently...")
            annotations, resolved_refs = await asyncio.gather(
                _do_annotation(), _do_resolve_refs()
            )
            paper.resolved_references = resolved_refs

            # 4. Save to file system (after annotation so annotations are available)
            if paper.metadata:
                self.file_manager.save_metadata(arxiv_id, category, paper.metadata)
            if paper.content:
                self.file_manager.save_content_md(arxiv_id, category, paper.content)
                self.file_manager.save_content_json(arxiv_id, category, paper.content)

            # Fetch arXiv metadata for resolved references (must be after resolution)
            ref_metadata = {}
            if resolved_refs:
                arxiv_refs = self.ref_resolver.get_arxiv_references(resolved_refs)
                logger.info(f"Found {len(arxiv_refs)} arXiv references")
                if arxiv_refs:
                    ids = [r.arxiv_id for r in arxiv_refs[:max_ref_pages] if r.arxiv_id]
                    ref_metadata = await self.arxiv_client.get_papers_batch(ids, use_cache)

            # 6. Create Notion pages
            paper.status = PaperStatus.CREATING
            result = self.notion_creator.create_paper_with_references(
                paper, ref_metadata, max_ref_pages, annotations=annotations
            )

            if result.success:
                paper.status = PaperStatus.COMPLETED
                paper.notion_page_id = result.page_id
                logger.info(f"✅ Created: {result.url}  ({result.children_pages} ref pages)")
                duration_ms = int(_time.time() * 1000) - start_ms
                self.file_manager.log_import({
                    "arxiv_id": arxiv_id,
                    "category": category,
                    "status": "completed",
                    "notion_page_id": result.page_id,
                    "notion_url": result.url,
                    "duration_ms": duration_ms,
                    "blocks_created": result.blocks_created,
                    "ref_pages_created": result.children_pages,
                    "annotated_paragraphs": len(annotations),
                })
            else:
                paper.status = PaperStatus.FAILED
                paper.error = result.error
                logger.error(f"❌ Failed: {result.error}")
                self.file_manager.log_error({
                    "arxiv_id": arxiv_id,
                    "stage": "notion_create",
                    "error_type": "APIError",
                    "message": result.error or "",
                })

            return paper

        except Exception:
            error_msg = format_exception()
            logger.error(f"Processing failed: {error_msg}")
            paper.status = PaperStatus.FAILED
            paper.error = error_msg
            self.file_manager.log_error({
                "arxiv_id": arxiv_id,
                "stage": "process_paper",
                "error_type": "Exception",
                "message": str(error_msg)[:500],
            })
            return paper
    
    async def process_papers(
        self,
        arxiv_ids: List[str],
        with_references: bool = True,
        use_cache: bool = True,
        annotate: bool = True,
    ) -> List[PaperData]:
        """
        批量处理论文

        Args:
            arxiv_ids: arXiv ID 列表
            with_references: 是否处理参考文献
            use_cache: 是否使用缓存
            annotate: 是否使用 Qwen 注解

        Returns:
            论文数据列表
        """
        results = []

        for i, arxiv_id in enumerate(arxiv_ids):
            logger.info(f"\n{'='*50}")
            logger.info(f"处理 [{i+1}/{len(arxiv_ids)}]: {arxiv_id}")

            paper = await self.process_paper(
                arxiv_id,
                with_references=with_references,
                use_cache=use_cache,
                annotate=annotate,
            )
            results.append(paper)

            # 批次间延迟
            if i < len(arxiv_ids) - 1:
                await asyncio.sleep(2)

        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "arxiv_api": self.arxiv_client.get_stats(),
            "ar5iv_extractor": self.ar5iv_extractor.get_stats(),
            "ref_resolver": self.ref_resolver.get_stats(),
            "notion_creator": self.notion_creator.get_stats()
        }


async def main_async(args):
    """异步主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 配置日志
    setup_logging(
        level="DEBUG" if args.verbose else "INFO",
        log_file=Path(args.log_file) if args.log_file else None,
        verbose=args.verbose
    )
    
    # 检查环境变量
    if not os.getenv("NOTION_TOKEN"):
        logger.error("请设置环境变量 NOTION_TOKEN")
        logger.info("获取方式: https://www.notion.so/my-integrations")
        sys.exit(1)
    
    if not os.getenv("NOTION_ROOT_PAGE_ID"):
        logger.error("请设置环境变量 NOTION_ROOT_PAGE_ID")
        sys.exit(1)
    
    # 加载配置
    try:
        config = AppConfig.from_env()
        config.cache.enabled = not args.no_cache
        config.reference.create_ref_pages = args.with_refs
        config.reference.search_missing_ids = args.search_refs
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        sys.exit(1)
    
    # Handle --from-file
    if getattr(args, 'from_file', None):
        import json as _json
        cfg = _json.loads(Path(args.from_file).read_text())
        args.arxiv_ids = [cfg["arxiv_id"]]
        args.category = cfg.get("category", getattr(args, 'category', ""))
        opts = cfg.get("import_options", {})
        args.with_refs = opts.get("with_refs", args.with_refs)
        args.no_annotate = not opts.get("annotate", True)
        args.max_refs = opts.get("max_refs", args.max_refs)

    # 规范化 arXiv IDs
    arxiv_ids = [normalize_arxiv_id(id_) for id_ in args.arxiv_ids]
    arxiv_ids = [id_ for id_ in arxiv_ids if id_]

    if not arxiv_ids:
        logger.error("没有有效的 arXiv ID")
        sys.exit(1)

    logger.info(f"准备处理 {len(arxiv_ids)} 篇论文")

    # 创建处理器
    processor = Ar5ivToNotion(config)

    # 处理论文
    if len(arxiv_ids) == 1:
        paper = await processor.process_paper(
            arxiv_ids[0],
            category=getattr(args, 'category', ""),
            with_references=args.with_refs,
            use_cache=not args.no_cache,
            max_ref_pages=args.max_refs,
            annotate=not getattr(args, 'no_annotate', False),
        )

        if paper.status == PaperStatus.COMPLETED:
            logger.info(f"\n✅ 成功! 页面 ID: {paper.notion_page_id}")
        else:
            logger.error(f"\n❌ 失败: {paper.error}")
            sys.exit(1)
    else:
        results = await processor.process_papers(
            arxiv_ids,
            with_references=args.with_refs,
            use_cache=not args.no_cache,
            annotate=not getattr(args, 'no_annotate', False),
        )
        
        # 统计
        success = sum(1 for p in results if p.status == PaperStatus.COMPLETED)
        failed = len(results) - success
        
        logger.info(f"\n{'='*50}")
        logger.info(f"处理完成: 成功={success}, 失败={failed}")
    
    # 显示统计
    if args.verbose:
        logger.info(f"\n统计信息: {processor.get_stats()}")


def main():
    """主函数入口"""
    parser = argparse.ArgumentParser(
        description="将 arXiv 论文导入 Notion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python main.py 1706.03762
    python main.py 1706.03762 --with-refs --max-refs 10
    python main.py 2301.08362 1810.04805 --verbose
    python main.py 1706.03762 --no-cache --search-refs

环境变量:
    NOTION_TOKEN         Notion API Token (必需)
    NOTION_ROOT_PAGE_ID  目标根页面 ID (必需)
        """
    )
    
    parser.add_argument(
        "arxiv_ids",
        nargs="+",
        help="arXiv ID（如 1706.03762, 2301.08362）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细日志"
    )
    
    parser.add_argument(
        "--with-refs",
        action="store_true",
        default=True,
        help="处理参考文献并创建子页面（默认启用）"
    )
    
    parser.add_argument(
        "--no-refs",
        action="store_true",
        help="不处理参考文献"
    )
    
    parser.add_argument(
        "--search-refs",
        action="store_true",
        help="搜索没有 arXiv ID 的参考文献"
    )
    
    parser.add_argument(
        "--max-refs",
        type=int,
        default=20,
        help="最大参考文献子页面数（默认 20）"
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="不使用缓存"
    )
    
    parser.add_argument(
        "--log-file",
        help="日志文件路径"
    )

    parser.add_argument(
        "--category",
        default="",
        help="File system category folder (default: auto-detect from arXiv primary category)",
    )

    parser.add_argument(
        "--no-annotate",
        dest="no_annotate",
        action="store_true",
        help="Skip Qwen LLM annotation step",
    )

    parser.add_argument(
        "--from-file",
        dest="from_file",
        metavar="PATH",
        help="Load paper config from a JSON file (see examples/single/)",
    )

    args = parser.parse_args()
    
    # 处理 --no-refs 参数
    if args.no_refs:
        args.with_refs = False
    
    # 运行异步主函数
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()