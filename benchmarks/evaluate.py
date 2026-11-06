"""Per-kind structural precision/recall; labels require audited golden truth."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from benchmarks.corpus import GoldenPaper
from domain.scientific_document_v2 import ScientificDocument

@dataclass(frozen=True)
class KindMetrics:
    kind: str
    true_positive: int
    false_positive: int
    false_negative: int

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 1.0

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 1.0

def _signature(kind: str, label: dict) -> tuple:
    return (kind, label.get("source_anchor"), label.get("text", "").strip())

def evaluate_document(doc: ScientificDocument, gold: GoldenPaper) -> dict[str, KindMetrics]:
    if doc.paper_id != gold.paper_id:
        raise ValueError("Gold and document paper IDs mismatch")
    expected = Counter(
        _signature(kind, row) for kind, labels in gold.labels.items()
        for row in labels
    )
    kinds = set(gold.labels)
    observed = Counter(
        _signature(node.kind, {"source_anchor": node.source_anchor,
                                "text": node.text})
        for node in doc.nodes if node.kind in kinds
    )
    output = {}
    for kind in sorted(kinds):
        e = Counter({key: amount for key, amount in expected.items() if key[0] == kind})
        o = Counter({key: amount for key, amount in observed.items() if key[0] == kind})
        tp = sum((e & o).values())
        output[kind] = KindMetrics(kind, tp, sum((o - e).values()),
                                    sum((e - o).values()))
    return output
