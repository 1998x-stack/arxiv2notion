# AGENTS.md

## Commands

```bash
# Run tests (asyncio_mode=auto is in pytest.ini — no CLI flag needed)
pytest tests/ -v
pytest tests/test_qwen_annotator.py -v

# Lint / typecheck (pyrightconfig.json has machine-specific pythonPath — update it)
black .
mypy .

# Run the tool
python main.py 1706.03762
python main.py 1706.03762 --no-refs --no-annotate
python main.py --from-file examples/single/1706.03762.json
```

## Architecture gotchas

- **Sync/async split**: `fetch/` (arxiv_api, ar5iv_extractor) is async with `aiohttp`. `notion/creator.py` is **synchronous** (`notion-client` is sync-only, uses `time.sleep` for rate limiting). `storage/file_manager.py` is sync. The `main.py` orchestrator runs under `asyncio.run()` and calls sync Notion code directly — no executor wrapper.
- **Qwen via DashScope**: `process/qwen_annotator.py` uses the `openai` library in DashScope-compatible mode (`base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"`). It's not calling the Qwen API directly.
- **CLI double-negative**: `--with-refs` defaults to `True`. Use `--no-refs` to disable. `--no-annotate` uses `dest="no_annotate"` — access as `args.no_annotate`.
- **`--from-file`**: Parsed manually inside `main_async()`, not via argparse subparsers. Reads the JSON, then mutates `args.arxiv_ids`, `args.category`, etc.
- **Cache auto-creation**: `CacheConfig.__post_init__` creates `./cache/arxiv/` and `./cache/ar5iv/` on import. No manual setup needed.
- **pytest.ini** sets `asyncio_mode = auto` — the `--asyncio-mode=auto` flag in CLAUDE.md is redundant.
- **`conftest.py`** manually inserts project root into `sys.path` for imports.

## Package layout

```
main.py              # Entry point, arg parser, Ar5ivToNotion orchestrator
config.py            # AppConfig + per-domain config dataclasses
models.py            # All dataclasses (PaperData, Section, Reference, ParagraphAnnotation, etc.)
utils.py             # Logging, ID normalisation, URL builders, JSON I/O
fetch/               # Async: arxiv_api.py (aiohttp), ar5iv_extractor.py (aiohttp + bs4)
process/             # qwen_annotator.py (openai→DashScope), reference_resolver.py
notion/              # converter.py (PaperData→blocks), creator.py (sync notion-client)
storage/             # file_manager.py (sync I/O for papers/ tree + logs/ JSONL)
```

Each subpackage (`fetch/`, `process/`, `notion/`, `storage/`) is a flat namespace — no `__init__.py` wrappers, modules are imported directly by name.

## Notion API specifics

- The Notion integration must be **manually added** to the target page in Notion's UI (Connections menu). Without this, all API calls return 404.
- `NOTION_ROOT_PAGE_ID` is a page UUID (32 hex chars with hyphens), not a database ID.
- 100-block batching is handled automatically by `_append_blocks_batched()`. Do not batch manually.

## Environment

- `.env` is required at runtime (not just CI). `AppConfig.from_env()` calls `load_dotenv()`.
- `pyrightconfig.json` has a machine-specific `pythonPath` — may need updating per developer.
- Docker: `docker compose run arxiv2notion 1706.03762 --no-refs`
