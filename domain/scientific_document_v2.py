"""Portable, versioned scientific IR across ar5iv and nano-ar5iv.

It deliberately distinguishes structural parsing from scientific verification.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any
from domain.nodes import ScientificNode, InlineSpan, NODE_KINDS
from domain.provenance import DocumentSource
from domain.relations import ScientificRelation

SCHEMA_VERSION = "2.0"

@dataclass
class ScientificDocument:
    paper_id: str
    source: DocumentSource
    nodes: list[ScientificNode] = field(default_factory=list)
    relations: list[ScientificRelation] = field(default_factory=list)
    references: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    status: str = "NOT_EVALUATED"
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported scientific document schema")
        if self.paper_id != self.source.paper_id:
            raise ValueError("Document/source identity mismatch")
        ids = [x.node_id for x in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate document node ID")
        known = set(ids)
        for node in self.nodes:
            if node.kind not in NODE_KINDS:
                raise ValueError(f"Unknown node kind: {node.kind}")
            if node.parent_id is not None and node.parent_id not in known:
                raise ValueError("Missing parent node")
            if any(child not in known for child in node.children):
                raise ValueError("Missing child node")
        if self.status == "VERIFIED":
            raise ValueError("Schema-only validation cannot assert scientific fidelity")

    @property
    def content_hash(self) -> str:
        payload = {
            "schema_version": self.schema_version, "paper_id": self.paper_id,
            "source": self.source.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "relations": [e.to_dict() for e in self.relations],
            "references": self.references,
        }
        return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "paper_id": self.paper_id,
            "source": self.source.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "relations": [e.to_dict() for e in self.relations],
            "references": self.references, "warnings": self.warnings,
            "status": self.status, "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScientificDocument":
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported scientific document schema")
        nodes = [
            ScientificNode(**{**n, "children": tuple(n.get("children", [])),
                 "inline_spans": tuple(InlineSpan(**s) for s in n.get("inline_spans", []))})
            for n in data.get("nodes", [])
        ]
        document = cls(
            paper_id=data["paper_id"], source=DocumentSource(**data["source"]),
            nodes=nodes, relations=[ScientificRelation(**x) for x in data.get("relations", [])],
            references=data.get("references", []),
            warnings=data.get("warnings", []),
            status=data.get("status", "NOT_EVALUATED"),
        )
        document.validate()
        if "content_hash" in data and document.content_hash != data["content_hash"]:
            raise ValueError("Scientific document content hash mismatch")
        return document
