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
from utils import setup_logging, normalize_arxiv_id


async def run(args):
    load_dotenv()
    setup_logging(level="INFO")

    papers_file = Path(__file__).parent / "papers.json"
    papers = json.loads(papers_file.read_text())

    if args.category:
        papers = [p for p in papers if p["category"] == args.category]
        logger.info(f"Filtered to {len(papers)} papers in category '{args.category}'")

    if args.limit:
        papers = papers[: args.limit]
        logger.info(f"Limiting to first {args.limit} papers")

    logger.info(f"Total papers to import: {len(papers)}")

    if args.dry_run:
        logger.info("DRY RUN — printing papers only, no Notion or API calls")
        for i, p in enumerate(papers):
            logger.info(f"  [{i+1}] {p['arxiv_id']} ({p['category']}) — {p['title']}")
        logger.info(f"Done. Would import {len(papers)} papers.")
        return

    config = AppConfig.from_env()
    processor = Ar5ivToNotion(config)

    results = {"success": 0, "failed": 0}

    for i, paper_cfg in enumerate(papers):
        arxiv_id = paper_cfg["arxiv_id"]
        category = paper_cfg.get("category", "")
        opts = paper_cfg.get("import_options", {})
        annotate = opts.get("annotate", True)
        with_refs = opts.get("with_refs", True)
        max_refs = opts.get("max_refs", 20)

        logger.info(f"\n[{i+1}/{len(papers)}] {arxiv_id} ({category})")

        paper = await processor.process_paper(
            arxiv_id=normalize_arxiv_id(arxiv_id),
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

        if i < len(papers) - 1:
            await asyncio.sleep(2)

    logger.info(f"\nDone: success={results['success']}, failed={results['failed']}")


def main():
    parser = argparse.ArgumentParser(description="Batch import papers to Notion")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print paper list without making any API calls")
    parser.add_argument("--category",
                        help="Only import papers in this category (ai_agent, deep_learning, reinforcement_learning)")
    parser.add_argument("--limit", type=int,
                        help="Maximum number of papers to import")
    parser.add_argument("--no-annotate", action="store_true", dest="no_annotate",
                        help="Skip Qwen annotation")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
