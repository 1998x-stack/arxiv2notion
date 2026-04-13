# Design Spec: arxiv2notion Full Redesign

**Date:** 2026-04-13  
**Status:** Approved  
**Scope:** Bug fixes, Qwen LLM annotation, Academic Premium Notion layout, structured file system + logging, examples/ folder, reference formatting

---

## Overview

Six coordinated improvements to the `arxiv2notion` pipeline:

1. **Bug fixes** — 5 confirmed bugs in existing code
2. **Notion Academic Premium layout** — richer use of all Notion block types
3. **Qwen3.6-plus annotation** — per-paragraph AI reading notes (Chinese, toggle placement)
4. **File system + log system** — structured `papers/` tree + JSONL logs
5. **`examples/` folder** — 60-paper stubs + batch import script
6. **Reference formatting** — structured, linked, grouped

Architecture approach: **additive modules**. The existing linear pipeline (`ArxivAPI → Ar5iv → NotionCreate`) is extended with two new modules and surgical fixes. No redesign of core data models.

---

## 1. Bug Fixes

### 1.1 `aiohttp.ClientTimeout` (ar5iv_extractor.py:90)

**Problem:** `session.get(url, timeout=60)` passes a raw int; aiohttp requires a `ClientTimeout` object and will raise a `ValueError`.

**Fix:** Replace with `aiohttp.ClientTimeout(total=self.config.timeout)` in `_fetch_page()`.

### 1.2 Per-call `ClientSession` (ar5iv_extractor.py:555)

**Problem:** `async with aiohttp.ClientSession() as session:` is created inside `extract_paper()`, so each paper creates and destroys a session. Defeats connection pooling.

**Fix:** Accept an optional `session: Optional[aiohttp.ClientSession]` parameter on `extract_paper()`. When called from a batch context (future or `process_papers()`), a single session is created by the caller and passed down.

### 1.3 `format_exception` output (utils.py:60)

**Problem:** `repr(traceback.format_exception(...))` produces a Python repr of a list — e.g. `"['Traceback (most recent call last):\\n', ...]"` — unreadable in logs.

**Fix:** Replace with `traceback.format_exc()` which returns a clean, newline-delimited string.

### 1.4 CacheConfig subcache dirs (config.py:57–63)

**Problem:** `CacheConfig` defines `arxiv_cache_dir = Path("./cache/arxiv")` and `ar5iv_cache_dir = Path("./cache/ar5iv")` as independent fields. When `AppConfig.from_env()` sets a custom `CACHE_DIR`, the subcache dirs ignore it and always point to `./cache/arxiv`.

**Fix:** Remove hardcoded defaults for subcache dirs. Compute them from `cache_dir` in `CacheConfig.__post_init__`:
```python
def __post_init__(self):
    self.arxiv_cache_dir = self.cache_dir / "arxiv"
    self.ar5iv_cache_dir = self.cache_dir / "ar5iv"
    self.ensure_directories()
```

### 1.5 Dead `_rate_limit_wait` method (notion_creator.py:70)

**Problem:** `_rate_limit_wait()` is defined as `async def` but never awaited anywhere in the class. All actual waiting is done via `time.sleep()`. This is dead, misleading code.

**Fix:** Remove the method entirely.

---

## 2. New Module: `file_manager.py`

### 2.1 File System Layout

```
papers/
├── ai_agent/
│   └── {arxiv_id}/
│       ├── metadata.json          # arXiv API metadata (ArxivMetadata.to_dict())
│       ├── content.md             # full paper text as readable Markdown
│       ├── content.json           # structured Ar5ivContent.to_dict()
│       └── llm_annotations.jsonl  # one JSON line per paragraph annotation
├── deep_learning/
│   └── {arxiv_id}/
│       └── ...
└── reinforcement_learning/
    └── {arxiv_id}/
        └── ...

logs/
├── import.jsonl    # one entry per paper import run
├── llm_calls.jsonl # one entry per Qwen API call
└── errors.jsonl    # structured error entries

examples/
├── papers.json     # all 60 paper stubs [{arxiv_id, category, title, intro}]
└── single/
    ├── 1706.03762.json
    └── ...         # one file per paper, import config format
```

### 2.2 Log Entry Schemas

**`logs/import.jsonl`** — one dict per line:
```json
{
  "ts": "2026-04-13T14:23:00",
  "arxiv_id": "1706.03762",
  "category": "deep_learning",
  "status": "completed",
  "notion_page_id": "abc123",
  "notion_url": "https://notion.so/...",
  "duration_ms": 12400,
  "blocks_created": 342,
  "ref_pages_created": 18,
  "annotated_paragraphs": 47,
  "error": null
}
```

**`logs/llm_calls.jsonl`** — one dict per line:
```json
{
  "ts": "2026-04-13T14:22:10",
  "arxiv_id": "1706.03762",
  "section_title": "Model Architecture",
  "para_idx": 3,
  "tokens_in": 312,
  "tokens_out": 89,
  "latency_ms": 1240,
  "model": "qwen-plus",
  "cached": false,
  "error": null
}
```

