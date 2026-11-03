"""M01 golden regression tests: document identity, parsing, cache, rendering.

Everything in this module is offline and deterministic.
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from bs4 import BeautifulSoup

from config import ArxivConfig, CacheConfig, QwenConfig
from domain.paper_document import (
    assess_quality, build_paper_document, iter_paragraph_refs,
)
from fetch.ar5iv_extractor import Ar5ivExtractor
from models import Ar5ivContent, Equation, PaperData, ParagraphAnnotation, Section
from notion.converter import NotionConverter
from process.qwen_annotator import QwenAnnotator
from storage.file_manager import FileManager


def _content(paragraphs, title="Title", section_title="Methods", abstract="Abstract text"):
    return Ar5ivContent(
        paper_id="1706.03762", title=title, abstract=abstract,
        sections=[Section(title=section_title, level=2, paragraphs=paragraphs)],
    )


def test_canonical_document_stable_ids_across_serialization_and_reimport():
    paper = PaperData(arxiv_id="1706.03762v2", content=_content(["First paragraph", "Second paragraph"]))
    first = build_paper_document(paper)
    second = build_paper_document(paper)
    assert first.content_hash == second.content_hash
    assert [n.node_id for n in first.nodes] == [n.node_id for n in second.nodes]
    assert first.base_arxiv_id == "1706.03762"
    assert first.revision == 2
    assert first.to_dict()["schema_version"] == "1.0"


def test_adding_unrelated_paragraph_does_not_change_existing_node_ids():
    original = list(iter_paragraph_refs(_content(["One", "Two"])))
    inserted = list(iter_paragraph_refs(_content(["New", "One", "Two"])))
    assert [x.node_id for x in original] == [x.node_id for x in inserted[1:]]


def test_same_named_sibling_sections_get_distinct_node_ids():
    content = Ar5ivContent(
        paper_id="1706.03762", title="Paper", abstract="Abstract",
        sections=[
            Section(title="Methods", level=2, paragraphs=["method A"]),
            Section(title="Methods", level=2, paragraphs=["method B"]),
        ],
    )
    refs = list(iter_paragraph_refs(content))
    assert len(refs) == 2
    assert refs[0].node_id != refs[1].node_id
    assert len({n.node_id for n in build_paper_document(
        PaperData(arxiv_id="1706.03762", content=content)
    ).nodes}) == 5  # abstract, two headings, two paragraphs


def test_content_hash_changes_with_text_not_extract_timestamp():
    content = _content(["Old body"])
    first = build_paper_document(PaperData(arxiv_id="1706.03762", content=content))
    content.full_text = "ignored legacy renderer text"
    assert build_paper_document(PaperData(
        arxiv_id="1706.03762", content=content
    )).content_hash == first.content_hash
    content.sections[0].paragraphs = ["Updated body"]
    assert build_paper_document(PaperData(
        arxiv_id="1706.03762", content=content
    )).content_hash != first.content_hash


def test_empty_and_abstract_only_quality_gate():
    blank = Ar5ivContent(paper_id="1706.03762", title="Title only")
    quality = assess_quality(blank)
    assert quality.status == "unavailable"
    assert not quality.cacheable_full_text
    abstract_only = Ar5ivContent(
        paper_id="1706.03762", title="Paper", abstract="Abstract"
    )
    quality = assess_quality(abstract_only)
    assert quality.status == "partial"
    assert not quality.cacheable_full_text
    good = assess_quality(_content(["Body paragraph"]))
    assert good.status == "full"
    assert good.cacheable_full_text


def test_empty_html_is_not_accepted_as_full_text():
    extractor = Ar5ivExtractor(config=ArxivConfig(request_delay=0))
    assert extractor.parse_html(
        "<html><head><title>Paper title</title></head><body>Nothing</body></html>",
        "1706.03762",
    ) is None


def test_nested_sections_are_not_flattened_or_duplicated():
    html = """
    <section class="ltx_section" id="S1">
      <h2 class="ltx_title">Root</h2>
      <div class="ltx_para"><p class="ltx_p">Root paragraph with content.</p></div>
      <section class="ltx_subsection" id="S1.SS1">
        <h3 class="ltx_title">Child</h3>
        <div class="ltx_para"><p class="ltx_p">Child paragraph with content.</p></div>
        <section class="ltx_subsubsection" id="S1.SS1.SSS1">
          <h4 class="ltx_title">Grandchild</h4>
          <div class="ltx_para"><p class="ltx_p">Grandchild paragraph with content.</p></div>
        </section>
      </section>
    </section>
    """
    extractor = Ar5ivExtractor()
    parent = BeautifulSoup(html, "lxml").select_one("section.ltx_section")
    section = extractor._parse_section(parent)
    assert section.source_anchor == "S1"
    assert len(section.subsections) == 1
    assert section.subsections[0].title == "Child"
    assert len(section.subsections[0].subsections) == 1
    assert section.subsections[0].subsections[0].title == "Grandchild"


def test_equation_preserves_mathml_and_uses_annotation_fallback():
    html = (
        '<div class="ltx_equation"><math><semantics>'
        '<mrow><mi>x</mi></mrow>'
        '<annotation encoding="application/x-tex">x^2+y^2</annotation>'
        '</semantics></math></div>'
    )
    extractor = Ar5ivExtractor()
    node = BeautifulSoup(html, "lxml").select_one("div")
    result = extractor._parse_equation(node)
    assert result.latex == "x^2+y^2"
    assert "<math>" in result.mathml
    assert "mathml" in result.to_dict()
    assert Equation(**result.to_dict()).mathml == result.mathml


def test_table_caption_does_not_use_previous_figures_caption():
    html = (
        '<figure><figcaption>Table 1: Wrong</figcaption>'
        '<table class="ltx_tabular"><tr><td>1</td></tr></table></figure>'
        '<figure><figcaption>Table 2: Correct</figcaption>'
        '<table class="ltx_tabular"><tr><td>2</td></tr></table></figure>'
    )
    soup = BeautifulSoup(html, "lxml")
    table = Ar5ivExtractor()._parse_table(soup.select("table")[1])
    assert table.caption == "Correct"


def test_render_does_not_truncate_table_rows():
    section = Section(
        title="Results", level=2,
        ordered_content=[{"type": "table", "data": {
            "headers": ["score"],
            "rows": [[str(x)] for x in range(25)],
        }}],
    )
    blocks = NotionConverter()._convert_section(section, [])
    table = next(x for x in blocks if x["type"] == "table")
    assert len(table["table"]["children"]) == 26


def test_render_limit_fails_loudly_not_silently():
    from notion.blocks import NotionBlockBuilder
    with pytest.raises(ValueError, match="2000"):
        NotionBlockBuilder.rich_text("x" * 2001)
    with pytest.raises(ValueError, match="Section limit"):
        NotionConverter(max_sections=1)._convert_sections([
            Section(title="One", level=2), Section(title="Two", level=2),
        ], [])


def test_annotations_on_duplicate_titles_are_linked_by_node_id():
    content = Ar5ivContent(
        paper_id="1706.03762", title="Paper", abstract="Abstract",
        sections=[
            Section(title="Methods", level=2, paragraphs=["First paragraph"]),
            Section(title="Methods", level=2, paragraphs=["Second paragraph"]),
        ],
    )
    refs = list(iter_paragraph_refs(content))
    annotations = [
        ParagraphAnnotation("Methods", 0, "First", "Explanation A", [],
                            node_id=refs[0].node_id),
        ParagraphAnnotation("Methods", 0, "Second", "Explanation B", [],
                            node_id=refs[1].node_id),
    ]
    blocks = NotionConverter().convert_paper(
        PaperData(arxiv_id="1706.03762", content=content),
        annotations=annotations,
    )
    toggles = [b for b in blocks if b["type"] == "toggle"
               and b["toggle"]["rich_text"][0]["text"]["content"] == "🤖 AI 阅读笔记"]
    assert len(toggles) == 2
    assert "Explanation A" in json.dumps(toggles[0], ensure_ascii=False)
    assert "Explanation B" in json.dumps(toggles[1], ensure_ascii=False)


def test_canonical_artifact_is_written(tmp_path):
    content = _content(["Paragraph"])
    doc = build_paper_document(PaperData(arxiv_id="1706.03762", content=content))
    fm = FileManager(base_dir=tmp_path)
    fm.save_document("1706.03762", "deep_learning", doc)
    saved = json.loads((tmp_path / "papers" / "deep_learning" /
                        "1706.03762" / "document.json").read_text())
    assert saved["content_hash"] == doc.content_hash
    assert saved["nodes"]


def test_annotation_cache_rejects_legacy_and_corrupt_data(tmp_path):
    fm = FileManager(base_dir=tmp_path)
    config = QwenConfig(api_key="fake", min_para_length=1)
    annotator = QwenAnnotator(config=config, file_manager=fm)
    content = _content(["A paragraph longer than the threshold"])
    fingerprint = annotator.cache_fingerprint(content, "1706.03762")
    ann = ParagraphAnnotation("Methods", 0, "A", "test", [])
    fm.save_annotations("1706.03762", "other", [ann])
    assert not fm.has_annotations("1706.03762", "other", fingerprint)
    fm.save_annotations("1706.03762", "other", [ann], fingerprint=fingerprint)
    assert fm.has_annotations("1706.03762", "other", fingerprint)
    (tmp_path / "papers" / "other" / "1706.03762" /
     "llm_annotations.jsonl").write_text("CORRUPTED")
    assert not fm.has_annotations("1706.03762", "other", fingerprint)


def test_annotation_cache_fingerprint_invalidation(tmp_path, monkeypatch):
    import process.qwen_annotator as mod
    fm = FileManager(base_dir=tmp_path)
    cfg = QwenConfig(api_key="fake")
    annotator = QwenAnnotator(cfg, fm)
    original = _content(["Body 1"])
    token = annotator.cache_fingerprint(original)
    assert token != annotator.cache_fingerprint(_content(["Body 2"]))
    cfg.model = "different-model"
    assert token != annotator.cache_fingerprint(original)
    cfg.model = "qwen-plus"
    monkeypatch.setattr(mod, "USER_TEMPLATE", mod.USER_TEMPLATE + "\nV2")
    assert token != annotator.cache_fingerprint(original)


@pytest.mark.asyncio
async def test_annotation_success_writes_versioned_manifest(tmp_path):
    fm = FileManager(base_dir=tmp_path)
    cfg = QwenConfig(api_key="fake", min_para_length=1)
    annotator = QwenAnnotator(cfg, fm)
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="通俗解读：Test"))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4),
    )
    annotator._call_api = AsyncMock(return_value=response)
    content = _content(["Text long enough to annotate"])
    result = await annotator.annotate_paper(content, "1706.03762", "other")
    assert len(result) == 2  # abstract + one paragraph
    assert all(a.node_id for a in result)
    assert fm.has_annotations(
        "1706.03762", "other", annotator.cache_fingerprint(content, "1706.03762")
    )
    second = await annotator.annotate_paper(content, "1706.03762", "other")
    assert all(a.cached for a in second)
    assert annotator._call_api.await_count == 2


@pytest.mark.asyncio
async def test_failed_annotation_does_not_poison_cache(tmp_path):
    fm = FileManager(base_dir=tmp_path)
    cfg = QwenConfig(api_key="fake", min_para_length=1)
    annotator = QwenAnnotator(cfg, fm)
    annotator._call_api = AsyncMock(side_effect=RuntimeError("fake API failure"))
    content = _content(["Text to annotate"])
    result = await annotator.annotate_paper(content, "1706.03762", "other")
    assert any(a.plain_explanation == "（注释生成失败）" for a in result)
    assert not fm.has_annotations(
        "1706.03762", "other", annotator.cache_fingerprint(content, "1706.03762")
    )


def test_long_rich_text_blocks_are_lossless():
    from notion.blocks import NotionBlockBuilder as Builder
    text = "English " + ("数" * 4105) + " last"
    for rendered, key in (
        (Builder.quote(text), "quote"),
        (Builder.callout(text), "callout"),
        (Builder.paragraph(text), "paragraph"),
    ):
        parts = rendered[key]["rich_text"]
        assert "".join(x["text"]["content"] for x in parts) == text
        assert all(len(x["text"]["content"]) <= 2000 for x in parts)
    table = Builder.table(["column"], [[text]])
    cell = table["table"]["children"][1]["table_row"]["cells"][0]
    assert "".join(x["text"]["content"] for x in cell) == text


def test_paragraph_chunker_does_not_lose_spaces():
    from notion.blocks import NotionBlockBuilder, _text_to_rich_texts
    source = "  " + ("a" * 2030) + "   " + ("b" * 2050) + "   "
    rich_text = _text_to_rich_texts(source, NotionBlockBuilder, 2000)
    assert "".join(x["text"]["content"] for x in rich_text) == source


def test_rendering_unrenderable_equation_fails_explicitly():
    section = Section(
        title="Proof", level=2,
        ordered_content=[{"type": "equation", "data": {
            "latex": "", "mathml": "<math><mi>x</mi></math>"
        }}],
    )
    with pytest.raises(ValueError, match="LaTeX"):
        NotionConverter()._convert_section(section, [])


def test_validator_rejects_too_many_rich_text_elements():
    from notion.validator import NotionPayloadError, validate_notion_blocks
    block = {
        "type": "paragraph",
        "paragraph": {"rich_text": [
            {"type": "text", "text": {"content": "small"}}
            for _ in range(101)
        ]},
    }
    with pytest.raises(NotionPayloadError, match="100 elements"):
        validate_notion_blocks([block])


def test_markdown_keeps_formula_table_figure_and_references_in_order(tmp_path):
    from models import Reference
    section = Section(
        title="Results", level=2,
        ordered_content=[
            {"type": "para", "data": "Before formula"},
            {"type": "equation", "data": {"latex": r"E=mc^2", "mathml": "<math/>"}},
            {"type": "figure", "data": {"src": "https://example.org/img.png",
                                       "alt": "plot", "caption": "Result plot"}},
            {"type": "table", "data": {"headers": ["Method", "Score"],
                                       "rows": [["A", "0.5"], ["B", "0.9"]]}},
            {"type": "para", "data": "After table"},
        ],
    )
    content = Ar5ivContent(
        paper_id="1706.03762", title="Paper", sections=[section],
        references=[Reference(raw_text="A. Author, Title (2024)")],
    )
    fm = FileManager(base_dir=tmp_path)
    fm.save_content_md("1706.03762", "other", content)
    markdown = (tmp_path / "papers" / "other" /
                "1706.03762" / "content.md").read_text()
    tokens = ["Before formula", "E=mc^2", "img.png", "| Method | Score |",
              "| A | 0.5 |", "After table", "A. Author, Title (2024)"]
    offsets = [markdown.index(t) for t in tokens]
    assert offsets == sorted(offsets)


def test_markdown_keeps_equation_mathml_fallback(tmp_path):
    section = Section(
        title="Proof", level=2,
        ordered_content=[{"type": "equation", "data": {
            "latex": "", "mathml": "<math><mi>x</mi></math>"
        }}],
    )
    fm = FileManager(base_dir=tmp_path)
    fm.save_content_md(
        "1706.03762", "other",
        Ar5ivContent(paper_id="1706.03762", title="Proof", sections=[section]),
    )
    text = (tmp_path / "papers" / "other" /
            "1706.03762" / "content.md").read_text()
    assert "<math><mi>x</mi></math>" in text


def test_appendix_sections_are_preserved():
    html = (
        '<section class="ltx_section" id="S1">'
        '<h2 class="ltx_title">Main</h2>'
        '<div class="ltx_para"><p class="ltx_p">Main content paragraph.</p></div>'
        '</section>'
        '<section class="ltx_appendix" id="A1">'
        '<h2 class="ltx_title">Appendix A: Details</h2>'
        '<div class="ltx_para"><p class="ltx_p">Proof details are preserved.</p></div>'
        '</section>'
    )
    soup = BeautifulSoup(html, "lxml")
    sections = Ar5ivExtractor()._extract_sections(soup)
    assert [x.title for x in sections] == ["Main", "Appendix A: Details"]
    assert sections[1].source_anchor == "A1"
    assert "Proof details" in sections[1].paragraphs[0]


def test_table_header_not_duplicated_and_row_headings_preserved():
    html = (
        '<table class="ltx_tabular">'
        '<thead><tr><th>Method</th><th>Score</th></tr></thead>'
        '<tbody><tr><th>Baseline</th><td>0.9</td></tr></tbody>'
        '</table>'
    )
    element = BeautifulSoup(html, "lxml").select_one("table")
    table = Ar5ivExtractor()._parse_table(element)
    assert table.headers == ["Method", "Score"]
    assert table.rows == [["Baseline", "0.9"]]
