"""Multi-source resolution that never silently selects conflicting content."""
from __future__ import annotations
from dataclasses import dataclass, field
from domain.scientific_document_v2 import ScientificDocument
from models import Ar5ivContent
from domain.provenance import DocumentSource
from adapters.legacy_to_v2 import from_legacy
from fetch.providers.base import Provider, SourceCandidate
from quality.report import QualityReport
from quality.structural import evaluate
from quality.source_selector import choose
from utils import normalize_arxiv_id, is_valid_arxiv_id
from fetch.providers.identity import check_declared_identity

@dataclass
class ResolutionResult:
    status: str
    document: ScientificDocument | None
    candidate: SourceCandidate | None
    legacy_content: Ar5ivContent | None = None
    reports: list[QualityReport] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

class MultiSourceResolver:
    def __init__(self, providers: list[Provider]):
        if not providers:
            raise ValueError("At least one source provider required")
        self.providers = providers

    async def resolve(self, paper_id: str) -> ResolutionResult:
        normalized = normalize_arxiv_id(paper_id)
        if not is_valid_arxiv_id(normalized):
            raise ValueError("Invalid arXiv identifier")
        entries = []
        failures = []
        for provider in self.providers:
            try:
                candidate = await provider.fetch(normalized)
                if candidate.paper_id != normalized:
                    failures.append(f"{provider.name}:version_mismatch")
                    continue
                if not candidate.available:
                    failures.append(f"{provider.name}:{candidate.error or 'unavailable'}")
                    continue
                identity_warnings = check_declared_identity(candidate)
                parsed = provider.parse(candidate)
                if parsed is None:
                    failures.append(f"{provider.name}:empty_parsed_article")
                    continue
                parsed.source_provider = provider.name
                source = DocumentSource.from_bytes(
                    provider=provider.name, url=candidate.url,
                    paper_id=normalized, content=candidate.html,
                )
                document = from_legacy(parsed, source)
                document.warnings.extend(identity_warnings)
                report = evaluate(document)
                entries.append((document, report, candidate, parsed))
            except (ValueError, TypeError, OSError) as exc:
                failures.append(f"{provider.name}:{type(exc).__name__}")
        selected = choose([(document, report) for document, report, _, _ in entries])
        if selected.selected_index is not None:
            document, _, candidate, parsed = entries[selected.selected_index]
        else:
            document = candidate = parsed = None
        return ResolutionResult(
            status=selected.status, document=document, candidate=candidate,
            legacy_content=parsed,
            reports=[report for _, report, _, _ in entries], failures=failures,
        )
