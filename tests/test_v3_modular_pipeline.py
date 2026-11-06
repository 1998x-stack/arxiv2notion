"""V3 modular architecture and real interface tests (offline, deterministic)."""
import asyncio
from hashlib import sha256
import json

import pytest

from adapters.legacy_to_v2 import from_legacy
from adapters.nano_to_v2 import from_nano_artifact, read_nano_artifact
from benchmarks.corpus import GoldenPaper, load_golden
from benchmarks.evaluate import evaluate_document
from benchmarks.compare import compare_metrics
from domain.nodes import ScientificNode
from domain.provenance import DocumentSource
from domain.scientific_document_v2 import ScientificDocument
from fetch.ar5iv_extractor import Ar5ivExtractor
from fetch.providers.base import SourceCandidate
from fetch.providers.resolver import MultiSourceResolver
from notion.compiler_v2 import compile_document, ScientificCompileError
from notion.media import require_external_media_url, UnsafeMediaURL
from notion.verifier import NotionReadbackVerifier
from parsing.latexhtml import Ar5ivHTMLParser
from quality.structural import evaluate

HTML = """<html><head><title>Paper - ar5iv</title></head>
<h1 class="ltx_title">Paper</h1>
<div class="ltx_abstract"><p class="ltx_p">Abstract sentence.</p></div>
<section class="ltx_section" id="S1"><h2 class="ltx_title">Introduction</h2>
<div class="ltx_para"><p class="ltx_p">A paragraph with sufficient content.</p></div>
<div class="ltx_equation"><math alttext="x=1"><mi>x</mi></math></div>
<figure class="ltx_figure"><img src="/assets/fig.png" alt="x"/>
<figcaption class="ltx_caption">Figure 1: A figure</figcaption></figure>
<table class="ltx_tabular"><tr><td>A</td><td>B</td></tr></table>
</section></html>"""


def prepared():
    content = Ar5ivHTMLParser().parse_html(HTML, "1706.03762")
    assert content is not None
    source = DocumentSource.from_bytes(
        provider="ar5iv", url="https://ar5iv.labs.arxiv.org/html/1706.03762",
        paper_id="1706.03762", content=HTML.encode(),
    )
    return content, from_legacy(content, source)


def test_extractor_moved_into_focused_parser_mixins():
    assert issubclass(Ar5ivExtractor, Ar5ivHTMLParser)
    assert "_parse_section" not in Ar5ivExtractor.__dict__
    assert "_fetch_page" not in Ar5ivHTMLParser.__dict__
    content = Ar5ivExtractor().parse_html(HTML, "1706.03762")
    assert content and content.sections[0].paragraphs


def test_v2_schema_roundtrip_and_structural_gate():
    _, document = prepared()
    assert document.schema_version == "2.0"
    assert evaluate(document).status == "ACCEPTED"
    decoded = ScientificDocument.from_dict(document.to_dict())
    assert decoded.content_hash == document.content_hash
    assert len(decoded.nodes) >= 5
    assert len(set(n.node_id for n in decoded.nodes)) == len(decoded.nodes)


def test_v2_schema_corruption_rejected():
    _, document = prepared()
    obj = document.to_dict()
    obj["nodes"][0]["text"] = "tampered"
    with pytest.raises(ValueError, match="hash"):
        ScientificDocument.from_dict(obj)


def test_v2_parent_anchors_are_resolvable():
    _, document = prepared()
    nodes = {n.node_id: n for n in document.nodes}
    for node in document.nodes:
        if node.parent_id:
            assert node.parent_id in nodes


def test_notion_compiler_preserves_ordered_semantic_content():
    _, document = prepared()
    result = compile_document(document)
    types = [block["type"] for block in result.blocks]
    assert types.index("paragraph") < types.index("equation") < types.index("image")
    assert "table" in types
    assert len(result.node_block_map) == len(document.nodes)
    assert result.source_hash == document.content_hash


def test_notion_compiler_fails_closed_for_missing_formula():
    _, document = prepared()
    replaced = [
        ScientificNode(**{**node.__dict__, "payload": {}, "text": ""})
        if node.kind == "equation" else node
        for node in document.nodes
    ]
    document.nodes = replaced
    with pytest.raises(ScientificCompileError, match="LaTeX"):
        compile_document(document)


def test_notion_compiler_fails_closed_for_unsupported_nodes():
    _, document = prepared()
    document.nodes.append(
        ScientificNode(node_id="unknown-test", kind="unknown", parent_id=None,
                       ordinal=100, text="unhandled")
    )
    with pytest.raises(ScientificCompileError, match="Unrenderable"):
        compile_document(document)


