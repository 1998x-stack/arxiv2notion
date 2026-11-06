"""No silent provider preference over scientifically conflicting documents."""
from __future__ import annotations
from dataclasses import dataclass
from domain.scientific_document_v2 import ScientificDocument
from quality.report import QualityReport

@dataclass(frozen=True)
class Selection:
    status: str
    selected_index: int | None
    reason: str

def choose(candidates: list[tuple[ScientificDocument, QualityReport]]) -> Selection:
    eligible = [(i, d, q) for i, (d, q) in enumerate(candidates)
                if q.status == "ACCEPTED"]
    if not eligible:
        return Selection("REVIEW_REQUIRED" if candidates else "FALLBACK",
                         None, "No structurally accepted source")
    ids = {d.paper_id for _, d, _ in eligible}
    if len(ids) > 1:
        return Selection("REVIEW_REQUIRED", None, "Paper version mismatch")
    # Cross-provider disagreement must not be disguised as confident success.
    signatures = {
        tuple((n.kind, n.text, str(sorted(n.payload.items())))
              for n in d.nodes)
        for _, d, _ in eligible
    }
    if len(signatures) > 1:
        return Selection("REVIEW_REQUIRED", None, "Provider content divergence")
    return Selection("ACCEPTED", eligible[0][0], "Identical structural content")
