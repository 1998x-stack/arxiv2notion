"""SQLite write-ahead journal for safe, resumable Notion imports.

Invariants:
* One logical paper (parent + kind + arXiv ID) owns one stable job key.
* A changed payload cannot silently append to an existing page.
* Intent is durable BEFORE a non-idempotent HTTP request.
* Only remote read-back can advance confirmed block counts.
* A per-job lease prevents two local workers from writing concurrently.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import sqlite3
import time
from pathlib import Path
from typing import Iterator
from uuid import uuid4


class ImportConflict(RuntimeError):
    """A different payload, remote edit, or concurrent worker blocks the import."""


class ImportUncertain(RuntimeError):
    """The outcome of a remote write cannot be confirmed safely."""


class ImportJournal:
    def __init__(self, path: str | Path, lease_seconds: int = 900):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lease_seconds = lease_seconds
        # WAL permits readers during a writer transaction. Journal mode must
        # be set outside BEGIN IMMEDIATE (SQLite rejects changing it inside).
        with sqlite3.connect(str(self.path), timeout=15) as setup:
            setup.execute("PRAGMA journal_mode=WAL")
            setup.execute("PRAGMA synchronous=FULL")
        with self._transaction() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS import_jobs (
                    job_key TEXT PRIMARY KEY,
                    parent_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    marker_title TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    expected_blocks INTEGER NOT NULL,
                    page_id TEXT,
                    status TEXT NOT NULL DEFAULT 'new',
                    confirmed_blocks INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    lease_owner TEXT,
                    lease_until REAL NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS block_batches (
                    job_key TEXT NOT NULL REFERENCES import_jobs(job_key),
                    batch_offset INTEGER NOT NULL,
                    batch_count INTEGER NOT NULL,
                    payload_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(job_key, batch_offset)
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_import_parent ON import_jobs(parent_id)")

    @staticmethod
    def key(parent_id: str, kind: str, resource_id: str) -> str:
        payload = "\0".join((parent_id, kind, resource_id))
        return sha256(payload.encode("utf-8")).hexdigest()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(str(self.path), timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA busy_timeout=15000")
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, job_key: str) -> dict | None:
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM import_jobs WHERE job_key=?", (job_key,)
            ).fetchone()
        return dict(row) if row else None

    def acquire(
        self,
        *,
        parent_id: str,
        kind: str,
        resource_id: str,
        marker_title: str,
        payload_hash: str,
        expected_blocks: int,
    ) -> tuple[str, str, dict]:
        """Lease a job, creating it on first use; never replace its payload."""
        key = self.key(parent_id, kind, resource_id)
        owner = uuid4().hex
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM import_jobs WHERE job_key=?", (key,)
            ).fetchone()
            if row is None:
                db.execute("""
                    INSERT INTO import_jobs (
                        job_key, parent_id, resource_id, kind, marker_title,
                        payload_hash, expected_blocks, status, lease_owner,
                        lease_until, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?, ?)
                """, (
                    key, parent_id, resource_id, kind, marker_title,
                    payload_hash, expected_blocks, owner,
                    now + self.lease_seconds, now, now,
                ))
            else:
                if row["payload_hash"] != payload_hash or row["expected_blocks"] != expected_blocks:
                    raise ImportConflict(
                        "Existing import has different content; explicit update/migration is required"
                    )
                if row["marker_title"] != marker_title:
                    raise ImportConflict("Import title changed; remote identity requires reconciliation")
                if row["lease_owner"] and row["lease_until"] > now:
                    raise ImportConflict("Import is already leased by another worker")
                db.execute("""
                    UPDATE import_jobs
                    SET lease_owner=?, lease_until=?, updated_at=?
                    WHERE job_key=?
                """, (owner, now + self.lease_seconds, now, key))
            row = db.execute(
                "SELECT * FROM import_jobs WHERE job_key=?", (key,)
            ).fetchone()
        return key, owner, dict(row)

    def _owned(self, db: sqlite3.Connection, key: str, owner: str) -> None:
        row = db.execute(
            "SELECT lease_owner FROM import_jobs WHERE job_key=?", (key,)
        ).fetchone()
        if row is None or row["lease_owner"] != owner:
            raise ImportConflict("Job lease lost or not owned by this process")

    def update(
        self,
        key: str,
        owner: str,
        *,
        status: str,
        page_id: str | None = None,
        confirmed_blocks: int | None = None,
        error: str | None = None,
    ) -> None:
        now = time.time()
        with self._transaction() as db:
            self._owned(db, key, owner)
            previous = db.execute(
                "SELECT page_id, confirmed_blocks FROM import_jobs WHERE job_key=?", (key,)
            ).fetchone()
            existing_id = previous["page_id"]
            if existing_id and page_id and existing_id != page_id:
                raise ImportConflict("Different remote page ID for existing import")
            count = previous["confirmed_blocks"]
            if confirmed_blocks is not None:
                if confirmed_blocks < count:
                    raise ImportConflict("Confirmed block count must not decrease")
                count = confirmed_blocks
            db.execute("""
                UPDATE import_jobs
                SET status=?, page_id=?, confirmed_blocks=?, last_error=?,
                    lease_until=?, updated_at=?
                WHERE job_key=?
            """, (
                status, existing_id or page_id, count, error,
                now + self.lease_seconds, now, key,
            ))

    def batch_intent(
        self,
        key: str,
        owner: str,
        offset: int,
        count: int,
        payload_hash: str,
    ) -> None:
        now = time.time()
        with self._transaction() as db:
            self._owned(db, key, owner)
            existing = db.execute("""
                SELECT batch_count, payload_hash, status FROM block_batches
                WHERE job_key=? AND batch_offset=?
            """, (key, offset)).fetchone()
            if existing and (existing["batch_count"] != count or
                             existing["payload_hash"] != payload_hash):
                raise ImportConflict("A batch already exists with a different payload")
            db.execute("""
                INSERT INTO block_batches
                    (job_key, batch_offset, batch_count, payload_hash, status, updated_at)
                VALUES (?, ?, ?, ?, 'in_flight', ?)
                ON CONFLICT(job_key, batch_offset) DO UPDATE SET
                    status='in_flight', updated_at=excluded.updated_at
            """, (key, offset, count, payload_hash, now))

    def batch_confirm(
        self, key: str, owner: str, offset: int, count: int
    ) -> None:
        with self._transaction() as db:
            self._owned(db, key, owner)
            cur = db.execute("""
                UPDATE block_batches SET status='confirmed', updated_at=?
                WHERE job_key=? AND batch_offset=? AND batch_count=?
            """, (time.time(), key, offset, count))
            if cur.rowcount != 1:
                raise ImportConflict("Missing batch intent; cannot confirm a write")

    def mark_verified(self, key: str, owner: str, count: int) -> None:
        """Record the observed remote prefix; remote observation is authoritative."""
        with self._transaction() as db:
            self._owned(db, key, owner)
            current = db.execute(
                "SELECT confirmed_blocks, expected_blocks FROM import_jobs WHERE job_key=?",
                (key,),
            ).fetchone()
            if count < current["confirmed_blocks"] or count > current["expected_blocks"]:
                raise ImportConflict("Remote block count regressed or exceeded expected count")
            db.execute("""
                UPDATE import_jobs SET confirmed_blocks=?, updated_at=?, lease_until=?
                WHERE job_key=?
            """, (count, time.time(), time.time() + self.lease_seconds, key))

    def release(self, key: str, owner: str) -> None:
        with self._transaction() as db:
            db.execute("""
                UPDATE import_jobs SET lease_owner=NULL, lease_until=0,
                    updated_at=? WHERE job_key=? AND lease_owner=?
            """, (time.time(), key, owner))

    def batches(self, key: str) -> list[dict]:
        with self._transaction() as db:
            rows = db.execute("""
                SELECT batch_offset, batch_count, payload_hash, status
                FROM block_batches WHERE job_key=? ORDER BY batch_offset
            """, (key,)).fetchall()
        return [dict(row) for row in rows]
