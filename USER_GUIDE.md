# User Guide — arxiv2notion

## Prerequisites

- **Python 3.10+** — check with `python --version`
- **Notion account** with API access (free or paid)
- **DashScope account** — optional, required only for AI reading notes

---

## Installation

### 1. Clone and install

```bash
git clone https://github.com/yourusername/arxiv2notion.git
cd arxiv2notion

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. Environment setup

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` in any text editor. The minimal working configuration is:

```
NOTION_TOKEN=secret_xxx
NOTION_ROOT_PAGE_ID=your_page_id
```

Everything else is optional and has sensible defaults.

### 3. Notion setup

#### Step 1 — Create an integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g. `arxiv2notion`) and select your workspace
4. Under "Capabilities", ensure **"Read content"** and **"Insert content"** are enabled
5. Click **"Submit"**
6. Copy the **"Internal Integration Token"** (starts with `secret_`) — this is your `NOTION_TOKEN`

#### Step 2 — Get the root page ID

1. In Notion, open or create the page where papers should be imported
2. Click **"..."** in the top-right corner, then **"Copy link"**
3. The link looks like: `https://www.notion.so/My-Papers-abc123def456...`
4. The page ID is the last part after the final `-` (or the full hex string if there is no `-`): `abc123def456...`
5. Set this as `NOTION_ROOT_PAGE_ID` in your `.env`

#### Step 3 — Grant the integration access

The integration cannot see pages unless it is explicitly added:

1. Open the root page in Notion
2. Click **"..."** → **"Connections"** (or **"Add connections"**)
3. Search for your integration name and click to add it
4. The integration now has access to that page and all its children

---

## Configuration Reference

All settings live in `.env`. None require a restart after change — they are read at launch.

| Variable | Type | Default | Description |
|---|---|---|---|
| `NOTION_TOKEN` | string | — | **Required.** Notion internal integration secret |
| `NOTION_ROOT_PAGE_ID` | string | — | **Required.** ID of the parent page for all imports |
| `DASHSCOPE_API_KEY` | string | — | Optional. DashScope key for Qwen AI notes |
| `QWEN_MODEL` | string | `qwen-plus` | DashScope model name |
| `QWEN_ENABLED` | bool | `true` | Set `false` to disable annotation globally |
| `ARXIV_REQUEST_DELAY` | float | `3.0` | Seconds between arXiv API calls (min 3 s per ToS) |
| `CACHE_ENABLED` | bool | `true` | Cache arXiv metadata and ar5iv HTML locally |
| `CACHE_DIR` | path | `./cache` | Directory for HTTP caches |
| `LOG_LEVEL` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

---

## Importing Papers

### Single paper

```bash
python main.py 1706.03762
```

The arXiv ID can be in any common format — `1706.03762`, `cs/0610101`, or a full URL.

### With references

Reference sub-pages are enabled by default. To control them:

```bash
# Create up to 20 reference sub-pages (default)
python main.py 1706.03762 --with-refs --max-refs 20

# Skip reference sub-pages entirely
python main.py 1706.03762 --no-refs

# Search arXiv for references that don't have an arXiv ID in their text
python main.py 1706.03762 --with-refs --search-refs
```

### Batch import (multiple IDs)

Pass multiple IDs directly; papers are processed sequentially with a 2-second gap:

```bash
python main.py 1706.03762 1810.04805 2301.08362
```

### Batch import from the curated list

`examples/papers.json` contains 60 curated papers across three categories: `deep_learning`, `reinforcement_learning`, and `ai_agent`.

```bash
# Import 5 deep learning papers
python examples/batch_import.py --category deep_learning --limit 5

# Import all RL papers
python examples/batch_import.py --category reinforcement_learning

# Dry run — show which papers would be imported without importing
python examples/batch_import.py --category ai_agent --dry-run
```

### From a JSON config file

Each paper in `examples/single/` is a standalone JSON config:

```json
{
  "arxiv_id": "1706.03762",
  "category": "deep_learning",
  "import_options": {
    "with_refs": true,
    "annotate": true,
    "max_refs": 20
  }
}
```

Import it with:

```bash
python main.py --from-file examples/single/1706.03762.json
```

You can create your own JSON config files following this schema and point `--from-file` at them.

---

## AI Reading Notes (Qwen)

When `DASHSCOPE_API_KEY` is set, each substantive paragraph (100+ characters) is annotated in Chinese by Qwen3 and added to the Notion page as a collapsible toggle block directly after the paragraph:

```
3. Model Architecture
   The encoder maps an input sequence of symbol ...

   ▶  AI Reading Notes
      编码器将输入符号序列映射到连续表示序列。Transformer 摒弃了传统的
      循环结构，完全依赖自注意力机制来建模序列内部依赖关系...
```

### How to get a DashScope API key

