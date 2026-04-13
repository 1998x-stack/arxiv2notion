# arxiv2notion

> One command to turn any arXiv paper into a beautifully structured Notion page — with AI reading notes.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![arXiv](https://img.shields.io/badge/arXiv-API-red)
![Notion API](https://img.shields.io/badge/Notion-API-black)

```
┌─────────────────────────────────────────────────────────────────┐
│  📄  Attention Is All You Need                                   │
│ ─────────────────────────────────────────────────────────────── │
│  ℹ️  [Callout]  Authors · 2017 · cs.CL                          │
│      arXiv: 1706.03762 | PDF | ar5iv                            │
│ ─────────────────────────────────────────────────────────────── │
│  " The dominant sequence transduction models are based on ...   │
│    [Abstract quote block]                                       │
│ ─────────────────────────────────────────────────────────────── │
│  📑  Table of Contents                                          │
│ ─────────────────────────────────────────────────────────────── │
│  1. Introduction                                                │
│  2. Background                                                  │
│  3. Model Architecture                                          │
│     ▶  [AI Reading Notes]  核心思想：用自注意力替代循环...        │
│  4. Why Self-Attention                                          │
│     ▶  [AI Reading Notes]  作者从三个维度对比了...               │
│  ...                                                            │
│ ─────────────────────────────────────────────────────────────── │
│  📚  References                                                 │
│      └─ 📎 [1409.0473] Neural Machine Translation ...           │
│      └─ 📎 [1412.6980] Adam: A Method for ...                   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Full paper extraction** — fetches metadata from the arXiv API and full structured content (sections, figures, tables, equations, references) from ar5iv (the HTML version of arXiv papers)
- **AI reading notes** — annotates every substantive paragraph in Chinese using Qwen3 LLM via DashScope, embedded as collapsible toggles in Notion
- **Rich Notion layout** — creates pages with an Academic Premium structure: blue info callout, table of contents, quote-style abstract, section headings, and reference sub-pages
- **Reference sub-pages** — automatically resolves arXiv IDs from the reference list and creates linked child pages with metadata and abstracts
- **Local file cache** — saves all content to `papers/{category}/{arxiv_id}/` and caches HTTP responses; re-importing a paper reuses the cache and skips redundant LLM calls
- **60 curated examples** — ready-to-import paper lists covering deep learning, reinforcement learning, and AI agents

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yourusername/arxiv2notion.git
cd arxiv2notion
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env: set NOTION_TOKEN and NOTION_ROOT_PAGE_ID

# 3. Import a paper
python main.py 1706.03762
```

## Installation

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Requires **Python 3.10+**.

## Configuration

Copy `.env.example` to `.env` and fill in the values.

| Variable | Required | Default | Description |
|---|---|---|---|
| `NOTION_TOKEN` | Yes | — | Notion internal integration token |
| `NOTION_ROOT_PAGE_ID` | Yes | — | ID of the Notion page that will contain all papers |
| `DASHSCOPE_API_KEY` | No | — | DashScope API key for Qwen AI reading notes |
| `QWEN_MODEL` | No | `qwen-plus` | DashScope model ID |
| `QWEN_ENABLED` | No | `true` | Set to `false` to disable annotation globally |
| `ARXIV_REQUEST_DELAY` | No | `3.0` | Seconds between arXiv API requests (min 3 s) |
| `CACHE_ENABLED` | No | `true` | Enable HTTP and content caching |
| `CACHE_DIR` | No | `./cache` | Cache directory path |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`) |

## Usage

```bash
# Import a single paper
python main.py 1706.03762

# Import with reference sub-pages (up to 20, enabled by default)
python main.py 1706.03762 --with-refs --max-refs 20

# Skip AI annotation
python main.py 1706.03762 --no-annotate

# Import multiple papers in sequence
python main.py 1706.03762 1810.04805 2301.08362

# Import from a JSON config file (see examples/single/)
python main.py --from-file examples/single/1706.03762.json

# Batch import from the curated list (60 papers)
python examples/batch_import.py --category deep_learning --limit 5

# Verbose output
python main.py 1706.03762 -v

# Bypass cache
python main.py 1706.03762 --no-cache
```

### All CLI options

| Flag | Default | Description |
|---|---|---|
| `arxiv_ids` | (required) | One or more arXiv IDs |
| `--with-refs` | enabled | Create reference sub-pages |
| `--no-refs` | — | Skip reference sub-pages |
| `--max-refs N` | 20 | Maximum number of reference sub-pages |
| `--search-refs` | — | Search arXiv for references without an ID |
| `--no-annotate` | — | Skip Qwen LLM annotation |
| `--no-cache` | — | Ignore existing cache |
| `--category` | auto | File system category folder |
| `--from-file PATH` | — | Load config from JSON file |
| `--log-file PATH` | — | Write logs to a file |
| `-v` / `--verbose` | — | Debug-level output |

## Notion Page Structure

```
📄  <Paper Title>
├── ℹ️  [Callout]  Authors · Year · Category · arXiv / PDF / ar5iv links
├── "  [Quote]    Abstract
├── 📑  Table of Contents
├── 1.  Introduction
│       ▶  AI Reading Notes  (toggle)
├── 2.  Background
│       ▶  AI Reading Notes  (toggle)
├── ...
├── ──  [Divider]
└── 📚  References
        ├── 📎  [Child page]  [1409.0473] Neural Machine Translation ...
        └── 📎  [Child page]  [1412.6980] Adam: A Method for ...
```

## File System Output

```
papers/
└── deep_learning/
    └── 1706.03762/
        ├── metadata.json       # arXiv metadata (title, authors, abstract, ...)
        ├── content.md          # Full paper as Markdown
        ├── content.json        # Structured content (sections, figures, refs)
        └── llm_annotations.jsonl  # Qwen paragraph annotations (cached)

logs/
├── import.jsonl    # One entry per successful import (timestamps, URLs, stats)
├── llm_calls.jsonl # One entry per Qwen API call
└── errors.jsonl    # One entry per error
```

## Project Structure

```
arxiv2notion/
├── main.py                  # Entry point; Ar5ivToNotion orchestrator
├── config.py                # Config dataclasses (NotionConfig, QwenConfig, ...)
├── models.py                # Data models (PaperData, ParagraphAnnotation, ...)
├── utils.py                 # Logging setup, ID normalisation helpers
├── fetch/
│   ├── arxiv_api.py         # arXiv API client (metadata, batch queries)
│   └── ar5iv_extractor.py   # ar5iv HTML extractor (sections, figures, tables)
├── process/
│   ├── reference_resolver.py  # arXiv ID extraction from reference lists
│   └── qwen_annotator.py      # Qwen3 paragraph annotation via DashScope
├── storage/
│   └── file_manager.py        # papers/ tree and logs/ JSONL writer
├── notion/
│   ├── converter.py           # Paper content → Notion block trees
│   └── creator.py             # Notion API page creation (batched)
├── examples/
│   ├── papers.json            # 60 curated papers (deep_learning, rl, ai_agent)
│   ├── batch_import.py        # Batch import script
│   └── single/                # Per-paper JSON configs
├── requirements.txt
└── .env.example
```

## Rate Limits

- **arXiv API**: 3-second delay between requests (enforced automatically)
- **Notion API**: 0.35-second delay between block writes; 100-block batching handled automatically
- **DashScope**: subject to your plan limits; ~500-1500 tokens per annotated paragraph

## License

MIT
