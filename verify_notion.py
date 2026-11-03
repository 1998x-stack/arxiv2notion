"""Read-only Notion and import journal diagnostics. Never writes to Notion."""
import argparse
import json
import os
from pathlib import Path
import sqlite3


def inspect_journal(path):
    path = Path(path)
    if not path.exists():
        return {"status": "missing", "jobs": 0}
    db = sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)
    try:
        rows = db.execute("SELECT status, COUNT(*) FROM import_jobs GROUP BY status").fetchall()
        issues = db.execute(
            "SELECT resource_id, status, confirmed_blocks, expected_blocks, last_error "
            "FROM import_jobs WHERE status NOT IN ('complete','new') ORDER BY updated_at DESC LIMIT 20"
        ).fetchall()
        return {"status": "available", "jobs": sum(n for _, n in rows),
                "by_state": dict(rows),
                "requires_attention": [dict(zip(
                    ("resource_id","status","confirmed_blocks","expected_blocks","error"), row
                )) for row in issues]}
    finally:
        db.close()


def inspect_remote(token, root_id, client=None):
    if not token or not root_id:
        raise ValueError("NOTION_TOKEN and NOTION_ROOT_PAGE_ID required")
    if client is None:
        from notion_client import Client
        client = Client(auth=token, retry=False)
    page = client.pages.retrieve(page_id=root_id)
    if page.get("object") != "page":
        raise ValueError("Notion root page not accessible")
    cursor, seen, count = None, set(), 0
    while True:
        args = {"block_id": root_id, "page_size": 100}
        if cursor:
            args["start_cursor"] = cursor
        result = client.blocks.children.list(**args)
        count += len(result.get("results", []))
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")
        if not cursor or cursor in seen or len(seen) >= 1000:
            raise ValueError("Unsafe Notion pagination")
        seen.add(cursor)
    return {"read_only_check": "passed", "root_child_blocks": count,
            "live_write_certified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("IMPORT_STATE_DB", "./data/imports.sqlite3"))
    parser.add_argument("--remote", action="store_true")
    args = parser.parse_args()
    report = {"journal": inspect_journal(args.db)}
    if args.remote:
        try:
            report["notion"] = inspect_remote(
                os.getenv("NOTION_TOKEN"), os.getenv("NOTION_ROOT_PAGE_ID"))
        except Exception as exc:
            report["notion"] = {"read_only_check": "failed", "error": str(exc)}
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
