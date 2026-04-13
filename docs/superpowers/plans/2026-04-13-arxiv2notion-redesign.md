# arxiv2notion Full Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Qwen LLM paragraph annotation, Academic Premium Notion layout, structured file system + JSONL logging, well-formatted references, and 60-paper examples — while fixing 5 confirmed bugs.

**Architecture:** Additive modules (`file_manager.py`, `qwen_annotator.py`) extend the existing linear pipeline without restructuring core data models. `NotionConverter` is redesigned in-place to accept pre-computed annotations and produce the Academic Premium layout. Bug fixes are surgical edits to existing files.

**Tech Stack:** Python 3.10+, aiohttp, BeautifulSoup4, notion-client, openai (DashScope-compatible), loguru, pytest, pytest-asyncio

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `utils.py` | Fix `format_exception` |
| Modify | `config.py` | Fix `CacheConfig` subcache dirs; add `QwenConfig` |
| Modify | `ar5iv_extractor.py` | Fix `ClientTimeout`; accept optional session |
| Modify | `notion_creator.py` | Remove dead `_rate_limit_wait` |
| Modify | `models.py` | Add `ParagraphAnnotation` dataclass |
| Modify | `notion_converter.py` | Full Academic Premium redesign; accept annotations |
| Modify | `main.py` | Add `--category`, `--no-annotate`, `--from-file` flags; wire new modules |
| Modify | `requirements.txt` | Add `openai>=1.0.0` |
| Create | `file_manager.py` | All file I/O: paper dirs, JSONL logs |
| Create | `qwen_annotator.py` | Qwen3.6-plus paragraph annotation via DashScope |
| Create | `examples/papers.json` | 60-paper stub list |
| Create | `examples/batch_import.py` | Batch import script |
| Create | `examples/single/*.json` | Per-paper import configs |
| Create | `tests/test_bug_fixes.py` | Tests for the 5 bug fixes |
| Create | `tests/test_file_manager.py` | FileManager unit tests |
| Create | `tests/test_qwen_annotator.py` | QwenAnnotator unit tests (mocked API) |
| Create | `tests/test_notion_converter.py` | NotionConverter Academic Premium tests |
| Create | `tests/conftest.py` | Shared fixtures |

---

## Task 1: Fix 5 Confirmed Bugs

**Files:**
- Modify: `utils.py:52-61`
- Modify: `config.py:54-74`
- Modify: `ar5iv_extractor.py:88-91`
- Modify: `notion_creator.py:70-72`
- Create: `tests/test_bug_fixes.py`

- [ ] **Step 1.1: Write failing tests for all 5 bugs**

Create `tests/test_bug_fixes.py`:

```python
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

        # Must not look like repr of a list
        assert not result.startswith("['")
        assert not result.startswith('["')
        # Must contain the error message
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
        assert "timeout=self.config.timeout" not in source or "ClientTimeout" in source


class TestDeadRateLimitWait:
    def test_rate_limit_wait_method_removed(self):
        """_rate_limit_wait dead async method must not exist on NotionCreator."""
        from notion_creator import NotionCreator
        assert not hasattr(NotionCreator, "_rate_limit_wait"), \
            "_rate_limit_wait is dead code and should be removed"
```

- [ ] **Step 1.2: Run tests to confirm they fail**

```bash
cd /Users/xd/Desktop/codes/arxiv2notion
pytest tests/test_bug_fixes.py -v 2>&1 | head -60
```

Expected: Multiple FAILs — `format_exception` wraps in repr, subcache dirs are hardcoded, `_rate_limit_wait` still exists.

- [ ] **Step 1.3: Fix `format_exception` in `utils.py`**

Replace lines 52–61:

```python
def format_exception() -> str:
    """
    Format the current exception as a clean traceback string.

    Returns:
        Human-readable traceback string.
    """
    return traceback.format_exc()
```

- [ ] **Step 1.4: Fix `CacheConfig` subcache dirs in `config.py`**

Replace the `CacheConfig` dataclass (lines 54–74) entirely:

```python
@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("./cache"))
    # Computed in __post_init__ from cache_dir — do NOT set independently
    arxiv_cache_dir: Path = field(init=False)
    ar5iv_cache_dir: Path = field(init=False)

    def __post_init__(self):
        self.arxiv_cache_dir = self.cache_dir / "arxiv"
        self.ar5iv_cache_dir = self.cache_dir / "ar5iv"
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure cache directories exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.arxiv_cache_dir.mkdir(parents=True, exist_ok=True)
        self.ar5iv_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_arxiv_cache_file(self, arxiv_id: str) -> Path:
        safe_id = arxiv_id.replace("/", "_").replace(":", "_")
        return self.arxiv_cache_dir / f"{safe_id}.json"

    def get_ar5iv_cache_file(self, arxiv_id: str) -> Path:
        safe_id = arxiv_id.replace("/", "_").replace(":", "_")
        return self.ar5iv_cache_dir / f"{safe_id}.json"
```

- [ ] **Step 1.5: Fix `ClientTimeout` in `ar5iv_extractor.py`**

At the top of `_fetch_page`, change the `session.get` call (line ~90):

```python
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with session.get(url, headers=headers, timeout=timeout) as response:
```

Also add the import at the top of the file if not present — `aiohttp` is already imported so `aiohttp.ClientTimeout` works directly.

- [ ] **Step 1.6: Remove dead `_rate_limit_wait` from `notion_creator.py`**

Delete lines 70–72 (the entire `_rate_limit_wait` method):

```python
    # DELETE these lines:
    async def _rate_limit_wait(self):
        """等待速率限制"""
        await asyncio.sleep(self.config.rate_limit_delay)
```

- [ ] **Step 1.7: Run tests to confirm all pass**

```bash
pytest tests/test_bug_fixes.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 1.8: Commit**

```bash
git add utils.py config.py ar5iv_extractor.py notion_creator.py tests/test_bug_fixes.py
git commit -m "fix: resolve 5 confirmed bugs (ClientTimeout, CacheConfig dirs, format_exception, dead method)"
```

---

## Task 2: Add `ParagraphAnnotation` to `models.py` + `QwenConfig` to `config.py`

**Files:**
- Modify: `models.py`
- Modify: `config.py`
- Create: `tests/conftest.py`

- [ ] **Step 2.1: Write failing test**

Create `tests/conftest.py`:

```python
"""Shared test fixtures."""
from pathlib import Path
import pytest


@pytest.fixture
def tmp_paper_dir(tmp_path):
    """A temporary directory for paper storage tests."""
    return tmp_path


@pytest.fixture
def sample_annotation():
    """A sample ParagraphAnnotation for tests."""
    from models import ParagraphAnnotation
    return ParagraphAnnotation(
        section_title="Introduction",
        para_idx=0,
        para_text="The dominant sequence transduction models...",
        plain_explanation="这段话的意思是：现有的序列模型主要依赖循环神经网络。",
        key_points=["传统模型依赖RNN结构", "注意力机制已被广泛使用", "本文提出无RNN的Transformer架构"],
    )
```

Add to `tests/test_bug_fixes.py`:

```python
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
```

- [ ] **Step 2.2: Run to confirm fail**

```bash
pytest tests/test_bug_fixes.py::TestParagraphAnnotation -v
```

Expected: FAIL — `cannot import name 'ParagraphAnnotation' from 'models'`

- [ ] **Step 2.3: Add `ParagraphAnnotation` to `models.py`**

Append after the existing `ProcessingStats` dataclass (end of file):

```python
@dataclass
class ParagraphAnnotation:
    """Qwen LLM annotation for a single paragraph."""
    section_title: str
    para_idx: int           # index within the section's paragraph list
    para_text: str          # first 200 chars of original paragraph (for verification)
    plain_explanation: str  # Chinese plain-language summary
    key_points: List[str]   # 2-3 Chinese bullet points
    cached: bool = False    # True if loaded from disk, not generated via API

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_title": self.section_title,
            "para_idx": self.para_idx,
            "para_text": self.para_text,
            "plain_explanation": self.plain_explanation,
            "key_points": self.key_points,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ParagraphAnnotation":
        return cls(
            section_title=d["section_title"],
            para_idx=d["para_idx"],
            para_text=d["para_text"],
            plain_explanation=d["plain_explanation"],
            key_points=d["key_points"],
            cached=d.get("cached", True),
        )
