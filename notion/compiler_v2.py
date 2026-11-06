"""Compile canonical ScientificDocument V2 into existing Notion block format.

Strict mode rejects unrepresentable semantic content; no silent data loss.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from domain.scientific_document_v2 import ScientificDocument
from notion.blocks import NotionBlockBuilder as B, _para_to_notion_blocks
from notion.media import require_external_media_url
from notion.validator import validate_notion_blocks

class ScientificCompileError(ValueError):
    pass

@dataclass(frozen=True)
class CompiledPage:
    blocks: list[dict[str, Any]]
    node_block_map: dict[str, tuple[int, ...]]
    source_hash: str

def _render_table(node):
    data = node.payload
    if "table_rows" in data and not data.get("rows"):
        rows = []
        for r in data["table_rows"]:
            rows.append([c.get("text", "") if isinstance(c, dict) else str(c)
                         for c in r])
        headers = []
    else:
        headers, rows = data.get("headers") or [], data.get("rows") or []
    if not headers and not rows:
        raise ScientificCompileError(f"Empty table: {node.node_id}")
    return B.table(headers, rows)

def compile_document(document: ScientificDocument) -> CompiledPage:
    document.validate()
    blocks: list[dict] = []
    mapping: dict[str, tuple[int, ...]] = {}
    for node in document.nodes:
        start = len(blocks)
        kind = node.kind
        if kind == "heading":
            blocks.append(B.heading(node.text, level=node.payload.get("level", 2)))
        elif kind == "abstract":
            blocks.append(B.quote(node.text))
        elif kind == "paragraph":
            blocks.extend(_para_to_notion_blocks(node.text, B, 2000))
        elif kind == "theorem":
            blocks.append(B.callout(node.text, icon="📐"))
        elif kind == "proof":
            blocks.append(B.quote("Proof: " + node.text))
        elif kind == "algorithm":
            blocks.append(B.code(node.text or node.payload.get("steps", ""),
                                 language="plain text"))
        elif kind == "code":
            blocks.append(B.code(node.text,
                                 language=node.payload.get("language", "plain text")))
        elif kind == "equation":
            latex = node.payload.get("latex") or node.payload.get("source_tex") or node.text
            if not latex:
                raise ScientificCompileError(
                    f"Equation has no renderable LaTeX: {node.node_id}")
            blocks.append(B.equation(latex))
        elif kind == "figure":
            url = node.payload.get("src") or node.payload.get("href")
            try:
                safe = require_external_media_url(url)
            except ValueError as exc:
                raise ScientificCompileError(f"Figure media unavailable: {node.node_id}") from exc
            blocks.append(B.image(safe, node.payload.get("caption")))
        elif kind == "table":
            blocks.append(_render_table(node))
        elif kind == "footnote":
            blocks.append(B.paragraph("Footnote: " + node.text))
        elif kind in ("citation", "cross_reference"):
            blocks.append(B.paragraph(node.text))
        else:
            raise ScientificCompileError(
                f"Unrenderable scientific node {kind}: {node.node_id}")
        if not blocks[start:]:
            raise ScientificCompileError(f"Node not rendered: {node.node_id}")
        mapping[node.node_id] = tuple(range(start, len(blocks)))
    validate_notion_blocks(blocks)
    return CompiledPage(blocks, mapping, document.content_hash)
