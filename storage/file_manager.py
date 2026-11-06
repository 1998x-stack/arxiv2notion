"""
File system manager.
Responsibility: All paper content I/O and structured JSONL logging.
"""
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List

from loguru import logger

from models import ArxivMetadata, Ar5ivContent, ParagraphAnnotation, Section
from domain.paper_document import PaperDocument
from domain.scientific_document_v2 import ScientificDocument
from utils import is_valid_arxiv_id


class FileManager:
    """
    Manages the papers/ directory tree and logs/ JSONL streams.

    Directory layout:
        papers/{category}/{arxiv_id}/
            metadata.json
            content.md
            content.json
            llm_annotations.jsonl
        logs/
            import.jsonl
            llm_calls.jsonl
            errors.jsonl
    """

    def __init__(self, base_dir: Path = Path(".")):
        self.base_dir = base_dir
        self.papers_dir = base_dir / "papers"
        self.logs_dir = base_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    # ── Paper directory helpers ──────────────────────────────────────────────

    def get_paper_dir(self, arxiv_id: str, category: str) -> Path:
        """Return (and create) the directory for a specific paper."""
        if not is_valid_arxiv_id(arxiv_id):
            raise ValueError(f"Invalid arXiv ID: {arxiv_id!r}")
        if not isinstance(category, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", category):
            raise ValueError(f"Invalid paper category: {category!r}")
        safe_id = arxiv_id.replace("/", "__")  # legacy IDs have an archive separator
        p = self.papers_dir / category / safe_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ── Paper content persistence ────────────────────────────────────────────

    def save_metadata(self, arxiv_id: str, category: str, metadata: ArxivMetadata) -> None:
        """Write ArxivMetadata to metadata.json."""
        path = self.get_paper_dir(arxiv_id, category) / "metadata.json"
        path.write_text(
            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.debug(f"Saved metadata: {path}")

    def save_content_md(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None:
        """Write full paper content as human-readable Markdown."""
        path = self.get_paper_dir(arxiv_id, category) / "content.md"
        lines = [f"# {content.title}", ""]
        if content.authors:
            lines += [f"**Authors:** {', '.join(content.authors)}", ""]
        if content.abstract:
            lines += ["## Abstract", "", content.abstract, ""]
        for section in content.sections:
            lines += _section_to_md(section)
        if content.references:
            lines += ["## References", ""]
            for ref in content.references:
                lines += [f"- {ref.raw_text}", ""]
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.debug(f"Saved content.md: {path}")

    def save_content_json(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None:
        """Write structured Ar5ivContent to content.json."""
        path = self.get_paper_dir(arxiv_id, category) / "content.json"
        path.write_text(
            json.dumps(content.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def save_document(self, arxiv_id: str, category: str, document: PaperDocument) -> None:
        """Write the canonical structural snapshot for inspection and recovery."""
        path = self.get_paper_dir(arxiv_id, category) / "document.json"
        temp = path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(document.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temp.replace(path)

    def save_scientific_document(
        self, arxiv_id: str, category: str, document: ScientificDocument,
    ) -> None:
        """Atomically persist source-bound IR V2 with its SHA256 evidence."""
        document.validate()
        path = self.get_paper_dir(arxiv_id, category) / "document-v2.json"
        temp = path.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(document.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(path)

    # ── Annotation persistence ───────────────────────────────────────────────

    def _annotation_path(self, arxiv_id: str, category: str) -> Path:
        return self.get_paper_dir(arxiv_id, category) / "llm_annotations.jsonl"

    def has_annotations(
        self, arxiv_id: str, category: str, fingerprint: str | None = None
    ) -> bool:
        """Verify cache identity AND bytes when a fingerprint is requested."""
        p = self._annotation_path(arxiv_id, category)
        if not p.exists() or p.stat().st_size == 0:
            return False
        if fingerprint is None:  # Backwards-compatible low-level file check.
            return True
        manifest_path = p.with_name("llm_annotations.manifest.json")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            body = p.read_bytes()
            return (
                manifest.get("schema_version") == 1
                and manifest.get("fingerprint") == fingerprint
                and manifest.get("sha256") == hashlib.sha256(body).hexdigest()
                and manifest.get("count") == len(body.splitlines())
            )
        except (OSError, ValueError, TypeError):
            return False

    def save_annotations(
        self, arxiv_id: str, category: str, annotations: List[ParagraphAnnotation],
        fingerprint: str | None = None,
    ) -> None:
        """Atomically replace JSONL then publish a matching version manifest."""
        path = self._annotation_path(arxiv_id, category)
        manifest = path.with_name("llm_annotations.manifest.json")
        # Invalidate stale manifests BEFORE replacing the data. An interrupted
        # update must never make old cache metadata validate new data.
        manifest.unlink(missing_ok=True)
        body = "".join(json.dumps(a.to_dict(), ensure_ascii=False) + "\n"
                       for a in annotations)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(path)
        if fingerprint:
            meta = {
                "schema_version": 1,
                "fingerprint": fingerprint,
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "count": len(annotations),
            }
            tmp_manifest = manifest.with_name(manifest.name + ".tmp")
            tmp_manifest.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            tmp_manifest.replace(manifest)
        logger.debug(f"Saved {len(annotations)} annotations: {path}")

    def load_annotations(self, arxiv_id: str, category: str) -> List[ParagraphAnnotation]:
        """Load annotations from JSONL; marks each as cached=True."""
        path = self._annotation_path(arxiv_id, category)
        if not path.exists():
            return []
        annotations = []
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                ann = ParagraphAnnotation.from_dict(d)
                ann.cached = True
                annotations.append(ann)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Skipping malformed annotation line: {e}")
        return annotations

    # ── JSONL log helpers ────────────────────────────────────────────────────

    def _append_log(self, filename: str, event: dict) -> None:
        """Append a dict as one JSONL line with a timestamp."""
        path = self.logs_dir / filename
        entry = {"ts": datetime.now().isoformat(timespec="seconds"), **event}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def log_import(self, event: dict) -> None:
        """Append to logs/import.jsonl."""
        self._append_log("import.jsonl", event)

    def log_llm_call(self, event: dict) -> None:
        """Append to logs/llm_calls.jsonl."""
        self._append_log("llm_calls.jsonl", event)

    def log_error(self, event: dict) -> None:
        """Append to logs/errors.jsonl."""
        self._append_log("errors.jsonl", event)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _section_to_md(section: Section) -> List[str]:
    """Render paragraphs, math, figures and tables in document order."""
    prefix = "#" * max(1, min(section.level, 6))
    lines = [f"{prefix} {section.title}", ""]

    def render_table(data: dict) -> list[str]:
        headers = list(data.get("headers") or [])
        rows = list(data.get("rows") or [])
        width = max([len(headers)] + [len(row) for row in rows] + [0])
        if not width:
            return []
        if not headers:
            headers = [f"Column {idx + 1}" for idx in range(width)]
        def cell(value) -> str:
            return str(value).replace("|", r"\|").replace("\n", "<br>")
        def markdown_row(values) -> str:
            padded = list(values) + [""] * (width - len(values))
            return "| " + " | ".join(cell(v) for v in padded[:width]) + " |"
        result = [markdown_row(headers), markdown_row(["---"] * width)]
        result.extend(markdown_row(row) for row in rows)
        return result + [""]

    if section.ordered_content:
        items = section.ordered_content
    else:
        items = [{"type": "para", "data": paragraph}
                 for paragraph in section.paragraphs]
        items += [{"type": "equation", "data": eq.to_dict()}
                  for eq in section.equations]
        items += [{"type": "figure", "data": fig.to_dict()}
                  for fig in section.figures]
        items += [{"type": "table", "data": table.to_dict()}
                  for table in section.tables]

    for item in items:
        kind = item.get("type")
        data = item.get("data")
        if kind == "para":
            lines += [str(data), ""]
        elif kind == "equation" and isinstance(data, dict):
            if data.get("latex"):
                lines += ["$$", data["latex"], "$$", ""]
            elif data.get("mathml"):
                lines += ["~~~xml", data["mathml"], "~~~", ""]
        elif kind == "figure" and isinstance(data, dict):
            lines += [f"![{data.get('alt') or ''}]({data.get('src') or ''})", ""]
            if data.get("caption"):
                lines += [f"*{data['caption']}*", ""]
        elif kind == "table" and isinstance(data, dict):
            if data.get("caption"):
                lines += [f"*{data['caption']}*", ""]
            lines += render_table(data)

    for sub in section.subsections:
        lines += _section_to_md(sub)
    return lines
