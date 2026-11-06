"""Regression tests for the LaTeXML/ar5iv structural HTML adapter.

All fixtures are synthetic and network-free; live ar5iv availability is not
assumed in CI. These exercise parser contracts, not pixel-perfect rendering.
"""
import asyncio

from bs4 import BeautifulSoup

from config import ArxivConfig
from fetch.ar5iv_extractor import Ar5ivExtractor, MAX_HTML_BYTES
from domain.paper_document import build_paper_document
from models import PaperData


PAPER_HTML = """
<html><head><title>Example - ar5iv</title></head><body>
<h1 class="ltx_title">Example</h1>
<div class="ltx_abstract"><div class="ltx_para"><p class="ltx_p">
A short abstract.</p></div></div>
<section class="ltx_section" id="S1">
  <h2 class="ltx_title"><span class="ltx_tag">1</span> Introduction</h2>
  <div class="ltx_theorem">
    <div class="ltx_title">Theorem 1.</div>
    <div class="ltx_para"><p class="ltx_p">A short assertion.</p></div>
  </div>
  <ul class="ltx_itemize"><li class="ltx_item">
    <div class="ltx_para"><p class="ltx_p">
    Proof with <span class="ltx_Math">
    <math alttext="x+y"><semantics><mi>x</mi></semantics></math>
    </span> inside the item.</p></div></li>
  </ul>
  <div class="ltx_equationgroup">
    <div class="ltx_equation" id="E1">
      <math alttext="x=1"><mi>x</mi></math></div>
    <div class="ltx_equation" id="E2">
      <math><semantics><mi>y</mi>
      <annotation encoding="application/x-tex">y=2</annotation>
      </semantics></math></div>
  </div>
  <figure class="ltx_figure" id="F1">
    <img src="/html/1706.03762/fig1.svg" alt="diagram"/>
    <figcaption class="ltx_caption">Figure 1: A diagram</figcaption>
  </figure>
  <figure class="ltx_table" id="T1">
    <figcaption class="ltx_caption">Table 1: Scores</figcaption>
    <table class="ltx_tabular">
      <thead><tr><th>Method</th><th>Score</th></tr></thead>
      <tbody><tr><td colspan="2">Merged</td></tr>
             <tr><td>A</td><td>0.9</td></tr></tbody>
    </table>
  </figure>
  <div class="ltx_proof"><p class="ltx_p">Closing proof.</p></div>
  <section class="ltx_subsection" id="S1.SS1">
    <h3 class="ltx_title"><span class="ltx_tag">1.1</span> Details</h3>
    <div class="ltx_para"><p class="ltx_p">Nested details.</p></div>
  </section>
</section>
<div class="ltx_bibliography">
  <ul><li class="ltx_bibitem"><span class="ltx_tag">[1]</span>
  One Author. Some work. arXiv:1706.03762 (2017).</li></ul>
</div>
</body></html>
"""


def test_nested_semantic_wrappers_are_not_dropped_or_duplicated():
    extractor = Ar5ivExtractor()
    paper = extractor.parse_html(PAPER_HTML, "1706.03762")
    assert paper is not None
    assert len(paper.sections) == 1
    section = paper.sections[0]
    assert section.title == "Introduction"
    assert section.source_anchor == "S1"
    assert [item["type"] for item in section.ordered_content] == [
        "para", "para", "equation", "equation", "figure", "table", "para"
    ]
    assert len(section.paragraphs) == 3
    assert "x+y" in section.paragraphs[1]
    assert len(section.subsections) == 1
    assert section.subsections[0].title == "Details"
    assert section.subsections[0].paragraphs == ["Nested details."]
    assert len(paper.equations) == 2  # group/member must not double-count
    assert [equation.latex for equation in paper.equations] == ["x=1", "y=2"]
    assert len(paper.figures) == 1
    assert paper.figures[0].src == "https://ar5iv.labs.arxiv.org/html/1706.03762/fig1.svg"
    assert len(paper.tables) == 1
    assert paper.tables[0].caption == "Scores"
    assert paper.tables[0].rows == [["Merged", ""], ["A", "0.9"]]
    assert len(paper.references) == 1
    assert paper.references[0].arxiv_id == "1706.03762"


