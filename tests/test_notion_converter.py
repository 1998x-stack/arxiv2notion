"""Tests for NotionConverter Academic Premium layout."""
from datetime import datetime
from typing import List, Dict

import pytest


def block_types(blocks: List[Dict]) -> List[str]:
    return [b["type"] for b in blocks]


def find_blocks(blocks: List[Dict], block_type: str) -> List[Dict]:
    return [b for b in blocks if b["type"] == block_type]


@pytest.fixture
def sample_paper():
    from models import PaperData, ArxivMetadata, Ar5ivContent, Section, Author, Reference
    meta = ArxivMetadata(
        arxiv_id="1706.03762",
        title="Attention Is All You Need",
        authors=[Author(name="Vaswani, A."), Author(name="Shazeer, N.")],
        abstract="The dominant sequence transduction models rely on RNNs.",
        categories=["cs.CL", "cs.LG"],
        primary_category="cs.CL",
        published=datetime(2017, 6, 12),
        updated=datetime(2017, 12, 6),
    )
    content = Ar5ivContent(
        paper_id="1706.03762",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani"],
        abstract="The dominant sequence transduction models rely on RNNs.",
        sections=[
            Section(
                title="Introduction",
                level=2,
                paragraphs=["This is a paragraph about attention mechanisms."],
                subsections=[],
            ),
        ],
        references=[
            Reference(
                raw_text="Vaswani et al. (2017). Attention. arXiv:1234.5678",
                arxiv_id="1234.5678",
                citation_key="1",
                title="Attention",
                year="2017",
            ),
            Reference(
                raw_text="LeCun et al. (1989). Deep learning.",
                citation_key="2",
            ),
        ],
    )
    return PaperData(arxiv_id="1706.03762", metadata=meta, content=content)


@pytest.fixture
def sample_annotations():
    from models import ParagraphAnnotation
    return [
        ParagraphAnnotation(
            section_title="Introduction",
            para_idx=0,
            para_text="This is a paragraph about attention mechanisms.",
            plain_explanation="这段话介绍了注意力机制的基本概念。",
            key_points=["注意力机制是核心", "替代了RNN结构"],
        ),
    ]