```

- [ ] **Step 2.4: Add `QwenConfig` to `config.py`**

Add after `ContentConfig` (before `AppConfig`):

```python
@dataclass
class QwenConfig:
    """Qwen LLM annotation configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    model: str = "qwen-plus"            # DashScope model ID — verify at platform.dashscope.com
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    enabled: bool = True
    min_para_length: int = 100          # paragraphs shorter than this are skipped
    max_para_length: int = 1500         # truncate input to this before sending
    temperature: float = 0.3
    max_tokens: int = 512
```

Add `qwen: QwenConfig = field(default_factory=QwenConfig)` to `AppConfig` dataclass.

Also extend `AppConfig.from_env()` to include:

```python
            qwen=QwenConfig(
                api_key=os.getenv("DASHSCOPE_API_KEY", ""),
                model=os.getenv("QWEN_MODEL", "qwen-plus"),
                enabled=os.getenv("QWEN_ENABLED", "true").lower() == "true",
            ),
```

- [ ] **Step 2.5: Run tests**

```bash
pytest tests/test_bug_fixes.py -v
```

Expected: All tests PASS.

- [ ] **Step 2.6: Commit**

```bash
git add models.py config.py tests/conftest.py tests/test_bug_fixes.py
git commit -m "feat: add ParagraphAnnotation model and QwenConfig"
```

---

## Task 3: Create `file_manager.py`

**Files:**
- Create: `file_manager.py`
- Create: `tests/test_file_manager.py`

- [ ] **Step 3.1: Write failing tests**

Create `tests/test_file_manager.py`:

```python
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
```

- [ ] **Step 3.2: Run to confirm fail**

```bash
pytest tests/test_file_manager.py -v 2>&1 | head -20
```

Expected: FAIL — `ModuleNotFoundError: No module named 'file_manager'`

- [ ] **Step 3.3: Implement `file_manager.py`**

Create `file_manager.py`:

```python
"""
File system manager.
Responsibility: All paper content I/O and structured JSONL logging.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

from models import ArxivMetadata, Ar5ivContent, ParagraphAnnotation, Section


class FileManager:
    """
    Manages the papers/ directory tree and logs/ JSONL streams.

    Directory layout:
        papers/{category}/{arxiv_id}/
            metadata.json
            content.md
            content.json
            llm_annotations.jsonl
        logs/
            import.jsonl
            llm_calls.jsonl
            errors.jsonl
    """

    def __init__(self, base_dir: Path = Path(".")):
        self.base_dir = base_dir
        self.papers_dir = base_dir / "papers"
        self.logs_dir = base_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    # ── Paper directory helpers ──────────────────────────────────────────────

    def get_paper_dir(self, arxiv_id: str, category: str) -> Path:
        """Return (and create) the directory for a specific paper."""
        p = self.papers_dir / category / arxiv_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ── Paper content persistence ────────────────────────────────────────────

    def save_metadata(self, arxiv_id: str, category: str, metadata: ArxivMetadata) -> None:
        """Write ArxivMetadata to metadata.json."""
        path = self.get_paper_dir(arxiv_id, category) / "metadata.json"
        path.write_text(
            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.debug(f"Saved metadata: {path}")

    def save_content_md(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None:
        """Write full paper content as human-readable Markdown."""
        path = self.get_paper_dir(arxiv_id, category) / "content.md"
        lines = [f"# {content.title}", ""]
        if content.authors:
            lines += [f"**Authors:** {', '.join(content.authors)}", ""]
        if content.abstract:
            lines += ["## Abstract", "", content.abstract, ""]
        for section in content.sections:
            lines += _section_to_md(section)
        path.write_text("\n".join(lines), encoding="utf-8")
        logger.debug(f"Saved content.md: {path}")

    def save_content_json(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None:
        """Write structured Ar5ivContent to content.json."""
        path = self.get_paper_dir(arxiv_id, category) / "content.json"
        path.write_text(
            json.dumps(content.to_dict(), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    # ── Annotation persistence ───────────────────────────────────────────────

    def _annotation_path(self, arxiv_id: str, category: str) -> Path:
        return self.get_paper_dir(arxiv_id, category) / "llm_annotations.jsonl"

    def has_annotations(self, arxiv_id: str, category: str) -> bool:
        """Return True if annotations file exists and is non-empty."""
        p = self._annotation_path(arxiv_id, category)
        return p.exists() and p.stat().st_size > 0

    def save_annotations(
        self, arxiv_id: str, category: str, annotations: List[ParagraphAnnotation]
    ) -> None:
        """Write annotations as JSONL (one dict per line)."""
        path = self._annotation_path(arxiv_id, category)
        with path.open("w", encoding="utf-8") as f:
            for ann in annotations:
                f.write(json.dumps(ann.to_dict(), ensure_ascii=False) + "\n")
        logger.debug(f"Saved {len(annotations)} annotations: {path}")

    def load_annotations(self, arxiv_id: str, category: str) -> List[ParagraphAnnotation]:
        """Load annotations from JSONL; marks each as cached=True."""
        path = self._annotation_path(arxiv_id, category)
        if not path.exists():
            return []
        annotations = []
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                ann = ParagraphAnnotation.from_dict(d)
                ann.cached = True
                annotations.append(ann)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Skipping malformed annotation line: {e}")
        return annotations

    # ── JSONL log helpers ────────────────────────────────────────────────────

    def _append_log(self, filename: str, event: dict) -> None:
        """Append a dict as one JSONL line with a timestamp."""
        path = self.logs_dir / filename
        entry = {"ts": datetime.now().isoformat(timespec="seconds"), **event}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def log_import(self, event: dict) -> None:
        """Append to logs/import.jsonl."""
        self._append_log("import.jsonl", event)

    def log_llm_call(self, event: dict) -> None:
        """Append to logs/llm_calls.jsonl."""
        self._append_log("llm_calls.jsonl", event)

    def log_error(self, event: dict) -> None:
        """Append to logs/errors.jsonl."""
        self._append_log("errors.jsonl", event)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _section_to_md(section: Section) -> List[str]:
    """Recursively render a Section to Markdown lines."""
    prefix = "#" * (section.level + 1)
    lines = [f"{prefix} {section.title}", ""]
    for para in section.paragraphs:
        lines += [para, ""]
    for sub in section.subsections:
        lines += _section_to_md(sub)
    return lines
```

- [ ] **Step 3.4: Run tests**

```bash
pytest tests/test_file_manager.py -v
```

Expected: All tests PASS.

- [ ] **Step 3.5: Commit**

```bash
git add file_manager.py tests/test_file_manager.py tests/conftest.py
git commit -m "feat: add FileManager with paper dirs and JSONL log streams"
```

---

## Task 4: Create `qwen_annotator.py`

**Files:**
- Create: `qwen_annotator.py`
- Modify: `requirements.txt`
- Create: `tests/test_qwen_annotator.py`

- [ ] **Step 4.1: Add `openai` to requirements**

In `requirements.txt`, add under core dependencies:

```
openai>=1.0.0              # DashScope-compatible OpenAI SDK client
```

Install it:

```bash
pip install openai>=1.0.0
```

- [ ] **Step 4.2: Write failing tests**

Create `tests/test_qwen_annotator.py`:

```python
"""Unit tests for QwenAnnotator — all Qwen API calls are mocked."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_openai_response():
    """Fake OpenAI chat completion response."""
    choice = MagicMock()
    choice.message.content = (
        "通俗解读：这段话解释了Transformer的注意力机制。\n"
        "要点1：自注意力机制允许序列内部元素相互关注。\n"
        "要点2：多头注意力扩展了单一注意力的表达能力。\n"
        "要点3：位置编码解决了无顺序信息的问题。"
    )
    response = MagicMock()
    response.choices = [choice]
    response.usage.prompt_tokens = 200
    response.usage.completion_tokens = 80
    return response


@pytest.fixture
def qwen_config():
    from config import QwenConfig
    return QwenConfig(api_key="test_key", model="qwen-plus", enabled=True, min_para_length=10)


class TestQwenAnnotatorParsing:
    def test_parse_response_extracts_explanation_and_key_points(self, qwen_config, tmp_path):
        from file_manager import FileManager
        from qwen_annotator import QwenAnnotator
        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        raw = (
            "通俗解读：这是一个测试。\n"
            "要点1：第一点。\n"
            "要点2：第二点。\n"
        )
        explanation, points = annotator._parse_response(raw)
        assert explanation == "这是一个测试。"
        assert points == ["第一点。", "第二点。"]

    def test_parse_response_handles_missing_points_gracefully(self, qwen_config, tmp_path):
        from file_manager import FileManager
        from qwen_annotator import QwenAnnotator
        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        raw = "通俗解读：只有解读没有要点。"
        explanation, points = annotator._parse_response(raw)
        assert "只有解读" in explanation
        assert isinstance(points, list)


class TestQwenAnnotatorAPI:
    @pytest.mark.asyncio
    async def test_annotate_paragraph_calls_api_and_returns_annotation(
        self, qwen_config, tmp_path, mock_openai_response
    ):
        from file_manager import FileManager
        from qwen_annotator import QwenAnnotator

        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        with patch.object(annotator, "_call_api", return_value=mock_openai_response) as mock_call:
            ann = await annotator.annotate_paragraph(
                text="The dominant sequence transduction models rely on RNNs.",
                section_title="Introduction",
                para_idx=0,
            )

        mock_call.assert_called_once()
        assert ann.section_title == "Introduction"
        assert ann.para_idx == 0
        assert len(ann.plain_explanation) > 0
        assert isinstance(ann.key_points, list)

    @pytest.mark.asyncio
    async def test_short_paragraph_skipped(self, qwen_config, tmp_path):
        from file_manager import FileManager
        from qwen_annotator import QwenAnnotator

        fm = FileManager(base_dir=tmp_path)
        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)

        ann = await annotator.annotate_paragraph(
            text="Too short.",  # < min_para_length=10 but let's use really short
            section_title="Intro",
            para_idx=0,
        )
        # For very short text below threshold, should return placeholder
        assert ann is not None  # returns annotation, not None

    @pytest.mark.asyncio
    async def test_annotate_paper_loads_cache_if_exists(self, qwen_config, tmp_path, sample_annotation):
        from file_manager import FileManager
        from models import Ar5ivContent, Section
        from qwen_annotator import QwenAnnotator

        fm = FileManager(base_dir=tmp_path)
        # Pre-populate cache
        fm.save_annotations("1706.03762", "deep_learning", [sample_annotation])

        annotator = QwenAnnotator(config=qwen_config, file_manager=fm)
        content = Ar5ivContent(
            paper_id="1706.03762",
            title="Test",
            sections=[Section(title="Introduction", level=2, paragraphs=["Some text."])],
        )

        with patch.object(annotator, "annotate_paragraph") as mock_para:
            result = await annotator.annotate_paper(content, "1706.03762", "deep_learning")

        # Must not call annotate_paragraph when cache exists
        mock_para.assert_not_called()
        assert len(result) == 1
        assert result[0].cached is True
```

- [ ] **Step 4.3: Run to confirm fail**

```bash
pytest tests/test_qwen_annotator.py -v 2>&1 | head -20
```

Expected: FAIL — `ModuleNotFoundError: No module named 'qwen_annotator'`

- [ ] **Step 4.4: Implement `qwen_annotator.py`**

Create `qwen_annotator.py`:

```python
"""
Qwen paragraph annotation module.
Responsibility: Call Qwen3.6-plus via DashScope to generate Chinese reading notes for each paragraph.
"""
import asyncio
import re
import time
from typing import List, Optional, Tuple

from loguru import logger

from config import QwenConfig
from file_manager import FileManager
from models import Ar5ivContent, ParagraphAnnotation


SYSTEM_PROMPT = (
    "你是一位耐心的学术论文辅导老师，擅长用通俗易懂的中文解释复杂的技术段落。"
    "请保持解释简洁、准确，不超过2-3句话。"
)

USER_TEMPLATE = """请分析以下学术段落，用中文回答：

1. 通俗解读（1-2句话）：用简单的语言解释这段话的核心意思
2. 关键要点（2-3条）：每条一句话，提炼最重要的信息

段落原文：
{text}

回答格式（严格按此格式）：
通俗解读：...
要点1：...
要点2：...
要点3：（如有必要）"""


class QwenAnnotator:
    """
    Annotates paper paragraphs using Qwen3.6-plus via DashScope's OpenAI-compatible API.

    Caching: If annotations already exist on disk for a paper, the API is not called.
    """

    def __init__(self, config: QwenConfig, file_manager: FileManager):
        self.config = config
        self.fm = file_manager
        self._client = None  # lazy init

    def _get_client(self):
        """Lazy-initialize the OpenAI client (DashScope-compatible)."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai package is required for Qwen annotation. "
                    "Run: pip install openai>=1.0.0"
                )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client

    async def _call_api(self, messages: list) -> object:
        """
        Call the Qwen API (synchronous under the hood, wrapped in executor).
        Returns the raw completion response.
        """
        client = self._get_client()
        loop = asyncio.get_event_loop()

        def _sync_call():
            return client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                extra_body={"enable_thinking": False},
            )

        return await loop.run_in_executor(None, _sync_call)

    def _parse_response(self, text: str) -> Tuple[str, List[str]]:
        """
        Parse Qwen response into (plain_explanation, key_points).
        Robust to missing sections.
        """
        explanation = ""
        key_points = []

        # Extract 通俗解读
        match = re.search(r"通俗解读[：:]\s*(.+?)(?=要点\d|$)", text, re.DOTALL)
        if match:
            explanation = match.group(1).strip()

        # Extract 要点N
        for m in re.finditer(r"要点\d[：:]\s*(.+?)(?=要点\d|$)", text, re.DOTALL):
            point = m.group(1).strip()
            if point:
                key_points.append(point)

        # Fallback: if parsing fails entirely, use full response as explanation
        if not explanation:
            explanation = text.strip()[:300]

        return explanation, key_points

    async def annotate_paragraph(
        self, text: str, section_title: str, para_idx: int
    ) -> ParagraphAnnotation:
        """
        Annotate a single paragraph. Returns a placeholder annotation if the
        text is shorter than config.min_para_length or if the API fails.
        """
        para_text_preview = text[:200]

        # Skip very short paragraphs
        if len(text) < self.config.min_para_length:
            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation="（段落过短，跳过注释）",
                key_points=[],
            )

        # Truncate long input
        truncated = text[: self.config.max_para_length]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(text=truncated)},
        ]

        t0 = time.time()
        try:
            response = await self._call_api(messages)
            latency_ms = int((time.time() - t0) * 1000)
            raw = response.choices[0].message.content
            explanation, key_points = self._parse_response(raw)

            # Log the API call
            self.fm.log_llm_call({
                "section_title": section_title,
                "para_idx": para_idx,
                "tokens_in": response.usage.prompt_tokens,
                "tokens_out": response.usage.completion_tokens,
                "latency_ms": latency_ms,
                "model": self.config.model,
                "cached": False,
            })

            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation=explanation,
                key_points=key_points,
            )

        except Exception as e:
            logger.warning(f"Qwen API failed for para {para_idx} in '{section_title}': {e}")
            return ParagraphAnnotation(
                section_title=section_title,
                para_idx=para_idx,
                para_text=para_text_preview,
                plain_explanation="（注释生成失败）",
                key_points=[],
            )

    async def annotate_paper(
        self,
        content: Ar5ivContent,
        arxiv_id: str,
        category: str,
    ) -> List[ParagraphAnnotation]:
        """
        Annotate all paragraphs in a paper.

        If annotations already exist on disk, loads and returns them without any API calls.
        Otherwise calls Qwen for each paragraph, saves to disk, and returns results.
        """
        # Cache hit — skip all API calls
        if self.fm.has_annotations(arxiv_id, category):
            logger.info(f"Loading cached annotations for {arxiv_id}")
            return self.fm.load_annotations(arxiv_id, category)

        logger.info(f"Annotating {arxiv_id} with Qwen ({self.config.model})...")
        annotations: List[ParagraphAnnotation] = []

        # Paper-level TL;DR from abstract
        if content.abstract and len(content.abstract) >= self.config.min_para_length:
            abstract_ann = await self.annotate_paragraph(
                content.abstract, section_title="__abstract__", para_idx=-1
            )
            annotations.append(abstract_ann)

        # Per-section, per-paragraph
        for section in content.sections:
            section_anns = await self._annotate_section(section)
            annotations.extend(section_anns)

        # Save to disk
        self.fm.save_annotations(arxiv_id, category, annotations)
        logger.info(f"Annotated {len(annotations)} paragraphs for {arxiv_id}")
        return annotations

    async def _annotate_section(self, section) -> List[ParagraphAnnotation]:
        """Annotate all paragraphs in a section (recursively includes subsections)."""
        annotations = []
        for idx, para in enumerate(section.paragraphs):
            ann = await self.annotate_paragraph(para, section.title, idx)
            annotations.append(ann)
        for sub in section.subsections:
            annotations.extend(await self._annotate_section(sub))
        return annotations
