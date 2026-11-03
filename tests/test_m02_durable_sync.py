"""Offline M02 failure injection: SQLite journaling and real API call shapes."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from config import NotionConfig
from models import CreationResult, Reference
from notion.creator import NotionCreator
from notion.durable_sync import DurableNotionWriter
from storage.import_journal import ImportConflict, ImportJournal


def paragraph(value):
    return {
        "object": "block", "type": "paragraph",
        "paragraph": {"rich_text": [
            {"type": "text", "text": {"content": value}},
        ]},
    }


class FakeNotion:
    """Minimal Notion-compatible pages/blocks API backed by in-memory objects."""

    def __init__(self):
        self.tree = {"root": []}
        self.created_count = 0
        self.append_count = 0
        self.create_timeout_after_write = False
        self.append_timeout_after_write = False
        self.append_timeout_before_write = False
        self.pages = SimpleNamespace(create=self.create)
        self.blocks = SimpleNamespace(
            children=SimpleNamespace(list=self.list_children, append=self.append)
        )

    def _store(self, owner, blocks):
        for item in blocks:
            node = deepcopy(item)
            self.created_count += 1
            node_id = "block-" + str(self.created_count)
            node["id"] = node_id
            kind = node["type"]
            nested = node.get(kind, {}).pop("children", [])
            node["has_children"] = bool(nested)
            self.tree[owner].append(node)
            self.tree[node_id] = []
            if nested:
                self._store(node_id, nested)

    def create(self, *, parent, icon, properties, children):
        page_id = "page-" + str(
            sum(1 for nodes in self.tree.values()
                for item in nodes if item.get("type") == "child_page") + 1
        )
        title = properties["title"][0]["text"]["content"]
        self.tree[parent["page_id"]].append({
            "type": "child_page", "id": page_id,
            "child_page": {"title": title},
        })
        self.tree[page_id] = []
        self._store(page_id, children)
        if self.create_timeout_after_write:
            self.create_timeout_after_write = False
            raise TimeoutError("create response was lost")
        return {"id": page_id, "url": "https://www.notion.so/" + page_id}

    def list_children(self, *, block_id, page_size=100, start_cursor=None):
        items = self.tree[block_id]
        start = int(start_cursor or "0")
        page = items[start:start + page_size]
        next_pos = start + len(page)
        return {
            "results": deepcopy(page),
            "has_more": next_pos < len(items),
            "next_cursor": str(next_pos) if next_pos < len(items) else None,
        }

    def append(self, *, block_id, children):
        self.append_count += 1
        if self.append_timeout_before_write:
            self.append_timeout_before_write = False
            raise TimeoutError("append request failed before server wrote")
        self._store(block_id, children)
        if self.append_timeout_after_write:
            self.append_timeout_after_write = False
            raise TimeoutError("append response was lost")
        return {"results": []}


@pytest.fixture
def config():
    return NotionConfig(
        token="fake", root_page_id="root", rate_limit_delay=0,
        max_retries=1, max_blocks_per_request=100,
    )


@pytest.fixture
def remote():
    return FakeNotion()


@pytest.fixture
def journal(tmp_path):
    return ImportJournal(tmp_path / "state" / "imports.sqlite3")


def writer(remote, config, journal, *, retry=False):
    return DurableNotionWriter(
        client=remote, config=config, journal=journal,
        allow_uncertain_retry=retry,
    )


def sync(remote, config, journal, count=120, retry=False, content=None):
    blocks = [paragraph(str(i)) for i in range(count)] if content is None else content
    return writer(remote, config, journal, retry=retry).sync_page(
        parent_id="root", resource_id="1706.03762",
        kind="paper", title="A Paper", icon="📄", blocks=blocks,
    )


def job(journal):
    return journal.get(ImportJournal.key("root", "paper", "1706.03762"))


def test_create_and_append_are_read_back_verified(remote, config, journal):
    result = sync(remote, config, journal, count=215)
    assert result.success
    assert result.blocks_created == 215
    assert result.page_id == "page-1"
    assert len(remote.tree["page-1"]) == 215
    assert remote.append_count == 2
    assert job(journal)["confirmed_blocks"] == 215
    assert job(journal)["status"] == "complete"
    assert [b["status"] for b in journal.batches(job(journal)["job_key"])] == [
        "confirmed", "confirmed", "confirmed",
    ]


def test_duplicate_import_reuses_page_and_does_not_append(remote, config, journal):
    first = sync(remote, config, journal, count=105)
    second = sync(remote, config, journal, count=105)
    assert first.success and second.success
    assert first.page_id == second.page_id
    assert remote.append_count == 1
    assert len(remote.tree["root"]) == 1


def test_restart_uses_same_sqlite_checkpoints(remote, config, journal):
    first = sync(remote, config, journal, count=105)
    reopened = ImportJournal(journal.path)
    second = sync(remote, config, reopened, count=105)
    assert first.page_id == second.page_id
    assert second.success
    assert len(reopened.batches(job(reopened)["job_key"])) == 2


def test_create_committed_but_response_lost_is_discovered(remote, config, journal):
    remote.create_timeout_after_write = True
    result = sync(remote, config, journal, count=4)
    assert result.success
    assert len(remote.tree["root"]) == 1
    assert job(journal)["status"] == "complete"


def test_append_committed_but_response_lost_is_confirmed(remote, config, journal):
    remote.append_timeout_after_write = True
    result = sync(remote, config, journal, count=125)
    assert result.success
    assert result.blocks_created == 125
    assert remote.append_count == 1


def test_append_uncertain_stops_and_refuses_blind_resume(remote, config, journal):
    remote.append_timeout_before_write = True
    failed = sync(remote, config, journal, count=105)
    assert not failed.success
    assert "not confirmed" in failed.error
    assert failed.page_id == "page-1"
    assert job(journal)["status"] == "uncertain"
    second = sync(remote, config, journal, count=105)
    assert not second.success
    assert "reconciliation" in second.error
    assert remote.append_count == 1
    assert len(remote.tree["page-1"]) == 100


def test_explicit_retry_after_reconciliation_is_not_automatic(remote, config, journal):
    remote.append_timeout_before_write = True
    assert not sync(remote, config, journal, count=105).success
    resumed = sync(remote, config, journal, count=105, retry=True)
    assert resumed.success
    assert len(remote.tree["page-1"]) == 105
    assert remote.append_count == 2


def test_existing_remote_edit_causes_conflict(remote, config, journal):
    assert sync(remote, config, journal, count=5).success
    remote.tree["page-1"][0]["paragraph"]["rich_text"][0]["text"]["content"] = "human edit"
    result = sync(remote, config, journal, count=5)
    assert not result.success
    assert "mismatch" in result.error
    assert remote.append_count == 0


def test_changed_document_does_not_mutate_existing_page(remote, config, journal):
    assert sync(remote, config, journal, count=5).success
    changed = [paragraph("new content")] * 5
    result = sync(remote, config, journal, count=5, content=changed)
    assert not result.success
    assert "different content" in result.error
    assert len(remote.tree["root"]) == 1


def test_never_create_another_page_when_first_outcome_unknown(remote, config, journal):
    # Emulate a process that recorded intent and died before the HTTP reply,
    # when no marked page is discoverable.
    blocks = [paragraph("0")]
    w = writer(remote, config, journal)
    from notion.durable_sync import _hash
    payload = _hash([w._projection(b, remote=False) for b in blocks])
    marker = "⟦A2N:" + ImportJournal.key("root", "paper", "1706.03762")[:16] + "⟧"
    key, owner, record = journal.acquire(
        parent_id="root", kind="paper", resource_id="1706.03762",
        marker_title="A Paper " + marker, payload_hash=payload,
        expected_blocks=1,
    )
    journal.update(key, owner, status="create_in_flight")
    journal.release(key, owner)
    failed = sync(remote, config, journal, count=1)
    assert not failed.success
    assert "do not create another" in failed.error
    assert not remote.tree["root"]


def test_concurrent_claim_is_rejected(journal):
    args = dict(
        parent_id="root", resource_id="1706.03762", kind="paper",
        marker_title="A Paper", payload_hash="contenthash", expected_blocks=2,
    )
    key, owner, _ = journal.acquire(**args)
    with pytest.raises(ImportConflict, match="leased"):
        ImportJournal(journal.path).acquire(**args)
    journal.release(key, owner)
    _, owner2, _ = journal.acquire(**args)
    journal.release(key, owner2)


def test_journal_batch_rejects_conflicting_payload(journal):
    args = dict(
        parent_id="root", resource_id="1706.03762", kind="paper",
        marker_title="A Paper", payload_hash="contenthash", expected_blocks=2,
    )
    key, owner, _ = journal.acquire(**args)
    journal.batch_intent(key, owner, 0, 2, "hash-a")
    with pytest.raises(ImportConflict, match="different payload"):
        journal.batch_intent(key, owner, 0, 2, "hash-b")
    journal.release(key, owner)


def test_reference_page_idempotence(remote, config, journal):
    creator = NotionCreator(config, journal=journal)
    creator.client = remote
    ref = Reference(raw_text="Test reference", arxiv_id="2401.00123")
    first = creator.create_reference_page(ref, "root")
    second = creator.create_reference_page(ref, "root")
    assert first.success and second.success
    assert first.page_id == second.page_id
    assert len(remote.tree["root"]) == 1


def test_remote_child_page_discovery_precedes_creating_new_page(
    remote, config, journal
):
    # A separate process created this marker-bearing page but no local page ID.
    key = ImportJournal.key("root", "paper", "1706.03762")
    marked = f"A Paper ⟦A2N:{key[:16]}⟧"
    remote.create(
        parent={"page_id": "root"}, icon={"emoji": "📄"},
        properties={"title": [{"text": {"content": marked}}]},
        children=[paragraph("0")],
    )
    result = sync(remote, config, journal, count=1)
    assert result.success
    assert result.page_id == "page-1"
    assert len(remote.tree["root"]) == 1


def test_remote_table_and_nested_blocks_readback(remote, config, journal):
    from notion.blocks import NotionBlockBuilder
    blocks = [
        NotionBlockBuilder.table(["a", "b"], [["x", "y"], ["z", "w"]]),
        NotionBlockBuilder.toggle(
            "Read more", children=[NotionBlockBuilder.paragraph("long note")],
        ),
        NotionBlockBuilder.image("https://example.org/image.png", "Figure"),
    ]
    result = sync(remote, config, journal, content=blocks)
    assert result.success
    assert sync(remote, config, journal, content=blocks).success
    assert len(remote.tree["root"]) == 1


def test_paginated_remote_readback(remote, config, journal):
    assert sync(remote, config, journal, count=235).success
    assert sync(remote, config, journal, count=235).success
    assert remote.append_count == 2
