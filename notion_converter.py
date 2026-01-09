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


class NotionConverter:
    """
    Notion 内容转换器
    
    将论文数据转换为 Notion blocks
    """
    
    def __init__(
        self,
        max_text_length: int = 2000,
        include_equations: bool = True,
        include_figures: bool = True,
        include_tables: bool = True,
        max_sections: int = 50,
    ):
        """
        初始化转换器
        
        Args:
            max_text_length: 最大文本长度
            include_equations: 是否包含公式
            include_figures: 是否包含图片
            include_tables: 是否包含表格
            max_sections: 最大章节数
        """
        self.max_text_length = max_text_length
        self.include_equations = include_equations
        self.include_figures = include_figures
        self.include_tables = include_tables
        self.max_sections = max_sections
        
        self.builder = NotionBlockBuilder
    
    def convert_paper(self, paper: PaperData) -> List[Dict[str, Any]]:
        """
        转换完整论文为 Notion blocks
        
        Args:
            paper: 论文数据
            
        Returns:
            Notion blocks 列表
        """
        blocks = []
        
        try:
            # 1. 元数据头部
            blocks.extend(self._create_header(paper))
            
            # 2. 摘要
            blocks.extend(self._create_abstract(paper))
            
            # 3. 目录
            blocks.append(self.builder.divider())
            blocks.append(self.builder.heading("📑 Table of Contents", level=2))
            blocks.append(self.builder.table_of_contents())
            blocks.append(self.builder.divider())
            
            # 4. 章节内容
            if paper.content and paper.content.sections:
                blocks.extend(self._convert_sections(paper.content.sections))
            
            # 5. 图片（如果有）
            if paper.content and paper.content.figures and self.include_figures:
                blocks.extend(self._create_figures_section(paper.content.figures))
            
            # 6. 表格（如果有）
            if paper.content and paper.content.tables and self.include_tables:
                blocks.extend(self._create_tables_section(paper.content.tables))
            
            # 7. 参考文献
            if paper.content and paper.content.references:
                blocks.extend(self._create_references_section(paper.content.references))
            
            logger.debug(f"转换论文完成: {len(blocks)} blocks")
            
        except Exception:
            error_message = format_exception()
            logger.error(f"转换论文失败: {error_message}")
        
        return blocks
    
    def _create_header(self, paper: PaperData) -> List[Dict[str, Any]]:
        """创建论文头部信息"""
        blocks = []
        
        metadata = paper.metadata
        
        # 基本信息 callout
        if metadata:
            category_emoji = get_category_emoji(metadata.primary_category)
            
            info_text = (
                f"📅 Published: {format_date(metadata.published)}\n"
                f"👥 Authors: {format_authors([str(a) for a in metadata.authors])}\n"
                f"🏷️ Categories: {', '.join(metadata.categories[:5])}"
            )
            
            if metadata.doi:
                info_text += f"\n🔗 DOI: {metadata.doi}"
            
            if metadata.journal_ref:
                info_text += f"\n📰 Journal: {metadata.journal_ref}"
            
            blocks.append(self.builder.callout(info_text, icon=category_emoji, color="blue_background"))
        else:
            # 使用 ar5iv 内容
            if paper.content:
                info_text = f"👥 Authors: {format_authors(paper.content.authors)}"
                blocks.append(self.builder.callout(info_text, icon="📄", color="blue_background"))
        
        # 链接
        links_text = []
        arxiv_url = build_arxiv_url(paper.arxiv_id, "abs")
        pdf_url = build_arxiv_url(paper.arxiv_id, "pdf")
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{paper.arxiv_id}"
        
        blocks.append(self.builder.paragraph_with_rich_text([
            self.builder.rich_text("🔗 Links: ", bold=True),
            self.builder.rich_text("arXiv", link=arxiv_url, color="blue"),
            self.builder.rich_text(" | "),
            self.builder.rich_text("PDF", link=pdf_url, color="blue"),
            self.builder.rich_text(" | "),
            self.builder.rich_text("ar5iv", link=ar5iv_url, color="blue"),
        ]))
        
        blocks.append(self.builder.divider())
        
        return blocks
    
    def _create_abstract(self, paper: PaperData) -> List[Dict[str, Any]]:
        """创建摘要部分"""
        blocks = []
        
        abstract = None
        if paper.content and paper.content.abstract:
            abstract = paper.content.abstract
        elif paper.metadata and paper.metadata.abstract:
            abstract = paper.metadata.abstract
        
        if abstract:
            blocks.append(self.builder.heading("📝 Abstract", level=2))
            blocks.append(self.builder.quote(abstract))
        
        return blocks
    
    def _convert_sections(self, sections: List[Section]) -> List[Dict[str, Any]]:
        """转换章节内容"""
        blocks = []
        section_count = 0
        
        for section in sections:
            if section_count >= self.max_sections:
                blocks.append(self.builder.callout(
                    f"⚠️ 章节数量超过限制 ({self.max_sections})，部分内容已省略",
                    icon="⚠️",
                    color="yellow_background"
                ))
                break
            
            section_blocks = self._convert_section(section)
            blocks.extend(section_blocks)
            section_count += 1
        
        return blocks
    
    def _convert_section(self, section: Section) -> List[Dict[str, Any]]:
        """转换单个章节"""
        blocks = []
        
        # 标题
        level = min(section.level, 3)
        blocks.append(self.builder.heading(section.title, level=level))
        
        # 段落
        for para in section.paragraphs:
            if len(para) > self.max_text_length:
                # 分割长段落
                chunks = self._split_text(para)
                for chunk in chunks:
                    blocks.append(self.builder.paragraph(chunk))
            else:
                blocks.append(self.builder.paragraph(para))
        
        # 公式
        if self.include_equations and section.equations:
            for eq in section.equations[:10]:  # 限制数量
                if eq.latex:
                    blocks.append(self.builder.equation(eq.latex))
        
        # 图片
        if self.include_figures and section.figures:
            for fig in section.figures[:5]:
                if fig.src and fig.src.startswith("http"):
                    blocks.append(self.builder.image(fig.src, fig.caption))
        
        # 表格
        if self.include_tables and section.tables:
            for table in section.tables[:3]:
                if table.headers or table.rows:
                    blocks.append(self.builder.table(table.headers, table.rows[:20]))
        
        # 子章节
        for subsection in section.subsections:
            blocks.extend(self._convert_section(subsection))
        
        return blocks
    
    def _create_figures_section(self, figures: List[Figure]) -> List[Dict[str, Any]]:
        """创建图片部分"""
        blocks = []
        
        blocks.append(self.builder.divider())
        blocks.append(self.builder.heading("🖼️ Figures", level=2))
        
        for i, fig in enumerate(figures[:20]):  # 限制数量
            if fig.src and fig.src.startswith("http"):
                blocks.append(self.builder.image(fig.src, fig.caption or f"Figure {i+1}"))
        
        return blocks
    
    def _create_tables_section(self, tables: List[Table]) -> List[Dict[str, Any]]:
        """创建表格部分"""
        blocks = []
        
        blocks.append(self.builder.divider())
        blocks.append(self.builder.heading("📊 Tables", level=2))
        
        for i, table in enumerate(tables[:10]):
            if table.caption:
                blocks.append(self.builder.paragraph(table.caption, bold=True))
            
            if table.headers or table.rows:
                blocks.append(self.builder.table(table.headers, table.rows[:30]))
        
        return blocks
    
    def _create_references_section(self, references: List[Reference]) -> List[Dict[str, Any]]:
        """创建参考文献部分"""
        blocks = []
        
        blocks.append(self.builder.divider())
        blocks.append(self.builder.heading("📚 References", level=2))
        
        # 分组：有 arXiv ID 的和没有的
        arxiv_refs = [r for r in references if r.arxiv_id]
        other_refs = [r for r in references if not r.arxiv_id]
        
        if arxiv_refs:
            blocks.append(self.builder.callout(
                f"🔗 Found {len(arxiv_refs)} arXiv references (can create sub-pages)",
                icon="📄",
                color="green_background"
            ))
        
        # 显示参考文献列表
        for ref in references[:100]:  # 限制数量
            ref_text = ref.raw_text
            if len(ref_text) > 500:
                ref_text = ref_text[:497] + "..."
            
            if ref.arxiv_id:
                # 有 arXiv ID 的显示链接
                arxiv_url = build_arxiv_url(ref.arxiv_id)
                blocks.append(self.builder.paragraph_with_rich_text([
                    self.builder.rich_text(f"[{ref.citation_key or '?'}] ", bold=True),
                    self.builder.rich_text(ref_text[:200] + "... ", italic=True),
                    self.builder.rich_text(f"[arXiv:{ref.arxiv_id}]", link=arxiv_url, color="blue"),
                ]))
            else:
                blocks.append(self.builder.bulleted_list_item(f"[{ref.citation_key or '?'}] {ref_text}"))
        
        return blocks
    
    def _split_text(self, text: str) -> List[str]:
        """分割长文本"""
        if len(text) <= self.max_text_length:
            return [text]
        
        chunks = []
        remaining = text
        
        while remaining:
            if len(remaining) <= self.max_text_length:
                chunks.append(remaining)
                break
            
            chunk = remaining[:self.max_text_length]
            
            # 尝试在句子边界分割
            last_period = max(
                chunk.rfind('. '),
                chunk.rfind('。'),
                chunk.rfind('! '),
                chunk.rfind('? '),
            )
            
            if last_period > self.max_text_length * 0.5:
                chunk = chunk[:last_period + 1]
            
            chunks.append(chunk.strip())
            remaining = remaining[len(chunk):].strip()
        
        return chunks
    
    def create_reference_page_blocks(self, ref: Reference, metadata: Optional[ArxivMetadata] = None) -> List[Dict[str, Any]]:
        """
        为参考文献创建子页面内容
        
        Args:
            ref: 参考文献
            metadata: arXiv 元数据（如果有）
            
        Returns:
            Notion blocks 列表
        """
        blocks = []
        
        if metadata:
            # 使用元数据创建丰富内容
            category_emoji = get_category_emoji(metadata.primary_category)
            
            info_text = (
                f"📅 Published: {format_date(metadata.published)}\n"
                f"👥 Authors: {format_authors([str(a) for a in metadata.authors])}\n"
                f"🏷️ Categories: {', '.join(metadata.categories[:5])}"
            )
            
            blocks.append(self.builder.callout(info_text, icon=category_emoji, color="blue_background"))
            
            # 链接
            arxiv_url = build_arxiv_url(ref.arxiv_id, "abs")
            pdf_url = build_arxiv_url(ref.arxiv_id, "pdf")
            
            blocks.append(self.builder.paragraph_with_rich_text([
                self.builder.rich_text("🔗 Links: ", bold=True),
                self.builder.rich_text("arXiv", link=arxiv_url, color="blue"),
                self.builder.rich_text(" | "),
                self.builder.rich_text("PDF", link=pdf_url, color="blue"),
            ]))
            
            blocks.append(self.builder.divider())
            
            # 摘要
            if metadata.abstract:
                blocks.append(self.builder.heading("📝 Abstract", level=2))
                blocks.append(self.builder.quote(metadata.abstract))
        else:
            # 只有原始引用文本
            blocks.append(self.builder.callout(
                "ℹ️ This reference was found in the paper but detailed metadata could not be retrieved.",
                icon="ℹ️",
                color="gray_background"
            ))
            
            blocks.append(self.builder.heading("Original Citation", level=2))
            blocks.append(self.builder.paragraph(ref.raw_text))
            
            if ref.arxiv_id:
                arxiv_url = build_arxiv_url(ref.arxiv_id)
                blocks.append(self.builder.bookmark(arxiv_url, f"arXiv:{ref.arxiv_id}"))
        
        return blocks


