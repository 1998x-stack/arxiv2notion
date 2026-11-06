"""ar5iv HTML source adapter (reuses bounded V2 fetch implementation)."""
from __future__ import annotations
import aiohttp
from config import ArxivConfig
from fetch.ar5iv_extractor import Ar5ivExtractor
from fetch.providers.base import SourceCandidate
from utils import is_valid_arxiv_id, normalize_arxiv_id

class Ar5ivProvider:
    name = "ar5iv"

    def __init__(self, config: ArxivConfig | None = None):
        self.extractor = Ar5ivExtractor(config=config or ArxivConfig())

    async def fetch(self, paper_id: str) -> SourceCandidate:
        paper_id = normalize_arxiv_id(paper_id)
        if not is_valid_arxiv_id(paper_id):
            raise ValueError("Invalid arXiv ID")
        url = self.extractor.config.ar5iv_base_url.rstrip("/") + "/" + paper_id
        async with aiohttp.ClientSession() as session:
            html = await self.extractor._fetch_page(session, url)
        return SourceCandidate(paper_id, self.name, url,
                               html.encode("utf-8") if html else None,
                               None if html else "ar5iv_unavailable")

    def parse(self, candidate: SourceCandidate):
        if candidate.provider != self.name or not candidate.html:
            raise ValueError("ar5iv candidate is missing or mismatched")
        return self.extractor.parse_html(candidate.html.decode("utf-8"), candidate.paper_id)
