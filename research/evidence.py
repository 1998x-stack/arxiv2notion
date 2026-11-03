"""Evidence-bound reading-note candidates, with append-only human review.

Source attribution is mechanically verifiable. Scientific support is NOT:
a located quote does not prove an LLM explanation or inference correct.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Any


SCHEMA = "claim-candidates-v1"
VERDICTS = {"supported", "unsupported", "insufficient"}
_SKIP = {"（段落过短，跳过注释）", "（注释生成失败）"}


def _hash(value: Any) -> str:
    return sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def derive_candidates(document: dict, annotations: list[dict]) -> dict:
    if document.get("schema_version") != "1.0":
        raise ValueError("Unknown canonical document schema")
    content_hash = document.get("content_hash")
    if not isinstance(content_hash, str) or len(content_hash) != 64:
        raise ValueError("Canonical content hash missing")
    nodes = {n["node_id"]: n for n in document.get("nodes", [])}
    candidates: list[dict] = []
    for annotation in annotations:
        node_id = annotation.get("node_id")
        node = nodes.get(node_id)
        if not node or node.get("kind") not in ("paragraph", "abstract"):
            raise ValueError("Annotation without a valid source paragraph node ID")
        if not node.get("text"):
            raise ValueError("Annotation points to an empty source")
        original = node["text"]
        if annotation.get("para_text") != original[:200]:
            raise ValueError("Stale annotation preview does not match source")
        explanation = (annotation.get("plain_explanation") or "").strip()
        texts = [explanation] + list(annotation.get("key_points") or [])
        for ordinal, candidate in enumerate(texts):
            if not candidate or candidate in _SKIP:
                continue
            quote = original[:min(240, len(original))]
            numbers = set(re.findall(r"(?<!\w)\d+(?:\.\d+)?%?", candidate))
            source_numbers = set(re.findall(r"(?<!\w)\d+(?:\.\d+)?%?", original))
            claim_id = "c_" + _hash([
                content_hash, node_id, ordinal, candidate
            ])[:24]
            candidates.append({
                "claim_id": claim_id,
                "arxiv_id": document["arxiv_id"],
                "document_hash": content_hash,
                "source_node_id": node_id,
                "source_anchor": node.get("source_anchor"),
                "section_title": node.get("section_title"),
                "claim_type": "explanation" if ordinal == 0 else "key_point",
                "ordinal": ordinal,
                "text": candidate,
                "quote": quote,
                "start": 0, "end": len(quote),
                "source_match": True,
                "numeric_warning": bool(numbers - source_numbers),
                "verification": "needs_review",
            })
    return {"schema_version": SCHEMA, "arxiv_id": document["arxiv_id"],
            "document_hash": content_hash, "claims": candidates}


def check_binding(claim: dict, document: dict) -> None:
    """Raise unless every provenance character is found at claimed offsets."""
    if claim.get("document_hash") != document.get("content_hash"):
        raise ValueError("Stale claim: document content hash changed")
    if claim.get("arxiv_id") != document.get("arxiv_id"):
        raise ValueError("Claim bound to a different paper")
    nodes = {n["node_id"]: n for n in document.get("nodes", [])}
    node = nodes.get(claim.get("source_node_id"))
    if not node:
        raise ValueError("Claim source node missing")
    start, end = claim.get("start"), claim.get("end")
    if (not isinstance(start, int) or not isinstance(end, int)
            or start < 0 or end <= start or end > len(node["text"])):
        raise ValueError("Invalid source character span")
    if node["text"][start:end] != claim.get("quote"):
        raise ValueError("Claim quote not present at the declared source span")
    ordinal = claim.get("ordinal")
    if not isinstance(ordinal, int) or ordinal < 0:
        raise ValueError("Invalid candidate ordinal")
    expected_type = "explanation" if ordinal == 0 else "key_point"
    if claim.get("claim_type") != expected_type:
        raise ValueError("Candidate claim type/ordinal mismatch")
    expected_id = "c_" + _hash([
        claim["document_hash"], claim["source_node_id"],
        ordinal, claim.get("text"),
    ])[:24]
    if claim.get("claim_id") != expected_id:
        raise ValueError("Candidate ID does not match immutable source and text")
    expected_quote = node["text"][:min(240, len(node["text"]))]
    if start != 0 or end != len(expected_quote) or claim.get("quote") != expected_quote:
        raise ValueError("Candidate evidence excerpt was altered")



def save_candidates(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


class ReviewLedger:
    """Append-only decisions, never inferred from model-generated prose."""
    def __init__(self, db_path: str | Path = "./data/reviews.sqlite3"):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS review_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id TEXT NOT NULL,
                    arxiv_id TEXT NOT NULL,
                    document_hash TEXT NOT NULL,
                    claim_text TEXT NOT NULL,
                    source_node_id TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_review_claim ON review_events(claim_id)")

    def record(
        self, *, claim: dict, document: dict, reviewer: str,
        verdict: str, notes: str = "",
    ) -> int:
        if verdict not in VERDICTS:
            raise ValueError("Unsupported verdict")
        if not reviewer or not reviewer.strip():
            raise ValueError("Human reviewer must be supplied")
        check_binding(claim, document)
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("""
                INSERT INTO review_events(
                    claim_id, arxiv_id, document_hash, claim_text, source_node_id,
                    reviewer, verdict, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim["claim_id"], claim["arxiv_id"], claim["document_hash"],
                claim["text"], claim["source_node_id"],
                reviewer.strip(), verdict, notes,
            ))
            return cursor.lastrowid

    def latest(self, claim: dict) -> dict | None:
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("""
                SELECT event_id, reviewer, verdict, notes, created_at
                FROM review_events
                WHERE claim_id=? AND document_hash=? AND claim_text=?
                  AND source_node_id=?
                ORDER BY event_id DESC LIMIT 1
            """, (
                claim["claim_id"], claim["document_hash"],
                claim["text"], claim["source_node_id"],
            )).fetchone()
        return dict(row) if row else None

    def history(self, claim_id: str) -> list[dict]:
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM review_events WHERE claim_id=? ORDER BY event_id",
                (claim_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def render_markdown(data: dict, ledger: ReviewLedger | None = None) -> str:
    lines = [f"# Review notes for arXiv:{data['arxiv_id']}", ""]
    for claim in data["claims"]:
        review = ledger.latest(claim) if ledger else None
        verdict = review["verdict"] if review else "needs_review"
        url = f"https://arxiv.org/abs/{claim['arxiv_id']}"
        lines.extend([
            f"## {claim['claim_type']} — {verdict}", "",
            claim["text"], "",
            f"> {claim['quote']}", "",
            f"Source: {url} · node \`{claim['source_node_id']}\` "
            f"· chars {claim['start']}–{claim['end']}", "",
        ])
        if claim["numeric_warning"]:
            lines.extend(["Numerical consistency: **manual verification required**", ""])
    return "\n".join(lines)
