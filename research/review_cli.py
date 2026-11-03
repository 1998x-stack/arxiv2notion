"""Manual evidence review CLI, separate from automated annotation generation."""
import argparse
import json
import os
from pathlib import Path

from research.evidence import (
    ReviewLedger, derive_candidates, render_markdown, save_candidates,
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run(argv=None):
    parser = argparse.ArgumentParser(description="Evidence-grounded reading review")
    parser.add_argument("--ledger", default=os.getenv("REVIEWS_DB", "./data/reviews.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--document", required=True)
    generate.add_argument("--annotations", required=True)
    generate.add_argument("--out", required=True)
    record = sub.add_parser("record")
    record.add_argument("--document", required=True)
    record.add_argument("--claims", required=True)
    record.add_argument("--claim-id", required=True)
    record.add_argument("--reviewer", required=True)
    record.add_argument("--verdict", choices=["supported", "unsupported", "insufficient"],
                        required=True)
    record.add_argument("--notes", default="")
    report = sub.add_parser("report")
    report.add_argument("--claims", required=True)
    export = sub.add_parser("export")
    export.add_argument("--claims", required=True)
    export.add_argument("--out")
    args = parser.parse_args(argv)

    if args.command == "generate":
        doc = read_json(args.document)
        anns_path = Path(args.annotations)
        anns = [json.loads(line) for line in anns_path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
        data = derive_candidates(doc, anns)
        save_candidates(args.out, data)
        payload = {"claims": len(data["claims"]), "path": str(args.out)}
    else:
        data = read_json(args.claims)
        ledger = ReviewLedger(args.ledger)
        if args.command == "record":
            doc = read_json(args.document)
            claim = next((x for x in data["claims"] if x["claim_id"] == args.claim_id), None)
            if claim is None:
                raise ValueError("Claim not found")
            event_id = ledger.record(
                claim=claim, document=doc, reviewer=args.reviewer,
                verdict=args.verdict, notes=args.notes,
            )
            payload = {"event_id": event_id, "verdict": args.verdict}
        elif args.command == "report":
            payload = {"arxiv_id": data["arxiv_id"], "claims": [
                {"claim_id": x["claim_id"], "source_node_id": x["source_node_id"],
                 "verdict": (ledger.latest(x) or {}).get("verdict", "needs_review"),
                 "numeric_warning": x["numeric_warning"]}
                for x in data["claims"]
            ]}
        else:
            markdown = render_markdown(data, ledger)
            if args.out:
                Path(args.out).write_text(markdown, encoding="utf-8")
                payload = {"exported": str(args.out)}
            else:
                print(markdown)
                return 0
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
