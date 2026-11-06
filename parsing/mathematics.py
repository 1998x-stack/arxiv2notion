"""LaTeXML/ar5iv semantic parsing components, preserving historical extractor API."""
from __future__ import annotations
import re
from typing import List
from bs4 import Tag
from models import Equation

class MathematicsMixin:
    def _math_to_marker(self, math_node: Tag) -> str:
        """
        Convert a <math> element to a $...$ or $$...$$ LaTeX marker.

        Priority:
          1. alttext attribute  — LaTeXML always sets this
          2. <annotation encoding="application/x-tex"> — fallback inside <semantics>
          3. Empty string       — can't render without LaTeX source
        """
        latex = (math_node.get("alttext") or "").strip()

        if not latex:
            ann = math_node.find(
                "annotation", attrs={"encoding": "application/x-tex"}
            )
            if ann:
                latex = ann.get_text().strip()

        if not latex:
            # Preserve evidence rather than silently dropping an inline
            # MathML-only formula. Notion displays the XML as text.
            return " [MathML: " + str(math_node) + "] "

        display = (math_node.get("display") or "inline").lower()
        return f" $${latex}$$ " if display == "block" else f"${latex}$"

    # CSS classes on <span> wrappers that are purely math containers —
    # we skip their non-math text children (those are visual/ARIA rendering artifacts)
    _MATH_WRAPPER_CLASSES = {"ltx_Math", "ltx_eqn_cell", "ltx_eqn_display"}
    # CSS classes on tags whose entire subtree is non-semantic (equation numbers, labels)
    _SKIP_CLASSES = {"ltx_tag", "ltx_tag_equation", "ltx_tag_ref", "ltx_rule"}

    def _extract_para_with_math(self, elem: Tag) -> str:
        """
        Extract paragraph text, preserving math as $...$ / $$...$$ markers.

        Handles the common ar5iv HTML pattern where <math> is wrapped inside
        <span class="ltx_Math">. That span may also contain visual rendering
        artifacts (plain text, aria-hidden spans) — those are skipped so that
        only the clean LaTeX marker is emitted.
        """
        from bs4 import NavigableString

        parts: List[str] = []
        for node in elem.children:
            if isinstance(node, NavigableString):
                parts.append(str(node))
                continue

            if not hasattr(node, "name") or not node.name:
                continue

            node_classes = set(node.get("class") or [])
            if node.get("aria-hidden") == "true" or node.name in ("script", "style"):
                continue

            # ── Direct <math> element ──────────────────────────────────────
            if node.name == "math":
                parts.append(self._math_to_marker(node))

            # ── <span class="ltx_Math"> (and similar wrappers) ────────────
            # These wrap a <math> but also carry visual/ARIA text nodes that
            # are rendering artifacts. Go straight to the inner <math>.
            elif node_classes & self._MATH_WRAPPER_CLASSES:
                math_node = node.find("math")
                if math_node:
                    parts.append(self._math_to_marker(math_node))
                # If no inner <math> found, skip — the wrapper has no useful text

            # ── Tags that are purely decorative (equation numbers, etc.) ──
            elif node_classes & self._SKIP_CLASSES:
                pass  # intentionally dropped

            # ── Everything else: recurse (strong, em, a, sub, sup, …) ─────
            else:
                parts.append(self._extract_para_with_math(node))

        text = "".join(parts)
        text = re.sub(r"[ \t]+", " ", text).strip()
        return text

    def _parse_equation(self, eq: Tag) -> Optional[Equation]:
        """Keep MathML even if LaTeX cannot be recovered."""
        math_elem = eq.select_one("math")
        if math_elem is None:
            return None
        latex = (math_elem.get("alttext") or "").strip()
        if not latex:
            annotation = math_elem.find("annotation", attrs={"encoding": "application/x-tex"})
            latex = annotation.get_text(strip=True) if annotation else ""
        tag = eq.select_one(".ltx_tag")
        label = clean_text(tag.get_text()) if tag else None
        return Equation(latex=latex, mathml=str(math_elem), label=label, inline=False)

    def _extract_equations(self, soup: BeautifulSoup) -> List[Equation]:
        """One equation per semantic equation node; no group/member double count."""
        equations = []
        for node in soup.select(".ltx_equation, .ltx_equationgroup"):
            if node.find_parent(class_="ltx_equation"):
                continue
            if "ltx_equationgroup" in (node.get("class") or ()) and node.select(".ltx_equation"):
                continue
            equation = self._parse_equation(node)
            if equation:
                equations.append(equation)
        return equations

