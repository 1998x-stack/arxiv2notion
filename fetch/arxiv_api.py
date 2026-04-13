"""
arXiv API 交互模块
职责：通过 arXiv API 获取论文元数据和搜索论文
遵循 CleanRL 设计原则：单一职责、显式依赖、易于测试
"""
import asyncio
import re
import sys
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree as ET

import aiohttp
from loguru import logger

from config import ArxivConfig, CacheConfig
from models import ArxivMetadata, Author
from utils import (
    save_json,
    load_json,
    normalize_arxiv_id,
    build_arxiv_api_url,
    build_arxiv_search_url,
    format_exception,
    clean_text,
)


# arXiv API XML 命名空间
ARXIV_NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom'
}


class ArxivApiClient:
    """
    arXiv API 客户端
    
    负责与 arXiv API 交互，获取论文元数据和搜索论文。
    遵循 arXiv API 使用规范（最少 3 秒请求间隔）。
    """
    
    def __init__(
        self,
        config: Optional[ArxivConfig] = None,
        cache_config: Optional[CacheConfig] = None,
    ):
        """
        初始化客户端
        
        Args:
            config: arXiv API 配置
            cache_config: 缓存配置
        """
        self.config = config or ArxivConfig()
        self.cache_config = cache_config or CacheConfig()
        
        self._last_request_time: Optional[datetime] = None
        
        # 统计
        self.request_count = 0
        self.cache_hits = 0
        self.errors = 0
    
    async def _ensure_rate_limit(self):
        """确保遵守速率限制"""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self.config.request_delay:
                await asyncio.sleep(self.config.request_delay - elapsed)
        
        self._last_request_time = datetime.now()
    
    async def _fetch_xml(
        self,
        session: aiohttp.ClientSession,
        url: str,
        retry_count: int = 0
    ) -> Optional[str]:
        """
        获取 XML 响应
        
        Args:
            session: aiohttp 会话
            url: 请求 URL
            retry_count: 当前重试次数
            
        Returns:
            XML 字符串或 None
        """
        await self._ensure_rate_limit()
        
        headers = {
            "User-Agent": "ar5iv-to-notion/1.0 (Academic Research Tool)",
            "Accept": "application/atom+xml",
        }
        
        try:
            self.request_count += 1
            
            async with session.get(url, headers=headers, timeout=self.config.timeout) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 503:
                    # 服务暂时不可用
                    wait_time = 30 * (retry_count + 1)
                    logger.warning(f"arXiv 服务暂时不可用，等待 {wait_time} 秒")
                    await asyncio.sleep(wait_time)
                    if retry_count < self.config.max_retries:
                        return await self._fetch_xml(session, url, retry_count + 1)
                else:
                    logger.warning(f"arXiv API HTTP {response.status}: {url}")
                    self.errors += 1
                    
        except asyncio.TimeoutError:
            logger.warning(f"arXiv API 请求超时: {url}")
            self.errors += 1
            if retry_count < self.config.max_retries:
                await asyncio.sleep(10 * (retry_count + 1))
                return await self._fetch_xml(session, url, retry_count + 1)
                
        except Exception:
            error_message = format_exception()
            logger.error(f"arXiv API 请求失败 {url}: {error_message}")
            self.errors += 1
        
        return None
    
    def _parse_entry(self, entry: ET.Element) -> Optional[ArxivMetadata]:
        """
        解析单个条目
        
        Args:
            entry: XML 条目元素
            
        Returns:
            ArxivMetadata 或 None
        """
        try:
            # 提取 ID
            id_elem = entry.find('atom:id', ARXIV_NS)
            if id_elem is None or id_elem.text is None:
                return None
            
            arxiv_id = id_elem.text.split('/')[-1]
            arxiv_id = normalize_arxiv_id(arxiv_id)
            
            # 提取标题
            title_elem = entry.find('atom:title', ARXIV_NS)
            title = clean_text(title_elem.text) if title_elem is not None and title_elem.text else "Unknown Title"
            
            # 提取摘要
            summary_elem = entry.find('atom:summary', ARXIV_NS)
            abstract = clean_text(summary_elem.text) if summary_elem is not None and summary_elem.text else ""
            
            # 提取作者
            authors = []
            for author_elem in entry.findall('atom:author', ARXIV_NS):
                name_elem = author_elem.find('atom:name', ARXIV_NS)
                if name_elem is not None and name_elem.text:
                    affiliation_elem = author_elem.find('arxiv:affiliation', ARXIV_NS)
                    affiliation = affiliation_elem.text if affiliation_elem is not None else None
                    authors.append(Author(
                        name=clean_text(name_elem.text),
                        affiliation=affiliation
                    ))
            
            # 提取分类
            categories = []
            primary_category = ""
            for cat in entry.findall('atom:category', ARXIV_NS):
                term = cat.get('term', '')
                if term:
                    categories.append(term)
            
            primary_cat = entry.find('arxiv:primary_category', ARXIV_NS)
            if primary_cat is not None:
                primary_category = primary_cat.get('term', '')
            elif categories:
                primary_category = categories[0]
            
            # 提取日期
            published_elem = entry.find('atom:published', ARXIV_NS)
            updated_elem = entry.find('atom:updated', ARXIV_NS)
            
            def parse_date(elem):
                if elem is not None and elem.text:
                    try:
                        return datetime.fromisoformat(elem.text.replace('Z', '+00:00'))
                    except:
                        pass
                return datetime.now()
            
            published = parse_date(published_elem)
            updated = parse_date(updated_elem)
            
            # 提取 DOI
            doi = None
            doi_elem = entry.find('arxiv:doi', ARXIV_NS)
            if doi_elem is not None:
                doi = doi_elem.text
            
            # 提取期刊引用
            journal_ref = None
            journal_elem = entry.find('arxiv:journal_ref', ARXIV_NS)
            if journal_elem is not None:
                journal_ref = journal_elem.text
            
            # 提取评论
            comment = None
            comment_elem = entry.find('arxiv:comment', ARXIV_NS)
            if comment_elem is not None:
                comment = comment_elem.text
            
            # 构建 PDF URL
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            return ArxivMetadata(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                doi=doi,
                journal_ref=journal_ref,
                comment=comment,
                pdf_url=pdf_url
            )
            
        except Exception:
            error_message = format_exception()
            logger.error(f"解析 arXiv 条目失败: {error_message}")
            return None
    
    async def get_paper(
        self,
        arxiv_id: str,
        use_cache: bool = True
    ) -> Optional[ArxivMetadata]:
        """
        获取单篇论文元数据
        
        Args:
            arxiv_id: arXiv ID
            use_cache: 是否使用缓存
            
        Returns:
            ArxivMetadata 或 None
        """
        arxiv_id = normalize_arxiv_id(arxiv_id)
        
        # 检查缓存
        if use_cache and self.cache_config.enabled:
            cache_file = self.cache_config.get_arxiv_cache_file(arxiv_id)
            cached_data = await load_json(cache_file)
            if cached_data:
                self.cache_hits += 1
                logger.debug(f"使用缓存: {arxiv_id}")
                # 重建对象
                cached_data['authors'] = [Author(**a) if isinstance(a, dict) else Author(name=a) for a in cached_data.get('authors', [])]
                cached_data['published'] = datetime.fromisoformat(cached_data['published']) if isinstance(cached_data['published'], str) else cached_data['published']
                cached_data['updated'] = datetime.fromisoformat(cached_data['updated']) if isinstance(cached_data['updated'], str) else cached_data['updated']
                return ArxivMetadata(**cached_data)
        
        logger.info(f"获取 arXiv 元数据: {arxiv_id}")
        
        url = build_arxiv_api_url(arxiv_id)
        
        async with aiohttp.ClientSession() as session:
            xml_content = await self._fetch_xml(session, url)
            
            if not xml_content:
                return None
            
            try:
                root = ET.fromstring(xml_content)
                entry = root.find('atom:entry', ARXIV_NS)
                
                if entry is None:
                    logger.warning(f"未找到论文: {arxiv_id}")
                    return None
                
                metadata = self._parse_entry(entry)
                
                # 保存到缓存
                if metadata and self.cache_config.enabled:
                    cache_file = self.cache_config.get_arxiv_cache_file(arxiv_id)
                    await save_json(metadata.to_dict(), cache_file)
                
                return metadata
                
            except ET.ParseError:
                error_message = format_exception()
                logger.error(f"解析 arXiv XML 失败 {arxiv_id}: {error_message}")
                return None
    
    async def search_papers(
        self,
        query: str,
        max_results: int = 5
    ) -> List[ArxivMetadata]:
        """
        搜索论文
        
        Args:
            query: 搜索查询（标题、作者等）
            max_results: 最大结果数
            
        Returns:
            ArxivMetadata 列表
        """
        logger.info(f"搜索 arXiv: {query[:50]}...")
        
        url = build_arxiv_search_url(query, max_results)
        
        async with aiohttp.ClientSession() as session:
            xml_content = await self._fetch_xml(session, url)
            
            if not xml_content:
                return []
            
            try:
                root = ET.fromstring(xml_content)
                results = []
                
                for entry in root.findall('atom:entry', ARXIV_NS):
                    metadata = self._parse_entry(entry)
                    if metadata:
                        results.append(metadata)
                        
                        # 缓存搜索结果
                        if self.cache_config.enabled:
                            cache_file = self.cache_config.get_arxiv_cache_file(metadata.arxiv_id)
                            await save_json(metadata.to_dict(), cache_file)
                
                logger.debug(f"搜索返回 {len(results)} 个结果")
                return results
                
            except ET.ParseError:
                error_message = format_exception()
                logger.error(f"解析 arXiv 搜索结果失败: {error_message}")
                return []
    
    async def search_by_title(
        self,
        title: str,
        max_results: int = 3
    ) -> List[ArxivMetadata]:
        """
        按标题搜索论文
        
        Args:
            title: 论文标题
            max_results: 最大结果数
            
        Returns:
            ArxivMetadata 列表
        """
        # 清理标题用于搜索
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        # 使用标题字段搜索
        query = f'ti:"{clean_title}"'
        
        return await self.search_papers(query, max_results)
    
    async def get_papers_batch(
        self,
        arxiv_ids: List[str],
        use_cache: bool = True
    ) -> Dict[str, ArxivMetadata]:
        """
        批量获取论文元数据
        
        Args:
            arxiv_ids: arXiv ID 列表
            use_cache: 是否使用缓存
            
        Returns:
            ID -> ArxivMetadata 映射
        """
        results = {}
        
        for arxiv_id in arxiv_ids:
            metadata = await self.get_paper(arxiv_id, use_cache)
            if metadata:
                results[arxiv_id] = metadata
        
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "requests": self.request_count,
            "cache_hits": self.cache_hits,
            "errors": self.errors
        }


async def test_arxiv_api():
    """测试 arXiv API 客户端"""
    from utils import setup_logging
    
    setup_logging(level="DEBUG")
    
    client = ArxivApiClient()
    
    # 测试获取单篇论文
    logger.info("测试获取论文...")
    metadata = await client.get_paper("1706.03762")  # Attention Is All You Need
    
    if metadata:
        logger.info(f"标题: {metadata.title}")
        logger.info(f"作者: {[str(a) for a in metadata.authors[:3]]}")
        logger.info(f"分类: {metadata.primary_category}")
        logger.info(f"摘要: {metadata.abstract[:200]}...")
    
    # 测试搜索
    logger.info("\n测试搜索...")
    results = await client.search_by_title("Attention Is All You Need", max_results=3)
    
    for r in results:
        logger.info(f"  - {r.arxiv_id}: {r.title[:50]}...")
    
    logger.info(f"\n统计: {client.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_arxiv_api())