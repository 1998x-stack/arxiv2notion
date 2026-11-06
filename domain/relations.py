"""Explicit graph edges between citations, anchors and scientific nodes."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ScientificRelation:
    source_id: str
    kind: str
    target_id: str | None = None
    requested_target: str | None = None
    resolution: str = "UNRESOLVED"

    def to_dict(self) -> dict[str, Any]:
        return vars(self).copy()
