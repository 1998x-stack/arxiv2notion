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
from arxiv_api import ArxivApiClient
from ar5iv_extractor import Ar5ivExtractor
from reference_resolver import ReferenceResolver
from notion_converter import NotionConverter
from notion_creator import NotionCreator
from utils import setup_logging, normalize_arxiv_id, format_exception


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
        
        # 初始化各模块
        self.arxiv_client = ArxivApiClient(
            config=config.arxiv,
            cache_config=config.cache
        )
        
        self.ar5iv_extractor = Ar5ivExtractor(
            config=config.arxiv,
            cache_config=config.cache
        )
        
        self.ref_resolver = ReferenceResolver(
            config=config.reference,
            arxiv_client=self.arxiv_client
        )
        
        self.converter = NotionConverter(
            max_text_length=config.content.max_text_length,
            include_equations=config.content.include_equations,
            include_figures=config.content.include_figures,
            include_tables=config.content.include_tables,
            max_sections=config.content.max_sections,
        )
        
        self.notion_creator = NotionCreator(
            config=config.notion,
            converter=self.converter
        )
    
    async def process_paper(
        self,
        arxiv_id: str,
        with_references: bool = True,
        use_cache: bool = True,
        max_ref_pages: int = 20
    ) -> PaperData:
        """
        处理单篇论文
        
        Args:
            arxiv_id: arXiv ID
            with_references: 是否处理参考文献
            use_cache: 是否使用缓存
            max_ref_pages: 最大参考文献子页面数
            
        Returns:
            论文数据
        """
        arxiv_id = normalize_arxiv_id(arxiv_id)
        logger.info(f"开始处理论文: {arxiv_id}")
        
        paper = PaperData(arxiv_id=arxiv_id, status=PaperStatus.FETCHING)
        
        try:
            # 1. 获取 arXiv 元数据
            logger.info("获取 arXiv 元数据...")
            paper.metadata = await self.arxiv_client.get_paper(arxiv_id, use_cache)
            
            if not paper.metadata:
                paper.status = PaperStatus.FAILED
                paper.error = "无法获取 arXiv 元数据"
                return paper
            
            logger.info(f"标题: {paper.metadata.title}")
            
            # 2. 提取 ar5iv 内容
            logger.info("提取 ar5iv 内容...")
            paper.status = PaperStatus.PARSING
            paper.content = await self.ar5iv_extractor.extract_paper(arxiv_id, use_cache)
            
            if not paper.content:
                logger.warning("ar5iv 内容提取失败，将只使用元数据")
            else:
                logger.info(
                    f"内容提取完成: {len(paper.content.sections)} 章节, "
                    f"{len(paper.content.references)} 参考文献"
                )
            
            # 3. 解析参考文献
            ref_metadata = {}
            if with_references and paper.content and paper.content.references:
                logger.info("解析参考文献...")
                paper.resolved_references = await self.ref_resolver.resolve_references(
                    paper.content.references
                )
                
                # 获取有 arXiv ID 的参考文献的元数据
                arxiv_refs = self.ref_resolver.get_arxiv_references(paper.resolved_references)
                logger.info(f"找到 {len(arxiv_refs)} 个 arXiv 参考文献")
                
                if arxiv_refs:
                    arxiv_ids = [r.arxiv_id for r in arxiv_refs[:max_ref_pages] if r.arxiv_id]
                    ref_metadata = await self.arxiv_client.get_papers_batch(arxiv_ids, use_cache)
            
            # 4. 创建 Notion 页面
            logger.info("创建 Notion 页面...")
            paper.status = PaperStatus.CREATING
            
            result = self.notion_creator.create_paper_with_references(
                paper,
                ref_metadata,
                max_ref_pages
            )
            
            if result.success:
                paper.status = PaperStatus.COMPLETED
                paper.notion_page_id = result.page_id
                logger.info(f"✅ 创建成功: {result.url}")
                logger.info(f"   主页面 + {result.children_pages} 参考文献页面")
            else:
                paper.status = PaperStatus.FAILED
                paper.error = result.error
                logger.error(f"❌ 创建失败: {result.error}")
            
            return paper
            
        except Exception:
            error_message = format_exception()
            logger.error(f"处理失败: {error_message}")
            paper.status = PaperStatus.FAILED
            paper.error = error_message
            return paper
    
    async def process_papers(
        self,
        arxiv_ids: List[str],
        with_references: bool = True,
        use_cache: bool = True
    ) -> List[PaperData]:
        """
        批量处理论文
        
        Args:
            arxiv_ids: arXiv ID 列表
            with_references: 是否处理参考文献
            use_cache: 是否使用缓存
            
        Returns:
            论文数据列表
        """
        results = []
        
        for i, arxiv_id in enumerate(arxiv_ids):
            logger.info(f"\n{'='*50}")
            logger.info(f"处理 [{i+1}/{len(arxiv_ids)}]: {arxiv_id}")
            
            paper = await self.process_paper(arxiv_id, with_references, use_cache)
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
            with_references=args.with_refs,
            use_cache=not args.no_cache,
            max_ref_pages=args.max_refs
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
            use_cache=not args.no_cache
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
    
    args = parser.parse_args()
    
    # 处理 --no-refs 参数
    if args.no_refs:
        args.with_refs = False
    
    # 运行异步主函数
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()