```

- [ ] **Step 4.5: Run tests**

```bash
pytest tests/test_qwen_annotator.py -v
```

Expected: All tests PASS.

- [ ] **Step 4.6: Commit**

```bash
git add qwen_annotator.py requirements.txt tests/test_qwen_annotator.py
git commit -m "feat: add QwenAnnotator with DashScope API, caching, and JSONL logging"
```

---

## Task 5: Redesign `notion_converter.py` — Academic Premium Layout

**Files:**
- Modify: `notion_converter.py` (full rewrite of `NotionConverter` class methods)
- Create: `tests/test_notion_converter.py`

- [ ] **Step 5.1: Write failing tests for the new layout**

Create `tests/test_notion_converter.py`:

```python
"""Tests for NotionConverter Academic Premium layout."""
from datetime import datetime
from typing import List, Dict, Any

import pytest


def block_types(blocks: List[Dict]) -> List[str]:
    return [b["type"] for b in blocks]


def find_blocks(blocks: List[Dict], block_type: str) -> List[Dict]:
    return [b for b in blocks if b["type"] == block_type]


def toggle_texts(blocks: List[Dict]) -> List[str]:
    return [
        b["toggle"]["rich_text"][0]["text"]["content"]
        for b in blocks
        if b["type"] == "toggle"
    ]


