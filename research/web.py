"""Read-only, local-first research workspace.

No Notion tokens are required for browsing. Bind to loopback by default; the
HTTP service exposes local paper content and must not be published openly.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from research.catalog import PaperCatalog
from utils import is_valid_arxiv_id


STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}
ASSETS = Path(__file__).resolve().parent.parent / "web"


def _json_response(value, status=200):
    return status, "application/json; charset=utf-8", json.dumps(
        value, ensure_ascii=False
    ).encode("utf-8")


def _param(query, key, default=""):
    values = query.get(key, [])
    return values[0] if values else default


def _claims_for(paper_id, document, root, ledger_path):
    if not is_valid_arxiv_id(paper_id):
        return _json_response({"error": "Invalid arXiv ID"}, 400)
    if document is None:
        return _json_response({"error": "Paper not indexed"}, 404)
    safe = paper_id.replace("/", "__")
    candidates = list(Path(root).glob("*/" + safe + "/claim_candidates.json"))
    if not candidates:
        return _json_response({"schema_version": "claim-candidates-v1", "claims": []})
    if len(candidates) != 1:
        return _json_response({"error": "Ambiguous local paper folders"}, 409)
    try:
        data = json.loads(candidates[0].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _json_response({"error": "Unreadable claim manifest"}, 409)
    if data.get("document_hash") != document.get("content_hash"):
        return _json_response({"error": "Stale claims; regenerate from current document"}, 409)
    if data.get("arxiv_id") != paper_id or data.get("schema_version") != "claim-candidates-v1":
        return _json_response({"error": "Invalid claim manifest identity"}, 409)
    if Path(ledger_path).exists():
        from research.evidence import ReviewLedger
        ledger = ReviewLedger(ledger_path)
        for claim in data.get("claims", []):
            claim["latest_review"] = ledger.latest(claim)
    return _json_response(data)


def route(path: str, catalog: PaperCatalog, *, papers_root="papers",
          reviews_db="./data/reviews.sqlite3"):
    """Pure GET dispatcher, suitable for deterministic testing."""
    requested = urlsplit(path)
    name = requested.path
    if name in STATIC:
        filename, content_type = STATIC[name]
        try:
            content = (ASSETS / filename).read_bytes()
        except OSError:
            return _json_response({"error": "Missing workspace asset"}, 500)
        return 200, content_type, content
    query = parse_qs(requested.query)
    if name == "/api/overview":
        return _json_response(catalog.overview())
    if name == "/api/search":
        term = _param(query, "q")
        if len(term) > 250:
            return _json_response({"error": "Search query too long"}, 400)
        try:
            limit = int(_param(query, "limit", "30"))
        except ValueError:
            return _json_response({"error": "Invalid limit"}, 400)
        return _json_response(catalog.search(term, limit))
    if name in ("/api/paper", "/api/citations", "/api/backlinks", "/api/claims"):
        paper_id = _param(query, "id")
        if not is_valid_arxiv_id(paper_id):
            return _json_response({"error": "Invalid paper ID"}, 400)
        if name == "/api/paper":
            doc = catalog.paper(paper_id)
            return _json_response(doc, 200) if doc is not None else _json_response(
                {"error": "Paper not indexed"}, 404
            )
        if name == "/api/citations":
            return _json_response(catalog.citations(paper_id))
        if name == "/api/backlinks":
            return _json_response(catalog.cited_by(paper_id))
        return _claims_for(paper_id, catalog.paper(paper_id), papers_root, reviews_db)
    return _json_response({"error": "Not found"}, 404)


def serve(host="127.0.0.1", port=8765, *, db="./data/catalog.sqlite3",
          papers_root="./papers", reviews_db="./data/reviews.sqlite3"):
    catalog = PaperCatalog(db)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, mime, body = route(
                self.path, catalog, papers_root=papers_root,
                reviews_db=reviews_db,
            )
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.send_error(405, "Read-only workspace")

        def do_PUT(self):
            self.send_error(405, "Read-only workspace")

        def do_DELETE(self):
            self.send_error(405, "Read-only workspace")

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Research workspace: http://{host}:{port} (read-only)")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run local arxiv2notion research workspace")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default=os.getenv("CATALOG_DB", "./data/catalog.sqlite3"))
    parser.add_argument("--papers-root", default="./papers")
    parser.add_argument("--reviews-db", default=os.getenv("REVIEWS_DB", "./data/reviews.sqlite3"))
    parser.add_argument("--allow-network", action="store_true",
                        help="Explicitly permit non-loopback bind (no authentication!)")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "::1", "localhost") and not args.allow_network:
        parser.error("Non-loopback binding requires --allow-network")
    serve(args.host, args.port, db=args.db, papers_root=args.papers_root,
          reviews_db=args.reviews_db)


if __name__ == "__main__":
    main()
