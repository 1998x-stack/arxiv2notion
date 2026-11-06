"""Official arXiv HTML provider. Versions are never silently substituted."""
from __future__ import annotations
import aiohttp
from dataclasses import replace
from config import ArxivConfig
from fetch.ar5iv_extractor import Ar5ivExtractor
from fetch.providers.base import SourceCandidate
from utils import is_valid_arxiv_id, normalize_arxiv_id

class OfficialArxivHTMLProvider:
    name = "official_arxiv_html"

    def __init__(self, config: ArxivConfig | None = None):
        config = replace(config or ArxivConfig(),
                         ar5iv_base_url="https://arxiv.org/html")
        self.extractor = Ar5ivExtractor(config=config)

    async def fetch(self, paper_id: str) -> SourceCandidate:
        paper_id = normalize_arxiv_id(paper_id)
        if not is_valid_arxiv_id(paper_id):
            raise ValueError("Invalid arXiv ID")
        url = "https://arxiv.org/html/" + paper_id
        async with aiohttp.ClientSession() as session:
            html = await self.extractor._fetch_page(session, url)
        return SourceCandidate(paper_id, self.name, url,
                               html.encode("utf-8") if html else None,
                               None if html else "official_html_unavailable")

    def parse(self, candidate: SourceCandidate):
        if candidate.provider != self.name or not candidate.html:
            raise ValueError("Official HTML candidate is missing or mismatched")
        return self.extractor.parse_html(candidate.html.decode("utf-8"),
                                         candidate.paper_id)
