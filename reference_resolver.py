"""
参考文献解析模块
职责：解析参考文献，提取或搜索 arXiv ID
遵循 CleanRL 设计原则：单一职责、显式依赖、易于测试
"""
import asyncio
import re
import sys
import traceback
from typing import List, Optional, Dict, Any, Tuple

from loguru import logger

from config import ReferenceConfig
from models import Reference, ArxivMetadata
from arxiv_api import ArxivApiClient
from utils import (
    extract_arxiv_ids,
    calculate_similarity,
    format_exception,
    clean_text,
)


class ReferenceResolver:
    """
    参考文献解析器
    
    负责：
    1. 从参考文献文本中提取 arXiv ID
    2. 对于没有 arXiv ID 的参考文献，通过 arXiv API 搜索
    3. 验证和去重
    """
    
    def __init__(
        self,
        config: Optional[ReferenceConfig] = None,
        arxiv_client: Optional[ArxivApiClient] = None,
    ):
        """
        初始化解析器
        
        Args:
            config: 参考文献配置
            arxiv_client: arXiv API 客户端
        """
        self.config = config or ReferenceConfig()
        self.arxiv_client = arxiv_client or ArxivApiClient()
        
        # 统计
        self.total_refs = 0
        self.direct_match = 0
        self.search_match = 0
        self.no_match = 0
    
    def extract_arxiv_id_from_ref(self, ref: Reference) -> Optional[str]:
        """
        从参考文献中提取 arXiv ID
        
        Args:
            ref: 参考文献对象
            
        Returns:
            arXiv ID 或 None
        """
        # 首先检查是否已有
        if ref.arxiv_id:
            return ref.arxiv_id
        
        # 从原始文本提取
        ids = extract_arxiv_ids(ref.raw_text)
        if ids:
            return ids[0]
        
        # 从 URL 提取
        if ref.url:
            ids = extract_arxiv_ids(ref.url)
            if ids:
                return ids[0]
        
        return None
    
    def _extract_title_from_ref(self, ref: Reference) -> Optional[str]:
        """
        从参考文献中提取标题
        
        Args:
            ref: 参考文献对象
            
        Returns:
            标题或 None
        """
        if ref.title:
            return ref.title
        
        text = ref.raw_text
        
        # 方法1: 引号内的文本
        match = re.search(r'"([^"]+)"', text)
        if match:
            return match.group(1)
        
        match = re.search(r"'([^']+)'", text)
        if match:
            return match.group(1)
        
        # 方法2: 作者. (年份). 标题. 格式
        match = re.search(r'\.\s*\(?\d{4}\)?[\.:]?\s*(.+?)\.\s*(?:In|arXiv|Proceedings|Journal)', text)
        if match:
            return match.group(1).strip()
        
        # 方法3: 移除作者和年份，取第一个句子
        text = re.sub(r'^\[\d+\]\s*', '', text)
        text = re.sub(r'^[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*(?:,?\s*(?:and|&)\s*[A-Z][a-z]+)*\.\s*', '', text)
        text = re.sub(r'^\(?\d{4}\)?[\.:]?\s*', '', text)
        
        parts = text.split('.')
        if parts and len(parts[0]) > 10:
            return parts[0].strip()
        
        return None
    
    async def resolve_reference(self, ref: Reference) -> Reference:
        """
        解析单个参考文献
        
        Args:
            ref: 参考文献对象
            
        Returns:
            更新后的参考文献对象
        """
        self.total_refs += 1
        
        # 步骤1: 直接提取 arXiv ID
        arxiv_id = self.extract_arxiv_id_from_ref(ref)
        if arxiv_id:
            ref.arxiv_id = arxiv_id
            self.direct_match += 1
            logger.debug(f"直接匹配: {arxiv_id}")
            return ref
        
        # 步骤2: 如果配置允许，通过 arXiv API 搜索
        if self.config.search_missing_ids:
            title = self._extract_title_from_ref(ref)
            
            if title and len(title) > 15:
                try:
                    results = await self.arxiv_client.search_by_title(
                        title,
                        max_results=self.config.max_search_results
                    )
                    
                    for metadata in results:
                        similarity = calculate_similarity(title, metadata.title)
                        
                        if similarity >= self.config.min_title_similarity:
                            ref.arxiv_id = metadata.arxiv_id
                            ref.title = metadata.title
                            self.search_match += 1
                            logger.debug(f"搜索匹配: {metadata.arxiv_id} (相似度: {similarity:.2f})")
                            return ref
                    
                except Exception:
                    error_message = format_exception()
                    logger.warning(f"搜索失败: {error_message}")
        
        self.no_match += 1
        return ref
    
    async def resolve_references(
        self,
        references: List[Reference],
        max_concurrent: int = 2
    ) -> List[Reference]:
        """
        批量解析参考文献
        
        Args:
            references: 参考文献列表
            max_concurrent: 最大并发数
            
        Returns:
            更新后的参考文献列表
        """
        logger.info(f"开始解析 {len(references)} 个参考文献")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_resolve(ref: Reference) -> Reference:
            async with semaphore:
                return await self.resolve_reference(ref)
        
        tasks = [bounded_resolve(ref) for ref in references]
        resolved = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = []
        for i, result in enumerate(resolved):
            if isinstance(result, Exception):
                logger.error(f"解析参考文献 {i} 失败: {result}")
                results.append(references[i])
            else:
                results.append(result)
        
        logger.info(
            f"参考文献解析完成: "
            f"直接匹配={self.direct_match}, "
            f"搜索匹配={self.search_match}, "
            f"未匹配={self.no_match}"
        )
        
        return results
    
    def get_arxiv_references(self, references: List[Reference]) -> List[Reference]:
        """获取有 arXiv ID 的参考文献"""
        return [ref for ref in references if ref.arxiv_id]
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "total": self.total_refs,
            "direct_match": self.direct_match,
            "search_match": self.search_match,
            "no_match": self.no_match,
            "match_rate": (self.direct_match + self.search_match) / self.total_refs if self.total_refs > 0 else 0
        }


