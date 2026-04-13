"""Tests for the 5 confirmed bug fixes."""
import sys
import traceback
from pathlib import Path

import pytest


class TestFormatException:
    def test_returns_clean_string_not_repr(self):
        """format_exception must return a clean traceback string, not repr(list)."""
        from utils import format_exception
        try:
            raise ValueError("test error")
        except ValueError:
            result = format_exception()

        assert not result.startswith("['")
        assert not result.startswith('["')
        assert "ValueError" in result
        assert "test error" in result

    def test_returns_string(self):
        from utils import format_exception
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            result = format_exception()
        assert isinstance(result, str)


class TestCacheConfigSubcacheDirs:
    def test_subcache_dirs_inherit_custom_cache_dir(self):
        """When cache_dir is custom, arxiv_cache_dir and ar5iv_cache_dir must follow it."""
        from config import CacheConfig
        custom = CacheConfig(cache_dir=Path("/tmp/my_cache"))
        assert custom.arxiv_cache_dir == Path("/tmp/my_cache/arxiv")
        assert custom.ar5iv_cache_dir == Path("/tmp/my_cache/ar5iv")

    def test_default_subcache_dirs(self):
        from config import CacheConfig
        cfg = CacheConfig()
        assert cfg.arxiv_cache_dir == cfg.cache_dir / "arxiv"
        assert cfg.ar5iv_cache_dir == cfg.cache_dir / "ar5iv"


class TestClientTimeout:
    def test_fetch_page_uses_client_timeout_object(self):
        """_fetch_page must pass a ClientTimeout object, not a raw int."""
        import inspect
        import aiohttp
        from ar5iv_extractor import Ar5ivExtractor
        source = inspect.getsource(Ar5ivExtractor._fetch_page)
        assert "ClientTimeout" in source, "_fetch_page must use aiohttp.ClientTimeout"


class TestDeadRateLimitWait:
    def test_rate_limit_wait_method_removed(self):
        """_rate_limit_wait dead async method must not exist on NotionCreator."""
        from notion_creator import NotionCreator
        assert not hasattr(NotionCreator, "_rate_limit_wait"), \
            "_rate_limit_wait is dead code and should be removed"


class TestQwenConfig:
    def test_qwen_config_defaults(self):
        from config import QwenConfig
        cfg = QwenConfig()
        assert cfg.model == "qwen-plus"
        assert cfg.enabled is True
        assert cfg.min_para_length == 100
        assert cfg.max_para_length == 1500

    def test_app_config_has_qwen_field(self):
        from config import get_test_config
        cfg = get_test_config()
        assert hasattr(cfg, "qwen")
        from config import QwenConfig
        assert isinstance(cfg.qwen, QwenConfig)


class TestParagraphAnnotation:
    def test_can_import_and_instantiate(self):
        from models import ParagraphAnnotation
        ann = ParagraphAnnotation(
            section_title="Intro",
            para_idx=0,
            para_text="Some text.",
            plain_explanation="通俗解读",
            key_points=["要点1", "要点2"],
        )
        assert ann.section_title == "Intro"
        assert ann.cached is False  # default

    def test_to_dict_roundtrip(self):
        from models import ParagraphAnnotation
        ann = ParagraphAnnotation(
            section_title="Methods",
            para_idx=2,
            para_text="Technical paragraph.",
            plain_explanation="方法说明",
            key_points=["A", "B"],
            cached=True,
        )
        d = ann.to_dict()
        assert d["section_title"] == "Methods"
        assert d["cached"] is True
        assert d["key_points"] == ["A", "B"]
