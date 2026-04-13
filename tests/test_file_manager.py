"""Unit tests for FileManager."""
import json
from pathlib import Path
from datetime import datetime

import pytest


class TestFileManagerPaperDir:
    def test_get_paper_dir_returns_correct_path(self, tmp_path):
        from file_manager import FileManager
        fm = FileManager(base_dir=tmp_path)
        p = fm.get_paper_dir("1706.03762", "deep_learning")
        assert p == tmp_path / "papers" / "deep_learning" / "1706.03762"

    def test_save_metadata_creates_file(self, tmp_path):
        from file_manager import FileManager
        from models import ArxivMetadata, Author
        fm = FileManager(base_dir=tmp_path)
        meta = ArxivMetadata(
            arxiv_id="1706.03762",
            title="Attention Is All You Need",
            authors=[Author(name="Vaswani, A.")],
            abstract="...",
            categories=["cs.CL"],
            primary_category="cs.CL",
            published=datetime(2017, 6, 12),
            updated=datetime(2017, 12, 6),
        )
        fm.save_metadata("1706.03762", "deep_learning", meta)
        p = tmp_path / "papers" / "deep_learning" / "1706.03762" / "metadata.json"
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["arxiv_id"] == "1706.03762"
        assert data["title"] == "Attention Is All You Need"

    def test_save_content_md_creates_readable_file(self, tmp_path):
        from file_manager import FileManager
        from models import Ar5ivContent, Section
        fm = FileManager(base_dir=tmp_path)
        content = Ar5ivContent(
            paper_id="1706.03762",
            title="Attention Is All You Need",
            abstract="The dominant...",
            sections=[
                Section(title="Introduction", level=2, paragraphs=["First para."])
            ],
        )
        fm.save_content_md("1706.03762", "deep_learning", content)
        p = tmp_path / "papers" / "deep_learning" / "1706.03762" / "content.md"
        assert p.exists()
        text = p.read_text()
        assert "# Attention Is All You Need" in text
        assert "## Introduction" in text
        assert "First para." in text


class TestFileManagerAnnotations:
    def test_has_annotations_false_when_no_file(self, tmp_path):
        from file_manager import FileManager
        fm = FileManager(base_dir=tmp_path)
        assert fm.has_annotations("1706.03762", "deep_learning") is False

    def test_save_and_load_annotations_roundtrip(self, tmp_path, sample_annotation):
        from file_manager import FileManager
        fm = FileManager(base_dir=tmp_path)
        fm.save_annotations("1706.03762", "deep_learning", [sample_annotation])
        assert fm.has_annotations("1706.03762", "deep_learning") is True
        loaded = fm.load_annotations("1706.03762", "deep_learning")
        assert len(loaded) == 1
        assert loaded[0].section_title == sample_annotation.section_title
        assert loaded[0].plain_explanation == sample_annotation.plain_explanation
        assert loaded[0].cached is True  # must be marked cached when loaded


class TestFileManagerLogs:
    def test_log_import_appends_jsonl(self, tmp_path):
        from file_manager import FileManager
        fm = FileManager(base_dir=tmp_path)
        fm.log_import({"arxiv_id": "1706.03762", "status": "completed"})
        fm.log_import({"arxiv_id": "1810.04805", "status": "failed"})
        log_path = tmp_path / "logs" / "import.jsonl"
        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["arxiv_id"] == "1706.03762"

    def test_log_error_appends_jsonl(self, tmp_path):
        from file_manager import FileManager
        fm = FileManager(base_dir=tmp_path)
        fm.log_error({"arxiv_id": "1706.03762", "stage": "ar5iv_extract", "error_type": "TimeoutError"})
        log_path = tmp_path / "logs" / "errors.jsonl"
        assert log_path.exists()

    def test_log_llm_call_appends_jsonl(self, tmp_path):
        from file_manager import FileManager
        fm = FileManager(base_dir=tmp_path)
        fm.log_llm_call({"arxiv_id": "1706.03762", "tokens_in": 200, "tokens_out": 80})
        log_path = tmp_path / "logs" / "llm_calls.jsonl"
        assert log_path.exists()
