"""Read-only verification of a Notion page using the durable writer's projection."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from notion.durable_sync import DurableNotionWriter

@dataclass(frozen=True)
class VerificationResult:
    status: str
    expected_blocks: int
    matched_blocks: int
    reason: str | None = None

class NotionReadbackVerifier:
    def __init__(self, writer: DurableNotionWriter):
        self.writer = writer

    def verify(self, page_id: str, expected: list[dict[str, Any]]) -> VerificationResult:
        # An incomplete remote prefix is *not* a successful complete import.
        try:
            matched = self.writer._snapshot(page_id, expected)
        except Exception as exc:
            # Keep error type only: avoid leaking tokens or remote payloads in reports.
            return VerificationResult("MISMATCH", len(expected), 0,
                                      type(exc).__name__)
        return VerificationResult(
            "MATCH" if matched == len(expected) else "INCOMPLETE",
            len(expected), matched,
            None if matched == len(expected) else "missing_expected_blocks",
        )
