"""Local research catalog CLI (no Notion credentials required).

Usage:
  python -m research.cli index --papers-root papers
  python -m research.cli search "transformer"
  python -m research.cli paper 1706.03762
  python -m research.cli citations 1706.03762
  python -m research.cli backlinks 1706.03762
  python -m research.cli overview
"""
import argparse
import json
import os
from research.catalog import PaperCatalog


def run(argv=None):
    parser = argparse.ArgumentParser(description="Offline arxiv2notion research catalog")
    parser.add_argument("--db", default=os.getenv("CATALOG_DB", "./data/catalog.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)
    idx = sub.add_parser("index", help="Index local canonical document.json files")
    idx.add_argument("--papers-root", default="./papers")
    search = sub.add_parser("search", help="Search papers by ID, title and abstract")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    for cmd in ("paper", "citations", "backlinks"):
        sub.add_parser(cmd).add_argument("arxiv_id")
    sub.add_parser("overview")
    args = parser.parse_args(argv)
    db = PaperCatalog(args.db)
    if args.command == "index":
        result = db.index_directory(args.papers_root)
    elif args.command == "search":
        result = db.search(args.query, args.limit)
    elif args.command == "paper":
        result = db.paper(args.arxiv_id)
    elif args.command == "citations":
        result = db.citations(args.arxiv_id)
    elif args.command == "backlinks":
        result = db.cited_by(args.arxiv_id)
    else:
        result = db.overview()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result is None or (
        args.command == "index" and result["errors"]
    ) else 0


if __name__ == "__main__":
    raise SystemExit(run())
