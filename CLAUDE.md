# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_arxiv_api.py -v

# Run async tests
pytest tests/ -v --asyncio-mode=auto

# Code formatting
black .

# Type checking
mypy .

# Run the tool
python main.py 1706.03762
python main.py 1706.03762 --with-refs --max-refs 10
python main.py 1706.03762 --no-cache -v
```

## Architecture

This is a pipeline tool that imports arXiv papers into Notion as rich structured pages.

### Data Flow

```
ArxivAPI → ArxivMetadata
                       \
                        → PaperData → NotionConverter → blocks → NotionCreator → Notion pages
                       /
Ar5ivExtractor → Ar5ivContent
```

The main orchestrator is `Ar5ivToNotion` in `main.py`, which coordinates all modules in sequence:
1. Fetch arXiv metadata via `arxiv_api.py`
2. Extract full content from ar5iv HTML via `ar5iv_extractor.py`
3. Resolve references (extract arXiv IDs from raw text) via `reference_resolver.py`
4. Convert content to Notion block format via `notion_converter.py`
5. Create pages in Notion via `notion_creator.py`

### Key Design Decisions

- **Async throughout**: `arxiv_api.py` and `ar5iv_extractor.py` use `aiohttp`; `notion_creator.py` uses synchronous `notion-client` (with `time.sleep`) despite being called from async context. The main loop runs with `asyncio.run()`.
- **Batching**: Notion API has a 100-block-per-request limit. `NotionCreator._append_blocks_batched()` handles this automatically.
- **Caching**: All HTTP responses are cached as JSON to `./cache/arxiv/` and `./cache/ar5iv/`. Disable with `--no-cache`.
- **Graceful fallback**: If ar5iv content extraction fails, the tool falls back to metadata-only mode.

### Configuration

All config is loaded via `AppConfig.from_env()` which reads `.env` file. Required env vars:
- `NOTION_TOKEN` — Notion Internal Integration Token
- `NOTION_ROOT_PAGE_ID` — Target page where papers are created as children

Config dataclasses in `config.py`: `NotionConfig`, `ArxivConfig`, `CacheConfig`, `ReferenceConfig`, `ContentConfig`.

### Data Models (`models.py`)

- `ArxivMetadata` — from arXiv API (title, authors, abstract, categories)
- `Ar5ivContent` — from ar5iv HTML (sections, figures, tables, equations, references)
- `PaperData` — merged container passed through the pipeline
- `Reference` — parsed reference entry (may or may not have an `arxiv_id`)
- `NotionBlockData` — intermediate Notion block representation
- `CreationResult` — result from Notion page creation

### Rate Limits

- arXiv API: 3-second delay between requests (`ArxivConfig.request_delay`)
- Notion API: 0.35-second delay between requests (`NotionConfig.rate_limit_delay`), with exponential backoff on `rate_limited` errors
