"""Verify declared HTML identity; never treat a paper URL as version evidence."""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from fetch.providers.base import SourceCandidate
from utils import normalize_arxiv_id, is_valid_arxiv_id

_VERSION = re.compile(r"v[1-9]\d*$", re.I)

def check_declared_identity(candidate: SourceCandidate) -> list[str]:
    if not candidate.html:
        raise ValueError("Missing HTML bytes")
    requested = normalize_arxiv_id(candidate.paper_id)
    soup = BeautifulSoup(candidate.html, "lxml")
    declared = []
    for node in soup.select(
        'meta[name="citation_arxiv_id"], meta[name="arxiv_id"], '
        'meta[property="citation_arxiv_id"]'
    ):
        value = normalize_arxiv_id(node.get("content", ""))
        if is_valid_arxiv_id(value):
            declared.append(value)
    for node in soup.select('link[rel="canonical"]'):
        href = node.get("href", "")
        parsed = urlsplit(href)
        if parsed.hostname not in {"arxiv.org", "www.arxiv.org",
                                   "ar5iv.labs.arxiv.org"}:
            continue
        path = parsed.path
        match = re.search(r"/(?:html|abs)/(.+)$", path)
        if match:
            value = match.group(1)
            if is_valid_arxiv_id(value):
                declared.append(value)

    def base(value: str) -> str:
        return _VERSION.sub("", value)

    for value in declared:
        if base(value) != base(requested):
            raise ValueError("HTML declares a different arXiv paper")
        if _VERSION.search(value) and _VERSION.search(requested) and value != requested:
            raise ValueError("HTML declares a different arXiv revision")
    if _VERSION.search(requested) and not any(
        _VERSION.search(value) and value == requested for value in declared
    ):
        return ["requested_revision_not_confirmed_by_html_metadata"]
    return []
