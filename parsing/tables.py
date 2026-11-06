"""LaTeXML/ar5iv semantic parsing components, preserving historical extractor API."""
from typing import Optional, List
from bs4 import Tag, BeautifulSoup
from models import Table
from utils import clean_text
import re

class TablesMixin:
    def _parse_table(self, table: Tag) -> Optional[Table]:
        """Parse only rows of this table, excluding nested tabulars.

        Colspans are expanded into empty cells and active rowspans are
        represented by empty placeholder cells to fit Notion's rectangular
        table contract. The canonical HTML remains the source of exact layout.
        """
        wrapper = table.find_parent("figure")
        caption_elem = (
            (wrapper.select_one("figcaption, .ltx_caption") if wrapper else None)
            or table.find("caption")
        )
        caption = clean_text(caption_elem.get_text(" ", strip=True)) if caption_elem else None
        if caption:
            caption = re.sub(r"^Table\s*[\w.]+[:.]\s*", "", caption, flags=re.I)
        headers = []
        rows = []
        occupied = {}  # column index -> number of *future* rows still occupied

        for tr in table.find_all("tr"):
            if tr.find_parent("table") is not table:
                continue
            cells = tr.find_all(["td", "th"], recursive=False)
            if not cells:
                continue
            result = []
            col = 0

            def advance() -> None:
                nonlocal col
                while col in occupied:
                    result.append("")
                    occupied[col] -= 1
                    if occupied[col] <= 0:
                        del occupied[col]
                    col += 1

            for cell in cells:
                advance()
                value = clean_text(self._extract_para_with_math(cell))
                try:
                    width = max(1, min(int(cell.get("colspan", 1)), 100))
                    height = max(1, min(int(cell.get("rowspan", 1)), 100))
                except (ValueError, TypeError):
                    width = height = 1
                for offset in range(width):
                    result.append(value if offset == 0 else "")
                    if height > 1:
                        occupied[col + offset] = height - 1
                col += width
            advance()
            if tr.find_parent("thead") is not None and not headers:
                headers = result
            elif result and any(result):
                rows.append(result)

        width = max([len(headers)] + [len(row) for row in rows], default=0)
        if width:
            if headers:
                headers.extend([""] * (width - len(headers)))
            for row in rows:
                row.extend([""] * (width - len(row)))
            return Table(caption=caption, headers=headers, rows=rows,
                         label=(wrapper.get("id") if wrapper else table.get("id")))
        return None

    def _extract_tables(self, soup: BeautifulSoup) -> List[Table]:
        """提取所有表格"""
        tables = []
        
        for table in soup.select("table.ltx_tabular"):
            table_data = self._parse_table(table)
            if table_data:
                tables.append(table_data)
        
        return tables

