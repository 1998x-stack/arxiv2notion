"""
Notion Block 构建器
职责：提供构建各种 Notion block 的静态方法及 LaTeX/段落渲染工具

支持的 Notion 元素：
- heading_1/2/3, paragraph, callout, quote, code
- equation, table, bulleted_list_item, numbered_list_item
- divider, toggle, image, bookmark, embed, table_of_contents
"""
import re
from typing import List, Dict, Any, Optional


class NotionBlockBuilder:
    """提供构建各种 Notion block 的静态方法"""

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
        link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建富文本对象"""
        if len(text) > NotionBlockBuilder.MAX_TEXT_LENGTH:
            text = text[: NotionBlockBuilder.MAX_TEXT_LENGTH - 3] + "..."

        result = {"type": "text", "text": {"content": text}}
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
        level = max(1, min(3, level))
        block_type = f"heading_{level}"
        return {
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "color": color,
            },
        }

    @staticmethod
    def paragraph(
        text: str, bold: bool = False, italic: bool = False, color: str = "default"
    ) -> Dict[str, Any]:
        """创建段落 block"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [NotionBlockBuilder.rich_text(text, bold=bold, italic=italic)],
                "color": color,
            },
        }

    @staticmethod
    def paragraph_with_rich_text(rich_texts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建带富文本的段落"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich_texts},
        }

    @staticmethod
    def callout(text: str, icon: str = "💡", color: str = "gray_background") -> Dict[str, Any]:
        """创建提示框 block"""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "icon": {"emoji": icon},
                "color": color,
            },
        }

    @staticmethod
    def quote(text: str, color: str = "default") -> Dict[str, Any]:
        """创建引用 block"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {"rich_text": [NotionBlockBuilder.rich_text(text)], "color": color},
        }

    @staticmethod
    def code(text: str, language: str = "plain text") -> Dict[str, Any]:
        """创建代码 block"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [NotionBlockBuilder.rich_text(text)],
                "language": language,
            },
        }

    @staticmethod
    def equation(latex: str) -> Dict[str, Any]:
        """创建公式 block"""
        return {
            "object": "block",
            "type": "equation",
            "equation": {"expression": latex},
        }

    @staticmethod
    def bulleted_list_item(text: str, children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """创建无序列表项"""
        block = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [NotionBlockBuilder.rich_text(text)]
            },
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
            },
        }
        if children:
            block["numbered_list_item"]["children"] = children
        return block

    @staticmethod
    def divider() -> Dict[str, Any]:
        """创建分隔线"""
        return {"object": "block", "type": "divider", "divider": {}}

    @staticmethod
    def toggle(text: str, children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """创建可折叠内容"""
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {"rich_text": [NotionBlockBuilder.rich_text(text)]},
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
            "image": {"type": "external", "external": {"url": url}},
        }
        if caption:
            block["image"]["caption"] = [NotionBlockBuilder.rich_text(caption)]
        return block

    @staticmethod
    def bookmark(url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """创建书签 block"""
        block = {"object": "block", "type": "bookmark", "bookmark": {"url": url}}
        if caption:
            block["bookmark"]["caption"] = [NotionBlockBuilder.rich_text(caption)]
        return block

    @staticmethod
    def embed(url: str) -> Dict[str, Any]:
        """创建嵌入 block（用于 PDF 等）"""
        return {"object": "block", "type": "embed", "embed": {"url": url}}

    @staticmethod
    def table(headers: List[str], rows: List[List[str]]) -> Dict[str, Any]:
        """创建表格 block"""
        table_width = len(headers) if headers else (len(rows[0]) if rows else 0)
        table_rows = []

        if headers:
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [[NotionBlockBuilder.rich_text(cell)] for cell in headers]
                },
            })

        for row in rows:
            padded_row = row + [""] * (table_width - len(row))
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [NotionBlockBuilder.rich_text(cell)]
                        for cell in padded_row[:table_width]
                    ]
                },
            })

        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": table_width,
                "has_column_header": bool(headers),
                "has_row_header": False,
                "children": table_rows,
            },
        }

    @staticmethod
    def table_of_contents() -> Dict[str, Any]:
        """创建目录 block"""
        return {
            "object": "block",
            "type": "table_of_contents",
            "table_of_contents": {"color": "default"},
        }

    @staticmethod
    def equation_rich_text(latex: str) -> Dict[str, Any]:
        """Create an inline equation rich_text element (KaTeX rendered inline)."""
        return {"type": "equation", "equation": {"expression": latex}}


# ── LaTeX cleanup for KaTeX ───────────────────────────────────────────────────

_LATEX_REPLACEMENTS = [
    (r"\\bm\{", r"\\boldsymbol{"),
    (r"\\mbox\{([^}]*)\}", r"\\text{\1}"),
    (r"\\hbox\{([^}]*)\}", r"\\text{\1}"),
    (r"\\rm\b", r"\\mathrm"),
    (r"\\bf\b", r"\\mathbf"),
]

_LATEX_STRIP_PATTERNS = [
    r"\\label\{[^}]*\}",
    r"\\tag\*?\{[^}]*\}",
    r"\\notag\b",
    r"\\nonumber\b",
]


def _clean_latex(latex: str) -> str:
    """Clean LaTeX extracted from ar5iv for KaTeX rendering in Notion."""
    for pat in _LATEX_STRIP_PATTERNS:
        latex = re.sub(pat, "", latex)
    for pat, repl in _LATEX_REPLACEMENTS:
        latex = re.sub(pat, repl, latex)
    return latex.strip()


# ── Paragraph → Notion blocks ─────────────────────────────────────────────────

_BLOCK_MATH_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
_INLINE_MATH_RE = re.compile(r"\$([^$\n]+?)\$")


def _para_to_notion_blocks(
    para_text: str,
    builder: "NotionBlockBuilder",
    max_text_length: int = 2000,
) -> List[Dict[str, Any]]:
    """Convert a paragraph string (possibly containing $...$ / $$...$$) to Notion blocks."""
    blocks: List[Dict[str, Any]] = []
    display_parts = _BLOCK_MATH_RE.split(para_text)

    for i, part in enumerate(display_parts):
        if i % 2 == 1:
            latex = _clean_latex(part.strip())
            if latex:
                blocks.append({
                    "object": "block",
                    "type": "equation",
                    "equation": {"expression": latex},
                })
        else:
            if not part.strip():
                continue
            rich_texts = _text_to_rich_texts(part, builder, max_text_length)
            if rich_texts:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": rich_texts},
                })
    return blocks


def _text_to_rich_texts(
    text: str,
    builder: "NotionBlockBuilder",
    max_text_length: int = 2000,
) -> List[Dict[str, Any]]:
    """Convert plain text (possibly containing $...$ inline math) to rich_text objects."""
    rich_texts: List[Dict[str, Any]] = []
    inline_parts = _INLINE_MATH_RE.split(text)

    for j, chunk in enumerate(inline_parts):
        if j % 2 == 1:
            latex = _clean_latex(chunk.strip())
            if latex:
                rich_texts.append(builder.equation_rich_text(latex))
        else:
            if not chunk:
                continue
            remaining = chunk
            while remaining:
                if len(remaining) <= max_text_length:
                    rich_texts.append(builder.rich_text(remaining))
                    break
                cut = remaining.rfind(" ", 0, max_text_length)
                cut = cut if cut > 0 else max_text_length
                rich_texts.append(builder.rich_text(remaining[:cut]))
                remaining = remaining[cut:].lstrip()

    return rich_texts


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
