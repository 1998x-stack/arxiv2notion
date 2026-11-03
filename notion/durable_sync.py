"""Durable Notion page writer with remote read-back and safe resume.

A unique title marker lets us rediscover a page when pages.create commits
server-side but its HTTP response is lost. The marker is deliberately visible:
Notion currently offers no client-supplied idempotency key for page creation.

Important: an unchanged remote snapshot after a timed-out write is NOT proof
the request failed. The default is to stop in an uncertain state; an operator
can opt into replay only after independent reconciliation.
"""
from __future__ import annotations

from hashlib import sha256
import json
import time
from typing import Any

from loguru import logger
from notion_client.errors import APIResponseError

from config import NotionConfig
from models import CreationResult
from storage.import_journal import ImportConflict, ImportJournal, ImportUncertain


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


def _rich(items: list[dict]) -> list[dict]:
    result = []
    for item in items or []:
        kind = item.get("type", "text")
        if kind == "text":
            text = item.get("text") or {}
            attrs: dict[str, Any] = {
                "type": "text",
                "content": text.get("content", item.get("plain_text", "")),
            }
            link = (text.get("link") or {}).get("url") or item.get("href")
            if link:
                attrs["url"] = link
        elif kind == "equation":
            attrs = {
                "type": "equation",
                "expression": (item.get("equation") or {}).get("expression", ""),
            }
        else:
            # Unsupported rich_text must not be silently treated as equivalent.
            raise ImportConflict(f"Unsupported Notion rich-text kind: {kind}")
        style = item.get("annotations") or {}
        normalized_style = {
            key: value for key, value in style.items()
            if value not in (False, None, "default")
        }
        if normalized_style:
            attrs["annotations"] = normalized_style
        result.append(attrs)
    return result