@pytest.mark.parametrize("url", [
    "http://example.org/a.png",
    "https://localhost/img.png",
    "https://192.168.0.1/img.png",
    "javascript:alert(1)",
    "https://user:pw@example.org/img.png",
])
def test_notion_media_rejects_unsafe_urls(url):
    with pytest.raises(UnsafeMediaURL):
        require_external_media_url(url)


def test_notion_verifier_requires_complete_remote_prefix():
    class FakeWriter:
        def __init__(self, count):
            self.count = count
        def _snapshot(self, page_id, expected):
            return self.count
    assert NotionReadbackVerifier(FakeWriter(3)).verify("id", [{}, {}, {}]).status == "MATCH"
    assert NotionReadbackVerifier(FakeWriter(2)).verify("id", [{}, {}, {}]).status == "INCOMPLETE"


class FakeProvider:
    def __init__(self, name, html=HTML, missing=False):
        self.name = name
        self.html = html
        self.missing = missing

    async def fetch(self, paper_id):
        return SourceCandidate(paper_id, self.name,
                               f"https://example.org/{paper_id}",
                               None if self.missing else self.html.encode(),
                               "missing" if self.missing else None)

    def parse(self, candidate):
        return Ar5ivHTMLParser().parse_html(candidate.html.decode(), candidate.paper_id)


def test_resolver_successful_fallback_and_provenance():
    resolver = MultiSourceResolver([
        FakeProvider("first", missing=True), FakeProvider("second")
    ])
    result = asyncio.run(resolver.resolve("1706.03762"))
    assert result.status == "ACCEPTED"
    assert result.document.source.provider == "second"
    assert result.document.source.sha256 == sha256(HTML.encode()).hexdigest()
    assert result.failures == ["first:missing"]


def test_resolver_does_not_auto_merge_conflicting_html():
    resolver = MultiSourceResolver([
        FakeProvider("first"), FakeProvider("second", HTML.replace(
            "A paragraph with sufficient content.", "Different valid body content."
        ))
    ])
    result = asyncio.run(resolver.resolve("1706.03762"))
    assert result.status == "REVIEW_REQUIRED"
    assert result.document is None
    assert len(result.reports) == 2


def test_resolver_unavailable_is_fallback():
    result = asyncio.run(MultiSourceResolver(
        [FakeProvider("first", missing=True)]
    ).resolve("1706.03762"))
    assert result.status == "FALLBACK" and result.document is None


def test_nano_artifact_is_lossless_in_quality_claims(tmp_path):
    record = {
        "schema_version": "1.0", "quality_status": "NOT_EVALUATED",
        "nodes": [{"id": "s1", "kind": "heading", "parent_id": None,
                   "text": "Introduction", "source_id": "S1"}],
        "equations": [{"id": "eq1", "source_tex": "x=1", "parent_id": "s1"}],
        "assets": [], "citations": [], "relations": [], "warnings": []
    }
    content = json.dumps(record).encode()
    path = tmp_path / "paper-document.json"
    path.write_bytes(content)
    result = read_nano_artifact(path, root=tmp_path, paper_id="1706.03762",
                                expected_sha256=sha256(content).hexdigest())
    assert result.status == "NOT_EVALUATED"
    assert any(node.kind == "equation" for node in result.nodes)
    with pytest.raises(ValueError, match="hash"):
        read_nano_artifact(path, root=tmp_path, paper_id="1706.03762",
                           expected_sha256="0" * 64)


def test_golden_metrics_precise_recall_and_diff(tmp_path):
    _, document = prepared()
    first = next(node for node in document.nodes if node.kind == "paragraph")
    golden = GoldenPaper(document.paper_id, "a" * 64, {
        "paragraph": [
            {"source_anchor": first.source_anchor, "text": first.text},
            {"source_anchor": "S99", "text": "Missing paragraph"},
        ]
    })
    report = evaluate_document(document, golden)
    assert report["paragraph"].true_positive == 1
    assert report["paragraph"].false_negative == 1
    assert report["paragraph"].recall == .5
    assert compare_metrics(report, report)["paragraph"]["recall_delta"] == 0
    source = tmp_path / "sample.html"
    source.write_text(HTML)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "paper_id": document.paper_id, "reviewed": True,
        "source_file": "sample.html",
        "source_sha256": sha256(HTML.encode()).hexdigest(),
        "labels": golden.labels
    }))
    loaded = load_golden(manifest, tmp_path)
    assert loaded.labels == golden.labels
