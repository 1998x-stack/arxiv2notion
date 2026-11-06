"""LaTeXML/ar5iv semantic parsing components, preserving historical extractor API."""
from __future__ import annotations
import re
from typing import List, Optional, Any
from bs4 import BeautifulSoup, Tag
from models import Section
from utils import clean_text

class SemanticBlocksMixin:
    def _extract_sections(self, soup: BeautifulSoup) -> List[Section]:
        """提取章节结构"""
        sections = []
        
        # 查找所有顶级章节
        for section in soup.select("section.ltx_section, section.ltx_appendix"):
            # A section nested in another top-level section is handled recursively.
            if section.find_parent("section", class_=["ltx_section", "ltx_appendix"]):
                continue
            section_data = self._parse_section(section, level=2)
            if section_data:
                sections.append(section_data)
        
        return sections

    def _parse_section(self, elem: Tag, level: int = 2) -> Optional[Section]:
        """Parse only this section's own body, preserving nested container order.

        LaTeXML wraps content in ltx_para, theorem, proof, lists and other
        intermediate containers. Descend into those, but stop at child
        sections and at every emitted semantic block to prevent duplicates.
        """
        title_elem = next(
            (candidate for candidate in elem.select(".ltx_title")
             if candidate.find_parent("section") is elem),
            None,
        )
        if title_elem is None:
            title_elem = next(
                (candidate for candidate in elem.find_all(re.compile(r"^h[1-6]$"))
                 if candidate.find_parent("section") is elem),
                None,
            )
        if title_elem is None:
            return None

        # Work on a clone: deleting section-number tags must not modify the
        # document DOM used by other extraction passes.
        title_copy = BeautifulSoup(str(title_elem), "lxml")
        for tag in title_copy.select(".ltx_tag"):
            tag.decompose()
        title = clean_text(title_copy.get_text(" ", strip=True))
        if not title or re.match(r"^(references|bibliography)\b", title, re.I):
            return None

        ordered_content = []
        paragraphs = []
        figures = []
        tables = []
        equations = []

        def emit(kind: str, value: Any) -> None:
            if kind == "para":
                if value:
                    paragraphs.append(value)
                    ordered_content.append({"type": "para", "data": value})
            elif kind == "figure" and value:
                figures.append(value)
                ordered_content.append({"type": "figure", "data": value.to_dict()})
            elif kind == "table" and value:
                tables.append(value)
                ordered_content.append({"type": "table", "data": value.to_dict()})
            elif kind == "equation" and value:
                equations.append(value)
                ordered_content.append({"type": "equation", "data": value.to_dict()})

        def visit(node: Tag) -> None:
            if node is not elem and node.name == "section":
                return
            if node.name in ("script", "style", "nav", "footer"):
                return
            classes = set(node.get("class") or ())
            if node.get("aria-hidden") == "true" or classes.intersection(
                {"ltx_title", "ltx_bibliography", "ltx_abstract",
                 "ltx_authors", "ltx_caption", "ltx_note"}
            ):
                return
            if node.name == "p":
                emit("para", self._extract_para_with_math(node))
                return
            if node.name == "figure" or classes.intersection({"ltx_figure", "ltx_table"}):
                table = node.select_one("table.ltx_tabular")
                if table:
                    emit("table", self._parse_table(table))
                elif node.select_one("img"):
                    for figure in self._parse_figure_panels(node):
                        emit("figure", figure)
                return
            if node.name == "table" and "ltx_tabular" in classes:
                emit("table", self._parse_table(node))
                return
            if "ltx_equationgroup" in classes:
                members = node.select(".ltx_equation")
                if members:
                    for equation in members:
                        if equation.find_parent(class_="ltx_equation") is None:
                            emit("equation", self._parse_equation(equation))
                else:
                    emit("equation", self._parse_equation(node))
                return
            if "ltx_equation" in classes:
                emit("equation", self._parse_equation(node))
                return
            # List items without ltx_p still contain meaningful text.
            if node.name == "li" and not node.find("p"):
                emit("para", self._extract_para_with_math(node))
                return
            for child in node.children:
                if isinstance(child, Tag):
                    visit(child)

        visit(elem)

        subsections = []
        valid_sections = {"ltx_section", "ltx_subsection", "ltx_subsubsection",
                          "ltx_paragraph", "ltx_subparagraph", "ltx_appendix"}
        for subsection in elem.select("section"):
            if subsection.find_parent("section") is not elem:
                continue
            if not valid_sections.intersection(subsection.get("class") or ()):
                continue
            sub_data = self._parse_section(subsection, level=min(level + 1, 6))
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
            source_anchor=elem.get("id"),
        )

    def _extract_full_text(self, sections: List[Section]) -> str:
        """Render the section's semantic blocks in source order for search/export."""
        result = []

        def walk(section: Section) -> None:
            result.append("#" * max(1, min(section.level, 6)) + " " + section.title)
            items = section.ordered_content or [
                {"type": "para", "data": text} for text in section.paragraphs
            ]
            for item in items:
                kind, data = item.get("type"), item.get("data")
                if kind == "para" and isinstance(data, str):
                    result.append(data)
                elif kind == "equation" and isinstance(data, dict):
                    latex = data.get("latex") or ""
                    mathml = data.get("mathml") or ""
                    if latex:
                        result.append("$$" + latex + "$$")
                    elif mathml:
                        result.append(mathml)
                elif kind == "figure" and isinstance(data, dict):
                    url = data.get("src") or ""
                    alt = data.get("alt") or ""
                    if url:
                        result.append("![" + alt + "](" + url + ")")
                    if data.get("caption"):
                        result.append(data["caption"])
                elif kind == "table" and isinstance(data, dict):
                    if data.get("caption"):
                        result.append(data["caption"])
                    for row in ([data["headers"]] if data.get("headers") else []) + data.get("rows", []):
                        result.append("| " + " | ".join(str(cell).replace("|", r"\|") for cell in row) + " |")
            for child in section.subsections:
                walk(child)

        for section in sections:
            walk(section)
        return "\n\n".join(result)