class DurableNotionWriter:
    def __init__(
        self,
        *,
        client: Any,
        config: NotionConfig,
        journal: ImportJournal,
        allow_uncertain_retry: bool = False,
    ):
        self.client = client
        self.config = config
        self.journal = journal
        self.allow_uncertain_retry = allow_uncertain_retry
        self.batch_size = max(1, min(100, config.max_blocks_per_request))

    def _list_children(self, block_id: str) -> list[dict]:
        """Read all pages of children, not only Notion's first page of results."""
        cursor = None
        seen_cursors = set()
        children: list[dict] = []
        while True:
            kwargs: dict[str, Any] = {"block_id": block_id, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            response = self.client.blocks.children.list(**kwargs)
            children.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
            if not cursor or cursor in seen_cursors:
                raise ImportUncertain("Pagination cursor missing or repeated")
            seen_cursors.add(cursor)
            if len(seen_cursors) > 1000:
                raise ImportUncertain("Notion pagination exceeded safety limit")
        return children

    def _projection(self, block: dict, remote: bool) -> dict:
        kind = block.get("type")
        data = block.get(kind) or {}
        result: dict[str, Any] = {"type": kind}
        if kind == "table_row":
            result["cells"] = [_rich(cell) for cell in data.get("cells", [])]
        elif kind == "table":
            result["table_width"] = data.get("table_width")
            result["has_column_header"] = bool(data.get("has_column_header"))
            result["has_row_header"] = bool(data.get("has_row_header"))
        elif kind == "equation":
            result["expression"] = data.get("expression", "")
        elif kind in ("image", "bookmark", "embed"):
            if kind == "image":
                if data.get("type") != "external":
                    raise ImportConflict("Non-external image requires separate upload mapping")
                result["url"] = (data.get("external") or {}).get("url", "")
            else:
                result["url"] = data.get("url", "")
        elif kind == "divider" or kind == "table_of_contents":
            pass
        elif kind in ("paragraph", "heading_1", "heading_2", "heading_3",
                      "callout", "quote", "code", "bulleted_list_item",
                      "numbered_list_item", "toggle"):
            result["rich_text"] = _rich(data.get("rich_text", []))
            color = data.get("color")
            if color and color != "default":
                result["color"] = color
            if kind == "callout":
                result["icon"] = (data.get("icon") or {}).get("emoji")
            if kind == "code":
                result["language"] = data.get("language", "")
        else:
            raise ImportConflict(f"Unsupported Notion block kind: {kind}")
        if kind in ("image", "bookmark"):
            result["caption"] = _rich(data.get("caption", []))

        if remote and block.get("has_children"):
            child_blocks = self._list_children(block["id"])
        else:
            child_blocks = data.get("children", [])
        if child_blocks:
            result["children"] = [
                self._projection(child, remote=remote) for child in child_blocks
            ]
        return result

    def _snapshot(self, page_id: str, expected: list[dict]) -> int:
        """Return matched top-level prefix length or fail closed on any drift."""
        top_level = [
            block for block in self._list_children(page_id)
            if block.get("type") != "child_page"
        ]
        if len(top_level) > len(expected):
            raise ImportConflict(
                f"Remote page contains {len(top_level)} content blocks; "
                f"expected {len(expected)}"
            )
        for idx, remote_block in enumerate(top_level):
            actual = self._projection(remote_block, remote=True)
            wanted = self._projection(expected[idx], remote=False)
            if actual != wanted:
                raise ImportConflict(
                    f"Remote block mismatch at offset {idx}; "
                    "manual edits or unexpected API normalization require review"
                )
        return len(top_level)

    def _lookup(self, parent_id: str, marker: str) -> list[str]:
        found = []
        for block in self._list_children(parent_id):
            if block.get("type") != "child_page":
                continue
            title = (block.get("child_page") or {}).get("title", "")
            if title.endswith(marker):
                found.append(block["id"])
        return found

    def _rate_limit_call(self, call, **kwargs):
        for attempt in range(max(1, self.config.max_retries)):
            try:
                time.sleep(self.config.rate_limit_delay)
                return call(**kwargs)
            except APIResponseError as exc:
                if exc.code != "rate_limited":
                    raise
                if attempt + 1 >= max(1, self.config.max_retries):
                    raise
                retry_after = (getattr(exc, "headers", None) or {}).get(
                    "retry-after"
                )
                try:
                    wait = max(0.0, float(retry_after)) if retry_after else 2 ** attempt
                except (ValueError, TypeError):
                    wait = 2 ** attempt
                time.sleep(wait)
        raise ImportUncertain("Request retry budget exceeded")

    def sync_page(
        self,
        *,
        parent_id: str,
        resource_id: str,
        kind: str,
        title: str,
        icon: str,
        blocks: list[dict],
    ) -> CreationResult:
        from notion.validator import validate_notion_blocks
        validate_notion_blocks(blocks)
        if not blocks:
            return CreationResult(
                success=False, title=title, error="Refusing an empty page payload",
            )
        logical_key = self.journal.key(parent_id, kind, resource_id)
        marker = f"⟦A2N:{logical_key[:16]}⟧"
        remote_title = f"{title[:max(1, 2000-len(marker)-1)]} {marker}"
        payload_hash = _hash([self._projection(b, remote=False) for b in blocks])
        key = owner = None
        try:
            key, owner, job = self.journal.acquire(
                parent_id=parent_id, kind=kind, resource_id=resource_id,
                marker_title=remote_title, payload_hash=payload_hash,
                expected_blocks=len(blocks),
            )
            page_id = job["page_id"]
            # Detect duplicates even if this process already knows a page ID.
            # Otherwise an old duplicate could be silently treated as success.
            found = self._lookup(parent_id, marker)
            if len(found) > 1:
                raise ImportConflict("Multiple marked Notion pages; manual deduplication required")
            if page_id and found and page_id != found[0]:
                raise ImportConflict("Journal page ID differs from marked Notion page")
            if not page_id:
                if found:
                    page_id = found[0]
                    self.journal.update(key, owner, status="discovered", page_id=page_id)
                elif job["status"] != "new":
                    raise ImportUncertain(
                        "Page-create request was previously attempted, but "
                        "no marked page was found; do not create another"
                    )
            if not page_id:
                first_batch = blocks[:self.batch_size]
                self.journal.batch_intent(
                    key, owner, 0, len(first_batch),
                    _hash([self._projection(x, False) for x in first_batch]),
                )
                self.journal.update(key, owner, status="create_in_flight")
                try:
                    created = self._rate_limit_call(
                        self.client.pages.create,
                        parent={"page_id": parent_id},
                        icon={"emoji": icon},
                        properties={"title": [{"text": {"content": remote_title}}]},
                        children=first_batch,
                    )
                    page_id = created["id"]
                    self.journal.update(
                        key, owner, status="created", page_id=page_id,
                    )
                except Exception as exc:
                    # The server may have committed despite losing its response.
                    found = self._lookup(parent_id, marker)
                    if len(found) != 1:
                        raise ImportUncertain(
                            f"Create outcome uncertain; found {len(found)} marked pages: {exc}"
                        ) from exc
                    page_id = found[0]
                    self.journal.update(
                        key, owner, status="discovered", page_id=page_id,
                    )

            # The remote is the source of truth, not a successful HTTP response.
            try:
                remote_count = self._snapshot(page_id, blocks)
            except ImportConflict:
                raise
            except Exception as exc:
                raise ImportUncertain(f"Remote read-back failed: {exc}") from exc
            self.journal.mark_verified(key, owner, remote_count)

            batches = self.journal.batches(key)
            inflight = [b for b in batches if b["status"] == "in_flight"]
            for batch in inflight:
                boundary = batch["batch_offset"] + batch["batch_count"]
                if remote_count >= boundary:
                    self.journal.batch_confirm(
                        key, owner, batch["batch_offset"], batch["batch_count"],
                    )
                elif remote_count == batch["batch_offset"]:
                    if not self.allow_uncertain_retry:
                        raise ImportUncertain(
                            f"Previously in-flight batch at {remote_count} not "
                            "observed remotely; explicit reconciliation is required"
                        )
                else:
                    raise ImportConflict("Remote has a partially applied batch")

            # The first batch must have been atomically created by Notion.
            if remote_count < min(self.batch_size, len(blocks)):
                raise ImportConflict(
                    "Created page is missing some initial blocks; not safe to append"
                )

            while remote_count < len(blocks):
                end = min(remote_count + self.batch_size, len(blocks))
                batch = blocks[remote_count:end]
                self.journal.batch_intent(
                    key, owner, remote_count, len(batch),
                    _hash([self._projection(x, False) for x in batch]),
                )
                self.journal.update(key, owner, status="append_in_flight")
                request_error = None
                try:
                    self._rate_limit_call(
                        self.client.blocks.children.append,
                        block_id=page_id, children=batch,
                    )
                except Exception as exc:
                    request_error = exc
                try:
                    observed = self._snapshot(page_id, blocks)
                except ImportConflict:
                    raise
                except Exception as exc:
                    raise ImportUncertain(
                        f"Cannot confirm append at {remote_count}: {exc}"
                    ) from exc
                if observed == end:
                    self.journal.batch_confirm(
                        key, owner, remote_count, len(batch),
                    )
                    self.journal.mark_verified(key, owner, observed)
                    remote_count = observed
                    continue
                if observed == remote_count:
                    raise ImportUncertain(
                        f"Append at {remote_count} not confirmed; "
                        f"error={request_error!r}; no blind retry"
                    )
                raise ImportConflict(
                    f"Remote append count unexpected: {observed}, wanted {end}"
                )

            self.journal.update(
                key, owner, status="complete",
                page_id=page_id, confirmed_blocks=remote_count,
            )
            return CreationResult(
                success=True, page_id=page_id, title=title,
                url=f"https://www.notion.so/{page_id.replace('-', '')}",
                blocks_created=remote_count,
            )
        except (ImportConflict, ImportUncertain) as exc:
            logger.error(f"Durable sync stopped safely: {exc}")
            if key and owner:
                self.journal.update(
                    key, owner,
                    status="conflict" if isinstance(exc, ImportConflict) else "uncertain",
                    error=str(exc),
                )
            job = self.journal.get(logical_key)
            return CreationResult(
                success=False, title=title,
                page_id=job["page_id"] if job else None,
                blocks_created=job["confirmed_blocks"] if job else 0,
                error=str(exc),
            )
        except Exception as exc:
            logger.exception("Durable sync encountered unexpected error")
            if key and owner:
                self.journal.update(
                    key, owner, status="uncertain",
                    error=f"Unexpected error: {exc}",
                )
            job = self.journal.get(logical_key)
            return CreationResult(
                success=False, title=title,
                page_id=job["page_id"] if job else None,
                blocks_created=job["confirmed_blocks"] if job else 0,
                error=f"Unexpected sync error: {exc}",
            )
        finally:
            if key and owner:
                self.journal.release(key, owner)