class ReferenceExtractor:
    """
    参考文献信息提取器
    
    从参考文献文本中提取结构化信息
    """
    
    VENUE_PATTERNS = [
        r'(NeurIPS|NIPS)\s*\d{4}',
        r'(ICML)\s*\d{4}',
        r'(ICLR)\s*\d{4}',
        r'(CVPR|ICCV|ECCV)\s*\d{4}',
        r'(ACL|EMNLP|NAACL)\s*\d{4}',
        r'(AAAI|IJCAI)\s*\d{4}',
        r'(Nature|Science|Cell)',
        r'(IEEE|ACM)\s+\w+',
        r'Proceedings\s+of\s+the\s+.+?(?=\.|,|$)',
        r'arXiv\s+preprint',
    ]
    
    def extract_authors(self, text: str) -> List[str]:
        """提取作者列表"""
        text = re.sub(r'^\[\d+\]\s*', '', text)
        
        match = re.match(
            r'^([A-Z][a-z]+(?:,\s*[A-Z]\.?)+(?:,\s*[A-Z][a-z]+(?:,\s*[A-Z]\.?)+)*(?:,?\s*(?:and|&)\s*[A-Z][a-z]+(?:,\s*[A-Z]\.?)+)?)\.',
            text
        )
        if match:
            author_str = match.group(1)
            authors = re.split(r',\s*(?:and|&)\s*|,\s*', author_str)
            return [a.strip() for a in authors if a.strip()]
        
        return []
    
    def extract_venue(self, text: str) -> Optional[str]:
        """提取期刊/会议名称"""
        for pattern in self.VENUE_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0)
        return None
    
    def extract_info(self, ref: Reference) -> Reference:
        """提取参考文献的结构化信息"""
        text = ref.raw_text
        
        if not ref.authors:
            ref.authors = self.extract_authors(text)
        
        if not ref.year:
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                ref.year = year_match.group(0)
        
        if not ref.venue:
            ref.venue = self.extract_venue(text)
        
        return ref


async def test_reference_resolver():
    """测试参考文献解析器"""
    from utils import setup_logging
    
    setup_logging(level="DEBUG")
    
    test_refs = [
        Reference(
            raw_text="[1] Vaswani et al. Attention is all you need. arXiv:1706.03762, 2017.",
            citation_key="1"
        ),
        Reference(
            raw_text='[2] Devlin et al. "BERT: Pre-training of Deep Bidirectional Transformers". NAACL 2019.',
            citation_key="2"
        ),
        Reference(
            raw_text="[3] Brown et al. Language models are few-shot learners. NeurIPS 2020. arXiv:2005.14165",
            citation_key="3"
        ),
    ]
    
    resolver = ReferenceResolver()
    resolved = await resolver.resolve_references(test_refs)
    
    for ref in resolved:
        logger.info(f"[{ref.citation_key}] arXiv: {ref.arxiv_id or 'N/A'}")
    
    logger.info(f"统计: {resolver.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_reference_resolver())