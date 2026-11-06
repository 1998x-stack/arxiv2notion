"""Load small pinned gold manifests; no network or auto-generated 'truth'."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class GoldenPaper:
    paper_id: str
    source_sha256: str
    labels: dict[str, list[dict[str, Any]]]

def load_golden(path: Path, root: Path) -> GoldenPaper:
    file = path.resolve()
    if not file.is_relative_to(root.resolve()) or file.stat().st_size > 2_000_000:
        raise ValueError("Golden manifest outside trusted root or oversize")
    obj = json.loads(file.read_text(encoding="utf-8"))
    if obj.get("reviewed") is not True:
        raise ValueError("Unreviewed fixture cannot be used as golden truth")
    source_file = (file.parent / obj["source_file"]).resolve()
    if not source_file.is_relative_to(root.resolve()):
        raise ValueError("Source snapshot outside trusted golden root")
    digest = sha256(source_file.read_bytes()).hexdigest()
    if digest != obj["source_sha256"]:
        raise ValueError("Golden source checksum mismatch")
    return GoldenPaper(obj["paper_id"], digest, obj.get("labels", {}))
