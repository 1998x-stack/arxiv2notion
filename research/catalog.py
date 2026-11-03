"""Local SQLite catalog of canonical research documents and citation evidence.

Edges indicate that a paper *mentions* a reference, not that its scientific
claims are supported. No fuzzy title-based entity merging is performed.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterator

from utils import is_valid_arxiv_id


def _stable_id(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:24]


def _base_arxiv(arxiv_id: str) -> str:
    return re.sub(r"v[1-9][0-9]*$", "", arxiv_id)


def reference_target(ref: dict[str, Any]) -> tuple[str, str]:
    """Only explicit valid identifiers count as verified identity keys."""
    arxiv = (ref.get("arxiv_id") or "").strip()
    if is_valid_arxiv_id(arxiv):
        return "arxiv", _base_arxiv(arxiv)
    doi = (ref.get("doi") or "").strip()
    doi = re.sub(r"^(https?://(?:dx\.)?doi\.org/|doi:)", "", doi, flags=re.I)
    if re.fullmatch(r"10\.\d{4,9}/\S+", doi, flags=re.I):
        return "doi", doi.lower()
    raw = " ".join(str(ref.get("raw_text") or "").split()).casefold()
    return "unresolved", _stable_id(raw)


class PaperCatalog:
    def __init__(self, db_path: str | Path = "./data/catalog.sqlite3"):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path, timeout=15) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS papers (
                    arxiv_id TEXT PRIMARY KEY,
                    base_arxiv_id TEXT NOT NULL,
                    revision INTEGER,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    document_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_paper_base
                    ON papers(base_arxiv_id);
                CREATE TABLE IF NOT EXISTS citation_edges (
                    edge_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL REFERENCES papers(arxiv_id)
                        ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL,
                    target_kind TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    citation_key TEXT,
                    raw_text TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    UNIQUE(source_id, ordinal)
                );
                CREATE INDEX IF NOT EXISTS idx_citation_target
                    ON citation_edges(target_kind, target_id);
            """)

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        with sqlite3.connect(self.path, timeout=15) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            yield db

    @staticmethod
    def _validate(document: dict) -> None:
        if document.get("schema_version") != "1.0":
            raise ValueError("Unknown PaperDocument schema version")
        if not is_valid_arxiv_id(document.get("arxiv_id", "")):
            raise ValueError("Invalid canonical arXiv ID")
        if not isinstance(document.get("content_hash"), str) or len(document["content_hash"]) != 64:
            raise ValueError("Missing canonical document content hash")
        if not isinstance(document.get("nodes"), list) or not isinstance(document.get("references"), list):
            raise ValueError("Missing canonical nodes/references")

    def upsert(self, document: dict | Any, *, references: list[dict] | None = None) -> int:
        if not isinstance(document, dict):
            document = document.to_dict()
        self._validate(document)
        arxiv_id = document["arxiv_id"]
        refs = references if references is not None else document["references"]
        if not isinstance(refs, list):
            refs = list(refs)
        if any(not isinstance(ref, dict) for ref in refs):
            raise ValueError("Citation entries must be dictionaries")
        metadata = document.get("metadata") or {}
        title = (document.get("title") or metadata.get("title") or
                 next((n.get("text") for n in document["nodes"] if n.get("kind") == "heading"), arxiv_id))
        abstract = metadata.get("abstract") or next(
            (n.get("text") for n in document["nodes"] if n.get("kind") == "abstract"), ""
        )
        quality = (document.get("quality") or {}).get("status", "unknown")
        with self._db() as db:
            db.execute("""
                INSERT INTO papers(arxiv_id, base_arxiv_id, revision, title, abstract,
                                   quality, content_hash, document_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(arxiv_id) DO UPDATE SET
                    base_arxiv_id=excluded.base_arxiv_id,
                    revision=excluded.revision, title=excluded.title,
                    abstract=excluded.abstract, quality=excluded.quality,
                    content_hash=excluded.content_hash,
                    document_json=excluded.document_json,
                    updated_at=CURRENT_TIMESTAMP
            """, (arxiv_id, document.get("base_arxiv_id") or _base_arxiv(arxiv_id),
                  document.get("revision"), title, abstract, quality,
                  document["content_hash"], json.dumps(document, ensure_ascii=False)))
            db.execute("DELETE FROM citation_edges WHERE source_id=?", (arxiv_id,))
            for ordinal, ref in enumerate(refs):
                kind, target = reference_target(ref)
                raw = str(ref.get("raw_text") or "")
                edge_id = "e_" + _stable_id(
                    json.dumps([arxiv_id, ordinal, kind, target, raw], ensure_ascii=False))
                db.execute("""
                    INSERT INTO citation_edges(edge_id, source_id, ordinal, target_kind,
                                               target_id, citation_key, raw_text, provenance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ar5iv_reference')
                """, (edge_id, arxiv_id, ordinal, kind, target,
                      ref.get("citation_key"), raw))
        return len(refs)

    def index_directory(self, root: str | Path) -> dict[str, Any]:
        root = Path(root)
        count, edges, errors = 0, 0, []
        if not root.exists():
            return {"papers": 0, "edges": 0, "errors": [], "missing_directory": True}
        for path in sorted(root.glob("*/*/document.json")):
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                edges += self.upsert(doc)
                count += 1
            except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
                errors.append({"file": str(path), "error": str(exc)})
        return {"papers": count, "edges": edges, "errors": errors}

    def search(self, text: str, limit: int = 20) -> list[dict]:
        limit = max(1, min(100, int(limit)))
        escaped = (text.strip().replace("!", "!!")
                   .replace("%", "!%").replace("_", "!_"))
        with self._db() as db:
            rows = db.execute("""
                SELECT arxiv_id, title, quality, content_hash
                FROM papers
                WHERE arxiv_id LIKE ? ESCAPE '\'
                   OR title LIKE ? ESCAPE '\'
                   OR abstract LIKE ? ESCAPE '\'
                ORDER BY updated_at DESC, arxiv_id LIMIT ?
            """, (f"%{escaped}%",)*3 + (limit,)).fetchall()
        return [dict(r) for r in rows]

    def paper(self, arxiv_id: str) -> dict | None:
        with self._db() as db:
            row = db.execute(
                "SELECT document_json FROM papers WHERE arxiv_id=?", (arxiv_id,)
            ).fetchone()
        return json.loads(row["document_json"]) if row else None

    def citations(self, arxiv_id: str) -> list[dict]:
        with self._db() as db:
            rows = db.execute("""
                SELECT edge_id, ordinal, target_kind, target_id,
                       citation_key, raw_text, provenance
                FROM citation_edges
                WHERE source_id=? ORDER BY ordinal
            """, (arxiv_id,)).fetchall()
        return [dict(r) for r in rows]

    def cited_by(self, arxiv_id: str) -> list[dict]:
        base_id = _base_arxiv(arxiv_id)
        with self._db() as db:
            rows = db.execute("""
                SELECT e.source_id, p.title, e.edge_id, e.citation_key, e.raw_text
                FROM citation_edges e JOIN papers p ON p.arxiv_id=e.source_id
                WHERE e.target_kind='arxiv' AND e.target_id=?
                ORDER BY e.source_id, e.ordinal
            """, (base_id,)).fetchall()
        return [dict(r) for r in rows]

    def overview(self) -> dict:
        with self._db() as db:
            p = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
            e = db.execute("SELECT COUNT(*) FROM citation_edges").fetchone()[0]
            resolved = db.execute("""
                SELECT COUNT(*) FROM citation_edges WHERE target_kind <> 'unresolved'
            """).fetchone()[0]
        return {"papers": p, "citations": e, "identified_citations": resolved,
                "unresolved_citations": e-resolved}
