"""Versioned, lossless-by-construction canonical representation for ar5iv content.

The canonical model is an adapter over the legacy Ar5ivContent model; it does
not pretend to know text offsets not supplied by the HTML parser. Source anchors
are HTML section IDs when available.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import re
from typing import Any, Iterator, Optional

from models import Ar5ivContent, PaperData, Section


SCHEMA_VERSION = "1.0"


def _digest(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ParseQuality:
    status: str  # full, partial, metadata_only, unavailable
    warnings: tuple[str, ...]
    section_count: int
    paragraph_count: int
    equation_count: int
    figure_count: int
    table_count: int
    has_abstract: bool

    @property
    def cacheable_full_text(self) -> bool:
        # An abstract-only response is NOT a trustworthy full-text cache.
        return self.paragraph_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "cacheable_full_text": self.cacheable_full_text}


@dataclass(frozen=True)
class DocumentNode:
    node_id: str
    kind: str
    section_id: str | None
    section_title: str | None
    paragraph_index: int | None
    source_anchor: str | None
    ordinal: int
    text: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParagraphRef:
    section: Section
    para_idx: int
    text: str
    node_id: str


@dataclass(frozen=True)
class PaperDocument:
    schema_version: str
    arxiv_id: str
    base_arxiv_id: str
    revision: int | None
    metadata: dict[str, Any] | None
    nodes: tuple[DocumentNode, ...]
    references: tuple[dict[str, Any], ...]
    quality: ParseQuality
    content_hash: str
    source: str
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "arxiv_id": self.arxiv_id,
            "base_arxiv_id": self.base_arxiv_id,
            "revision": self.revision,
            "metadata": self.metadata,
            "nodes": [n.to_dict() for n in self.nodes],
            "references": list(self.references),
            "quality": self.quality.to_dict(),
            "content_hash": self.content_hash,
            "source": self.source,
            "title": self.title,
        }


def _identity(arxiv_id: str) -> tuple[str, int | None]:
    match = re.search(r"v([1-9][0-9]*)$", arxiv_id)
    if not match:
        return arxiv_id, None
    return arxiv_id[:match.start()], int(match.group(1))


def _payload(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data")
    return data if isinstance(data, dict) else {}


def _section_items(section: Section) -> list[dict[str, Any]]:
    if section.ordered_content:
        return section.ordered_content
    items: list[dict[str, Any]] = [
        {"type": "para", "data": text} for text in section.paragraphs
    ]
    items.extend({"type": "equation", "data": x.to_dict()} for x in section.equations)
    items.extend({"type": "figure", "data": x.to_dict()} for x in section.figures)
    items.extend({"type": "table", "data": x.to_dict()} for x in section.tables)
    return items


def _build_nodes(content: Ar5ivContent) -> tuple[list[DocumentNode], list[ParagraphRef]]:
    nodes: list[DocumentNode] = []
    paragraphs: list[ParagraphRef] = []
    paper_id = content.paper_id

    if content.abstract:
        abstract = content.abstract
        nodes.append(DocumentNode(
            node_id="n_" + _digest([paper_id, "abstract", abstract])[:24],
            kind="abstract", section_id=None, section_title=None,
            paragraph_index=None, source_anchor=None, ordinal=0,
            text=abstract,
        ))

    def walk(sections: list[Section], parent: str) -> None:
        # Same-title siblings are disambiguated without shifting other titles.
        repeated_titles: dict[str, int] = {}
        for section in sections:
            title_key = section.title.strip().casefold()
            occurrence = repeated_titles.get(title_key, 0)
            repeated_titles[title_key] = occurrence + 1
            section_id = "s_" + _digest([paper_id, parent, title_key, occurrence])[:24]
            anchor = getattr(section, "source_anchor", None)
            nodes.append(DocumentNode(
                node_id=section_id, kind="heading", section_id=section_id,
                section_title=section.title, paragraph_index=None,
                source_anchor=anchor, ordinal=len(nodes), text=section.title,
                payload={"level": section.level},
            ))
            duplicate_content: dict[tuple[str, str], int] = {}
            paragraph_idx = 0
            for item in _section_items(section):
                kind = item.get("type")
                if kind not in ("para", "figure", "table", "equation"):
                    continue
                data = item.get("data")
                if kind == "para":
                    text = data if isinstance(data, str) else str(data or "")
                    payload: dict[str, Any] = {}
                else:
                    payload = _payload(item)
                    text = (
                        payload.get("latex", "") if kind == "equation" else
                        payload.get("caption", "") if kind in ("table", "figure") else ""
                    ) or ""
                signature = _digest([text, payload])
                duplicate_key = (kind, signature)
                occurrence = duplicate_content.get(duplicate_key, 0)
                duplicate_content[duplicate_key] = occurrence + 1
                node_id = "n_" + _digest(
                    [paper_id, section_id, kind, signature, occurrence]
                )[:24]
                idx = paragraph_idx if kind == "para" else None
                if kind == "para":
                    paragraphs.append(ParagraphRef(section, paragraph_idx, text, node_id))
                    paragraph_idx += 1
                nodes.append(DocumentNode(
                    node_id=node_id, kind="paragraph" if kind == "para" else kind,
                    section_id=section_id, section_title=section.title,
                    paragraph_index=idx, source_anchor=anchor, ordinal=len(nodes),
                    text=text, payload=payload,
                ))
            walk(section.subsections, section_id)

    walk(content.sections, "root")
    return nodes, paragraphs


def assess_quality(content: Ar5ivContent | None, metadata: Any = None) -> ParseQuality:
    if content is None:
        return ParseQuality(
            "metadata_only" if metadata else "unavailable",
            ("full_text_unavailable",), 0, 0, 0, 0, 0,
            bool(getattr(metadata, "abstract", None)),
        )
    nodes, _ = _build_nodes(content)
    counts = {
        kind: sum(n.kind == kind for n in nodes)
        for kind in ("heading", "paragraph", "equation", "figure", "table")
    }
    has_abstract = bool(content.abstract or getattr(metadata, "abstract", None))
    warnings: list[str] = []
    if counts["paragraph"] == 0:
        warnings.append("no_body_paragraphs")
    if counts["heading"] == 0:
        warnings.append("no_sections")
    if not has_abstract:
        warnings.append("no_abstract")
    if not content.title.strip():
        warnings.append("no_title")
    if counts["paragraph"] == 0 and not content.abstract:
        status = "metadata_only" if metadata else "unavailable"
    elif warnings:
        status = "partial"
    else:
        status = "full"
    return ParseQuality(
        status, tuple(warnings), counts["heading"], counts["paragraph"],
        counts["equation"], counts["figure"], counts["table"], has_abstract,
    )


def build_paper_document(paper: PaperData) -> PaperDocument:
    base_id, revision = _identity(paper.arxiv_id)
    nodes, _ = _build_nodes(paper.content) if paper.content else ([], [])
    quality = assess_quality(paper.content, paper.metadata)
    metadata = paper.metadata.to_dict() if paper.metadata else None
    references = tuple(r.to_dict() for r in paper.content.references) if paper.content else ()
    # Exclude timestamps, transient status and positional ordinals from content identity.
    hash_material = {
        "schema": SCHEMA_VERSION, "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "metadata": metadata,
        "nodes": [
            [n.node_id, n.kind, n.text, n.payload, n.source_anchor]
            for n in nodes
        ],
        "references": references,
    }
    return PaperDocument(
        SCHEMA_VERSION, paper.arxiv_id, base_id, revision, metadata,
        tuple(nodes), references, quality, _digest(hash_material),
        "ar5iv" if paper.content else "arxiv_metadata", paper.title,
    )


def iter_paragraph_refs(content: Ar5ivContent) -> Iterator[ParagraphRef]:
    """Yield references that share exactly the same IDs as PaperDocument nodes."""
    _, paragraphs = _build_nodes(content)
    yield from paragraphs