1. Register at [https://dashscope.aliyun.com](https://dashscope.aliyun.com)
2. Go to **API Keys** in the console
3. Create a key and copy it into `DASHSCOPE_API_KEY`

### Token cost estimate

Each paragraph annotation uses roughly 200–800 input tokens and up to 512 output tokens. A typical 10-section paper produces ~50–100 annotations, consuming approximately 30 000–80 000 tokens in total. Check the DashScope pricing page for current rates.

### Disabling annotation

Per-run:

```bash
python main.py 1706.03762 --no-annotate
```

Globally (in `.env`):

```
QWEN_ENABLED=false
```

---

## File System Output

Every imported paper is saved locally, regardless of whether Notion creation succeeds.

### Directory structure

```
papers/
└── {category}/
    └── {arxiv_id}/
        ├── metadata.json          # Full arXiv metadata
        ├── content.md             # Human-readable Markdown
        ├── content.json           # Structured JSON (sections, figures, refs)
        └── llm_annotations.jsonl  # Qwen annotations, one per line
```

**Category** is one of `deep_learning`, `reinforcement_learning`, `ai_agent`, or `other`, auto-detected from the paper's arXiv primary category. Override with `--category`.

### What `metadata.json` contains

```json
{
  "arxiv_id": "1706.03762",
  "title": "Attention Is All You Need",
  "authors": ["Vaswani, Ashish", "..."],
  "abstract": "...",
  "primary_category": "cs.CL",
  "categories": ["cs.CL", "cs.LG"],
  "published": "2017-06-12",
  "updated": "2023-08-02",
  "pdf_url": "https://arxiv.org/pdf/1706.03762",
  "arxiv_url": "https://arxiv.org/abs/1706.03762"
}
```

### Re-importing without re-annotating

Annotations are cached in `llm_annotations.jsonl`. On subsequent runs the annotator detects the existing file and loads it from disk instead of calling the LLM again, saving both time and tokens.

To force re-annotation, delete the `llm_annotations.jsonl` file for that paper, or use `--no-cache` to bypass the HTTP caches.

---

## Logs

All log files are JSONL (one JSON object per line), written to `logs/`.

### `logs/import.jsonl`

One entry per completed import:

| Field | Description |
|---|---|
| `ts` | ISO 8601 timestamp |
| `arxiv_id` | Paper ID |
| `category` | File system category |
| `status` | `completed` or `failed` |
| `notion_page_id` | ID of the created Notion page |
| `notion_url` | Direct URL to the page |
| `duration_ms` | Total processing time in milliseconds |
| `blocks_created` | Number of Notion blocks added |
| `ref_pages_created` | Number of reference child pages created |
| `annotated_paragraphs` | Number of paragraphs annotated by Qwen |

### `logs/llm_calls.jsonl`

One entry per Qwen API call, including model, token counts, latency, and whether the result was cached.

### `logs/errors.jsonl`

One entry per error, with fields `arxiv_id`, `stage` (which processing step failed), `error_type`, and `message`.

---

## Troubleshooting

**"ar5iv content extraction failed"**
The paper may not yet be indexed by ar5iv (common for papers published in the last few days). The tool falls back to arXiv-API-only metadata and still creates a Notion page, just without the full body text.

**"NOTION_TOKEN not set" or "NOTION_ROOT_PAGE_ID not set"**
Check that `.env` exists in the project root and contains the correct variable names. The file must be in the directory from which you run `python main.py`.

**"DASHSCOPE_API_KEY not set — skipping annotation"**
This is a warning, not an error. The paper will be imported without AI reading notes. Set `DASHSCOPE_API_KEY` in `.env` if you want annotations.

**Rate limit errors from the Notion API**
The default delay between Notion writes is 0.35 seconds. If you hit rate limits, try running smaller batches or adding `RATE_LIMIT_DELAY=0.5` to your `.env`.

**Rate limit errors from arXiv**
The minimum required delay is 3 seconds. Do not set `ARXIV_REQUEST_DELAY` below `3.0`.

**Notion 100-block limit**
Notion's API only accepts 100 blocks per request. The tool automatically splits large papers into batches, so this is handled transparently.

**Paper page is created but content is truncated**
By default the converter includes up to 50 sections, 30 figures, 20 tables, and 100 equations. These limits exist to keep pages within Notion's block budget. They are not configurable via CLI today.

---

## Advanced: Batch Import

`examples/batch_import.py` reads `examples/papers.json` and imports papers according to the `import_options` embedded in each entry.

### Filtering by category

```bash
python examples/batch_import.py --category deep_learning
python examples/batch_import.py --category reinforcement_learning
python examples/batch_import.py --category ai_agent
```

### Limiting the number of imports

```bash
python examples/batch_import.py --category deep_learning --limit 3
```

### Dry-run mode

Preview which papers would be imported without making any API calls:

```bash
python examples/batch_import.py --dry-run
```

### Adding your own papers to `examples/papers.json`

Append an object following this schema:

```json
{
  "arxiv_id": "2312.00752",
  "category": "deep_learning",
  "title": "Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
  "intro": "Optional short description for your own reference.",
  "import_options": {
    "with_refs": true,
    "annotate": true,
    "max_refs": 15
  }
}
```

`title` and `intro` are metadata for your reference only — the tool always fetches the authoritative title from the arXiv API.
