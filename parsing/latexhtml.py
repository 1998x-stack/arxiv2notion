"""LaTeXML/ar5iv semantic parsing components, preserving historical extractor API."""
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit
from ipaddress import ip_address
from typing import List, Optional
from bs4 import BeautifulSoup
from loguru import logger
from config import ArxivConfig
from domain.paper_document import assess_quality
from models import Ar5ivContent
from utils import build_ar5iv_url, clean_text, format_exception, normalize_arxiv_id

from parsing.mathematics import MathematicsMixin
from parsing.figures import FiguresMixin
from parsing.tables import TablesMixin
from parsing.references import ReferencesMixin
from parsing.semantic_blocks import SemanticBlocksMixin


class Ar5ivHTMLParser(SemanticBlocksMixin, MathematicsMixin, FiguresMixin, TablesMixin, ReferencesMixin):
    """Pure HTML-to-Ar5ivContent adapter, with no HTTP, cache or Notion writes."""

    def __init__(self, config=None):
        self.config = config or ArxivConfig()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取论文标题"""
        # 方法1: ltx_title 类
        title_elem = soup.select_one("h1.ltx_title")
        if title_elem:
            # 移除可能的标签号
            for tag in title_elem.select(".ltx_tag"):
                tag.decompose()
            return clean_text(title_elem.get_text())
        
        # 方法2: title 标签
        title_elem = soup.select_one("title")
        if title_elem:
            text = title_elem.get_text()
            text = re.sub(r"\s*[-|]\s*ar5iv.*$", "", text, flags=re.I)
            return clean_text(text)
        
        return "Unknown Title"

    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """提取作者列表"""
        authors = []
        
        # 方法1: ltx_personname
        for person in soup.select(".ltx_personname"):
            name = clean_text(person.get_text())
            if name and len(name) > 1 and name not in authors:
                authors.append(name)
        
        # 方法2: ltx_author
        if not authors:
            for author in soup.select(".ltx_author"):
                name = clean_text(author.get_text())
                if name and len(name) > 1 and name not in authors:
                    authors.append(name)
        
        return authors

    def _extract_affiliations(self, soup: BeautifulSoup) -> List[str]:
        """提取单位列表"""
        affiliations = []
        
        for contact in soup.select(".ltx_contact"):
            text = clean_text(contact.get_text())
            if text and "@" not in text and text not in affiliations:
                affiliations.append(text)
        
        return affiliations

    def _extract_abstract(self, soup: BeautifulSoup) -> Optional[str]:
        """提取摘要"""
        abstract_elem = soup.select_one(".ltx_abstract")
        if abstract_elem:
            # 移除标题
            title = abstract_elem.select_one(".ltx_title")
            if title:
                title.decompose()
            
            # 获取段落文本
            paragraphs = abstract_elem.select(".ltx_p")
            if paragraphs:
                return clean_text(" ".join(p.get_text() for p in paragraphs))
            
            return clean_text(abstract_elem.get_text())
        
        return None

    def parse_html(self, html: str, paper_id: str) -> Optional[Ar5ivContent]:
        """
        解析 HTML 提取论文内容
        
        Args:
            html: 页面 HTML
            paper_id: 论文 ID
            
        Returns:
            Ar5ivContent 对象或 None
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            
            title = self._extract_title(soup)
            authors = self._extract_authors(soup)
            affiliations = self._extract_affiliations(soup)
            abstract = self._extract_abstract(soup)
            sections = self._extract_sections(soup)
            figures = self._extract_figures(soup)
            tables = self._extract_tables(soup)
            equations = self._extract_equations(soup)
            references = self._extract_references(soup)
            base_url = self.config.ar5iv_base_url.rstrip("/") + "/" + normalize_arxiv_id(paper_id)
            def absolute(src):
                if not src:
                    return ""
                try:
                    resolved = urljoin(base_url, src)
                    parts = urlsplit(resolved)
                except ValueError:
                    return ""
                if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
                    return ""
                if parts.hostname == "localhost" or parts.hostname.endswith((".localhost", ".local")):
                    return ""
                try:
                    if not ip_address(parts.hostname).is_global:
                        return ""
                except ValueError:
                    pass  # DNS name, not an IP literal
                return resolved
            for figure in figures:
                figure.src = absolute(figure.src)
            def normalize_sections(items):
                for sec in items:
                    for figure in sec.figures:
                        figure.src = absolute(figure.src)
                    for item in sec.ordered_content:
                        if item.get("type") == "figure" and isinstance(item.get("data"), dict):
                            item["data"]["src"] = absolute(item["data"].get("src", ""))
                    normalize_sections(sec.subsections)
            normalize_sections(sections)
            full_text = self._extract_full_text(sections)

            content = Ar5ivContent(
                paper_id=paper_id,
                title=title,
                authors=authors,
                affiliations=affiliations,
                abstract=abstract,
                sections=sections,
                figures=figures,
                tables=tables,
                equations=equations,
                references=references,
                full_text=full_text,
            )
            if assess_quality(content).status == "unavailable":
                logger.warning(f"ar5iv returned no usable abstract or body: {paper_id}")
                return None
            return content

        except Exception:
            error_message = format_exception()
            logger.error(f"解析 HTML 失败 {paper_id}: {error_message}")
            return None

