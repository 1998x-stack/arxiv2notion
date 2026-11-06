"""Typed semantic document nodes. No renderer or network dependencies."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

NODE_KINDS = frozenset({
    "abstract", "heading", "paragraph", "theorem", "proof", "algorithm",
    "code", "equation", "figure", "table", "footnote", "citation",
    "cross_reference", "unknown",
})

@dataclass(frozen=True)
class InlineSpan:
    kind: str  # text, math, link, emphasis, citation, xref
    text: str
    target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "text": self.text, "target": self.target,
            "metadata": self.metadata,
        }

@dataclass(frozen=True)
class ScientificNode:
    node_id: str
    kind: str
    parent_id: str | None
    ordinal: int
    text: str = ""
    source_anchor: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    children: tuple[str, ...] = ()
    inline_spans: tuple[InlineSpan, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id, "kind": self.kind, "parent_id": self.parent_id,
            "ordinal": self.ordinal, "text": self.text,
            "source_anchor": self.source_anchor, "payload": self.payload,
            "children": list(self.children),
            "inline_spans": [x.to_dict() for x in self.inline_spans],
        }
