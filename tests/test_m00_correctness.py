"""Regression tests for M00 import correctness. No external services required."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from config import NotionConfig
from models import Ar5ivContent, CreationResult, PaperData, PaperStatus, Reference
from notion.creator import NotionCreator
from notion.validator import NotionPayloadError, validate_notion_blocks
from storage.file_manager import FileManager
from utils import is_valid_arxiv_id


@pytest.fixture
def creator():
    return NotionCreator(NotionConfig(token="fake_token", root_page_id="fake_root"))


def _paragraph(text="example"):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def test_invalid_initial_blocks_do_not_create_empty_page(monkeypatch, creator):
    import notion.creator as creator_module

    class ValidationError(Exception):
        code = "validation_error"
        message = "invalid block"

    create = Mock(side_effect=ValidationError())
    creator.client = SimpleNamespace(pages=SimpleNamespace(create=create))
    monkeypatch.setattr(creator_module, "APIResponseError", ValidationError)
    monkeypatch.setattr(creator_module.time, "sleep", lambda _: None)
    result = creator._create_page_sync("parent", "title", blocks=[_paragraph()])
    assert result.success is False
    assert "validation_error" in result.error
    assert create.call_count == 1


def test_unknown_create_outcome_is_not_blindly_retried(monkeypatch, creator):
    import notion.creator as creator_module

    create = Mock(side_effect=TimeoutError("response lost"))
    creator.client = SimpleNamespace(pages=SimpleNamespace(create=create))
    monkeypatch.setattr(creator_module.time, "sleep", lambda _: None)
    result = creator._create_page_sync("parent", "title", blocks=[_paragraph()])
    assert result.success is False
    assert "uncertain" in result.error
    assert create.call_count == 1


def test_partial_append_is_not_success(creator):
    paper = PaperData(arxiv_id="1706.03762")
    creator.converter.convert_paper = Mock(return_value=[_paragraph()] * 105)
    creator._create_page_sync = Mock(
        return_value=CreationResult(success=True, page_id="page-1", blocks_created=100)
    )
    creator._append_blocks_batched = Mock(return_value=3)
    result = creator.create_paper_page(paper)
    assert result.success is False
    assert result.page_id == "page-1"
    assert result.blocks_created == 103
    assert "103/105" in result.error


def test_no_refs_disables_reference_subpage_creation(creator):
    paper = PaperData(
        arxiv_id="1706.03762",
        content=Ar5ivContent(
            paper_id="1706.03762",
            title="Test",
            references=[Reference(raw_text="Citation", arxiv_id="1810.04805")],
        ),
    )
    creator.create_paper_page = Mock(
        return_value=CreationResult(success=True, page_id="page-1")
    )
    creator.create_reference_page = Mock()
    result = creator.create_paper_with_references(paper, with_references=False)
    assert result.success
    creator.create_reference_page.assert_not_called()


def test_reference_creation_failures_mark_import_incomplete(creator):
    paper = PaperData(
        arxiv_id="1706.03762",
        content=Ar5ivContent(
            paper_id="1706.03762", title="Test",
            references=[Reference(raw_text="Citation", arxiv_id="1810.04805")],
        ),
    )
    creator.create_paper_page = Mock(
        return_value=CreationResult(success=True, page_id="page-1")
    )
    creator.create_reference_page = Mock(
        return_value=CreationResult(success=False, error="rate limit")
    )
    result = creator.create_paper_with_references(paper, with_references=True)
    assert not result.success
    assert "1810.04805" in result.error
    assert result.page_id == "page-1"


@pytest.mark.parametrize("arxiv_id", [
    "1706.03762", "2402.01030v4", "hep-th/9901001", "math-ph/0301001"
])
def test_valid_arxiv_ids(arxiv_id):
    assert is_valid_arxiv_id(arxiv_id)


@pytest.mark.parametrize("arxiv_id", [
    "", "../etc/passwd", "2601.12345/../../../tmp", "foo", "1706.03762?x=1"
])
def test_reject_invalid_arxiv_ids(arxiv_id):
    assert not is_valid_arxiv_id(arxiv_id)


def test_file_manager_rejects_path_traversal(tmp_path):
    fm = FileManager(base_dir=tmp_path)
    with pytest.raises(ValueError):
        fm.get_paper_dir("../bad", "deep_learning")
    with pytest.raises(ValueError):
        fm.get_paper_dir("1706.03762", "../../bad")
    assert not (tmp_path / "bad").exists()


def test_file_manager_legacy_id_stays_in_one_directory(tmp_path):
    fm = FileManager(base_dir=tmp_path)
    assert fm.get_paper_dir("hep-th/9901001", "other") == (
        tmp_path / "papers" / "other" / "hep-th__9901001"
    )


def test_payload_rejects_oversized_text():
    payload = _paragraph("x" * 2001)
    with pytest.raises(NotionPayloadError, match="2000"):
        validate_notion_blocks([payload])


def test_payload_rejects_oversized_equation():
    payload = {"type": "equation", "equation": {"expression": "x" * 1001}}
    with pytest.raises(NotionPayloadError, match="1000"):
        validate_notion_blocks([payload])


def test_payload_rejects_oversized_batch():
    blocks = [{
        "type": "paragraph",
        "paragraph": {"rich_text": [
            {"type": "text", "text": {"content": "x" * 2000}}
            for _ in range(4)
        ]},
    } for _ in range(100)]
    with pytest.raises(NotionPayloadError, match="500 KB"):
        validate_notion_blocks(blocks)


def test_converter_error_is_propagated(monkeypatch):
    from notion.converter import NotionConverter

    converter = NotionConverter()
    def boom(_paper):
        raise ValueError("invalid document")
    monkeypatch.setattr(converter, "_create_header", boom)
    with pytest.raises(ValueError, match="invalid document"):
        converter.convert_paper(PaperData(arxiv_id="1706.03762"))


def test_cli_accepts_from_file_without_positional_arxiv_id():
    from main import build_parser

    args = build_parser().parse_args(["--from-file", "example.json", "--no-refs"])
    assert args.arxiv_ids == []
    assert args.from_file == "example.json"
    assert args.no_refs is True


@pytest.mark.asyncio
async def test_no_refs_overrides_from_file(tmp_path, monkeypatch):
    import json
    import main as entry

    config_file = tmp_path / "input.json"
    config_file.write_text(json.dumps({
        "arxiv_id": "1706.03762",
        "import_options": {"with_refs": True, "annotate": False},
    }))
    captured = {}

    class FakeProcessor:
        def __init__(self, config):
            pass

        async def process_paper(self, arxiv_id, **kwargs):
            captured.update(kwargs)
            return PaperData(
                arxiv_id=arxiv_id,
                status=PaperStatus.COMPLETED,
                notion_page_id="dummy",
            )

    monkeypatch.setenv("NOTION_TOKEN", "test")
    monkeypatch.setenv("NOTION_ROOT_PAGE_ID", "test")
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(entry, "Ar5ivToNotion", FakeProcessor)
    monkeypatch.setattr(entry, "setup_logging", lambda **kwargs: None)
    args = entry.build_parser().parse_args([
        "--from-file", str(config_file), "--no-refs",
    ])
    args.with_refs = False  # entry.main() applies explicit CLI opt-out
    await entry.main_async(args)
    assert captured["with_references"] is False
