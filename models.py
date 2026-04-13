"""
数据模型模块
职责：定义所有数据结构
遵循CleanRL设计原则：单一职责、显式依赖
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class PaperStatus(Enum):
    """论文处理状态"""
    PENDING = "pending"
    FETCHING = "fetching"
    PARSING = "parsing"
    CREATING = "creating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Author:
    """作者信息"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    
    def __str__(self) -> str:
        return self.name


@dataclass
class Figure:
    """图片数据"""
    src: str
    alt: Optional[str] = None
    caption: Optional[str] = None
    label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src,
            "alt": self.alt,
            "caption": self.caption,
            "label": self.label
        }


@dataclass
class Table:
    """表格数据"""
    caption: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "caption": self.caption,
            "headers": self.headers,
            "rows": self.rows,
            "label": self.label
        }


@dataclass
class Equation:
    """数学公式"""
    latex: str
    mathml: Optional[str] = None
    label: Optional[str] = None
    inline: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "latex": self.latex,
            "label": self.label,
            "inline": self.inline
        }


@dataclass
class Section:
    """章节结构"""
    title: str
    level: int  # 1-6
    paragraphs: List[str] = field(default_factory=list)
    subsections: List["Section"] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    equations: List[Equation] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "level": self.level,
            "paragraphs": self.paragraphs,
            "subsections": [s.to_dict() for s in self.subsections],
            "figures": [f.to_dict() for f in self.figures],
            "tables": [t.to_dict() for t in self.tables],
            "equations": [e.to_dict() for e in self.equations]
        }


@dataclass
class Reference:
    """参考文献"""
    raw_text: str
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    year: Optional[str] = None
    venue: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_key: Optional[str] = None  # 如 [1], [Smith2020]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "arxiv_id": self.arxiv_id,
            "doi": self.doi,
            "url": self.url,
            "citation_key": self.citation_key
        }


@dataclass
class ArxivMetadata:
    """arXiv API 元数据"""
    arxiv_id: str
    title: str
    authors: List[Author]
    abstract: str
    categories: List[str]
    primary_category: str
    published: datetime
    updated: datetime
    doi: Optional[str] = None
    journal_ref: Optional[str] = None
    comment: Optional[str] = None
    pdf_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": [str(a) for a in self.authors],
            "abstract": self.abstract,
            "categories": self.categories,
            "primary_category": self.primary_category,
            "published": self.published.isoformat(),
            "updated": self.updated.isoformat(),
            "doi": self.doi,
            "journal_ref": self.journal_ref,
            "comment": self.comment,
            "pdf_url": self.pdf_url
        }


@dataclass
class Ar5ivContent:
    """ar5iv 提取的完整内容"""
    paper_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    sections: List[Section] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    equations: List[Equation] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)
    full_text: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "affiliations": self.affiliations,
            "abstract": self.abstract,
            "sections": [s.to_dict() for s in self.sections],
            "figures": [f.to_dict() for f in self.figures],
            "tables": [t.to_dict() for t in self.tables],
            "equations": [e.to_dict() for e in self.equations],
            "references": [r.to_dict() for r in self.references],
            "full_text": self.full_text,
            "extracted_at": self.extracted_at.isoformat()
        }


@dataclass
class PaperData:
    """论文完整数据（合并 arXiv API 和 ar5iv）"""
    arxiv_id: str
    metadata: Optional[ArxivMetadata] = None
    content: Optional[Ar5ivContent] = None
    resolved_references: List[Reference] = field(default_factory=list)
    status: PaperStatus = PaperStatus.PENDING
    notion_page_id: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def title(self) -> str:
        if self.content and self.content.title:
            return self.content.title
        if self.metadata:
            return self.metadata.title
        return f"Paper {self.arxiv_id}"
    
    @property
    def authors(self) -> List[str]:
        if self.content and self.content.authors:
            return self.content.authors
        if self.metadata:
            return [str(a) for a in self.metadata.authors]
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "content": self.content.to_dict() if self.content else None,
            "resolved_references": [r.to_dict() for r in self.resolved_references],
            "status": self.status.value,
            "notion_page_id": self.notion_page_id,
            "error": self.error
        }


@dataclass
class NotionBlockData:
    """Notion Block 数据（用于统一处理）"""
    block_type: str
    content: Dict[str, Any]
    children: List["NotionBlockData"] = field(default_factory=list)
    
    def to_notion_format(self) -> Dict[str, Any]:
        """转换为 Notion API 格式"""
        result = {
            "object": "block",
            "type": self.block_type,
            self.block_type: self.content
        }
        
        # 某些 block 类型支持 children
        if self.children and self.block_type in ["toggle", "bulleted_list_item", "numbered_list_item", "to_do", "callout", "quote"]:
            result[self.block_type]["children"] = [
                child.to_notion_format() for child in self.children
            ]
        
        return result


@dataclass
class CreationResult:
    """页面创建结果"""
    success: bool
    page_id: Optional[str] = None
    title: str = ""
    url: Optional[str] = None
    error: Optional[str] = None
    blocks_created: int = 0
    children_pages: int = 0


@dataclass
class ProcessingStats:
    """处理统计"""
    total_papers: int = 0
    processed_papers: int = 0
    successful_papers: int = 0
    failed_papers: int = 0
    total_references: int = 0
    resolved_references: int = 0
    created_pages: int = 0
    created_blocks: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def get_duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_papers": self.total_papers,
            "processed_papers": self.processed_papers,
            "successful_papers": self.successful_papers,
            "failed_papers": self.failed_papers,
            "total_references": self.total_references,
            "resolved_references": self.resolved_references,
            "created_pages": self.created_pages,
            "created_blocks": self.created_blocks,
            "duration_seconds": self.get_duration()
        }


@dataclass
class ParagraphAnnotation:
    """Qwen LLM annotation for a single paragraph."""
    section_title: str
    para_idx: int           # index within the section's paragraph list
    para_text: str          # first 200 chars of original paragraph (for verification)
    plain_explanation: str  # Chinese plain-language summary
    key_points: List[str]   # 2-3 Chinese bullet points
    cached: bool = False    # True if loaded from disk, not generated via API

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_title": self.section_title,
            "para_idx": self.para_idx,
            "para_text": self.para_text,
            "plain_explanation": self.plain_explanation,
            "key_points": self.key_points,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ParagraphAnnotation":
        return cls(
            section_title=d["section_title"],
            para_idx=d["para_idx"],
            para_text=d["para_text"],
            plain_explanation=d["plain_explanation"],
            key_points=d["key_points"],
            cached=d.get("cached", True),
        )