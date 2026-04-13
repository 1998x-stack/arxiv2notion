"""
Notion 块转换模块
职责：将论文内容转换为丰富的 Notion blocks
遵循 CleanRL 设计原则：单一职责、显式依赖、易于测试

支持的 Notion 元素：
- heading_1/2/3: 标题
- paragraph: 段落（支持富文本）
- callout: 提示框（摘要、警告等）
- quote: 引用
- code: 代码块
- equation: 数学公式
- table: 表格
- bulleted_list_item: 无序列表
- numbered_list_item: 有序列表
- divider: 分隔线
- toggle: 可折叠内容
- image: 图片
- bookmark: 链接预览
"""
import re
import sys
import traceback
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger

from models import (
    PaperData,
    ArxivMetadata,
    Ar5ivContent,
    Section,
    Figure,
    Table,
    Equation,
    Reference,
    NotionBlockData,
)
from utils import (
    format_exception,
    clean_text,
    truncate_text,
    format_authors,
    format_date,
    build_arxiv_url,
    get_category_emoji,
)


class NotionBlockBuilder:
    """
    Notion Block 构建器
    
    提供构建各种 Notion block 的静态方法
    """
    
    # Notion rich_text 最大长度
    MAX_TEXT_LENGTH = 2000
    
    @staticmethod
    def rich_text(
        text: str,
        bold: bool = False,
        italic: bool = False,
        strikethrough: bool = False,
        underline: bool = False,
        code: bool = False,
        color: str = "default",
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建富文本对象"""
        if len(text) > NotionBlockBuilder.MAX_TEXT_LENGTH:
            text = text[:NotionBlockBuilder.MAX_TEXT_LENGTH - 3] + "..."
        
        result = {
            "type": "text",
            "text": {"content": text}
        }
        
        if link:
            result["text"]["link"] = {"url": link}
        
        annotations = {}
        if bold:
            annotations["bold"] = True
        if italic:
            annotations["italic"] = True
        if strikethrough:
            annotations["strikethrough"] = True
        if underline:
            annotations["underline"] = True
        if code:
            annotations["code"] = True
        if color != "default":
            annotations["color"] = color
        
        if annotations:
            result["annotations"] = annotations
        
        return result
    
    @staticmethod
    def heading(text: str, level: int = 1, color: str = "default") -> Dict[str, Any]:
        """创建标题 block"""
        level = max(1, min(3, level))  # Notion 只支持 1-3
        block_type = f"heading_{level}"
        
        return {
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "color": color
            }
        }
    
    @staticmethod
    def paragraph(
        text: str,
        bold: bool = False,
        italic: bool = False,
        color: str = "default"
    ) -> Dict[str, Any]:
        """创建段落 block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [NotionBlockBuilder.rich_text(text, bold=bold, italic=italic)],
                "color": color
            }
        }
    
    @staticmethod
    def paragraph_with_rich_text(rich_texts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建带富文本的段落"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": rich_texts
            }
        }
    
    @staticmethod
    def callout(
        text: str,
        icon: str = "💡",
        color: str = "gray_background"
    ) -> Dict[str, Any]:
        """创建提示框 block"""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "icon": {"emoji": icon},
                "color": color
            }
        }
    
    @staticmethod
    def quote(text: str, color: str = "default") -> Dict[str, Any]:
        """创建引用 block"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "color": color
            }
        }
    
    @staticmethod
    def code(text: str, language: str = "plain text") -> Dict[str, Any]:
        """创建代码 block"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "language": language
            }
        }
    
    @staticmethod
    def equation(latex: str) -> Dict[str, Any]:
        """创建公式 block"""
        return {
            "object": "block",
            "type": "equation",
            "equation": {
                "expression": latex
            }
        }
    
    @staticmethod
    def bulleted_list_item(text: str, children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """创建无序列表项"""
        block = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [NotionBlockBuilder.rich_text(text)]
            }
        }
        if children:
            block["bulleted_list_item"]["children"] = children
        return block
    
    @staticmethod
    def numbered_list_item(text: str, children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """创建有序列表项"""
        block = {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [NotionBlockBuilder.rich_text(text)]
            }
        }
        if children:
            block["numbered_list_item"]["children"] = children
        return block
    
    @staticmethod
    def divider() -> Dict[str, Any]:
        """创建分隔线"""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    @staticmethod
    def toggle(text: str, children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """创建可折叠内容"""
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [NotionBlockBuilder.rich_text(text)]
            }
        }
        if children:
            block["toggle"]["children"] = children
        return block
    
    @staticmethod
    def image(url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """创建图片 block"""
        block = {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": url}
            }
        }
        if caption:
            block["image"]["caption"] = [NotionBlockBuilder.rich_text(caption)]
        return block
    
    @staticmethod
    def bookmark(url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """创建书签 block"""
        block = {
            "object": "block",
            "type": "bookmark",
            "bookmark": {
                "url": url
            }
        }
        if caption:
            block["bookmark"]["caption"] = [NotionBlockBuilder.rich_text(caption)]
        return block
    
    @staticmethod
    def table(headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """创建表格 block"""
        table_width = len(headers) if headers else (len(rows[0]) if rows else 0)
        
        # 构建表格行
        table_rows = []
        
        # 表头行
        if headers:
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [NotionBlockBuilder.rich_text(cell)] for cell in headers
                    ]
                }
            })
        
        # 数据行
        for row in rows:
            # 确保每行有相同的列数
            padded_row = row + [""] * (table_width - len(row))
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [NotionBlockBuilder.rich_text(cell)] for cell in padded_row[:table_width]
                    ]
                }
            })
        
        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": table_width,
                "has_column_header": bool(headers),
                "has_row_header": False,
                "children": table_rows
            }
        }
    
    @staticmethod
    def table_of_contents() -> Dict[str, Any]:
        """创建目录 block"""
        return {
            "object": "block",
            "type": "table_of_contents",
            "table_of_contents": {
                "color": "default"
            }
        }