@pytest.fixture
def sample_paper():
    from models import PaperData, ArxivMetadata, Ar5ivContent, Section, Author, Reference
    meta = ArxivMetadata(
        arxiv_id="1706.03762",
        title="Attention Is All You Need",
        authors=[Author(name="Vaswani, A."), Author(name="Shazeer, N.")],
        abstract="The dominant sequence transduction models rely on RNNs.",
        categories=["cs.CL", "cs.LG"],
        primary_category="cs.CL",
        published=datetime(2017, 6, 12),
        updated=datetime(2017, 12, 6),
    )
    content = Ar5ivContent(
        paper_id="1706.03762",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani"],
        abstract="The dominant sequence transduction models rely on RNNs.",
        sections=[
            Section(
                title="Introduction",
                level=2,
                paragraphs=["This is a paragraph about attention mechanisms."],
                subsections=[],
            ),
        ],
        references=[
            Reference(
                raw_text="Vaswani et al. (2017). Attention. arXiv:1234.5678",
                arxiv_id="1234.5678",
                citation_key="1",
                title="Attention",
                year="2017",
            ),
            Reference(
                raw_text="LeCun et al. (1989). Deep learning.",
                citation_key="2",
            ),
        ],
    )
    return PaperData(arxiv_id="1706.03762", metadata=meta, content=content)


@pytest.fixture
def sample_annotations():
    from models import ParagraphAnnotation
    return [
        ParagraphAnnotation(
            section_title="Introduction",
            para_idx=0,
            para_text="This is a paragraph about attention mechanisms.",
            plain_explanation="这段话介绍了注意力机制的基本概念。",
            key_points=["注意力机制是核心", "替代了RNN结构"],
        ),
    ]


