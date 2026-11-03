"""M03 catalog regression fixtures: provenance, identity and incremental updates."""
import json
from models import Ar5ivContent, PaperData, Reference, Section
from domain.paper_document import build_paper_document
from research.catalog import PaperCatalog, reference_target


def sample(refs=None, *, paper_id="1706.03762", text="A paragraph"):
    paper = PaperData(arxiv_id=paper_id, content=Ar5ivContent(
        paper_id=paper_id, title="Attention Is All You Need",
        abstract="A study of attention", sections=[
            Section(title="Methods", level=2, paragraphs=[text]),
        ], references=refs or [],
    ))
    return build_paper_document(paper)


def test_official_ids_only_not_fuzzy_titles():
    assert reference_target({"arxiv_id": "2401.12345v2"}) == ("arxiv", "2401.12345")
    assert reference_target({"doi": "https://doi.org/10.1000/ABC"}) == (
        "doi", "10.1000/abc")
    assert reference_target({"title": "Identical title", "raw_text": "Citation"})[0] == "unresolved"
    assert reference_target({"arxiv_id": "../bad", "raw_text": "Citation"})[0] == "unresolved"


def test_roundtrip_catalog_with_duplicate_evidence(tmp_path):
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    refs = [
        Reference(raw_text="Same paper mention A", arxiv_id="2401.12345", citation_key="[1]"),
        Reference(raw_text="Same paper mention B", arxiv_id="2401.12345", citation_key="[2]"),
        Reference(raw_text="Unknown", title="Unverified"),
    ]
    doc = sample(refs)
    assert db.upsert(doc) == 3
    assert db.overview() == {
        "papers": 1, "citations": 3, "identified_citations": 2,
        "unresolved_citations": 1,
    }
    assert db.paper("1706.03762")["title"] == "Attention Is All You Need"
    assert len(db.search("attention")) == 1
    assert len(db.citations("1706.03762")) == 3
    assert db.citations("1706.03762")[0]["citation_key"] == "[1]"
    assert len(db.cited_by("2401.12345v2")) == 2
    assert db.upsert(doc) == 3
    assert db.overview()["citations"] == 3


def test_updates_replace_edges_not_accumulate(tmp_path):
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    a = sample([Reference(raw_text="Old", arxiv_id="2401.12345")])
    b = sample([Reference(raw_text="New", doi="10.1234/paper")], text="Updated text")
    db.upsert(a)
    db.upsert(b)
    assert db.cited_by("2401.12345") == []
    assert db.citations("1706.03762")[0]["target_kind"] == "doi"
    assert db.paper("1706.03762")["content_hash"] == b.content_hash


def test_versions_remain_separate_imports(tmp_path):
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    db.upsert(sample(paper_id="1706.03762v1"))
    db.upsert(sample(paper_id="1706.03762v2"))
    assert db.overview()["papers"] == 2


def test_search_escapes_wildcards_and_sql(tmp_path):
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    db.upsert(sample())
    assert not db.search("no_match%")
    assert not db.search("' OR 1=1 --")
    assert db.search("1706.03762")


def test_directory_rebuild_skips_corrupt_artifacts(tmp_path):
    root = tmp_path / "papers"
    good = root / "ai" / "1706.03762"
    good.mkdir(parents=True)
    (good / "document.json").write_text(
        json.dumps(sample().to_dict(), ensure_ascii=False))
    bad = root / "other" / "2401.12345"
    bad.mkdir(parents=True)
    (bad / "document.json").write_text("{invalid")
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    result = db.index_directory(root)
    assert result["papers"] == 1
    assert result["edges"] == 0
    assert len(result["errors"]) == 1
    assert db.overview()["papers"] == 1


def test_missing_directory_uses_empty_report(tmp_path):
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    assert db.index_directory(tmp_path / "not_exists")["missing_directory"]


def test_document_captures_title_without_api_metadata():
    d = sample()
    assert d.to_dict()["title"] == "Attention Is All You Need"
    assert d.content_hash != sample(text="changed").content_hash
