"""LaTeXML/ar5iv semantic parsing components, preserving historical extractor API."""
from __future__ import annotations
import re
from typing import List
from bs4 import BeautifulSoup
from models import Reference
from utils import clean_text, extract_arxiv_ids

class ReferencesMixin:
    def _extract_references(self, soup: BeautifulSoup) -> List[Reference]:
        """提取参考文献"""
        references = []
        
        for ref in soup.select(".ltx_bibitem"):
            raw_text = clean_text(ref.get_text())
            if not raw_text:
                continue
            
            # 提取引用键
            citation_key = None
            tag = ref.select_one(".ltx_tag")
            if tag:
                citation_key = clean_text(tag.get_text())
                # 移除引用键
                raw_text = re.sub(r"^\[\d+\]\s*", "", raw_text)
                raw_text = re.sub(r"^\[[\w\-]+\]\s*", "", raw_text)
            
            # 尝试提取 arXiv ID
            arxiv_ids = extract_arxiv_ids(raw_text)
            arxiv_id = arxiv_ids[0] if arxiv_ids else None
            
            # 尝试提取 DOI
            doi_match = re.search(r'10\.\d{4,}/[^\s]+', raw_text)
            doi = doi_match.group(0).rstrip('.,;') if doi_match else None
            
            # 尝试提取 URL
            url_match = re.search(r'https?://[^\s<>"]+', raw_text)
            url = url_match.group(0).rstrip('.,;)') if url_match else None
            
            # 尝试提取年份
            year_match = re.search(r'\b(19|20)\d{2}\b', raw_text)
            year = year_match.group(0) if year_match else None
            
            # 尝试提取标题（引号内的文本）
            title_match = re.search(r'"([^"]+)"', raw_text)
            if not title_match:
                title_match = re.search(r"'([^']+)'", raw_text)
            title = title_match.group(1) if title_match else None
            
            references.append(Reference(
                raw_text=raw_text,
                title=title,
                year=year,
                arxiv_id=arxiv_id,
                doi=doi,
                url=url,
                citation_key=citation_key
            ))
        
        return references

