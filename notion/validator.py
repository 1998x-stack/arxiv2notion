"""Fail closed on known Notion request limits before remote writes."""
import json
from typing import Any


class NotionPayloadError(ValueError):
    """A block tree violates a Notion API payload limit."""


def validate_notion_blocks(blocks: list[dict[str, Any]]) -> None:
    if not isinstance(blocks, list):
        raise NotionPayloadError("Notion blocks must be a list")

    def walk(node: Any, path: str) -> None:
        if isinstance(node, list):
            if path.endswith(".children") and len(node) > 100:
                raise NotionPayloadError(f"{path}: more than 100 children")
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
        elif isinstance(node, dict):
            if node.get("type") == "text" and isinstance(node.get("text"), dict):
                if len(node["text"].get("content", "")) > 2000:
                    raise NotionPayloadError(f"{path}: text exceeds 2000 characters")
            if node.get("type") == "equation" and isinstance(node.get("equation"), dict):
                if len(node["equation"].get("expression", "")) > 1000:
                    raise NotionPayloadError(f"{path}: equation exceeds 1000 characters")
            for key, value in node.items():
                if key == "rich_text" and isinstance(value, list) and len(value) > 100:
                    raise NotionPayloadError(f"{path}.rich_text: more than 100 elements")
                walk(value, f"{path}.{key}")

    for i, block in enumerate(blocks):
        if not isinstance(block, dict) or not block.get("type"):
            raise NotionPayloadError(f"blocks[{i}]: invalid block")
        walk(block, f"blocks[{i}]")

    # Each batch, not the entire document, must fit the API request-size limit.
    for offset in range(0, len(blocks), 100):
        batch = blocks[offset:offset + 100]
        encoded = json.dumps({"children": batch}, ensure_ascii=False).encode("utf-8")
        if len(encoded) > 500_000:
            raise NotionPayloadError(
                f"blocks[{offset}:{offset+len(batch)}]: request exceeds 500 KB"
            )
