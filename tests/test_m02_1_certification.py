"""Read-only certification never mutates remote data."""
from types import SimpleNamespace
import pytest
from verify_notion import inspect_remote, inspect_journal
from storage.import_journal import ImportJournal


def test_remote_pagination_read_only():
    calls = []
    def get(**kwargs):
        calls.append("retrieve")
        return {"object": "page"}
    def listing(**kwargs):
        calls.append("list")
        if len(calls) == 2:
            return {"results": [{"type": "child_page"}],
                    "has_more": True, "next_cursor": "2"}
        return {"results": [{"type": "paragraph"}], "has_more": False}
    client = SimpleNamespace(
        pages=SimpleNamespace(retrieve=get),
        blocks=SimpleNamespace(children=SimpleNamespace(list=listing)),
    )
    result = inspect_remote("fake", "root", client)
    assert result["read_only_check"] == "passed"
    assert result["root_child_blocks"] == 2
    assert result["live_write_certified"] is False
    assert calls == ["retrieve", "list", "list"]


def test_missing_credentials_rejected():
    with pytest.raises(ValueError, match="required"):
        inspect_remote("", "root")


def test_sqlite_diagnostics(tmp_path):
    db = tmp_path / "jobs.sqlite3"
    assert inspect_journal(db)["status"] == "missing"
    journal = ImportJournal(db)
    key, owner, _ = journal.acquire(
        parent_id="root", resource_id="1706.03762", kind="paper",
        marker_title="test", payload_hash="a", expected_blocks=1)
    journal.update(key, owner, status="uncertain", error="timeout")
    journal.release(key, owner)
    report = inspect_journal(db)
    assert report["by_state"]["uncertain"] == 1
    assert report["requires_attention"][0]["error"] == "timeout"
