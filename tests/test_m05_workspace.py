"""M05 read-only local HTTP workspace regression tests."""
import json
from models import Ar5ivContent, PaperData, Reference, Section
from domain.paper_document import build_paper_document
from research.catalog import PaperCatalog
from research.web import route


def fixture(tmp_path):
    db = PaperCatalog(tmp_path / "catalog.sqlite3")
    content = Ar5ivContent(
        paper_id="1706.03762", title="Attention and its Patterns",
        abstract="A test paper", sections=[
            Section(title="Methods", level=2, paragraphs=["This is a source paragraph."])
        ],
        references=[Reference(raw_text="One reference", arxiv_id="2401.00001")]
    )
    document = build_paper_document(PaperData(
        arxiv_id="1706.03762", content=content)).to_dict()
    db.upsert(document)
    return db, document


def get(db, route_path, tmp_path):
    status, mime, body = route(
        route_path, db, papers_root=tmp_path / "papers",
        reviews_db=tmp_path / "reviews.sqlite3",
    )
    if "json" in mime:
        return status, json.loads(body.decode("utf-8"))
    return status, body


def test_static_assets_are_served_from_allowlist(tmp_path):
    db, _ = fixture(tmp_path)
    for path in ("/", "/app.js", "/style.css"):
        status, body = get(db, path, tmp_path)
        assert status == 200
        assert body
    assert get(db, "/../../config.py", tmp_path)[0] == 404


def test_workspace_search_and_paper_detail(tmp_path):
    db, doc = fixture(tmp_path)
    assert get(db, "/api/overview", tmp_path)[1]["papers"] == 1
    status, items = get(db, "/api/search?q=Attention", tmp_path)
    assert status == 200
    assert items[0]["arxiv_id"] == "1706.03762"
    assert get(db, "/api/paper?id=1706.03762", tmp_path)[1]["content_hash"] == doc["content_hash"]
    assert get(db, "/api/citations?id=1706.03762", tmp_path)[1][0]["target_id"] == "2401.00001"
    assert get(db, "/api/backlinks?id=2401.00001", tmp_path)[1][0]["source_id"] == "1706.03762"


def test_search_and_path_inputs_are_bounded(tmp_path):
    db, _ = fixture(tmp_path)
    assert get(db, "/api/paper?id=../etc/passwd", tmp_path)[0] == 400
    assert get(db, "/api/paper?id=2401.12345", tmp_path)[0] == 404
    assert get(db, "/api/search?limit=NaN", tmp_path)[0] == 400
    assert get(db, "/api/search?q=" + "a" * 251, tmp_path)[0] == 400


def test_claims_stale_content_hash_is_rejected(tmp_path):
    db, doc = fixture(tmp_path)
    target = tmp_path / "papers" / "other" / "1706.03762"
    target.mkdir(parents=True)
    (target / "claim_candidates.json").write_text(json.dumps({
        "schema_version": "claim-candidates-v1",
        "document_hash": "0" * 64, "arxiv_id": "1706.03762",
        "claims": [],
    }))
    assert get(db, "/api/claims?id=1706.03762", tmp_path)[0] == 409
    (target / "claim_candidates.json").write_text(json.dumps({
        "schema_version": "claim-candidates-v1",
        "document_hash": doc["content_hash"], "arxiv_id": "1706.03762",
        "claims": [],
    }))
    assert get(db, "/api/claims?id=1706.03762", tmp_path) == (
        200, {"schema_version": "claim-candidates-v1",
              "document_hash": doc["content_hash"],
              "arxiv_id": "1706.03762", "claims": []},
    )


def test_missing_claim_artifact_is_empty_not_crash(tmp_path):
    db, _ = fixture(tmp_path)
    assert get(db, "/api/claims?id=1706.03762", tmp_path) == (
        200, {"schema_version": "claim-candidates-v1", "claims": []},
    )


def test_static_javascript_never_injects_html(tmp_path):
    db, _ = fixture(tmp_path)
    _, js = get(db, "/app.js", tmp_path)
    text = js.decode("utf-8")
    assert "textContent" in text
    assert "innerHTML" not in text
    assert "eval(" not in text
