"""
File system manager.
Responsibility: All paper content I/O and structured JSONL logging.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

from models import ArxivMetadata, Ar5ivContent, ParagraphAnnotation, Section


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
        p = self.papers_dir / category / arxiv_id
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
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.debug(f"Saved content.md: {path}")

    def save_content_json(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None:
        """Write structured Ar5ivContent to content.json."""
        path = self.get_paper_dir(arxiv_id, category) / "content.json"
        path.write_text(
            json.dumps(content.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    # ── Annotation persistence ───────────────────────────────────────────────

    def _annotation_path(self, arxiv_id: str, category: str) -> Path:
        return self.get_paper_dir(arxiv_id, category) / "llm_annotations.jsonl"

    def has_annotations(self, arxiv_id: str, category: str) -> bool:
        """Return True if annotations file exists and is non-empty."""
        p = self._annotation_path(arxiv_id, category)
        return p.exists() and p.stat().st_size > 0

    def save_annotations(
        self, arxiv_id: str, category: str, annotations: List[ParagraphAnnotation]
    ) -> None:
        """Write annotations as JSONL (one dict per line)."""
        path = self._annotation_path(arxiv_id, category)
        with path.open("w", encoding="utf-8") as f:
            for ann in annotations:
                f.write(json.dumps(ann.to_dict(), ensure_ascii=False) + "\n")
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
    """Recursively render a Section to Markdown lines."""
    prefix = "#" * (section.level + 1)
    lines = [f"{prefix} {section.title}", ""]
    for para in section.paragraphs:
        lines += [para, ""]
    for sub in section.subsections:
        lines += _section_to_md(sub)
    return lines
