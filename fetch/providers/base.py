"""Network-source contract and byte-level provenance for HTML candidates."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any

@dataclass(frozen=True)
class SourceCandidate:
    paper_id: str
    provider: str
    url: str
    html: bytes | None
    error: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.html)

class Provider(Protocol):
    name: str

    async def fetch(self, paper_id: str) -> SourceCandidate:
        ...

    def parse(self, candidate: SourceCandidate) -> Any:
        ...
