"""Backward compatible transformation from Ar5ivContent to ScientificDocument V2."""
from __future__ import annotations
from domain.paper_document import build_paper_document
from domain.nodes import ScientificNode
from domain.provenance import DocumentSource
from domain.scientific_document_v2 import ScientificDocument
from models import Ar5ivContent, PaperData

def from_legacy(content: Ar5ivContent, source: DocumentSource) -> ScientificDocument:
    if content.paper_id != source.paper_id:
        raise ValueError("Legacy content and source paper IDs do not match")
    legacy = build_paper_document(PaperData(arxiv_id=content.paper_id, content=content))
    # Annotate the existing canonical paragraph nodes with their semantic roles
    # without modifying legacy IDs or duplicating text nodes.
    semantic_roles = {}
    ambiguous = set()
    def visit_sections(sections):
        for section in sections:
            paragraph_idx = 0
            for item in section.ordered_content:
                if item.get("type") != "para":
                    continue
                key = (section.source_anchor, section.title, paragraph_idx)
                if key in semantic_roles:
                    ambiguous.add(key)
                semantic_roles[key] = item.get("semantic_role")
                paragraph_idx += 1
            visit_sections(section.subsections)
    visit_sections(content.sections)
    for key in ambiguous:
        semantic_roles.pop(key, None)
    nodes = []
    heading_stack: list[tuple[int, str]] = []
    for original in legacy.nodes:
        parent = original.section_id
        if original.kind == "heading":
            level = int(original.payload.get("level", 2))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            parent = heading_stack[-1][1] if heading_stack else None
            heading_stack.append((level, original.node_id))
        role = None
        if original.kind == "paragraph":
            role = semantic_roles.get(
                (original.source_anchor, original.section_title,
                 original.paragraph_index))
        nodes.append(ScientificNode(
            node_id=original.node_id, kind=role or original.kind,
            parent_id=parent, ordinal=original.ordinal,
            text=original.text, source_anchor=original.source_anchor,
            payload={**original.payload,
                     **({"semantic_role": role} if role else {}),
                     "section_title": original.section_title,
                     "paragraph_index": original.paragraph_index},
        ))
    document = ScientificDocument(
        paper_id=content.paper_id, source=source, nodes=nodes,
        references=[r.to_dict() for r in content.references],
        warnings=list(legacy.quality.warnings),
    )
    document.validate()
    return document
