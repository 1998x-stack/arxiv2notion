"""Explicit opt-in local nano-ar5iv M04 artifact provider.

No implicit subprocess or untrusted LaTeX execution is allowed here. The
nano-ar5iv HTTP service is not yet implemented.
"""
from __future__ import annotations
from pathlib import Path
from adapters.nano_to_v2 import read_nano_artifact
from fetch.providers.base import SourceCandidate

class NanoAr5ivProvider:
    name = "nano-ar5iv"

    async def fetch(self, paper_id: str) -> SourceCandidate:
        return SourceCandidate(
            paper_id, self.name, "", None,
            "nano_ar5iv_requires_trusted_local_normalization_artifact",
        )

    def parse(self, candidate: SourceCandidate):
        raise NotImplementedError(
            "Use read_trusted_artifact() for a verified local nano-ar5iv M04 output"
        )

    def read_trusted_artifact(self, *, path: Path, root: Path, paper_id: str,
                              sha256: str):
        return read_nano_artifact(path, root=root, paper_id=paper_id,
                                  expected_sha256=sha256)
