"""
Notion 内容转换模块
职责：将论文内容转换为丰富的 Notion blocks（Academic Premium 布局）
"""
from typing import List, Dict, Any, Optional

from loguru import logger

from models import PaperData, ArxivMetadata, Section, Reference, ParagraphAnnotation
from utils import (
    format_exception,
    truncate_text,
    format_authors,
    format_date,
    build_arxiv_url,
    get_category_emoji,
)
from notion.blocks import (
    NotionBlockBuilder,
    _clean_latex,
    _para_to_notion_blocks,
    _section_emoji,
)


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

            if self._content_is_effectively_empty(paper.content):
                blocks.extend(self._create_ar5iv_fallback(paper))
            else:
                blocks.extend(self._create_abstract(paper, tldr=tldr))

                blocks.append(self.builder.divider())
                blocks.append(self.builder.heading("📑 Contents", level=2))
                blocks.append(self.builder.table_of_contents())
                blocks.append(self.builder.divider())

                if paper.content.sections:
                    blocks.extend(self._convert_sections(paper.content.sections, annotations))

                if paper.content.references:
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
        else:
            blocks.append(
                self.builder.callout(
                    f"arXiv: {paper.arxiv_id}\nℹ️ 元数据和完整内容均不可用",
                    icon="📄",
                    color="gray_background",
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

    # ── ar5iv Fallback ────────────────────────────────────────────────────────

    @staticmethod
    def _content_is_effectively_empty(content) -> bool:
        """Treat content as empty when it has no sections and no abstract."""
        if content is None:
            return True
        has_sections = bool(content.sections)
        has_abstract = bool(content.abstract and content.abstract.strip())
        return not has_sections and not has_abstract

    def _create_ar5iv_fallback(self, paper: "PaperData") -> List[Dict[str, Any]]:
        """Fallback layout when ar5iv content extraction fails or returns empty."""
        blocks = []

        if paper.content is None:
            reason = "ar5iv 请求失败（网络错误、超时或页面不存在）"
        else:
            reason = "ar5iv 页面可访问，但无法解析出有效的章节和摘要内容"

        blocks.append(
            self.builder.callout(
                f"⚠️ 无法提取完整内容：{reason}。\n下方可直接浏览 arXiv PDF，无需下载。",
                icon="⚠️",
                color="yellow_background",
            )
        )

        pdf_url = build_arxiv_url(paper.arxiv_id, "pdf")
        blocks.append(self.builder.embed(pdf_url))
        blocks.append(self.builder.bookmark(pdf_url, "📄 在 arXiv 查看 PDF"))

        if paper.metadata and paper.metadata.abstract:
            blocks.append(self.builder.divider())
            blocks.append(self.builder.heading("📝 Abstract", level=2))
            blocks.append(self.builder.quote(paper.metadata.abstract))

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

        ann_map = {(a.section_title, a.para_idx): a for a in annotations}

        if section.ordered_content:
            para_idx = 0
            for item in section.ordered_content:
                itype = item["type"]

                if itype == "para":
                    para_text = item["data"]
                    para_blocks = _para_to_notion_blocks(para_text, self.builder, self.max_text_length)
                    blocks.extend(para_blocks)
                    ann = ann_map.get((section.title, para_idx))
                    if ann and ann.plain_explanation and ann.plain_explanation not in (
                        "（段落过短，跳过注释）", "（注释生成失败）"
                    ):
                        blocks.append(self._make_annotation_toggle(ann))
                    para_idx += 1

                elif itype == "figure" and self.include_figures:
                    src = item["data"].get("src", "")
                    caption = item["data"].get("caption")
                    if src.startswith("http"):
                        blocks.append(self.builder.image(src, caption))

                elif itype == "table" and self.include_tables:
                    tbl = item["data"]
                    headers = tbl.get("headers", [])
                    rows = tbl.get("rows", [])
                    if tbl.get("caption"):
                        blocks.append(self.builder.paragraph(tbl["caption"], bold=True))
                    if headers or rows:
                        blocks.append(self.builder.table(headers, rows[:20]))

                elif itype == "equation" and self.include_equations:
                    latex = _clean_latex(item["data"].get("latex", ""))
                    if latex:
                        blocks.append(self.builder.equation(latex))

        else:
            for idx, para in enumerate(section.paragraphs):
                para_blocks = _para_to_notion_blocks(para, self.builder, self.max_text_length)
                blocks.extend(para_blocks)
                ann = ann_map.get((section.title, idx))
                if ann and ann.plain_explanation and ann.plain_explanation not in (
                    "（段落过短，跳过注释）", "（注释生成失败）"
                ):
                    blocks.append(self._make_annotation_toggle(ann))

            if self.include_equations and section.equations:
                for eq in section.equations[:10]:
                    latex = _clean_latex(eq.latex or "")
                    if latex:
                        blocks.append(self.builder.equation(latex))

            if self.include_figures and section.figures:
                for fig in section.figures[:5]:
                    if fig.src and fig.src.startswith("http"):
                        blocks.append(self.builder.image(fig.src, fig.caption))

            if self.include_tables and section.tables:
                for tbl in section.tables[:3]:
                    if tbl.caption:
                        blocks.append(self.builder.paragraph(tbl.caption, bold=True))
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