**`logs/errors.jsonl`** — one dict per line:
```json
{
  "ts": "2026-04-13T14:22:55",
  "arxiv_id": "1706.03762",
  "stage": "ar5iv_extract",
  "error_type": "TimeoutError",
  "message": "Request to ar5iv timed out after 60s",
  "traceback_snippet": "..."
}
```

### 2.3 `FileManager` Class Interface

```python
class FileManager:
    def __init__(self, base_dir: Path = Path("."))
    
    def get_paper_dir(self, arxiv_id: str, category: str) -> Path
    def save_metadata(self, arxiv_id: str, category: str, metadata: ArxivMetadata) -> None
    def save_content_md(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None
    def save_content_json(self, arxiv_id: str, category: str, content: Ar5ivContent) -> None
    def save_annotations(self, arxiv_id: str, category: str, annotations: List[ParagraphAnnotation]) -> None
    def load_annotations(self, arxiv_id: str, category: str) -> List[ParagraphAnnotation]  # returns [] if not found
    def has_annotations(self, arxiv_id: str, category: str) -> bool
    
    def log_import(self, event: dict) -> None   # appends to logs/import.jsonl
    def log_llm_call(self, event: dict) -> None  # appends to logs/llm_calls.jsonl
    def log_error(self, event: dict) -> None    # appends to logs/errors.jsonl
```

All file I/O in `FileManager` is **synchronous** (no async needed — file writes are fast and infrequent).

---

## 3. New Module: `qwen_annotator.py`

### 3.1 API Configuration

- Model: `qwen-plus` (DashScope name for qwen3.6-plus)
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1` (OpenAI-compatible)
- API key: from `$DASHSCOPE_API_KEY` env var
- `enable_thinking`: disabled via `extra_body={"enable_thinking": False}`
- SDK: `openai` (OpenAI-compatible client, avoids adding dashscope dep)

### 3.2 `ParagraphAnnotation` Data Model

```python
@dataclass
class ParagraphAnnotation:
    section_title: str
    para_idx: int       # index within section
    para_text: str      # first 200 chars of original text (for verification)
    plain_explanation: str  # Chinese plain-language summary
    key_points: List[str]   # 2-3 Chinese bullet points
    cached: bool = False    # True if loaded from file, not API
```

### 3.3 Prompt Design

**System:** `你是一位耐心的学术论文辅导老师，擅长用通俗易懂的中文解释复杂的技术段落。`

**User:**
```
请分析以下学术段落，用中文回答：

1. 通俗解读（1-2句话）：用简单的语言解释这段话的核心意思
2. 关键要点（2-3条）：每条一句话，提炼最重要的信息

段落原文：
{text}

回答格式：
通俗解读：...
要点1：...
要点2：...
要点3：（如有必要）
```

### 3.4 Caching Strategy

Before calling the API, `QwenAnnotator` checks `FileManager.has_annotations(arxiv_id, category)`. If annotations exist on disk, they are loaded and returned without any API call. This means re-importing a paper to Notion does not re-annotate — annotation is done once per paper.

### 3.5 `QwenAnnotator` Class Interface

```python
class QwenAnnotator:
    def __init__(self, file_manager: FileManager, api_key: Optional[str] = None)
    
    async def annotate_paper(
        self,
        content: Ar5ivContent,
        arxiv_id: str,
        category: str
    ) -> List[ParagraphAnnotation]
    
    async def annotate_paragraph(
        self,
        text: str,
        section_title: str,
        para_idx: int
    ) -> ParagraphAnnotation
```

Paragraphs shorter than 100 chars (e.g. section intros, captions) are **skipped** — not worth annotating.

---

## 4. Notion Page Redesign (Academic Premium)

### 4.1 Full Page Structure

```
[💻 callout — blue_background]
   "📅 Published: YYYY-MM-DD  |  👥 Authors: A, B, C et al. (N authors)
    🏷️ cs.CL · cs.LG  |  📰 Journal: ...  |  🔗 DOI: ..."

[paragraph — links row]
   🔗 Links:  [arXiv]  |  [PDF]  |  [ar5iv]

[divider]

[heading_2 — "📝 Abstract"]
[quote — abstract text, amber/orange_background]

[callout — green_background — "💡 TL;DR"]
   One-sentence Qwen summary of the whole paper

[divider]

[heading_2 — "📑 Contents"]
[table_of_contents]

[divider]

For each section:
  [heading_1/2/3 — "📌 {Section Title}" or "🔬" depending on type]
  
  For each paragraph in section:
    [paragraph]
    [toggle — "🤖 AI 阅读笔记"]
      [callout — gray_background — "💬 通俗解读"]
        {plain_explanation}
      [bulleted_list_item] × 2-3 — key points

