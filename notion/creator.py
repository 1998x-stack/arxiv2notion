"""
Notion 页面创建模块
职责：使用 Notion API 创建页面和内容
遵循 CleanRL 设计原则：单一职责、显式依赖、易于测试
"""
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from notion_client import Client
from notion_client.errors import APIResponseError
from loguru import logger

from config import NotionConfig
from models import (
    PaperData,
    Reference,
    CreationResult,
    ProcessingStats,
    ArxivMetadata,
)
from notion import NotionConverter
from notion.validator import validate_notion_blocks
from notion.durable_sync import DurableNotionWriter
from storage.import_journal import ImportJournal
from utils import format_exception, get_category_emoji, truncate_text


class NotionCreator:
    """
    Notion 页面创建器
    
    负责：
    1. 创建论文主页面
    2. 分批添加内容 blocks
    3. 为参考文献创建子页面
    """
    
    MAX_BLOCKS_PER_REQUEST = 100
    
    def __init__(
        self,
        config: NotionConfig,
        converter: Optional[NotionConverter] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        journal: Optional[ImportJournal] = None,
        allow_uncertain_retry: bool = False,
    ):
        """
        初始化创建器
        
        Args:
            config: Notion 配置
            converter: 内容转换器
            progress_callback: 进度回调函数
        """
        self.config = config
        # SDK retries are intentionally disabled for durable imports:
        # pages.create/blocks.append are non-idempotent; our journal decides
        # which HTTP requests are safe to reattempt after remote read-back.
        self.client = Client(auth=config.token, retry=False) if journal is not None else Client(auth=config.token)
        self.converter = converter or NotionConverter()
        self.progress_callback = progress_callback
        
        self.stats = ProcessingStats()
        self.journal = journal
        self.allow_uncertain_retry = allow_uncertain_retry
    
    def _report_progress(self, message: str, current: int, total: int):
        """报告进度"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            percentage = (current / total * 100) if total > 0 else 0
            logger.info(f"[{percentage:.1f}%] {message}")
    
    def _create_page_sync(
        self,
        parent_id: str,
        title: str,
        icon: str = "📄",
        blocks: Optional[List[Dict]] = None
    ) -> CreationResult:
        """
        同步创建页面（带重试）
        
        Args:
            parent_id: 父页面 ID
            title: 页面标题
            icon: 页面图标
            blocks: 初始 blocks
            
        Returns:
            创建结果
        """
        for attempt in range(self.config.max_retries):
            try:
                time.sleep(self.config.rate_limit_delay)
                
                response = self.client.pages.create(
                    parent={"page_id": parent_id},
                    icon={"emoji": icon},
                    properties={
                        "title": [{"text": {"content": title}}]
                    },
                    children=blocks[:self.MAX_BLOCKS_PER_REQUEST] if blocks else []
                )
                
                page_id = response["id"]
                page_url = response.get("url", f"https://notion.so/{page_id.replace('-', '')}")
                
                return CreationResult(
                    success=True,
                    page_id=page_id,
                    title=title,
                    url=page_url,
                    blocks_created=len(blocks[:self.MAX_BLOCKS_PER_REQUEST]) if blocks else 0
                )
                
            except APIResponseError as e:
                logger.warning(f"API 错误 (尝试 {attempt+1}/{self.config.max_retries}): {e.code}, {e.message}")
                
                if e.code == "rate_limited":
                    wait_time = 2 ** attempt
                    logger.info(f"速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                
                if e.code == "validation_error":
                    logger.error("Initial blocks rejected; refusing to create an empty page")
                    return CreationResult(success=False, title=title,
                                          error=f"{e.code}: {e.message}")
                
                return CreationResult(
                    success=False,
                    title=title,
                    error=f"{e.code}: {e.message}"
                )
                
            except Exception:
                error_message = format_exception()
                logger.error(f"Page creation outcome uncertain, no blind retry: {error_message}")
                return CreationResult(
                    success=False, title=title,
                    error="Page creation outcome uncertain; reconcile remote page before retry",
                )
        
        return CreationResult(
            success=False,
            title=title,
            error="重试次数耗尽"
        )
    
    def _append_blocks_sync(self, page_id: str, blocks: List[Dict]) -> bool:
        """
        同步追加 blocks
        
        Args:
            page_id: 页面 ID
            blocks: blocks 列表
            
        Returns:
            是否成功
        """
        for attempt in range(self.config.max_retries):
            try:
                time.sleep(self.config.rate_limit_delay)
                
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=blocks
                )
                
                return True
                
            except APIResponseError as e:
                if e.code == "rate_limited":
                    wait_time = 2 ** attempt
                    logger.warning(f"速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"追加 blocks 失败: {e.code}, {e.message}")
                    return False
                    
            except Exception:
                error_message = format_exception()
                logger.error(f"Append outcome uncertain, no blind retry: {error_message}")
                return False
        
        return False
    
    def _append_blocks_batched(self, page_id: str, blocks: List[Dict]) -> int:
        """
        分批追加 blocks
        
        Args:
            page_id: 页面 ID
            blocks: blocks 列表
            
        Returns:
            成功追加的数量
        """
        total_appended = 0
        
        for i in range(0, len(blocks), self.MAX_BLOCKS_PER_REQUEST):
            batch = blocks[i:i + self.MAX_BLOCKS_PER_REQUEST]
            
            if self._append_blocks_sync(page_id, batch):
                total_appended += len(batch)
                logger.debug(f"追加 {len(batch)} blocks (总计 {total_appended})")
            else:
                logger.warning(f"批次追加失败: {i} - {i + len(batch)}")
                break
        
        return total_appended
    
    def create_paper_page(
        self,
        paper: PaperData,
        parent_id: Optional[str] = None,
        annotations: Optional[list] = None,
    ) -> CreationResult:
        """
        创建论文页面

        Args:
            paper: 论文数据
            parent_id: 父页面 ID（默认使用配置中的 root_page_id）
            annotations: 段落注解列表（可选）

        Returns:
            创建结果
        """
        parent_id = parent_id or self.config.root_page_id

        logger.info(f"创建论文页面: {paper.title}")

        try:
            # 转换内容
            blocks = self.converter.convert_paper(paper, annotations=annotations)
            validate_notion_blocks(blocks)
            logger.debug(f"转换完成: {len(blocks)} blocks")

            if self.journal is not None:
                icon = get_category_emoji(paper.metadata.primary_category) if paper.metadata else "📄"
                result = DurableNotionWriter(
                    client=self.client, config=self.config, journal=self.journal,
                    allow_uncertain_retry=self.allow_uncertain_retry,
                ).sync_page(
                    parent_id=parent_id, resource_id=paper.arxiv_id,
                    kind="paper", title=paper.title, icon=icon, blocks=blocks,
                )
                if result.success:
                    self.stats.created_pages += 1
                    self.stats.created_blocks += result.blocks_created
                return result

            # 确定图标
            icon = "📄"
            if paper.metadata:
                icon = get_category_emoji(paper.metadata.primary_category)
            
            # 创建页面（先添加前100个blocks）
            initial_blocks = blocks[:self.MAX_BLOCKS_PER_REQUEST]
            result = self._create_page_sync(
                parent_id,
                paper.title,
                icon,
                initial_blocks
            )
            
            if not result.success:
                return result
            
            result.blocks_created = len(initial_blocks)
            
            # 追加剩余 blocks
            if len(blocks) > self.MAX_BLOCKS_PER_REQUEST:
                remaining = blocks[self.MAX_BLOCKS_PER_REQUEST:]
                appended = self._append_blocks_batched(result.page_id, remaining)
                result.blocks_created += appended
                if appended != len(remaining):
                    result.success = False
                    result.error = (
                        f"Partial Notion import: confirmed {result.blocks_created}/"
                        f"{len(blocks)} blocks; page_id={result.page_id}"
                    )
                    logger.error(result.error)
                    return result

            logger.info(f"论文页面创建成功: {result.page_id} ({result.blocks_created} blocks)")
            
            self.stats.created_pages += 1
            self.stats.created_blocks += result.blocks_created
            
            return result
            
        except Exception:
            error_message = format_exception()
            logger.error(f"创建论文页面失败: {error_message}")
            return CreationResult(
                success=False,
                title=paper.title,
                error=error_message
            )
    
    def create_reference_page(
        self,
        ref: Reference,
        parent_id: str,
        metadata: Optional[ArxivMetadata] = None
    ) -> CreationResult:
        """
        创建参考文献子页面
        
        Args:
            ref: 参考文献
            parent_id: 父页面 ID
            metadata: arXiv 元数据
            
        Returns:
            创建结果
        """
        title = ref.title or f"[{ref.citation_key}] {truncate_text(ref.raw_text, 50)}"
        if ref.arxiv_id:
            title = f"[{ref.arxiv_id}] {title}"
        
        logger.debug(f"创建参考文献页面: {title[:50]}...")
        
        try:
            blocks = self.converter.create_reference_page_blocks(ref, metadata)
            validate_notion_blocks(blocks)

            icon = "📎"
            if metadata:
                icon = get_category_emoji(metadata.primary_category)
            
            if self.journal is not None:
                import hashlib
                identity = (
                    ref.arxiv_id or ref.doi or
                    hashlib.sha256(ref.raw_text.encode("utf-8")).hexdigest()
                )
                result = DurableNotionWriter(
                    client=self.client, config=self.config, journal=self.journal,
                    allow_uncertain_retry=self.allow_uncertain_retry,
                ).sync_page(
                    parent_id=parent_id, resource_id=identity,
                    kind="reference", title=title[:200],
                    icon=icon, blocks=blocks,
                )
            else:
                result = self._create_page_sync(
                    parent_id, title[:100], icon, blocks,
                )
            
            if result.success:
                self.stats.created_pages += 1
                self.stats.created_blocks += result.blocks_created
            
            return result
            
        except Exception:
            error_message = format_exception()
            logger.error(f"创建参考文献页面失败: {error_message}")
            return CreationResult(
                success=False,
                title=title,
                error=error_message
            )
    
    def create_paper_with_references(
        self,
        paper: PaperData,
        ref_metadata: Optional[Dict[str, ArxivMetadata]] = None,
        max_ref_pages: int = 20,
        annotations: Optional[list] = None,
        with_references: bool = True,
    ) -> CreationResult:
        """
        创建论文页面并为引用创建子页面

        Args:
            paper: 论文数据
            ref_metadata: 参考文献元数据映射
            max_ref_pages: 最大参考文献子页面数
            annotations: 段落注解列表（可选）

        Returns:
            创建结果
        """
        ref_metadata = ref_metadata or {}

        self.stats.start_time = datetime.now()
        self._report_progress(f"创建论文页面: {paper.title}", 0, 1)

        # 1. 创建主页面
        main_result = self.create_paper_page(paper, annotations=annotations)
        
        if not main_result.success:
            return main_result

        if not with_references or max_ref_pages <= 0:
            self.stats.end_time = datetime.now()
            return main_result

        # 2. 获取有 arXiv ID 的参考文献
        reference_source = paper.resolved_references
        if not reference_source and paper.content:
            reference_source = paper.content.references
        # One Notion child page per arXiv ID; repeated citations share identity.
        deduplicated = {}
        for reference in reference_source:
            if reference.arxiv_id and reference.arxiv_id not in deduplicated:
                deduplicated[reference.arxiv_id] = reference
        arxiv_refs = list(deduplicated.values())
        
        if not arxiv_refs:
            logger.info("没有找到有 arXiv ID 的参考文献")
            self.stats.end_time = datetime.now()
            return main_result
        
        # 限制数量
        arxiv_refs = arxiv_refs[:max_ref_pages]
        
        logger.info(f"为 {len(arxiv_refs)} 个参考文献创建子页面")
        self.stats.total_references = len(arxiv_refs)
        
        # 3. 创建参考文献子页面
        failed_references = []
        for i, ref in enumerate(arxiv_refs):
            self._report_progress(
                f"创建参考文献 [{i+1}/{len(arxiv_refs)}]: {ref.arxiv_id}",
                i + 1,
                len(arxiv_refs)
            )
            
            metadata = ref_metadata.get(ref.arxiv_id)
            
            ref_result = self.create_reference_page(
                ref,
                main_result.page_id,
                metadata
            )
            
            if ref_result.success:
                main_result.children_pages += 1
                self.stats.resolved_references += 1
            else:
                failed_references.append(ref.arxiv_id)
                logger.warning(f"参考文献页面创建失败: {ref.arxiv_id}")

        if failed_references:
            main_result.success = False
            main_result.error = (
                f"Partial reference import: {len(failed_references)} failed; "
                f"main page_id={main_result.page_id}; "
                f"failed IDs={', '.join(failed_references)}"
            )

        self.stats.end_time = datetime.now()
        
        logger.info(
            f"完成: 主页面 + {main_result.children_pages} 个参考文献页面, "
            f"共 {self.stats.created_blocks} blocks, "
            f"耗时 {self.stats.get_duration():.1f}s"
        )
        
        return main_result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.to_dict()


async def test_notion_creator():
    """测试 Notion 创建器"""
    import os
    from dotenv import load_dotenv
    from utils import setup_logging
    
    setup_logging(level="DEBUG")
    load_dotenv()
    
    token = os.getenv("NOTION_TOKEN")
    root_id = os.getenv("NOTION_ROOT_PAGE_ID")
    
    if not token or not root_id:
        logger.error("请设置 NOTION_TOKEN 和 NOTION_ROOT_PAGE_ID")
        return
    
    config = NotionConfig(token=token, root_page_id=root_id)
    creator = NotionCreator(config)
    
    # 创建测试数据
    from models import Author
    
    metadata = ArxivMetadata(
        arxiv_id="test.12345",
        title="Test Paper: A Comprehensive Study",
        authors=[Author(name="Test Author")],
        abstract="This is a test abstract for the paper...",
        categories=["cs.CL"],
        primary_category="cs.CL",
        published=datetime.now(),
        updated=datetime.now(),
    )
    
    paper = PaperData(
        arxiv_id="test.12345",
        metadata=metadata,
    )
    
    result = creator.create_paper_page(paper)
    
    if result.success:
        logger.info(f"测试成功! 页面: {result.url}")
    else:
        logger.error(f"测试失败: {result.error}")
    
    logger.info(f"统计: {creator.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_notion_creator())