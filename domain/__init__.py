"""Canonical research-paper domain model."""
from .paper_document import (
    DocumentNode, PaperDocument, ParagraphRef, ParseQuality,
    assess_quality, build_paper_document, iter_paragraph_refs,
)