def test_notion_converter():
    """测试 Notion 转换器"""
    from utils import setup_logging
    
    setup_logging(level="DEBUG")
    
    # 创建测试数据
    from datetime import datetime
    from models import Author
    
    metadata = ArxivMetadata(
        arxiv_id="1706.03762",
        title="Attention Is All You Need",
        authors=[Author(name="Vaswani, A."), Author(name="Shazeer, N.")],
        abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        categories=["cs.CL", "cs.LG"],
        primary_category="cs.CL",
        published=datetime(2017, 6, 12),
        updated=datetime(2017, 12, 6),
    )
    
    content = Ar5ivContent(
        paper_id="1706.03762",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer"],
        abstract="The dominant sequence transduction models...",
        sections=[
            Section(
                title="Introduction",
                level=2,
                paragraphs=["This is the introduction paragraph..."],
            ),
            Section(
                title="Background",
                level=2,
                paragraphs=["Background information here..."],
            ),
        ],
        references=[
            Reference(raw_text="[1] Some reference arXiv:1234.5678", arxiv_id="1234.5678", citation_key="1"),
            Reference(raw_text="[2] Another reference without arXiv", citation_key="2"),
        ],
    )
    
    paper = PaperData(
        arxiv_id="1706.03762",
        metadata=metadata,
        content=content,
    )
    
    converter = NotionConverter()
    blocks = converter.convert_paper(paper)
    
    logger.info(f"生成了 {len(blocks)} 个 blocks")
    for i, block in enumerate(blocks[:10]):
        logger.info(f"  Block {i+1}: {block['type']}")


if __name__ == "__main__":
    test_notion_converter()