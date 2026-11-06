"""
ar5iv 内容提取模块
职责：从 ar5iv 页面提取论文完整内容
遵循 CleanRL 设计原则：单一职责、显式依赖、易于测试
"""
import asyncio
import re
from urllib.parse import urljoin, urlsplit
from ipaddress import ip_address
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import aiohttp
from bs4 import BeautifulSoup, Tag
from loguru import logger

from config import ArxivConfig, CacheConfig
from domain.paper_document import assess_quality
from models import (
    Ar5ivContent,
    Section,
    Figure,
    Table,
    Equation,
    Reference,
)
from utils import (
    save_json,
    load_json,
    build_ar5iv_url,
    clean_text,
    truncate_text,
    format_exception,
    extract_arxiv_ids,
    normalize_arxiv_id,
    is_valid_arxiv_id,
)


EXTRACTOR_CACHE_VERSION = 2
MAX_HTML_BYTES = 20 * 1024 * 1024



from parsing.latexhtml import Ar5ivHTMLParser

class Ar5ivExtractor(Ar5ivHTMLParser):
    """
    ar5iv 内容提取器
    
    负责从 ar5iv HTML 页面提取论文的完整结构化内容。
    支持提取：标题、作者、摘要、章节、图片、表格、公式、参考文献。
    """
    
    def __init__(
        self,
        config: Optional[ArxivConfig] = None,
        cache_config: Optional[CacheConfig] = None,
    ):
        """
        初始化提取器
        
        Args:
            config: arXiv 配置
            cache_config: 缓存配置
        """
        self.config = config or ArxivConfig()
        self.cache_config = cache_config or CacheConfig()
        
        self.user_agent = "ar5iv-to-notion/1.0 (Academic Research Tool)"
        
        # 统计
        self.success_count = 0
        self.failure_count = 0

    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        url: str,
        retry_count: int = 0,
    ) -> Optional[str]:
        """Fetch bounded HTML with retry on transient errors, never on 404/410.

        No recursive retry or unconditional 120-second rate-limit sleep. An
        oversized Retry-After is respected by failing this attempt rather
        than hitting the upstream service earlier than requested.
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.5",
        }
        max_attempts = max(0, self.config.max_retries) + 1
        for attempt in range(retry_count, max_attempts):
            retry_after = None
            try:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                async with session.get(
                    url, headers=headers, timeout=timeout, allow_redirects=False
                ) as response:
                    status = response.status
                    if status == 200:
                        media_type = response.headers.get("Content-Type", "").lower()
                        if media_type and not any(
                            kind in media_type for kind in ("text/html", "application/xhtml+xml")
                        ):
                            logger.warning(f"Unexpected ar5iv content type {media_type}: {url}")
                            return None
                        if response.content_length is not None and response.content_length > MAX_HTML_BYTES:
                            logger.warning(f"ar5iv HTML exceeds byte limit: {url}")
                            return None
                        chunks = []
                        size = 0
                        async for chunk in response.content.iter_chunked(64 * 1024):
                            size += len(chunk)
                            if size > MAX_HTML_BYTES:
                                logger.warning(f"ar5iv HTML exceeds byte limit while streaming: {url}")
                                return None
                            chunks.append(chunk)
                        return b"".join(chunks).decode("utf-8", errors="replace")
                    if status in (404, 410):
                        logger.info(f"ar5iv has no HTML for paper: {url} ({status})")
                        return None
                    if status not in (429, 500, 502, 503, 504):
                        logger.warning(f"Unexpected ar5iv HTTP {status}: {url}")
                        return None
                    value = response.headers.get("Retry-After")
                    if value:
                        try:
                            retry_after = max(0.0, float(value))
                        except ValueError:
                            try:
                                until = parsedate_to_datetime(value)
                                if until.tzinfo is None:
                                    until = until.replace(tzinfo=timezone.utc)
                                retry_after = max(0.0, (until - datetime.now(timezone.utc)).total_seconds())
                            except (ValueError, TypeError, OverflowError):
                                retry_after = None
                    logger.warning(f"Transient ar5iv HTTP {status}, attempt {attempt + 1}: {url}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning(f"Transient ar5iv fetch error ({type(exc).__name__}): {url}")

            if attempt + 1 >= max_attempts:
                break
            if retry_after is not None and retry_after > 60:
                logger.warning(f"Retry-After exceeds 60s budget; deferring paper: {url}")
                break
            delay = retry_after if retry_after is not None else min(2 ** attempt * 3, 30)
            await asyncio.sleep(delay)

        return None

    async def extract_paper(
        self,
        arxiv_id: str,
        use_cache: bool = True
    ) -> Optional[Ar5ivContent]:
        """
        提取单篇论文内容
        
        Args:
            arxiv_id: 论文 ID
            use_cache: 是否使用缓存
            
        Returns:
            Ar5ivContent 对象或 None
        """
        arxiv_id = normalize_arxiv_id(arxiv_id)
        if not is_valid_arxiv_id(arxiv_id):
            logger.warning(f"Invalid arXiv identifier: {arxiv_id!r}")
            self.failure_count += 1
            return None

        # 检查缓存
        if use_cache and self.cache_config.enabled:
            cache_file = self.cache_config.get_ar5iv_cache_file(arxiv_id)
            cached_data = await load_json(cache_file)
            if cached_data:
                try:
                    if cached_data.get("_extractor_version") != EXTRACTOR_CACHE_VERSION:
                        raise ValueError("Legacy or stale HTML extraction cache")
                    cached_content = self._rebuild_content(cached_data)
                    if assess_quality(cached_content).cacheable_full_text:
                        logger.debug(f"使用缓存: {arxiv_id}")
                        return cached_content
                    logger.warning(f"Rejecting incomplete cached ar5iv content: {arxiv_id}")
                except (KeyError, TypeError, ValueError) as exc:
                    logger.warning(f"Rejecting invalid ar5iv cache for {arxiv_id}: {exc}")
        
        url = self.config.ar5iv_base_url.rstrip("/") + "/" + arxiv_id
        logger.info(f"提取 ar5iv 内容: {arxiv_id}")
        
        async with aiohttp.ClientSession() as session:
            html = await self._fetch_page(session, url)
            
            if not html:
                self.failure_count += 1
                return None
            
            content = self.parse_html(html, arxiv_id)
            
            if content:
                # 保存到缓存
                if self.cache_config.enabled and assess_quality(content).cacheable_full_text:
                    cache_file = self.cache_config.get_ar5iv_cache_file(arxiv_id)
                    serialized = content.to_dict()
                    serialized["_extractor_version"] = EXTRACTOR_CACHE_VERSION
                    await save_json(serialized, cache_file)
                
                self.success_count += 1
            else:
                self.failure_count += 1
            
            # 添加延迟
            await asyncio.sleep(self.config.request_delay)
            
            return content

    def _rebuild_content(self, data: Dict[str, Any]) -> Ar5ivContent:
        """从缓存数据重建 Ar5ivContent"""
        # 重建章节
        def rebuild_section(s: Dict) -> Section:
            return Section(
                title=s.get('title', ''),
                level=s.get('level', 2),
                paragraphs=s.get('paragraphs', []),
                subsections=[rebuild_section(sub) for sub in s.get('subsections', [])],
                figures=[Figure(**f) for f in s.get('figures', [])],
                tables=[Table(**t) for t in s.get('tables', [])],
                equations=[Equation(**e) for e in s.get('equations', [])],
                ordered_content=s.get('ordered_content', []),
                source_anchor=s.get("source_anchor"),
            )
        
        return Ar5ivContent(
            paper_id=data.get('paper_id', ''),
            title=data.get('title', ''),
            authors=data.get('authors', []),
            affiliations=data.get('affiliations', []),
            abstract=data.get('abstract'),
            sections=[rebuild_section(s) for s in data.get('sections', [])],
            figures=[Figure(**f) for f in data.get('figures', [])],
            tables=[Table(**t) for t in data.get('tables', [])],
            equations=[Equation(**e) for e in data.get('equations', [])],
            references=[Reference(**r) for r in data.get('references', [])],
            full_text=data.get('full_text', ''),
            extracted_at=datetime.fromisoformat(data['extracted_at']) if isinstance(data.get('extracted_at'), str) else datetime.now()
        )

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "success": self.success_count,
            "failure": self.failure_count,
            "total": self.success_count + self.failure_count
        }



async def test_ar5iv_extractor():
    """测试 ar5iv 提取器"""
    from utils import setup_logging
    
    setup_logging(level="DEBUG")
    
    extractor = Ar5ivExtractor()
    
    # 测试论文
    test_id = "1706.03762"  # Attention Is All You Need
    
    content = await extractor.extract_paper(test_id, use_cache=False)
    
    if content:
        logger.info(f"\n{'='*50}")
        logger.info(f"标题: {content.title}")
        logger.info(f"作者: {', '.join(content.authors[:3])}...")
        logger.info(f"摘要: {truncate_text(content.abstract or '', 200)}")
        logger.info(f"章节: {len(content.sections)}")
        logger.info(f"图片: {len(content.figures)}")
        logger.info(f"表格: {len(content.tables)}")
        logger.info(f"公式: {len(content.equations)}")
        logger.info(f"参考文献: {len(content.references)}")
        
        # 显示章节结构
        logger.info("\n章节结构:")
        for sec in content.sections[:5]:
            logger.info(f"  - {sec.title} ({len(sec.paragraphs)} 段落)")
            for sub in sec.subsections[:2]:
                logger.info(f"    - {sub.title}")
        
        # 显示参考文献（带 arXiv ID 的）
        logger.info("\n参考文献 (arXiv):")
        for ref in content.references[:5]:
            if ref.arxiv_id:
                logger.info(f"  - [{ref.citation_key}] {ref.arxiv_id}")
    
    logger.info(f"\n统计: {extractor.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_ar5iv_extractor())