class TestAcademicPremiumHeader:
    def test_header_contains_blue_callout(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        callouts = find_blocks(blocks, "callout")
        assert len(callouts) >= 1
        assert callouts[0]["callout"]["color"] == "blue_background"

    def test_header_callout_contains_published_and_authors(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        callout_text = blocks[0]["callout"]["rich_text"][0]["text"]["content"]
        assert "2017-06-12" in callout_text
        assert "Vaswani" in callout_text

    def test_header_contains_links_paragraph(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        paras = find_blocks(blocks, "paragraph")
        assert len(paras) >= 1


class TestAbstractAndTLDR:
    def test_abstract_uses_quote_block(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_abstract(sample_paper, tldr=None)
        quotes = find_blocks(blocks, "quote")
        assert len(quotes) == 1

    def test_tldr_callout_shown_when_provided(self, sample_paper):
        from notion.converter import NotionConverter
        from models import ParagraphAnnotation
        conv = NotionConverter()
        tldr = ParagraphAnnotation(
            section_title="__abstract__",
            para_idx=-1,
            para_text="...",
            plain_explanation="一句话总结：这篇论文提出了Transformer。",
            key_points=[],
        )
        blocks = conv._create_abstract(sample_paper, tldr=tldr)
        callouts = find_blocks(blocks, "callout")
        green_callouts = [c for c in callouts if c["callout"]["color"] == "green_background"]
        assert len(green_callouts) == 1
        text = green_callouts[0]["callout"]["rich_text"][0]["text"]["content"]
        assert "Transformer" in text


class TestSectionsWithAnnotations:
    def test_paragraph_followed_by_toggle(self, sample_paper, sample_annotations):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=sample_annotations)
        types = block_types(blocks)
        assert "paragraph" in types
        assert "toggle" in types
        para_idx = types.index("paragraph")
        toggle_idx = types.index("toggle")
        assert toggle_idx == para_idx + 1

    def test_toggle_label_is_ai_reading_notes(self, sample_paper, sample_annotations):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=sample_annotations)
        toggles = find_blocks(blocks, "toggle")
        toggle_texts = [b["toggle"]["rich_text"][0]["text"]["content"] for b in toggles]
        assert any("AI 阅读笔记" in t for t in toggle_texts)

    def test_no_toggle_when_no_annotations(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=[])
        assert "toggle" not in block_types(blocks)


class TestReferenceFormatting:
    def test_arxiv_refs_formatted_with_link(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_references_section(sample_paper.content.references)
        paras_with_link = []
        for b in blocks:
            if b["type"] == "paragraph":
                for rt in b["paragraph"]["rich_text"]:
                    if rt.get("text", {}).get("link"):
                        paras_with_link.append(b)
                        break
        assert len(paras_with_link) >= 1

    def test_non_arxiv_refs_in_toggle(self, sample_paper):
        from notion.converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_references_section(sample_paper.content.references)
        toggles = find_blocks(blocks, "toggle")
        assert any("其他参考文献" in b["toggle"]["rich_text"][0]["text"]["content"] for b in toggles)


class TestMathRendering:
    def test_inline_math_becomes_equation_rich_text(self):
        from notion.converter import _para_to_notion_blocks, NotionBlockBuilder
        builder = NotionBlockBuilder()
        blocks = _para_to_notion_blocks(
            "The loss is $L = -\\log p(y|x)$ for each sample.",
            builder,
        )
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"
        rt = blocks[0]["paragraph"]["rich_text"]
        eq_parts = [r for r in rt if r["type"] == "equation"]
        assert len(eq_parts) == 1
        assert eq_parts[0]["equation"]["expression"] == "L = -\\log p(y|x)"

    def test_display_math_becomes_equation_block(self):
        from notion.converter import _para_to_notion_blocks, NotionBlockBuilder
        builder = NotionBlockBuilder()
        blocks = _para_to_notion_blocks(
            "We minimise: $$E = mc^2$$ where $m$ is mass.",
            builder,
        )
        types = [b["type"] for b in blocks]
        assert "equation" in types
        eq_blocks = [b for b in blocks if b["type"] == "equation"]
        assert eq_blocks[0]["equation"]["expression"] == "E = mc^2"

    def test_clean_latex_strips_label_and_tag(self):
        from notion.converter import _clean_latex
        raw = r"E = mc^2 \label{eq:energy} \tag{1}"
        cleaned = _clean_latex(raw)
        assert r"\label" not in cleaned
        assert r"\tag" not in cleaned
        assert "E = mc^2" in cleaned

    def test_clean_latex_replaces_bm_with_boldsymbol(self):
        from notion.converter import _clean_latex
        raw = r"\bm{x} = \bm{A}\bm{b}"
        cleaned = _clean_latex(raw)
        assert r"\boldsymbol{" in cleaned
        assert r"\bm{" not in cleaned

    def test_plain_paragraph_unchanged(self):
        from notion.converter import _para_to_notion_blocks, NotionBlockBuilder
        builder = NotionBlockBuilder()
        blocks = _para_to_notion_blocks("No math here, just plain text.", builder)
        assert len(blocks) == 1
        assert blocks[0]["type"] == "paragraph"
        rt = blocks[0]["paragraph"]["rich_text"]
        assert all(r["type"] == "text" for r in rt)

    def test_extract_para_with_math_inline(self):
        """ar5iv extractor preserves inline math as $...$."""
        from bs4 import BeautifulSoup
        from fetch.ar5iv_extractor import Ar5ivExtractor
        html = '<p class="ltx_p">The value <math display="inline" alttext="x=1">x=1</math> holds.</p>'
        soup = BeautifulSoup(html, "lxml")
        para = soup.select_one("p.ltx_p")
        extractor = Ar5ivExtractor()
        text = extractor._extract_para_with_math(para)
        assert "$x=1$" in text
        assert "The value" in text
        assert "holds." in text

    def test_extract_para_with_math_display(self):
        """ar5iv extractor preserves display math as $$...$$."""
        from bs4 import BeautifulSoup
        from fetch.ar5iv_extractor import Ar5ivExtractor
        html = '<p class="ltx_p">Equation <math display="block" alttext="E=mc^2">E=mc^2</math> proved.</p>'
        soup = BeautifulSoup(html, "lxml")
        para = soup.select_one("p.ltx_p")
        extractor = Ar5ivExtractor()
        text = extractor._extract_para_with_math(para)
        assert "$$E=mc^2$$" in text

    def test_extract_para_ltx_math_span_no_artifact_text(self):
        """
        The <span class="ltx_Math"> wrapper pattern used by ar5iv must NOT leak
        the visual/ARIA rendering text (e.g. 'dmodel512subscript') into the output.
        Only the clean $alttext$ marker should appear.
        """
        from bs4 import BeautifulSoup
        from fetch.ar5iv_extractor import Ar5ivExtractor
        # Simulates ar5iv HTML: span wrapper contains both artifact text AND <math>
        html = (
            '<p class="ltx_p">The dimensionality is '
            '<span class="ltx_Math">'
            'dmodel512'                            # ← artifact text (should be dropped)
            '<math display="inline" alttext="d_{\\text{model}}=512">'
            '<semantics><mrow><msub><mi>d</mi><mtext>model</mtext></msub>'
            '<mo>=</mo><mn>512</mn></mrow>'
            '<annotation encoding="application/x-tex">d_{\\text{model}}=512</annotation>'
            '</semantics></math>'
            '</span>'
            ', and the inner-layer has dimensionality '
            '<span class="ltx_Math">dff2048'
            '<math display="inline" alttext="d_{ff}=2048"></math>'
            '</span>.'
            '</p>'
        )
        soup = BeautifulSoup(html, "lxml")
        para = soup.select_one("p.ltx_p")
        extractor = Ar5ivExtractor()
        text = extractor._extract_para_with_math(para)

        # Must contain the correct LaTeX markers
        assert "$d_{\\text{model}}=512$" in text
        assert "$d_{ff}=2048$" in text
        # Must NOT contain the garbled artifact text
        assert "dmodel512" not in text
        assert "dff2048" not in text
        assert "subscript" not in text.lower()

    def test_math_to_marker_uses_annotation_fallback(self):
        """_math_to_marker falls back to <annotation> when alttext is absent."""
        from bs4 import BeautifulSoup
        from fetch.ar5iv_extractor import Ar5ivExtractor
        html = (
            '<math display="inline">'
            '<semantics><mrow><mi>x</mi></mrow>'
            '<annotation encoding="application/x-tex">x^2</annotation>'
            '</semantics></math>'
        )
        soup = BeautifulSoup(html, "lxml")
        math_node = soup.find("math")
        extractor = Ar5ivExtractor()
        marker = extractor._math_to_marker(math_node)
        assert marker == "$x^2$"
