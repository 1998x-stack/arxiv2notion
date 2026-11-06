"""Conservative, deterministic structural quality report."""
from __future__ import annotations
from collections import Counter
from domain.scientific_document_v2 import ScientificDocument
from quality.report import QualityReport
from quality.mathematical import formula_warnings

def evaluate(document: ScientificDocument) -> QualityReport:
    document.validate()
    counts = Counter(node.kind for node in document.nodes)
    failures = []
    warnings = list(document.warnings) + formula_warnings(document)
    body_count = sum(counts[kind] for kind in (
        "paragraph", "theorem", "proof", "algorithm", "code", "footnote"
    ))
    if not body_count:
        failures.append("no_body_paragraphs")
    if not counts["heading"]:
        warnings.append("no_section_headings")
    if not document.nodes:
        failures.append("no_nodes")
    status = ("REJECTED" if failures
              else "REVIEW_REQUIRED" if warnings
              else "ACCEPTED")
    return QualityReport(
        status=status, provider=document.source.provider,
        section_count=counts["heading"], paragraph_count=body_count,
        equation_count=counts["equation"], figure_count=counts["figure"],
        table_count=counts["table"], warnings=tuple(dict.fromkeys(warnings)),
        hard_failures=tuple(failures),
    )
