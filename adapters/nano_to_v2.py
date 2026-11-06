"""Convert a nano-ar5iv M04 JSON artifact to the shared V2 IR.

No claim of verification is introduced. Only the supplied artifact is read.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from domain.nodes import ScientificNode
from domain.provenance import DocumentSource
from domain.relations import ScientificRelation
from domain.scientific_document_v2 import ScientificDocument

MAX_ARTIFACT_BYTES = 20 * 1024 * 1024

def from_nano_artifact(data: dict[str, Any], *,
                       paper_id: str, artifact_sha256: str) -> ScientificDocument:
    if data.get("schema_version") != "1.0":
        raise ValueError("Unexpected nano-ar5iv schema")
    if len(artifact_sha256) != 64:
        raise ValueError("Missing artifact SHA256")
    source = DocumentSource(
        provider="nano-ar5iv", url="", paper_id=paper_id,
        sha256=artifact_sha256, media_type="application/json",
        engine=str((data.get("engine") or {}).get("name", "nano-ar5iv")),
    )
    nodes = []
    for index, n in enumerate(data.get("nodes", [])):
        upstream_kind = n.get("kind", "unknown")
        if upstream_kind in ("part", "chapter", "section", "subsection",
                             "subsubsection", "subparagraph"):
            kind = "heading"
        elif upstream_kind == "paragraph_text":
            kind = "paragraph"
        elif upstream_kind in ("bibliography_item", "bibitem"):
            kind = "citation"
        elif upstream_kind in ("abstract", "heading", "paragraph", "theorem",
                               "proof", "algorithm", "code", "footnote",
                               "citation", "cross_reference", "figure",
                               "table", "equation"):
            kind = upstream_kind
        else:
            kind = "unknown"
        nodes.append(ScientificNode(
            node_id=n["id"], kind=kind, parent_id=n.get("parent_id"),
            ordinal=index, text=n.get("text") or n.get("title") or "",
            source_anchor=n.get("source_id"),
            payload={"source_ref": n.get("source_ref"),
                     "title": n.get("title"), "upstream_kind": upstream_kind,
                     "upstream_children": n.get("children", [])},
        ))
    by_id = {n.node_id for n in nodes}
    # Preserve M04 math/assets without silently discarding them.
    for group, kind in (("equations", "equation"), ("assets", "figure")):
        for obj in data.get(group, []):
            object_id = obj["id"]
            if object_id in by_id:
                continue
            actual_kind = "table" if obj.get("kind") == "table" else kind
            nodes.append(ScientificNode(
                node_id=object_id, kind=actual_kind,
                parent_id=obj.get("parent_id") if obj.get("parent_id") in by_id else None,
                ordinal=len(nodes), text=obj.get("caption") or "",
                source_anchor=obj.get("source_id"), payload=dict(obj),
            ))
            by_id.add(object_id)
    for item in nodes:
        if item.parent_id and item.parent_id not in by_id:
            raise ValueError("nano source has unresolved structural parent")
    relations = [ScientificRelation(
        source_id=r["source_id"], kind=r["kind"], target_id=r.get("target_id"),
        requested_target=r.get("requested_target"),
        resolution=r.get("resolution", "UNRESOLVED"),
    ) for r in data.get("relations", [])]
    warnings = list(data.get("warnings", []))
    if data.get("quality_status") != "NOT_EVALUATED":
        warnings.append("nano_quality_claim_not_independently_verified")
    doc = ScientificDocument(
        paper_id=paper_id, source=source, nodes=nodes, relations=relations,
        references=list(data.get("citations", [])), warnings=warnings,
    )
    doc.validate()
    return doc

def read_nano_artifact(path: Path, *, root: Path, paper_id: str,
                       expected_sha256: str) -> ScientificDocument:
    """Read only an allowlisted, locally produced and hashed artifact."""
    root = root.resolve()
    candidate = path.resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError("Artifact path outside trusted workspace")
    if candidate.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError("Oversize nano artifact")
    content = candidate.read_bytes()
    actual = sha256(content).hexdigest()
    if actual != expected_sha256:
        raise ValueError("nano artifact hash mismatch")
    return from_nano_artifact(json.loads(content), paper_id=paper_id,
                              artifact_sha256=actual)
