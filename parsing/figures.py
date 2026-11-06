"""LaTeXML/ar5iv semantic parsing components, preserving historical extractor API."""
import re
from typing import List, Optional
from bs4 import Tag, BeautifulSoup
from models import Figure
from utils import clean_text

class FiguresMixin:
    def _parse_figure(self, fig: Tag) -> Optional[Figure]:
        """Extract a figure; resolve image URLs once against the paper URL."""
        img = fig.select_one("img")
        if img is None:
            return None
        caption_elem = fig.select_one("figcaption, .ltx_caption")
        caption = clean_text(caption_elem.get_text(" ", strip=True)) if caption_elem else None
        if caption:
            caption = re.sub(r"^Figure\s*[\w.]+[:.]\s*", "", caption, flags=re.I)
        return Figure(
            src=img.get("src") or img.get("data-src") or "",
            alt=img.get("alt"),
            caption=caption,
            label=fig.get("id"),
        )

    def _parse_figure_panels(self, fig: Tag) -> List[Figure]:
        """Split multi-image figures into ordered panels without losing images.

        The first panel retains the parent caption/anchor for compatibility.
        Additional panels have stable suffixes derived from the same anchor.
        """
        first = self._parse_figure(fig)
        if first is None:
            return []
        result = [first]
        for index, image in enumerate(fig.select("img")[1:], start=2):
            result.append(Figure(
                src=image.get("src") or image.get("data-src") or "",
                alt=image.get("alt"),
                caption=None,
                label=(f"{fig.get('id')}:panel{index}" if fig.get("id") else None),
            ))
        return result

    def _extract_figures(self, soup: BeautifulSoup) -> List[Figure]:
        """提取所有图片"""
        figures = []
        
        for fig in soup.select("figure.ltx_figure"):
            for figure in self._parse_figure_panels(fig):
                if figure not in figures:
                    figures.append(figure)
        
        return figures

