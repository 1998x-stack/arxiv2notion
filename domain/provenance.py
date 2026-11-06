"""Content-addressed input provenance. Identifies observed source bytes."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
import re

@dataclass(frozen=True)
class DocumentSource:
    provider: str
    url: str
    sha256: str
    paper_id: str
    version: int | None = None
    media_type: str = "text/html"
    engine: str | None = None

    @classmethod
    def from_bytes(
        cls, *, provider: str, url: str, paper_id: str,
        content: bytes, media_type: str = "text/html", engine: str | None = None,
    ) -> "DocumentSource":
        match = re.search(r"v([1-9]\d*)$", paper_id)
        return cls(provider=provider, url=url, sha256=sha256(content).hexdigest(),
                   paper_id=paper_id, version=int(match.group(1)) if match else None,
                   media_type=media_type, engine=engine)

    def to_dict(self) -> dict[str, Any]:
        return vars(self).copy()