def test_full_text_respects_semantic_order_and_canonical_nodes():
    paper = Ar5ivExtractor().parse_html(PAPER_HTML, "1706.03762")
    assert paper
    full = paper.full_text
    snippets = ["A short assertion.", "$x+y$", "$$x=1$$", "$$y=2$$",
                "A diagram", "Scores", "Closing proof.", "Details", "Nested details."]
    starts = [full.index(item) for item in snippets]
    assert starts == sorted(starts)
    canonical = build_paper_document(PaperData(arxiv_id=paper.paper_id, content=paper))
    kinds = [node.kind for node in canonical.nodes]
    assert kinds.count("equation") == 2
    assert kinds.count("figure") == 1
    assert kinds.count("table") == 1
    assert kinds.count("paragraph") == 4


def test_title_extraction_does_not_mutate_dom():
    soup = BeautifulSoup(PAPER_HTML, "lxml")
    section = soup.select_one("section.ltx_section")
    heading = section.select_one("h2")
    assert "1" in heading.get_text()
    result = Ar5ivExtractor()._parse_section(section)
    assert result.title == "Introduction"
    assert "1" in heading.get_text()


def test_invalid_external_media_url_is_not_passed_to_notion():
    html = PAPER_HTML.replace("/html/1706.03762/fig1.svg", "javascript:alert(1)")
    paper = Ar5ivExtractor().parse_html(html, "1706.03762")
    assert paper
    assert paper.figures[0].src == ""
    assert paper.sections[0].figures[0].src == ""
    assert next(item for item in paper.sections[0].ordered_content
                if item["type"] == "figure")["data"]["src"] == ""


def test_unrenderable_math_preserves_mathml_instead_of_fabricating_latex():
    html = PAPER_HTML.replace('alttext="x=1"', "")
    paper = Ar5ivExtractor().parse_html(html, "1706.03762")
    assert paper
    assert paper.equations[0].latex == ""
    assert "<math" in paper.equations[0].mathml


def test_nested_tables_do_not_inflate_outer_row_count():
    markup = """
    <table class="ltx_tabular">
      <tr><td>Outer</td><td><table class="ltx_tabular">
        <tr><td>Inner</td></tr></table></td></tr>
    </table>
    """
    root = BeautifulSoup(markup, "lxml").select_one("table")
    parsed = Ar5ivExtractor()._parse_table(root)
    assert parsed is not None
    assert len(parsed.rows) == 1


class FakeBody:
    def __init__(self, parts):
        self.parts = parts

    async def iter_chunked(self, size):
        for part in self.parts:
            yield part


class FakeResponse:
    def __init__(self, status=200, parts=(b"<html>ok</html>",), headers=None,
                 content_length=None):
        self.status = status
        self.content = FakeBody(parts)
        self.headers = headers or {"Content-Type": "text/html"}
        self.content_length = content_length

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_retry_503_then_success_without_recursion(monkeypatch):
    delays = []

    async def no_wait(seconds):
        delays.append(seconds)

    monkeypatch.setattr("fetch.ar5iv_extractor.asyncio.sleep", no_wait)
    session = FakeSession([FakeResponse(status=503), FakeResponse()])
    extractor = Ar5ivExtractor(config=ArxivConfig(max_retries=1, timeout=12))
    result = asyncio.run(extractor._fetch_page(session, "https://ar5iv.labs.arxiv.org/html/1706.03762"))
    assert result == "<html>ok</html>"
    assert delays == [3]
    assert len(session.calls) == 2
    assert session.calls[0][1]["timeout"].total == 12
    assert session.calls[0][1]["allow_redirects"] is False


