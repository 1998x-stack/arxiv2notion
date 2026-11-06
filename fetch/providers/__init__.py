"""Provider-based paper source resolution.

Remote providers are intentionally opt-in and do not alter legacy import
behavior until a caller explicitly adopts MultiSourceResolver.
"""
from fetch.providers.base import SourceCandidate, Provider
from fetch.providers.ar5iv import Ar5ivProvider
from fetch.providers.official_arxiv import OfficialArxivHTMLProvider
from fetch.providers.nano_ar5iv import NanoAr5ivProvider
from fetch.providers.resolver import MultiSourceResolver, ResolutionResult

__all__ = [
    "SourceCandidate", "Provider", "Ar5ivProvider", "OfficialArxivHTMLProvider",
    "NanoAr5ivProvider", "MultiSourceResolver", "ResolutionResult",
]
