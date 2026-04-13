"""
ar5iv 内容提取模块
职责：从 ar5iv 页面提取论文完整内容
遵循 CleanRL 设计原则：单一职责、显式依赖、易于测试
"""
import asyncio
import re
import sys
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

import aiohttp
from bs4 import BeautifulSoup, Tag
from loguru import logger

from config import ArxivConfig, CacheConfig
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
)


class Ar5ivExtractor:
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
        retry_count: int = 0
    ) -> Optional[str]:
        """
        获取页面 HTML
        
        Args:
            session: aiohttp 会话
            url: 页面 URL
            retry_count: 当前重试次数
            
        Returns:
            HTML 内容或 None
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.read()
                    try:
                        return content.decode('utf-8')
                    except UnicodeDecodeError:
                        return content.decode('utf-8', errors='replace')
                        
                elif response.status == 404:
                    logger.warning(f"论文不存在于 ar5iv: {url}")
                    return None
                    
                elif response.status == 429:
                    wait_time = 120 * (retry_count + 1)
                    logger.warning(f"速率限制，等待 {wait_time} 秒: {url}")
                    await asyncio.sleep(wait_time)
                    if retry_count < self.config.max_retries:
                        return await self._fetch_page(session, url, retry_count + 1)
                else:
                    logger.warning(f"HTTP {response.status}: {url}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"请求超时: {url}")
            if retry_count < self.config.max_retries:
                await asyncio.sleep(10 * (retry_count + 1))
                return await self._fetch_page(session, url, retry_count + 1)
                
        except Exception:
            error_message = format_exception()
            logger.error(f"请求失败 {url}: {error_message}")
        
        return None
    
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
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Section]:
        """提取章节结构"""
        sections = []
        
        # 查找所有顶级章节
        for section in soup.select("section.ltx_section"):
            section_data = self._parse_section(section, level=2)
            if section_data:
                sections.append(section_data)
        
        return sections
    
    def _parse_section(self, elem: Tag, level: int = 2) -> Optional[Section]:
        """
        递归解析章节
        
        Args:
            elem: 章节元素
            level: 当前层级
            
        Returns:
            Section 对象或 None
        """
        # 提取标题
        title_elem = None
        for h_level in range(1, 7):
            title_elem = elem.select_one(f"h{h_level}.ltx_title")
            if title_elem:
                break
        
        if not title_elem:
            title_elem = elem.select_one(".ltx_title")
        
        if not title_elem:
            return None
        
        # 移除标签号
        for tag in title_elem.select(".ltx_tag"):
            tag.decompose()
        
        title = clean_text(title_elem.get_text())
        
        # 跳过参考文献和附录标题
        if re.match(r"^(references|bibliography|appendix|acknowledgement)", title, re.I):
            return None
        
        # Collect content in document order by iterating direct children
        ordered_content = []
        paragraphs = []
        figures = []
        tables = []
        equations = []

        for child in elem.children:
            if not hasattr(child, "name") or not child.name:
                continue
            classes = child.get("class") or []

            if "ltx_para" in classes:
                # Paragraph container — may hold multiple <p class="ltx_p">
                for para in child.find_all("p", class_="ltx_p"):
                    text = self._extract_para_with_math(para)
                    if text and len(text) > 10:
                        ordered_content.append({"type": "para", "data": text})
                        paragraphs.append(text)

            elif child.name == "figure":
                if "ltx_figure" in classes or "ltx_table" in classes:
                    if child.select_one("img"):
                        # Image figure
                        fig = self._parse_figure(child)
                        if fig:
                            ordered_content.append({"type": "figure", "data": fig.to_dict()})
                            figures.append(fig)
                    else:
                        # Table figure (table inside a <figure> wrapper)
                        tbl_elem = child.select_one("table.ltx_tabular")
                        if tbl_elem:
                            tbl = self._parse_table(tbl_elem)
                            if tbl:
                                # Grab caption from the figure wrapper
                                cap_elem = child.select_one("figcaption") or child.select_one(".ltx_caption")
                                if cap_elem and not tbl.caption:
                                    tbl.caption = re.sub(
                                        r"^Table\s*\d+[:.]\s*", "",
                                        clean_text(cap_elem.get_text()),
                                        flags=re.I,
                                    )
                                ordered_content.append({"type": "table", "data": tbl.to_dict()})
                                tables.append(tbl)

            elif "ltx_equation" in classes or "ltx_equationgroup" in classes:
                eq = self._parse_equation(child)
                if eq:
                    ordered_content.append({"type": "equation", "data": eq.to_dict()})
                    equations.append(eq)

            elif child.name == "table" and "ltx_tabular" in classes:
                # Bare table not wrapped in <figure>
                tbl = self._parse_table(child)
                if tbl:
                    ordered_content.append({"type": "table", "data": tbl.to_dict()})
                    tables.append(tbl)

        # Fallback: if no ordered content found via child iteration, use old deep-search approach
        if not ordered_content:
            for para_container in elem.find_all(class_="ltx_para", recursive=False):
                for para in para_container.find_all("p", class_="ltx_p"):
                    text = self._extract_para_with_math(para)
                    if text and len(text) > 10:
                        ordered_content.append({"type": "para", "data": text})
                        paragraphs.append(text)
            for fig_elem in elem.find_all("figure", class_="ltx_figure", recursive=False):
                fig = self._parse_figure(fig_elem)
                if fig:
                    ordered_content.append({"type": "figure", "data": fig.to_dict()})
                    figures.append(fig)
            for tbl_elem in elem.find_all("table", class_="ltx_tabular", recursive=False):
                tbl = self._parse_table(tbl_elem)
                if tbl:
                    ordered_content.append({"type": "table", "data": tbl.to_dict()})
                    tables.append(tbl)
            for eq_elem in elem.find_all(class_=["ltx_equation", "ltx_equationgroup"], recursive=False):
                eq = self._parse_equation(eq_elem)
                if eq:
                    ordered_content.append({"type": "equation", "data": eq.to_dict()})
                    equations.append(eq)

        # Subsections (always collected separately — they appear as <section> children)
        subsections = []
        for subsection in elem.select("section.ltx_subsection"):
            sub_data = self._parse_section(subsection, level=level + 1)
            if sub_data:
                subsections.append(sub_data)
        for subsubsection in elem.select("section.ltx_subsubsection"):
            sub_data = self._parse_section(subsubsection, level=level + 2)
            if sub_data:
                subsections.append(sub_data)

        return Section(
            title=title,
            level=level,
            paragraphs=paragraphs,
            subsections=subsections,
            figures=figures,
            tables=tables,
            equations=equations,
            ordered_content=ordered_content,
        )
    
    def _math_to_marker(self, math_node: Tag) -> str:
        """
        Convert a <math> element to a $...$ or $$...$$ LaTeX marker.

        Priority:
          1. alttext attribute  — LaTeXML always sets this
          2. <annotation encoding="application/x-tex"> — fallback inside <semantics>
          3. Empty string       — can't render without LaTeX source
        """
        latex = (math_node.get("alttext") or "").strip()

        if not latex:
            ann = math_node.find(
                "annotation", attrs={"encoding": "application/x-tex"}
            )
            if ann:
                latex = ann.get_text().strip()

        if not latex:
            return ""

        display = (math_node.get("display") or "inline").lower()
        return f" $${latex}$$ " if display == "block" else f"${latex}$"

    # CSS classes on <span> wrappers that are purely math containers —
    # we skip their non-math text children (those are visual/ARIA rendering artifacts)
    _MATH_WRAPPER_CLASSES = {"ltx_Math", "ltx_eqn_cell", "ltx_eqn_display"}
    # CSS classes on tags whose entire subtree is non-semantic (equation numbers, labels)
    _SKIP_CLASSES = {"ltx_tag", "ltx_tag_equation", "ltx_tag_ref", "ltx_rule"}

    def _extract_para_with_math(self, elem: Tag) -> str:
        """
        Extract paragraph text, preserving math as $...$ / $$...$$ markers.

        Handles the common ar5iv HTML pattern where <math> is wrapped inside
        <span class="ltx_Math">. That span may also contain visual rendering
        artifacts (plain text, aria-hidden spans) — those are skipped so that
        only the clean LaTeX marker is emitted.
        """
        from bs4 import NavigableString

        parts: List[str] = []
        for node in elem.children:
            if isinstance(node, NavigableString):
                parts.append(str(node))
                continue

            if not hasattr(node, "name") or not node.name:
                continue

            node_classes = set(node.get("class") or [])

            # ── Direct <math> element ──────────────────────────────────────
            if node.name == "math":
                parts.append(self._math_to_marker(node))

            # ── <span class="ltx_Math"> (and similar wrappers) ────────────
            # These wrap a <math> but also carry visual/ARIA text nodes that
            # are rendering artifacts. Go straight to the inner <math>.
            elif node_classes & self._MATH_WRAPPER_CLASSES:
                math_node = node.find("math")
                if math_node:
                    parts.append(self._math_to_marker(math_node))
                # If no inner <math> found, skip — the wrapper has no useful text

            # ── Tags that are purely decorative (equation numbers, etc.) ──
            elif node_classes & self._SKIP_CLASSES:
                pass  # intentionally dropped

            # ── Everything else: recurse (strong, em, a, sub, sup, …) ─────
            else:
                parts.append(self._extract_para_with_math(node))

        text = "".join(parts)
        text = re.sub(r"[ \t]+", " ", text).strip()
        return text

    def _parse_figure(self, fig: Tag) -> Optional[Figure]:
        """解析图片"""
        img = fig.select_one("img")
        if not img:
            return None
        
        src = img.get("src", "")
        # 转换为完整 URL
        if src.startswith("/"):
            src = f"https://ar5iv.labs.arxiv.org{src}"
        
        caption_elem = fig.select_one("figcaption.ltx_caption")
        caption = clean_text(caption_elem.get_text()) if caption_elem else None
        
        # 移除 "Figure X:" 前缀
        if caption:
            caption = re.sub(r"^Figure\s*\d+[:.]\s*", "", caption, flags=re.I)
        
        label = fig.get("id", None)
        
        return Figure(
            src=src,
            alt=img.get("alt"),
            caption=caption,
            label=label
        )
    
    def _parse_table(self, table: Tag) -> Optional[Table]:
        """解析表格"""
        # 提取标题
        caption = None
        caption_elem = table.find_previous("figcaption") or table.find_previous(class_="ltx_caption")
        if caption_elem:
            caption = clean_text(caption_elem.get_text())
            # 移除 "Table X:" 前缀
            caption = re.sub(r"^Table\s*\d+[:.]\s*", "", caption, flags=re.I)
        
        # 提取表头
        headers = []
        thead = table.select_one("thead")
        if thead:
            for th in thead.select("th, td"):
                headers.append(clean_text(th.get_text()))
        
        # 提取数据行
        rows = []
        tbody = table.select_one("tbody") or table
        for tr in tbody.select("tr"):
            row = [clean_text(td.get_text()) for td in tr.select("td")]
            if row and any(row):  # 至少有一个非空单元格
                rows.append(row)
        
        if headers or rows:
            return Table(
                caption=caption,
                headers=headers,
                rows=rows
            )
        
        return None
    
    def _parse_equation(self, eq: Tag) -> Optional[Equation]:
        """解析数学公式"""
        math_elem = eq.select_one("math")
        if math_elem:
            latex = math_elem.get("alttext", "")
            mathml = str(math_elem)
            
            # 提取标签
            label = None
            tag = eq.select_one(".ltx_tag")
            if tag:
                label = clean_text(tag.get_text())
            
            return Equation(
                latex=latex,
                mathml=mathml[:2000] if len(mathml) > 2000 else mathml,
                label=label,
                inline=False
            )
        
        return None
    
    def _extract_figures(self, soup: BeautifulSoup) -> List[Figure]:
        """提取所有图片"""
        figures = []
        
        for fig in soup.select("figure.ltx_figure"):
            figure = self._parse_figure(fig)
            if figure and figure not in figures:
                figures.append(figure)
        
        return figures
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Table]:
        """提取所有表格"""
        tables = []
        
        for table in soup.select("table.ltx_tabular"):
            table_data = self._parse_table(table)
            if table_data:
                tables.append(table_data)
        
        return tables
    
    def _extract_equations(self, soup: BeautifulSoup) -> List[Equation]:
        """提取数学公式"""
        equations = []
        
        for eq in soup.select(".ltx_equation, .ltx_equationgroup"):
            equation = self._parse_equation(eq)
            if equation:
                equations.append(equation)
        
        return equations
    
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
    
    def _extract_full_text(self, sections: List[Section]) -> str:
        """从章节提取完整文本"""
        texts = []
        
        def extract_section_text(section: Section):
            prefix = "#" * section.level + " "
            texts.append(prefix + section.title)
            texts.append("")
            
            for para in section.paragraphs:
                texts.append(para)
                texts.append("")
            
            for sub in section.subsections:
                extract_section_text(sub)
        
        for section in sections:
            extract_section_text(section)
        
        return "\n".join(texts)
    
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
            full_text = self._extract_full_text(sections)
            
            return Ar5ivContent(
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
            
        except Exception:
            error_message = format_exception()
            logger.error(f"解析 HTML 失败 {paper_id}: {error_message}")
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
        # 检查缓存
        if use_cache and self.cache_config.enabled:
            cache_file = self.cache_config.get_ar5iv_cache_file(arxiv_id)
            cached_data = await load_json(cache_file)
            if cached_data:
                logger.debug(f"使用缓存: {arxiv_id}")
                # 重建对象
                return self._rebuild_content(cached_data)
        
        url = build_ar5iv_url(arxiv_id)
        logger.info(f"提取 ar5iv 内容: {arxiv_id}")
        
        async with aiohttp.ClientSession() as session:
            html = await self._fetch_page(session, url)
            
            if not html:
                self.failure_count += 1
                return None
            
            content = self.parse_html(html, arxiv_id)
            
            if content:
                # 保存到缓存
                if self.cache_config.enabled:
                    cache_file = self.cache_config.get_ar5iv_cache_file(arxiv_id)
                    await save_json(content.to_dict(), cache_file)
                
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