[divider]

[heading_2 — "📚 参考文献 (References)"]
[callout — green_background]
   "✅ 找到 N 篇 arXiv 论文，已创建子页面"

For each reference WITH arXiv ID:
  [paragraph with rich_text]
    "[{key}]  {Authors} ({Year}). {Title}. {Venue}.  [→ arXiv:{id}]"
    where [→ arXiv:{id}] is a colored link

[toggle — "📎 其他参考文献 ({N} 篇)"]
  [bulleted_list_item] × N — non-arXiv refs

[divider]

[heading_2 — "🖼️ Figures"]
[image + caption] × N

[heading_2 — "📊 Tables"]
[bold paragraph — caption]
[table block] × N
```

### 4.2 Section Heading Emoji Strategy

Section titles get contextual emoji prefixes based on keywords:
- Introduction → 📌
- Method / Architecture / Model → 🔬
- Experiment / Result / Evaluation → 📊
- Related Work / Background → 📚
- Conclusion / Discussion → 💡
- Default → 📄

### 4.3 TL;DR Generation

The paper-level TL;DR is generated by calling Qwen once with the abstract text and asking for a single Chinese sentence summary. This is done as part of `QwenAnnotator.annotate_paper()`, stored as a special annotation with `section_title="__abstract__"`, `para_idx=-1`.

---

## 5. Reference Formatting

### 5.1 Format Template

For references where structured info is available:
```
[{citation_key}]  {LastName}, {First} et al. ({year}). {title}. {venue}.
```
With a `→ arXiv:{arxiv_id}` rich-text link appended in blue.

When `title` cannot be extracted from raw text, fall back to: `[{key}]  {raw_text truncated to 200 chars}  → [arXiv:{id}]`

### 5.2 Grouping

- **arXiv refs** (those with resolved `arxiv_id`): displayed as formatted paragraphs, each on its own line, directly in the References section.
- **Non-arXiv refs**: collected into a toggle `"📎 Other References (N)"` as bulleted list items — keeps the main references section clean.

### 5.3 Reference Sub-Pages

Reference sub-pages (created by `NotionCreator.create_reference_page`) also receive the redesigned layout:
- blue_background callout with metadata
- Abstract as quote
- Links row (arXiv + PDF)

---

## 6. `examples/` Folder

### 6.1 `examples/papers.json`

Array of 60 objects, one per paper:
```json
[
  {
    "arxiv_id": "1706.03762",
    "category": "deep_learning",
    "title": "Attention Is All You Need",
    "intro": "Transformer 原始论文，现代大模型基石。",
    "import_options": {
      "with_refs": true,
      "annotate": true,
      "max_refs": 20
    }
  },
  ...
]
```

Categories used: `"deep_learning"`, `"reinforcement_learning"`, `"ai_agent"`.

### 6.2 `examples/single/{arxiv_id}.json`

Per-paper config file (same schema as one entry in `papers.json`). Allows: `python main.py --from-file examples/single/1706.03762.json`.

### 6.3 `examples/batch_import.py`

Standalone script:
```python
# Usage: python examples/batch_import.py [--dry-run] [--category deep_learning]
# Reads examples/papers.json, imports each paper via main.py pipeline
# Logs results to logs/import.jsonl
# Respects --dry-run (parse + annotate, skip Notion creation)
```

---

## 7. Pipeline Integration

The updated `Ar5ivToNotion.process_paper()` flow:

```
1. Fetch arXiv metadata          (arxiv_api.py — unchanged)
2. Extract ar5iv content         (ar5iv_extractor.py — bug fixed)
3. Annotate paragraphs           (qwen_annotator.py — NEW, uses file cache)
4. Save to file system           (file_manager.py — NEW)
5. Resolve references            (reference_resolver.py — unchanged)
6. Convert to Notion blocks      (notion_converter.py — redesigned layout, accepts annotations)
7. Create Notion pages           (notion_creator.py — unchanged logic, uses new blocks)
```

Step 3 is skippable via `--no-annotate` flag (for fast re-imports when Notion page is deleted but paper was already annotated).

Step 4 happens after annotation so the JSONL file includes annotation data.

---

## 8. Updated CLI

New flags added to `main.py`:

| Flag | Default | Description |
|---|---|---|
| `--category` | auto-detect from arXiv primary category | Override file system category |
| `--no-annotate` | False | Skip Qwen annotation step |
| `--from-file PATH` | — | Load paper config from JSON file |

`--category` auto-detection maps arXiv primary category prefix to folder:
- `cs.*`, `stat.*`, `eess.*` → maps based on keywords in category description, defaulting to folder name based on arXiv category

---

## Out of Scope

- Multi-threaded batch import (sequential with delays is intentional for rate limiting)
- Notion database (vs page) integration
- Web UI or API server
- PDF processing (only ar5iv HTML is used)
