"""Separate structural quality from scientific fidelity verification."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class QualityReport:
    status: str  # ACCEPTED, REVIEW_REQUIRED, FALLBACK, REJECTED
    provider: str
    section_count: int
    paragraph_count: int
    equation_count: int
    figure_count: int
    table_count: int
    warnings: tuple[str, ...] = ()
    hard_failures: tuple[str, ...] = ()
    confidence: str = "STRUCTURAL_ONLY"

    def to_dict(self) -> dict[str, Any]:
        return vars(self).copy()
