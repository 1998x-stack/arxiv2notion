"""Tests for NotionConverter Academic Premium layout."""
from datetime import datetime
from typing import List, Dict, Any

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
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        callouts = find_blocks(blocks, "callout")
        assert len(callouts) >= 1
        assert callouts[0]["callout"]["color"] == "blue_background"

    def test_header_callout_contains_published_and_authors(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        callout_text = blocks[0]["callout"]["rich_text"][0]["text"]["content"]
        assert "2017-06-12" in callout_text
        assert "Vaswani" in callout_text

    def test_header_contains_links_paragraph(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_header(sample_paper)
        paras = find_blocks(blocks, "paragraph")
        assert len(paras) >= 1


class TestAbstractAndTLDR:
    def test_abstract_uses_quote_block(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_abstract(sample_paper, tldr=None)
        quotes = find_blocks(blocks, "quote")
        assert len(quotes) == 1

    def test_tldr_callout_shown_when_provided(self, sample_paper):
        from notion_converter import NotionConverter
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
        from notion_converter import NotionConverter
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
        from notion_converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=sample_annotations)
        toggles = find_blocks(blocks, "toggle")
        toggle_texts = [b["toggle"]["rich_text"][0]["text"]["content"] for b in toggles]
        assert any("AI 阅读笔记" in t for t in toggle_texts)

    def test_no_toggle_when_no_annotations(self, sample_paper):
        from notion_converter import NotionConverter
        conv = NotionConverter()
        section = sample_paper.content.sections[0]
        blocks = conv._convert_section(section, annotations=[])
        assert "toggle" not in block_types(blocks)


class TestReferenceFormatting:
    def test_arxiv_refs_formatted_with_link(self, sample_paper):
        from notion_converter import NotionConverter
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
        from notion_converter import NotionConverter
        conv = NotionConverter()
        blocks = conv._create_references_section(sample_paper.content.references)
        toggles = find_blocks(blocks, "toggle")
        assert any("其他参考文献" in b["toggle"]["rich_text"][0]["text"]["content"] for b in toggles)