def test_retry_after_above_budget_defers_without_sleep(monkeypatch):
    async def must_not_sleep(_):
        raise AssertionError("Should defer instead of violating upstream Retry-After")

    monkeypatch.setattr("fetch.ar5iv_extractor.asyncio.sleep", must_not_sleep)
    session = FakeSession([FakeResponse(status=429, headers={"Retry-After": "120"})])
    extractor = Ar5ivExtractor(config=ArxivConfig(max_retries=3))
    assert asyncio.run(extractor._fetch_page(session, "https://example.org")) is None
    assert len(session.calls) == 1


def test_bad_content_type_and_oversize_response_rejected():
    extractor = Ar5ivExtractor(config=ArxivConfig(max_retries=0))
    bad_type = FakeSession([FakeResponse(headers={"Content-Type": "application/pdf"})])
    assert asyncio.run(extractor._fetch_page(bad_type, "https://example.org")) is None
    too_big = FakeSession([FakeResponse(content_length=MAX_HTML_BYTES + 1)])
    assert asyncio.run(extractor._fetch_page(too_big, "https://example.org")) is None
    chunked = FakeSession([FakeResponse(parts=[b"x" * (MAX_HTML_BYTES + 1)])])
    assert asyncio.run(extractor._fetch_page(chunked, "https://example.org")) is None


def test_invalid_paper_id_fails_before_network_and_cache(tmp_path):
    from config import CacheConfig
    extractor = Ar5ivExtractor(cache_config=CacheConfig(cache_dir=tmp_path),
                               config=ArxivConfig(request_delay=0))
    assert asyncio.run(extractor.extract_paper("../../../../private")) is None
    assert extractor.failure_count == 1


def test_multi_panel_figures_keep_both_images_and_one_caption():
    html = """
    <section class="ltx_section"><h2 class="ltx_title">Panels</h2>
      <figure class="ltx_figure" id="F2">
        <div class="ltx_flex_figure">
          <img src="/html/1706.03762/left.svg" alt="left"/>
          <img src="/html/1706.03762/right.svg" alt="right"/>
        </div>
        <figcaption class="ltx_caption">Figure 2: Two panels</figcaption>
      </figure>
      <p class="ltx_p">After panels.</p>
    </section>
    """
    paper = Ar5ivExtractor().parse_html(html, "1706.03762")
    assert paper
    assert len(paper.figures) == 2
    assert [x.label for x in paper.figures] == ["F2", "F2:panel2"]
    assert [x.caption for x in paper.figures] == ["Two panels", None]
    assert paper.figures[1].src.endswith("/html/1706.03762/right.svg")
    assert [x["type"] for x in paper.sections[0].ordered_content] == [
        "figure", "figure", "para"
    ]


def test_private_network_media_hosts_do_not_escape():
    markup = PAPER_HTML.replace(
        "/html/1706.03762/fig1.svg", "https://127.0.0.1/private.png"
    )
    paper = Ar5ivExtractor().parse_html(markup, "1706.03762")
    assert paper and paper.figures[0].src == ""


def test_legacy_cache_triggers_fresh_parse_and_versioned_write(tmp_path, monkeypatch):
    from config import CacheConfig
    extractor = Ar5ivExtractor(config=ArxivConfig(request_delay=0),
                               cache_config=CacheConfig(cache_dir=tmp_path))
    calls = []

    async def stale_load(path):
        return {"paper_id": "1706.03762", "title": "old",
                "abstract": "old abstract",
                "sections": [{"title": "Old", "paragraphs": ["stale body"]}]}

    async def record_save(value, path):
        calls.append(("save", value, path))

    async def fake_fetch(session, url, retry_count=0):
        calls.append(("fetch", url))
        return PAPER_HTML

    monkeypatch.setattr("fetch.ar5iv_extractor.load_json", stale_load)
    monkeypatch.setattr("fetch.ar5iv_extractor.save_json", record_save)
    monkeypatch.setattr(extractor, "_fetch_page", fake_fetch)

    content = asyncio.run(extractor.extract_paper("1706.03762"))
    assert content and content.sections[0].title == "Introduction"
    assert [event[0] for event in calls] == ["fetch", "save"]
    assert calls[1][1]["_extractor_version"] == 2