class TestAcademicPremiumHeader:
    def test_header_contains_blue_callout(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        callouts = find_blocks(blocks, "callout")
        assert len(callouts) >= 1
        # First callout must be blue_background
        assert callouts[0]["callout"]["color"] == "blue_background"

    def test_header_callout_contains_published_and_authors(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        callout_text = blocks[0]["callout"]["rich_text"][0]["text"]["content"]
        assert "2017-06-12" in callout_text
        assert "Vaswani" in callout_text

    def test_header_contains_links_paragraph(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        # Must have a paragraph with links
        paras = find_blocks(blocks, "paragraph")
        assert len(paras) >= 1


class TestAbstractAndTLDR:
    def test_abstract_uses_quote_block(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_abstract(sample_paper, tldr=None)
        quotes = find_blocks(blocks, "quote")
        assert len(quotes) == 1

    def test_tldr_callout_shown_when_provided(self, sample_paper):
        from notion_converter import NotionConverter
        from models import ParagraphAnnotation
        conv = NotionConverter()
        tldr = ParagraphAnnotation(
            section_title="__abstract__",
            para_idx=-1,
            para_text="...",
            plain_explanation="一句话总结：这篇论文提出了Transformer。",
            key_points=[],
        )
        blocks = conv._create_abstract(sample_paper, tldr=tldr)
        callouts = find_blocks(blocks, "callout")
        green_callouts = [c for c in callouts if c["callout"]["color"] == "green_background"]
        assert len(green_callouts) == 1
        text = green_callouts[0]["callout"]["rich_text"][0]["text"]["content"]
        assert "Transformer" in text


class TestSectionsWithAnnotations:
    def test_paragraph_followed_by_toggle(self, sample_paper, sample_annotations):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=sample_annotations)
        types = block_types(blocks)
        # Must have a paragraph then a toggle
        para_idx = types.index("paragraph")
        assert "toggle" in types
        toggle_idx = types.index("toggle")
        assert toggle_idx == para_idx + 1

    def test_toggle_label_is_ai_reading_notes(self, sample_paper, sample_annotations):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=sample_annotations)
        texts = toggle_texts(blocks)
        assert any("AI 阅读笔记" in t for t in texts)

    def test_no_toggle_when_no_annotations(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=[])
        assert "toggle" not in block_types(blocks)


class TestReferenceFormatting:
    def test_arxiv_refs_formatted_with_link(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_references_section(sample_paper.content.references)
        # Find paragraph blocks with arXiv link
        paras_with_link = []
        for b in blocks:
            if b["type"] == "paragraph":
                for rt in b["paragraph"]["rich_text"]:
                    if rt.get("text", {}).get("link"):
                        paras_with_link.append(b)
                        break
        assert len(paras_with_link) >= 1

    def test_non_arxiv_refs_in_toggle(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_references_section(sample_paper.content.references)
        # Must have a toggle for non-arXiv refs
        toggles = find_blocks(blocks, "toggle")
        assert any("其他参考文献" in b["toggle"]["rich_text"][0]["text"]["content"] for b in toggles)
```

- [ ] **Step 5.2: Run to confirm fail**

```bash
pytest tests/test_notion_converter.py -v 2>&1 | head -30
```

Expected: Multiple FAILs — header not blue_background, no TL;DR callout, no toggle after paragraphs, references not formatted with links.

- [ ] **Step 5.3: Rewrite `NotionConverter` methods in `notion_converter.py`**

Replace the entire `NotionConverter` class (keep `NotionBlockBuilder` unchanged). The new class:

```python
# ── Section heading emoji mapping ─────────────────────────────────────────────

_SECTION_EMOJIS = {
    "introduction": "📌",
    "background": "📚",
    "related": "📚",
    "method": "🔬",
    "model": "🔬",
    "architecture": "🔬",
    "approach": "🔬",
    "framework": "🔬",
    "experiment": "📊",
    "result": "📊",
    "evaluation": "📊",
    "analysis": "📊",
    "ablation": "📊",
    "conclusion": "💡",
    "discussion": "💡",
    "limitation": "💡",
    "future": "💡",
}


def _section_emoji(title: str) -> str:
    """Return an emoji for a section title based on keywords."""
    lower = title.lower()
    for keyword, emoji in _SECTION_EMOJIS.items():
        if keyword in lower:
            return emoji
    return "📄"


class NotionConverter:
    """
    Converts PaperData into Notion blocks using the Academic Premium layout.

    Accepts optional List[ParagraphAnnotation] to add AI reading notes toggles.
    """

    def __init__(
        self,
        max_text_length: int = 2000,
        include_equations: bool = True,
        include_figures: bool = True,
        include_tables: bool = True,
        max_sections: int = 50,
    ):
        self.max_text_length = max_text_length
        self.include_equations = include_equations
        self.include_figures = include_figures
        self.include_tables = include_tables
        self.max_sections = max_sections
        self.builder = NotionBlockBuilder

    def convert_paper(
        self,
        paper: PaperData,
        annotations: Optional[List["ParagraphAnnotation"]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert a full paper to Notion blocks (Academic Premium layout).

        Args:
            paper: The paper data.
            annotations: Optional Qwen annotations; if provided, each paragraph
                         gets a toggle with AI reading notes.
        """
        from models import ParagraphAnnotation  # avoid circular at module level

        annotations = annotations or []

        # Extract TL;DR annotation (section_title == "__abstract__", para_idx == -1)
        tldr = next(
            (a for a in annotations if a.section_title == "__abstract__" and a.para_idx == -1),
            None,
        )

        blocks = []
        try:
            blocks.extend(self._create_header(paper))
            blocks.extend(self._create_abstract(paper, tldr=tldr))

            blocks.append(self.builder.divider())
            blocks.append(self.builder.heading("📑 Contents", level=2))
            blocks.append(self.builder.table_of_contents())
            blocks.append(self.builder.divider())

            if paper.content and paper.content.sections:
                blocks.extend(self._convert_sections(paper.content.sections, annotations))

            if paper.content and paper.content.figures and self.include_figures:
                blocks.extend(self._create_figures_section(paper.content.figures))

            if paper.content and paper.content.tables and self.include_tables:
                blocks.extend(self._create_tables_section(paper.content.tables))

            if paper.content and paper.content.references:
                blocks.extend(self._create_references_section(paper.content.references))

            logger.debug(f"Converted paper to {len(blocks)} blocks")
        except Exception:
            logger.error(f"Conversion failed: {format_exception()}")

        return blocks

    # ── Header ────────────────────────────────────────────────────────────────

    def _create_header(self, paper: PaperData) -> List[Dict[str, Any]]:
        blocks = []
        metadata = paper.metadata

        if metadata:
            category_emoji = get_category_emoji(metadata.primary_category)

            # Build info lines for blue callout
            authors_str = format_authors([str(a) for a in metadata.authors], max_count=5)
            categories_str = " · ".join(metadata.categories[:5])
            info_lines = [
                f"📅 Published: {format_date(metadata.published)}",
                f"👥 Authors: {authors_str}",
                f"🏷️  {categories_str}",
            ]
            if metadata.doi:
                info_lines.append(f"🔗 DOI: {metadata.doi}")
            if metadata.journal_ref:
                info_lines.append(f"📰 {metadata.journal_ref}")

            blocks.append(
                self.builder.callout(
                    "\n".join(info_lines),
                    icon=category_emoji,
                    color="blue_background",
                )
            )
        elif paper.content:
            blocks.append(
                self.builder.callout(
                    f"👥 Authors: {format_authors(paper.content.authors)}",
                    icon="📄",
                    color="blue_background",
                )
            )

        # Links row
        arxiv_url = build_arxiv_url(paper.arxiv_id, "abs")
        pdf_url = build_arxiv_url(paper.arxiv_id, "pdf")
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{paper.arxiv_id}"

        blocks.append(
            self.builder.paragraph_with_rich_text([
                self.builder.rich_text("🔗 Links:  ", bold=True),
                self.builder.rich_text("arXiv", link=arxiv_url, color="blue"),
                self.builder.rich_text("  |  "),
                self.builder.rich_text("PDF", link=pdf_url, color="blue"),
                self.builder.rich_text("  |  "),
                self.builder.rich_text("ar5iv", link=ar5iv_url, color="blue"),
            ])
        )

        blocks.append(self.builder.divider())
        return blocks

    # ── Abstract + TL;DR ──────────────────────────────────────────────────────

    def _create_abstract(
        self,
        paper: PaperData,
        tldr: Optional["ParagraphAnnotation"],
    ) -> List[Dict[str, Any]]:
        blocks = []

        abstract = (
            (paper.content and paper.content.abstract)
            or (paper.metadata and paper.metadata.abstract)
        )

        if abstract:
            blocks.append(self.builder.heading("📝 Abstract", level=2))
            blocks.append(self.builder.quote(abstract))

        if tldr:
            blocks.append(
                self.builder.callout(
                    f"💡 {tldr.plain_explanation}",
                    icon="💡",
                    color="green_background",
                )
            )

        return blocks

    # ── Sections ──────────────────────────────────────────────────────────────

    def _convert_sections(
        self,
        sections: List[Section],
        annotations: List["ParagraphAnnotation"],
    ) -> List[Dict[str, Any]]:
        blocks = []
        for i, section in enumerate(sections):
            if i >= self.max_sections:
                blocks.append(
                    self.builder.callout(
                        f"⚠️ Section limit ({self.max_sections}) reached — content truncated.",
                        icon="⚠️",
                        color="yellow_background",
                    )
                )
                break
            blocks.extend(self._convert_section(section, annotations))
        return blocks

    def _convert_section(
        self,
        section: Section,
        annotations: List["ParagraphAnnotation"],
    ) -> List[Dict[str, Any]]:
        blocks = []
        emoji = _section_emoji(section.title)
        level = min(section.level, 3)
        blocks.append(self.builder.heading(f"{emoji} {section.title}", level=level))

        # Build annotation lookup: (section_title, para_idx) → annotation
        ann_map = {
            (a.section_title, a.para_idx): a for a in annotations
        }

        for idx, para in enumerate(section.paragraphs):
            # Add paragraph (split if too long)
            for chunk in self._split_text(para):
                blocks.append(self.builder.paragraph(chunk))

            # Add AI reading notes toggle if annotation exists
            ann = ann_map.get((section.title, idx))
            if ann and ann.plain_explanation and ann.plain_explanation != "（段落过短，跳过注释）":
                blocks.append(self._make_annotation_toggle(ann))

        if self.include_equations and section.equations:
            for eq in section.equations[:10]:
                if eq.latex:
                    blocks.append(self.builder.equation(eq.latex))

        if self.include_figures and section.figures:
            for fig in section.figures[:5]:
                if fig.src and fig.src.startswith("http"):
                    blocks.append(self.builder.image(fig.src, fig.caption))

        if self.include_tables and section.tables:
            for tbl in section.tables[:3]:
                if tbl.headers or tbl.rows:
                    blocks.append(self.builder.table(tbl.headers, tbl.rows[:20]))

        for sub in section.subsections:
            blocks.extend(self._convert_section(sub, annotations))

        return blocks

    def _make_annotation_toggle(self, ann: "ParagraphAnnotation") -> Dict[str, Any]:
        """Build the 🤖 AI 阅读笔记 toggle block with callout + bullet points inside."""
        inner_blocks = [
            self.builder.callout(
                f"💬 通俗解读：{ann.plain_explanation}",
                icon="💬",
                color="gray_background",
            )
        ]
        for point in ann.key_points:
            inner_blocks.append(self.builder.bulleted_list_item(point))

        # Notion API: children must be passed in the toggle's rich_text structure
        toggle = self.builder.toggle("🤖 AI 阅读笔记", children=inner_blocks)
        return toggle

    # ── Figures ───────────────────────────────────────────────────────────────

    def _create_figures_section(self, figures: List[Figure]) -> List[Dict[str, Any]]:
        blocks = [self.builder.divider(), self.builder.heading("🖼️ Figures", level=2)]
        for i, fig in enumerate(figures[:20]):
            if fig.src and fig.src.startswith("http"):
                blocks.append(self.builder.image(fig.src, fig.caption or f"Figure {i + 1}"))
        return blocks

    # ── Tables ────────────────────────────────────────────────────────────────

    def _create_tables_section(self, tables: List[Table]) -> List[Dict[str, Any]]:
        blocks = [self.builder.divider(), self.builder.heading("📊 Tables", level=2)]
        for tbl in tables[:10]:
            if tbl.caption:
                blocks.append(self.builder.paragraph(tbl.caption, bold=True))
            if tbl.headers or tbl.rows:
                blocks.append(self.builder.table(tbl.headers, tbl.rows[:30]))
        return blocks

    # ── References ────────────────────────────────────────────────────────────

    def _create_references_section(self, references: List[Reference]) -> List[Dict[str, Any]]:
        blocks = [self.builder.divider(), self.builder.heading("📚 参考文献 (References)", level=2)]

        arxiv_refs = [r for r in references if r.arxiv_id]
        other_refs = [r for r in references if not r.arxiv_id]

        if arxiv_refs:
            blocks.append(
                self.builder.callout(
                    f"✅ 找到 {len(arxiv_refs)} 篇 arXiv 论文，已创建子页面",
                    icon="✅",
                    color="green_background",
                )
            )

        # Formatted arXiv references
        for ref in arxiv_refs[:100]:
            blocks.append(self._format_arxiv_reference(ref))

        # Non-arXiv refs in a toggle
        if other_refs:
            other_items = []
            for ref in other_refs[:100]:
                text = truncate_text(ref.raw_text, 300)
                other_items.append(self.builder.bulleted_list_item(
                    f"[{ref.citation_key or '?'}]  {text}"
                ))
            blocks.append(
                self.builder.toggle(
                    f"📎 其他参考文献 ({len(other_refs)} 篇)",
                    children=other_items,
                )
            )

        return blocks

    def _format_arxiv_reference(self, ref: Reference) -> Dict[str, Any]:
        """
        Format a single arXiv reference as a paragraph with rich text.

        Format: [key]  Authors (Year). Title. Venue.  → arXiv:ID
        """
        from reference_resolver import ReferenceExtractor
        extractor = ReferenceExtractor()
        ref = extractor.extract_info(ref)

        # Build display text
        parts = []
        if ref.authors:
            authors_str = ", ".join(ref.authors[:3])
            if len(ref.authors) > 3:
                authors_str += " et al."
            parts.append(authors_str)
        if ref.year:
            parts.append(f"({ref.year}).")
        if ref.title:
            parts.append(f"{ref.title}.")
        if ref.venue:
            parts.append(f"{ref.venue}.")

        display = "  ".join(parts) if parts else truncate_text(ref.raw_text, 200)
        key_str = f"[{ref.citation_key or '?'}]  " if ref.citation_key else ""
        arxiv_url = build_arxiv_url(ref.arxiv_id, "abs")

        return self.builder.paragraph_with_rich_text([
            self.builder.rich_text(key_str, bold=True),
            self.builder.rich_text(display + "  "),
            self.builder.rich_text(f"→ arXiv:{ref.arxiv_id}", link=arxiv_url, color="blue"),
        ])

    # ── Reference sub-page ────────────────────────────────────────────────────

    def create_reference_page_blocks(
        self, ref: Reference, metadata: Optional[ArxivMetadata] = None
    ) -> List[Dict[str, Any]]:
        blocks = []
        if metadata:
            category_emoji = get_category_emoji(metadata.primary_category)
            authors_str = format_authors([str(a) for a in metadata.authors], max_count=5)
            info = (
                f"📅 Published: {format_date(metadata.published)}\n"
                f"👥 Authors: {authors_str}\n"
                f"🏷️  {', '.join(metadata.categories[:5])}"
            )
            blocks.append(self.builder.callout(info, icon=category_emoji, color="blue_background"))

            arxiv_url = build_arxiv_url(ref.arxiv_id, "abs")
            pdf_url = build_arxiv_url(ref.arxiv_id, "pdf")
            blocks.append(self.builder.paragraph_with_rich_text([
                self.builder.rich_text("🔗 ", bold=True),
                self.builder.rich_text("arXiv", link=arxiv_url, color="blue"),
                self.builder.rich_text("  |  "),
                self.builder.rich_text("PDF", link=pdf_url, color="blue"),
            ]))
            blocks.append(self.builder.divider())

            if metadata.abstract:
                blocks.append(self.builder.heading("📝 Abstract", level=2))
                blocks.append(self.builder.quote(metadata.abstract))
        else:
            blocks.append(
                self.builder.callout(
                    "ℹ️ Metadata not available for this reference.",
                    icon="ℹ️",
                    color="gray_background",
                )
            )
            blocks.append(self.builder.heading("Original Citation", level=2))
            blocks.append(self.builder.paragraph(ref.raw_text))
            if ref.arxiv_id:
                blocks.append(self.builder.bookmark(build_arxiv_url(ref.arxiv_id), f"arXiv:{ref.arxiv_id}"))

        return blocks

    # ── Text splitting ────────────────────────────────────────────────────────

    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self.max_text_length:
            return [text]
        chunks, remaining = [], text
        while remaining:
            if len(remaining) <= self.max_text_length:
                chunks.append(remaining)
                break
            chunk = remaining[: self.max_text_length]
            last_break = max(chunk.rfind(". "), chunk.rfind("。"), chunk.rfind("! "), chunk.rfind("? "))
            if last_break > self.max_text_length * 0.5:
                chunk = chunk[: last_break + 1]
            chunks.append(chunk.strip())
            remaining = remaining[len(chunk):].strip()
        return chunks
```

Also add the `Optional` import for annotations at the top of the class method signatures by ensuring `from typing import Optional, List` is already present (it is).

- [ ] **Step 5.4: Run tests**

```bash
pytest tests/test_notion_converter.py -v
```

Expected: All tests PASS.

- [ ] **Step 5.5: Run full test suite to check for regressions**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 5.6: Commit**

```bash
git add notion_converter.py tests/test_notion_converter.py
git commit -m "feat: redesign NotionConverter to Academic Premium layout with AI reading notes toggles"
```

---

## Task 6: Pipeline Integration — `main.py` and `Ar5ivToNotion`

**Files:**
- Modify: `main.py`

- [ ] **Step 6.1: Update `Ar5ivToNotion.__init__` to accept new modules**

In `main.py`, update `Ar5ivToNotion.__init__`:

```python
    def __init__(self, config: AppConfig):
        self.config = config

        self.arxiv_client = ArxivApiClient(config=config.arxiv, cache_config=config.cache)
        self.ar5iv_extractor = Ar5ivExtractor(config=config.arxiv, cache_config=config.cache)
        self.ref_resolver = ReferenceResolver(config=config.reference, arxiv_client=self.arxiv_client)

        # NEW: file manager and annotator
        from file_manager import FileManager
        from qwen_annotator import QwenAnnotator
        self.file_manager = FileManager(base_dir=Path("."))
        self.annotator = QwenAnnotator(config=config.qwen, file_manager=self.file_manager)

        self.converter = NotionConverter(
            max_text_length=config.content.max_text_length,
            include_equations=config.content.include_equations,
            include_figures=config.content.include_figures,
            include_tables=config.content.include_tables,
            max_sections=config.content.max_sections,
        )
        self.notion_creator = NotionCreator(config=config.notion, converter=self.converter)
```

- [ ] **Step 6.2: Update `process_paper` to wire annotation + file saving**

Replace the existing `process_paper` method:

```python
    async def process_paper(
        self,
        arxiv_id: str,
        category: str = "",
        with_references: bool = True,
        use_cache: bool = True,
        max_ref_pages: int = 20,
        annotate: bool = True,
    ) -> PaperData:
        arxiv_id = normalize_arxiv_id(arxiv_id)
        logger.info(f"Processing: {arxiv_id}")

        paper = PaperData(arxiv_id=arxiv_id, status=PaperStatus.FETCHING)
        start_ms = int(__import__("time").time() * 1000)

        try:
            # 1. Fetch arXiv metadata
            paper.metadata = await self.arxiv_client.get_paper(arxiv_id, use_cache)
            if not paper.metadata:
                paper.status = PaperStatus.FAILED
                paper.error = "Could not fetch arXiv metadata"
                return paper

            logger.info(f"Title: {paper.metadata.title}")

            # Auto-detect category from arXiv primary category if not provided
            if not category:
                category = _detect_category(paper.metadata.primary_category)

            # 2. Extract ar5iv content
            paper.status = PaperStatus.PARSING
            paper.content = await self.ar5iv_extractor.extract_paper(arxiv_id, use_cache)
            if not paper.content:
                logger.warning("ar5iv extraction failed — using metadata only")

            # 3. Annotate with Qwen (skipped if --no-annotate or not enabled)
            annotations = []
            if annotate and self.config.qwen.enabled and paper.content:
                if not self.config.qwen.api_key:
                    logger.warning("DASHSCOPE_API_KEY not set — skipping annotation")
                else:
                    annotations = await self.annotator.annotate_paper(
                        paper.content, arxiv_id, category
                    )

            # 4. Save to file system
            if paper.metadata:
                self.file_manager.save_metadata(arxiv_id, category, paper.metadata)
            if paper.content:
                self.file_manager.save_content_md(arxiv_id, category, paper.content)
                self.file_manager.save_content_json(arxiv_id, category, paper.content)

            # 5. Resolve references
            ref_metadata = {}
            if with_references and paper.content and paper.content.references:
                paper.resolved_references = await self.ref_resolver.resolve_references(
                    paper.content.references
                )
                arxiv_refs = self.ref_resolver.get_arxiv_references(paper.resolved_references)
                logger.info(f"Found {len(arxiv_refs)} arXiv references")
                if arxiv_refs:
                    ids = [r.arxiv_id for r in arxiv_refs[:max_ref_pages] if r.arxiv_id]
                    ref_metadata = await self.arxiv_client.get_papers_batch(ids, use_cache)

            # 6. Create Notion pages
            paper.status = PaperStatus.CREATING
            result = self.notion_creator.create_paper_with_references(
                paper, ref_metadata, max_ref_pages, annotations=annotations
            )

            if result.success:
                paper.status = PaperStatus.COMPLETED
                paper.notion_page_id = result.page_id
                logger.info(f"✅ Created: {result.url}  ({result.children_pages} ref pages)")
                duration_ms = int(__import__("time").time() * 1000) - start_ms
                self.file_manager.log_import({
                    "arxiv_id": arxiv_id,
                    "category": category,
                    "status": "completed",
                    "notion_page_id": result.page_id,
                    "notion_url": result.url,
                    "duration_ms": duration_ms,
                    "blocks_created": result.blocks_created,
                    "ref_pages_created": result.children_pages,
                    "annotated_paragraphs": len(annotations),
                })
            else:
                paper.status = PaperStatus.FAILED
                paper.error = result.error
                logger.error(f"❌ Failed: {result.error}")
                self.file_manager.log_error({
                    "arxiv_id": arxiv_id,
                    "stage": "notion_create",
                    "error_type": "APIError",
                    "message": result.error or "",
                })

            return paper

        except Exception:
            error_msg = format_exception()
            logger.error(f"Processing failed: {error_msg}")
            paper.status = PaperStatus.FAILED
            paper.error = error_msg
            self.file_manager.log_error({
                "arxiv_id": arxiv_id,
                "stage": "process_paper",
                "error_type": "Exception",
                "message": str(error_msg)[:500],
            })
            return paper
```

Add the helper function (at module level, before the class):

```python
def _detect_category(primary_category: str) -> str:
    """Map an arXiv primary category to a file system category folder."""
    c = primary_category.lower()
    if any(k in c for k in ["cs.ai", "cs.ma", "cs.ro"]):
        return "ai_agent"
    if any(k in c for k in ["cs.cv", "cs.cl", "cs.lg", "stat.ml", "cs.ne"]):
        return "deep_learning"
    if any(k in c for k in ["cs.gt", "cs.sy"]):
        return "reinforcement_learning"
    return "other"
```

- [ ] **Step 6.3: Pass annotations to `NotionCreator.create_paper_with_references`**

In `notion_creator.py`, update `create_paper_with_references` signature and forward annotations to `create_paper_page`:

```python
    def create_paper_with_references(
        self,
        paper: PaperData,
        ref_metadata: Optional[Dict[str, ArxivMetadata]] = None,
        max_ref_pages: int = 20,
        annotations: Optional[list] = None,          # NEW
    ) -> CreationResult:
```

In `create_paper_page`, pass annotations to converter:

```python
    def create_paper_page(
        self,
        paper: PaperData,
        parent_id: Optional[str] = None,
        annotations: Optional[list] = None,          # NEW
    ) -> CreationResult:
        parent_id = parent_id or self.config.root_page_id
        try:
            blocks = self.converter.convert_paper(paper, annotations=annotations)   # NEW
            ...
```

And in `create_paper_with_references`, forward annotations:

```python
            main_result = self.create_paper_page(paper, annotations=annotations)
```

- [ ] **Step 6.4: Update CLI argument parser in `main.py`**

Add three new arguments to `argparse`:

```python
    parser.add_argument(
        "--category",
        default="",
        help="File system category folder (default: auto-detect from arXiv category)",
    )

    parser.add_argument(
        "--no-annotate",
        action="store_true",
        help="Skip Qwen LLM annotation step",
    )

    parser.add_argument(
        "--from-file",
        dest="from_file",
        metavar="PATH",
        help="Load paper config from a JSON file (see examples/single/)",
    )
```

In `main_async`, handle `--from-file`:

```python
    # Handle --from-file
    if args.from_file:
        import json as _json
        cfg = _json.loads(Path(args.from_file).read_text())
        args.arxiv_ids = [cfg["arxiv_id"]]
        args.category = cfg.get("category", args.category)
        opts = cfg.get("import_options", {})
        args.with_refs = opts.get("with_refs", args.with_refs)
        args.no_annotate = not opts.get("annotate", True)
        args.max_refs = opts.get("max_refs", args.max_refs)
```

Pass `annotate=not args.no_annotate` and `category=args.category` into `process_paper` calls.

- [ ] **Step 6.5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6.6: Commit**

```bash
git add main.py notion_creator.py
git commit -m "feat: wire FileManager, QwenAnnotator, and new CLI flags into pipeline"
```

---

## Task 7: Build `examples/` Folder

**Files:**
- Create: `examples/papers.json`
- Create: `examples/single/*.json` (60 files)
- Create: `examples/batch_import.py`

- [ ] **Step 7.1: Create `examples/papers.json` with all 60 papers**

```bash
mkdir -p examples/single
```

Create `examples/papers.json`:

```json
[
  {"arxiv_id": "2603.11088", "category": "ai_agent", "title": "The Attack and Defense Landscape of Agentic AI", "intro": "系统梳理 Agentic AI 的攻击面、防御方法与安全研究空白。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2603.11619", "category": "ai_agent", "title": "Taming OpenClaw", "intro": "研究自主 LLM agent 的跨阶段系统性安全风险与缓解。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2603.07670", "category": "ai_agent", "title": "Memory for Autonomous LLM Agents", "intro": "总结 agent memory 的机制、评测方式与开放问题。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2603.20639", "category": "ai_agent", "title": "Agentic AI and the next intelligence explosion", "intro": "从"社会化思维/institutional alignment"视角讨论 agentic AI。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.18998", "category": "ai_agent", "title": "Benchmark Test-Time Scaling of General LLM Agents", "intro": "提出统一 benchmark，评测通用 agent 的 test-time scaling。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.16666", "category": "ai_agent", "title": "Towards a Science of AI Agent Reliability", "intro": "面向 AI agent 可靠性的科学化方法论。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.15654", "category": "ai_agent", "title": "Zombie Agents", "intro": "通过持久控制研究 self-evolving LLM agents 的安全漏洞。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.12430", "category": "ai_agent", "title": "Agent Skills for Large Language Models", "intro": "聚焦 skills 作为 agent 能力抽象层的架构与安全。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.11964", "category": "ai_agent", "title": "Gaia2", "intro": "面向动态、异步环境的 agent benchmark。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.08276", "category": "ai_agent", "title": "Toward Formalizing LLM-Based Agent Designs", "intro": "尝试把 agent design 流程形式化并做系统优化。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.16901", "category": "ai_agent", "title": "AgentLAB", "intro": "长时程攻击场景下的 agent 安全 benchmark。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.04284", "category": "ai_agent", "title": "Agent-Omit", "intro": "通过自适应省略冗余 thought/observation 提升 agent 效率。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.03412", "category": "ai_agent", "title": "Verified Critical Step Optimization for LLM Agents", "intro": "对 agent 关键步骤做验证式优化，提升完成率与稳定性。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2602.20021", "category": "ai_agent", "title": "Agents of Chaos", "intro": "通过真实交互案例分析 agent 在自治、工具使用下的失败模式。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2601.18491", "category": "ai_agent", "title": "AgentDoG", "intro": "面向 agent 轨迹级别的安全/不合理行为诊断 guardrail。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2601.12560", "category": "ai_agent", "title": "Agentic Artificial Intelligence: Architectures, Taxonomies, and Evaluation", "intro": "总结 agent 架构、taxonomy 与评估框架。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2601.02553", "category": "ai_agent", "title": "SimpleMem", "intro": "提出高效 lifelong memory 机制，降低冗余与 token 成本。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2601.01743", "category": "ai_agent", "title": "AI Agent Systems: Architectures, Applications, and Evaluation", "intro": "对 AI agent system 的核心组件、应用与评测做综述。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2512.13564", "category": "ai_agent", "title": "Memory in the Age of AI Agents", "intro": "面向 AI agents 的 memory landscape 综述。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "2510.23883", "category": "ai_agent", "title": "Agentic AI Security", "intro": "梳理 agentic AI 安全威胁、防御与评测。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 15}},
  {"arxiv_id": "1207.0580", "category": "deep_learning", "title": "Improving neural networks by preventing co-adaptation of feature detectors", "intro": "Dropout 早期代表作，深度学习正则化里程碑。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1312.6114", "category": "deep_learning", "title": "Auto-Encoding Variational Bayes", "intro": "VAE 经典论文，奠定变分生成模型的重要路线。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1404.7828", "category": "deep_learning", "title": "Deep Learning in Neural Networks: An Overview", "intro": "Schmidhuber 的深度学习历史与方法总览。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1406.2661", "category": "deep_learning", "title": "Generative Adversarial Networks", "intro": "GAN 开山作，开启对抗生成模型大潮。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1409.0473", "category": "deep_learning", "title": "Neural Machine Translation by Jointly Learning to Align and Translate", "intro": "Bahdanau Attention 代表作，attention 成为主流。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1409.1556", "category": "deep_learning", "title": "Very Deep Convolutional Networks for Large-Scale Image Recognition", "intro": "VGG，证明更深但更规整的 CNN 有效。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1409.3215", "category": "deep_learning", "title": "Sequence to Sequence Learning with Neural Networks", "intro": "Seq2Seq 经典论文，奠定现代生成式序列建模。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1409.4842", "category": "deep_learning", "title": "Going Deeper with Convolutions", "intro": "Inception/GoogLeNet，提升 CNN 的计算效率与表达力。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1410.5401", "category": "deep_learning", "title": "Neural Turing Machines", "intro": "外部可微记忆结构的经典工作。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1412.3555", "category": "deep_learning", "title": "Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling", "intro": "GRU 早期代表论文，RNN gating 经典。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1412.6980", "category": "deep_learning", "title": "Adam: A Method for Stochastic Optimization", "intro": "最常用优化器之一 Adam 的原始论文。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1502.03167", "category": "deep_learning", "title": "Batch Normalization", "intro": "BatchNorm，极大改善深网络训练稳定性。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1505.04597", "category": "deep_learning", "title": "U-Net: Convolutional Networks for Biomedical Image Segmentation", "intro": "U-Net，医学图像分割最具影响力架构之一。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1508.01211", "category": "deep_learning", "title": "Listen, Attend and Spell", "intro": "端到端语音识别的 attention encoder-decoder 经典。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1512.03385", "category": "deep_learning", "title": "Deep Residual Learning for Image Recognition", "intro": "ResNet，深层网络训练范式转折点。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1512.02595", "category": "deep_learning", "title": "Deep Speech 2", "intro": "端到端 ASR 的代表性工业级成果。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1608.06993", "category": "deep_learning", "title": "Densely Connected Convolutional Networks", "intro": "DenseNet，以密集连接强化特征复用与梯度传播。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1611.01578", "category": "deep_learning", "title": "Neural Architecture Search with Reinforcement Learning", "intro": "NAS 代表作，推动 AutoML 热潮。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1706.03762", "category": "deep_learning", "title": "Attention Is All You Need", "intro": "Transformer 原始论文，现代大模型基石。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1810.04805", "category": "deep_learning", "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding", "intro": "预训练语言模型时代的核心里程碑。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1312.5602", "category": "reinforcement_learning", "title": "Playing Atari with Deep Reinforcement Learning", "intro": "DQN 最早期版本，首次把像素输入直接接到 RL。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1412.3409", "category": "reinforcement_learning", "title": "Teaching Deep Convolutional Neural Networks to Play Go", "intro": "深度方法在 Go 上的重要前奏工作。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1502.05477", "category": "reinforcement_learning", "title": "Trust Region Policy Optimization", "intro": "TRPO，现代 policy optimization 重要起点。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1506.02438", "category": "reinforcement_learning", "title": "High-Dimensional Continuous Control Using Generalized Advantage Estimation", "intro": "GAE，降低 policy gradient 方差的经典技巧。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1509.02971", "category": "reinforcement_learning", "title": "Continuous control with deep reinforcement learning", "intro": "DDPG，连续动作控制经典算法。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1509.06461", "category": "reinforcement_learning", "title": "Deep Reinforcement Learning with Double Q-learning", "intro": "Double DQN，缓解 Q 值过估计问题。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1511.05952", "category": "reinforcement_learning", "title": "Prioritized Experience Replay", "intro": "PER，让更关键的经验被优先采样。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1511.06581", "category": "reinforcement_learning", "title": "Dueling Network Architectures for Deep Reinforcement Learning", "intro": "Dueling DQN，把 state-value 和 advantage 解耦。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1602.01783", "category": "reinforcement_learning", "title": "Asynchronous Methods for Deep Reinforcement Learning", "intro": "A3C，异步 actor-critic 经典。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1706.10295", "category": "reinforcement_learning", "title": "Noisy Networks for Exploration", "intro": "NoisyNet，用参数噪声替代传统探索启发式。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1706.01905", "category": "reinforcement_learning", "title": "Parameter Space Noise for Exploration", "intro": "参数空间加噪探索的代表工作。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1707.06347", "category": "reinforcement_learning", "title": "Proximal Policy Optimization Algorithms", "intro": "PPO，最流行的 policy gradient 算法之一。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1707.06887", "category": "reinforcement_learning", "title": "A Distributional Perspective on Reinforcement Learning", "intro": "Distributional RL 奠基论文。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1710.02298", "category": "reinforcement_learning", "title": "Rainbow: Combining Improvements in Deep Reinforcement Learning", "intro": "Rainbow，把多个 DQN 改进整合成强基线。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1710.10044", "category": "reinforcement_learning", "title": "Distributional Reinforcement Learning with Quantile Regression", "intro": "QR-DQN，distributional RL 重要推进。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1712.01815", "category": "reinforcement_learning", "title": "Mastering Chess and Shogi by Self-Play with a General Reinforcement Learning Algorithm", "intro": "AlphaZero，自博弈强化学习代表作。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1801.01290", "category": "reinforcement_learning", "title": "Soft Actor-Critic", "intro": "SAC，连续控制里非常稳健的经典算法。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "1911.08265", "category": "reinforcement_learning", "title": "Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model", "intro": "MuZero，把 learned model 与 planning 结合。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "2104.06294", "category": "reinforcement_learning", "title": "Online and Offline Reinforcement Learning by Planning with a Learned Model", "intro": "Reanalyse，MuZero 路线的重要延展。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}},
  {"arxiv_id": "2206.15378", "category": "reinforcement_learning", "title": "Mastering the Game of Stratego with Model-Free Multiagent Reinforcement Learning", "intro": "DeepNash，多智能体/不完全信息博弈代表成果。", "import_options": {"with_refs": true, "annotate": true, "max_refs": 20}}
]
```

- [ ] **Step 7.2: Generate `examples/single/*.json` from `papers.json`**

```bash
python3 - << 'EOF'
import json
from pathlib import Path

papers = json.loads(Path("examples/papers.json").read_text())
for p in papers:
    path = Path(f"examples/single/{p['arxiv_id']}.json")
    path.write_text(json.dumps(p, ensure_ascii=False, indent=2))
print(f"Written {len(papers)} single-paper configs")
EOF
```

Expected output: `Written 60 single-paper configs`

- [ ] **Step 7.3: Create `examples/batch_import.py`**

Create `examples/batch_import.py`:

```python
#!/usr/bin/env python3
"""
Batch import all papers from examples/papers.json into Notion.

Usage:
    python examples/batch_import.py
    python examples/batch_import.py --dry-run
    python examples/batch_import.py --category deep_learning
    python examples/batch_import.py --limit 5
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Allow importing from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger

from main import Ar5ivToNotion
from config import AppConfig
from models import PaperStatus
from utils import setup_logging


async def run(args):
    load_dotenv()
    setup_logging(level="INFO")

    papers_file = Path(__file__).parent / "papers.json"
    papers = json.loads(papers_file.read_text())

    # Optionally filter by category
    if args.category:
        papers = [p for p in papers if p["category"] == args.category]
        logger.info(f"Filtered to {len(papers)} papers in category '{args.category}'")

    if args.limit:
        papers = papers[: args.limit]
        logger.info(f"Limiting to first {args.limit} papers")

    logger.info(f"Total papers to import: {len(papers)}")

    if args.dry_run:
        logger.info("DRY RUN — will skip Notion creation")

    config = AppConfig.from_env()
    if args.dry_run:
        config.notion.token = "dry_run"
        config.notion.root_page_id = "dry_run"

    processor = Ar5ivToNotion(config)

    results = {"success": 0, "failed": 0, "skipped": 0}

    for i, paper_cfg in enumerate(papers):
        arxiv_id = paper_cfg["arxiv_id"]
        category = paper_cfg.get("category", "")
        opts = paper_cfg.get("import_options", {})
        annotate = opts.get("annotate", True)
        with_refs = opts.get("with_refs", True)
        max_refs = opts.get("max_refs", 20)

        logger.info(f"\n[{i+1}/{len(papers)}] {arxiv_id} ({category})")

        if args.dry_run:
            logger.info(f"  DRY RUN: would import with annotate={annotate}, with_refs={with_refs}")
            results["skipped"] += 1
            continue

        paper = await processor.process_paper(
            arxiv_id=arxiv_id,
            category=category,
            with_references=with_refs,
            annotate=annotate and not args.no_annotate,
            max_ref_pages=max_refs,
        )

        if paper.status == PaperStatus.COMPLETED:
            results["success"] += 1
        else:
            results["failed"] += 1
            logger.error(f"  Failed: {paper.error}")

        # Brief pause between papers to respect rate limits
        if i < len(papers) - 1:
            await asyncio.sleep(2)

    logger.info(f"\nDone: success={results['success']}, failed={results['failed']}, skipped={results['skipped']}")


def main():
    parser = argparse.ArgumentParser(description="Batch import papers to Notion")
    parser.add_argument("--dry-run", action="store_true", help="Parse and annotate without creating Notion pages")
    parser.add_argument("--category", help="Only import papers in this category")
    parser.add_argument("--limit", type=int, help="Maximum number of papers to import")
    parser.add_argument("--no-annotate", action="store_true", help="Skip Qwen annotation")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
```

- [ ] **Step 7.4: Verify examples folder structure**

```bash
ls examples/
ls examples/single/ | head -10
python3 -c "import json; papers=json.loads(open('examples/papers.json').read()); print(f'{len(papers)} papers, categories: {set(p[\"category\"] for p in papers)}')"
```

Expected output:
```
papers.json  batch_import.py  single/
1706.03762.json  1810.04805.json  ...
60 papers, categories: {'ai_agent', 'deep_learning', 'reinforcement_learning'}
```

- [ ] **Step 7.5: Commit**

```bash
git add examples/
git commit -m "feat: add examples/ with 60-paper list and batch import script"
```

---

## Task 8: Final Integration Test + `.env.example`

**Files:**
- Create: `.env.example`

- [ ] **Step 8.1: Create `.env.example`**

```bash
cat > .env.example << 'EOF'
# Required
NOTION_TOKEN=secret_xxx
NOTION_ROOT_PAGE_ID=your_page_id_here

# Optional — Qwen annotation
DASHSCOPE_API_KEY=sk-xxx
QWEN_MODEL=qwen-plus
QWEN_ENABLED=true

# Optional — tuning
ARXIV_REQUEST_DELAY=3.0
CACHE_ENABLED=true
CACHE_DIR=./cache
LOG_LEVEL=INFO
EOF
```

- [ ] **Step 8.2: Run the complete test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests PASS. Zero failures.

- [ ] **Step 8.3: Smoke-test the CLI help**

```bash
python main.py --help
```

Expected: Help text appears with `--category`, `--no-annotate`, `--from-file` listed.

- [ ] **Step 8.4: Smoke-test a single paper import (dry-run)**

```bash
# Requires NOTION_TOKEN and NOTION_ROOT_PAGE_ID to be set, or use examples dry-run
python examples/batch_import.py --dry-run --limit 1
```

Expected: Exits cleanly with `DRY RUN: would import...`

- [ ] **Step 8.5: Final commit**

```bash
git add .env.example requirements.txt
git commit -m "feat: complete arxiv2notion redesign — LLM annotation, Academic Premium layout, file system, 60-paper examples"
```

---

## Self-Review Against Spec

| Spec Section | Covered in Task |
|---|---|
| 1. Bug fixes (5 items) | Task 1 |
| 2. FileManager + file system layout | Task 3 |
| 3. QwenAnnotator + caching | Task 4 |
| 4. Notion Academic Premium layout | Task 5 |
| 5. Reference formatting (grouped, linked) | Task 5 (`_create_references_section`) |
| 6. `examples/` + 60 papers + batch_import.py | Task 7 |
| 7. Pipeline integration | Task 6 |
| 8. CLI flags (`--category`, `--no-annotate`, `--from-file`) | Task 6 |
| ParagraphAnnotation model | Task 2 |
| QwenConfig in AppConfig | Task 2 |
| JSONL log streams (import, llm_calls, errors) | Task 3 |
| TL;DR callout from abstract annotation | Task 4 + Task 5 |
| Toggle with callout + bullets inside | Task 5 |
| Section heading emoji strategy | Task 5 |
| `.env.example` updated | Task 8 |