# ── Section heading emoji mapping ─────────────────────────────────────────────

_SECTION_EMOJIS = {
    "introduction": "📌",
    "background": "📚",
    "related": "📚",
    "method": "🔬",
    "model": "🔬",
    "architecture": "🔬",
    "approach": "🔬",
    "framework": "🔬",
    "experiment": "📊",
    "result": "📊",
    "evaluation": "📊",
    "analysis": "📊",
    "ablation": "📊",
    "conclusion": "💡",
    "discussion": "💡",
    "limitation": "💡",
    "future": "💡",
}


def _section_emoji(title: str) -> str:
    """Return an emoji prefix for a section title based on keywords."""
    lower = title.lower()
    for keyword, emoji in _SECTION_EMOJIS.items():
        if keyword in lower:
            return emoji
    return "📄"


class NotionConverter:
    """
    Converts PaperData into Notion blocks using the Academic Premium layout.

    Accepts optional List[ParagraphAnnotation] to add AI reading notes toggles.
    """

    def __init__(
        self,
        max_text_length: int = 2000,
        include_equations: bool = True,
        include_figures: bool = True,
        include_tables: bool = True,
        max_sections: int = 50,
    ):
        self.max_text_length = max_text_length
        self.include_equations = include_equations
        self.include_figures = include_figures
        self.include_tables = include_tables
        self.max_sections = max_sections
        self.builder = NotionBlockBuilder

    def convert_paper(
        self,
        paper: "PaperData",
        annotations: Optional[List["ParagraphAnnotation"]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert a full paper to Notion blocks (Academic Premium layout).

        Args:
            paper: The paper data.
            annotations: Optional Qwen annotations — each paragraph gets a toggle
                         with AI reading notes when its annotation is found.
        """
        annotations = annotations or []

        # TL;DR is the abstract annotation (section_title == "__abstract__", para_idx == -1)
        tldr = next(
            (a for a in annotations if a.section_title == "__abstract__" and a.para_idx == -1),
            None,
        )

        blocks = []
        try:
            blocks.extend(self._create_header(paper))
            blocks.extend(self._create_abstract(paper, tldr=tldr))

            blocks.append(self.builder.divider())
            blocks.append(self.builder.heading("📑 Contents", level=2))
            blocks.append(self.builder.table_of_contents())
            blocks.append(self.builder.divider())

            if paper.content and paper.content.sections:
                blocks.extend(self._convert_sections(paper.content.sections, annotations))

            if paper.content and paper.content.figures and self.include_figures:
                blocks.extend(self._create_figures_section(paper.content.figures))

            if paper.content and paper.content.tables and self.include_tables:
                blocks.extend(self._create_tables_section(paper.content.tables))

            if paper.content and paper.content.references:
                blocks.extend(self._create_references_section(paper.content.references))

            logger.debug(f"Converted paper to {len(blocks)} blocks")
        except Exception:
            logger.error(f"Conversion failed: {format_exception()}")

        return blocks

    # ── Header ────────────────────────────────────────────────────────────────

    def _create_header(self, paper: "PaperData") -> List[Dict[str, Any]]:
        blocks = []
        metadata = paper.metadata

        if metadata:
            category_emoji = get_category_emoji(metadata.primary_category)
            authors_str = format_authors([str(a) for a in metadata.authors], max_count=5)
            categories_str = " · ".join(metadata.categories[:5])
            info_lines = [
                f"📅 Published: {format_date(metadata.published)}",
                f"👥 Authors: {authors_str}",
                f"🏷️  {categories_str}",
            ]
            if metadata.doi:
                info_lines.append(f"🔗 DOI: {metadata.doi}")
            if metadata.journal_ref:
                info_lines.append(f"📰 {metadata.journal_ref}")

            blocks.append(
                self.builder.callout(
                    "\n".join(info_lines),
                    icon=category_emoji,
                    color="blue_background",
                )
            )
        elif paper.content:
            blocks.append(
                self.builder.callout(
                    f"👥 Authors: {format_authors(paper.content.authors)}",
                    icon="📄",
                    color="blue_background",
                )
            )

        # Links row
        arxiv_url = build_arxiv_url(paper.arxiv_id, "abs")
        pdf_url = build_arxiv_url(paper.arxiv_id, "pdf")
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{paper.arxiv_id}"

        blocks.append(
            self.builder.paragraph_with_rich_text([
                self.builder.rich_text("🔗 Links:  ", bold=True),
                self.builder.rich_text("arXiv", link=arxiv_url, color="blue"),
                self.builder.rich_text("  |  "),
                self.builder.rich_text("PDF", link=pdf_url, color="blue"),
                self.builder.rich_text("  |  "),
                self.builder.rich_text("ar5iv", link=ar5iv_url, color="blue"),
            ])
        )

        blocks.append(self.builder.divider())
        return blocks

    # ── Abstract + TL;DR ──────────────────────────────────────────────────────

    def _create_abstract(
        self,
        paper: "PaperData",
        tldr: Optional["ParagraphAnnotation"] = None,
    ) -> List[Dict[str, Any]]:
        blocks = []

        abstract = (
            (paper.content and paper.content.abstract)
            or (paper.metadata and paper.metadata.abstract)
        )

        if abstract:
            blocks.append(self.builder.heading("📝 Abstract", level=2))
            blocks.append(self.builder.quote(abstract))

        if tldr:
            blocks.append(
                self.builder.callout(
                    f"💡 {tldr.plain_explanation}",
                    icon="💡",
                    color="green_background",
                )
            )

        return blocks

    # ── Sections ──────────────────────────────────────────────────────────────

    def _convert_sections(
        self,
        sections: List["Section"],
        annotations: List["ParagraphAnnotation"],
    ) -> List[Dict[str, Any]]:
        blocks = []
        for i, section in enumerate(sections):
            if i >= self.max_sections:
                blocks.append(
                    self.builder.callout(
                        f"⚠️ Section limit ({self.max_sections}) reached — content truncated.",
                        icon="⚠️",
                        color="yellow_background",
                    )
                )
                break
            blocks.extend(self._convert_section(section, annotations))
        return blocks

    def _convert_section(
        self,
        section: "Section",
        annotations: List["ParagraphAnnotation"],
    ) -> List[Dict[str, Any]]:
        blocks = []
        emoji = _section_emoji(section.title)
        level = min(section.level, 3)
        blocks.append(self.builder.heading(f"{emoji} {section.title}", level=level))

        # Build annotation lookup: (section_title, para_idx) → annotation
        ann_map = {(a.section_title, a.para_idx): a for a in annotations}

        for idx, para in enumerate(section.paragraphs):
            for chunk in self._split_text(para):
                blocks.append(self.builder.paragraph(chunk))

            # Add AI reading notes toggle if annotation exists for this paragraph
            ann = ann_map.get((section.title, idx))
            if ann and ann.plain_explanation and ann.plain_explanation not in (
                "（段落过短，跳过注释）", "（注释生成失败）"
            ):
                blocks.append(self._make_annotation_toggle(ann))

        if self.include_equations and section.equations:
            for eq in section.equations[:10]:
                if eq.latex:
                    blocks.append(self.builder.equation(eq.latex))

        if self.include_figures and section.figures:
            for fig in section.figures[:5]:
                if fig.src and fig.src.startswith("http"):
                    blocks.append(self.builder.image(fig.src, fig.caption))

        if self.include_tables and section.tables:
            for tbl in section.tables[:3]:
                if tbl.headers or tbl.rows:
                    blocks.append(self.builder.table(tbl.headers, tbl.rows[:20]))

        for sub in section.subsections:
            blocks.extend(self._convert_section(sub, annotations))

        return blocks

    def _make_annotation_toggle(self, ann: "ParagraphAnnotation") -> Dict[str, Any]:
        """Build the AI 阅读笔记 toggle with callout + bullet points inside."""
        inner_blocks = [
            self.builder.callout(
                f"💬 通俗解读：{ann.plain_explanation}",
                icon="💬",
                color="gray_background",
            )
        ]
        for point in ann.key_points:
            inner_blocks.append(self.builder.bulleted_list_item(point))

        return self.builder.toggle("🤖 AI 阅读笔记", children=inner_blocks)

    # ── Figures ───────────────────────────────────────────────────────────────

    def _create_figures_section(self, figures: List["Figure"]) -> List[Dict[str, Any]]:
        blocks = [self.builder.divider(), self.builder.heading("🖼️ Figures", level=2)]
        for i, fig in enumerate(figures[:20]):
            if fig.src and fig.src.startswith("http"):
                blocks.append(self.builder.image(fig.src, fig.caption or f"Figure {i + 1}"))
        return blocks

    # ── Tables ────────────────────────────────────────────────────────────────

    def _create_tables_section(self, tables: List["Table"]) -> List[Dict[str, Any]]:
        blocks = [self.builder.divider(), self.builder.heading("📊 Tables", level=2)]
        for tbl in tables[:10]:
            if tbl.caption:
                blocks.append(self.builder.paragraph(tbl.caption, bold=True))
            if tbl.headers or tbl.rows:
                blocks.append(self.builder.table(tbl.headers, tbl.rows[:30]))
        return blocks

    # ── References ────────────────────────────────────────────────────────────

    def _create_references_section(self, references: List["Reference"]) -> List[Dict[str, Any]]:
        blocks = [self.builder.divider(), self.builder.heading("📚 参考文献 (References)", level=2)]

        arxiv_refs = [r for r in references if r.arxiv_id]
        other_refs = [r for r in references if not r.arxiv_id]

        if arxiv_refs:
            blocks.append(
                self.builder.callout(
                    f"✅ 找到 {len(arxiv_refs)} 篇 arXiv 论文，已创建子页面",
                    icon="✅",
                    color="green_background",
                )
            )

        for ref in arxiv_refs[:100]:
            blocks.append(self._format_arxiv_reference(ref))

        if other_refs:
            other_items = []
            for ref in other_refs[:100]:
                text = truncate_text(ref.raw_text, 300)
                other_items.append(
                    self.builder.bulleted_list_item(f"[{ref.citation_key or '?'}]  {text}")
                )
            blocks.append(
                self.builder.toggle(
                    f"📎 其他参考文献 ({len(other_refs)} 篇)",
                    children=other_items,
                )
            )

        return blocks

    def _format_arxiv_reference(self, ref: "Reference") -> Dict[str, Any]:
        """Format a single arXiv reference as a paragraph with rich text."""
        from process.reference_resolver import ReferenceExtractor
        extractor = ReferenceExtractor()
        ref = extractor.extract_info(ref)

        parts = []
        if ref.authors:
            authors_str = ", ".join(ref.authors[:3])
            if len(ref.authors) > 3:
                authors_str += " et al."
            parts.append(authors_str)
        if ref.year:
            parts.append(f"({ref.year}).")
        if ref.title:
            parts.append(f"{ref.title}.")
        if ref.venue:
            parts.append(f"{ref.venue}.")

        display = "  ".join(parts) if parts else truncate_text(ref.raw_text, 200)
        key_str = f"[{ref.citation_key or '?'}]  " if ref.citation_key else ""
        arxiv_url = build_arxiv_url(ref.arxiv_id, "abs")

        return self.builder.paragraph_with_rich_text([
            self.builder.rich_text(key_str, bold=True),
            self.builder.rich_text(display + "  "),
            self.builder.rich_text(f"→ arXiv:{ref.arxiv_id}", link=arxiv_url, color="blue"),
        ])

    # ── Reference sub-page ────────────────────────────────────────────────────

    def create_reference_page_blocks(
        self, ref: "Reference", metadata: Optional["ArxivMetadata"] = None
    ) -> List[Dict[str, Any]]:
        blocks = []
        if metadata:
            category_emoji = get_category_emoji(metadata.primary_category)
            authors_str = format_authors([str(a) for a in metadata.authors], max_count=5)
            info = (
                f"📅 Published: {format_date(metadata.published)}\n"
                f"👥 Authors: {authors_str}\n"
                f"🏷️  {', '.join(metadata.categories[:5])}"
            )
            blocks.append(self.builder.callout(info, icon=category_emoji, color="blue_background"))

            arxiv_url = build_arxiv_url(ref.arxiv_id, "abs")
            pdf_url = build_arxiv_url(ref.arxiv_id, "pdf")
            blocks.append(self.builder.paragraph_with_rich_text([
                self.builder.rich_text("🔗 ", bold=True),
                self.builder.rich_text("arXiv", link=arxiv_url, color="blue"),
                self.builder.rich_text("  |  "),
                self.builder.rich_text("PDF", link=pdf_url, color="blue"),
            ]))
            blocks.append(self.builder.divider())

            if metadata.abstract:
                blocks.append(self.builder.heading("📝 Abstract", level=2))
                blocks.append(self.builder.quote(metadata.abstract))
        else:
            blocks.append(
                self.builder.callout(
                    "ℹ️ Metadata not available for this reference.",
                    icon="ℹ️",
                    color="gray_background",
                )
            )
            blocks.append(self.builder.heading("Original Citation", level=2))
            blocks.append(self.builder.paragraph(ref.raw_text))
            if ref.arxiv_id:
                blocks.append(
                    self.builder.bookmark(build_arxiv_url(ref.arxiv_id), f"arXiv:{ref.arxiv_id}")
                )

        return blocks

    # ── Text splitting ────────────────────────────────────────────────────────

    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self.max_text_length:
            return [text]
        chunks, remaining = [], text
        while remaining:
            if len(remaining) <= self.max_text_length:
                chunks.append(remaining)
                break
            chunk = remaining[: self.max_text_length]
            last_break = max(
                chunk.rfind(". "), chunk.rfind("。"),
                chunk.rfind("! "), chunk.rfind("? ")
            )
            if last_break > self.max_text_length * 0.5:
                chunk = chunk[: last_break + 1]
            chunks.append(chunk.strip())
            remaining = remaining[len(chunk):].strip()
        return chunks