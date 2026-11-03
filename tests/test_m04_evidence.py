"""M04: source-bound claims are always unverified until explicit human review."""
import json
import pytest

from models import Ar5ivContent, PaperData, Section, ParagraphAnnotation
from domain.paper_document import build_paper_document
from research.evidence import (
    ReviewLedger, check_binding, derive_candidates,
    render_markdown, save_candidates,
)


def sample():
    content = Ar5ivContent(
        paper_id="1706.03762", title="Paper", abstract="Paper overview",
        sections=[Section(title="Methods", level=2, paragraphs=[
            "The model uses 12 attention heads and evaluates 3 datasets."
        ])],
    )
    doc = build_paper_document(PaperData(arxiv_id="1706.03762", content=content)).to_dict()
    node = next(n for n in doc["nodes"] if n["kind"] == "paragraph")
    ann = ParagraphAnnotation(
        "Methods", 0, node["text"][:200],
        "The system evaluates 3 datasets.", ["There are 12 attention heads."],
        node_id=node["node_id"],
    ).to_dict()
    return doc, [ann]


def test_claims_have_exact_source_and_never_auto_approve():
    doc, anns = sample()
    data = derive_candidates(doc, anns)
    assert data["document_hash"] == doc["content_hash"]
    assert len(data["claims"]) == 2
    for claim in data["claims"]:
        assert claim["verification"] == "needs_review"
        assert claim["source_match"]
        check_binding(claim, doc)
        assert claim["start"] == 0
        assert claim["end"] == len(claim["quote"])
    assert data["claims"][0]["claim_id"] != data["claims"][1]["claim_id"]


def test_detects_numbers_not_in_original():
    doc, anns = sample()
    anns[0]["plain_explanation"] = "The system evaluates 9 datasets."
    data = derive_candidates(doc, anns)
    assert data["claims"][0]["numeric_warning"]
    assert data["claims"][0]["verification"] == "needs_review"


def test_missing_source_ref_fails_closed():
    doc, anns = sample()
    anns[0]["node_id"] = None
    with pytest.raises(ValueError, match="node ID"):
        derive_candidates(doc, anns)


def test_stale_preview_fails_closed():
    doc, anns = sample()
    anns[0]["para_text"] = "Different paragraph"
    with pytest.raises(ValueError, match="Stale"):
        derive_candidates(doc, anns)


def test_tampered_source_span_rejected():
    doc, anns = sample()
    claim = derive_candidates(doc, anns)["claims"][0]
    claim["start"] = 1
    with pytest.raises(ValueError, match="quote"):
        check_binding(claim, doc)


def test_review_history_is_append_only(tmp_path):
    doc, anns = sample()
    claim = derive_candidates(doc, anns)["claims"][0]
    ledger = ReviewLedger(tmp_path / "reviews.sqlite3")
    id1 = ledger.record(
        claim=claim, document=doc, reviewer="reviewer-a",
        verdict="insufficient", notes="Needs the Methods section",
    )
    id2 = ledger.record(
        claim=claim, document=doc, reviewer="reviewer-b",
        verdict="supported", notes="Checked original text and context",
    )
    assert id2 > id1
    assert [r["verdict"] for r in ledger.history(claim["claim_id"])] == [
        "insufficient", "supported",
    ]
    assert ledger.latest(claim)["reviewer"] == "reviewer-b"


def test_changed_document_cannot_reuse_approved_evidence(tmp_path):
    doc, anns = sample()
    claim = derive_candidates(doc, anns)["claims"][0]
    ledger = ReviewLedger(tmp_path / "reviews.sqlite3")
    ledger.record(claim=claim, document=doc, reviewer="reviewer", verdict="supported")
    changed = json.loads(json.dumps(doc))
    changed["content_hash"] = "0" * 64
    with pytest.raises(ValueError, match="Stale"):
        ledger.record(claim=claim, document=changed,
                      reviewer="reviewer", verdict="supported")
    stale_claim = dict(claim, document_hash="0" * 64)
    assert ledger.latest(stale_claim) is None


def test_invalid_decision_and_reviewer_rejected(tmp_path):
    doc, anns = sample()
    claim = derive_candidates(doc, anns)["claims"][0]
    ledger = ReviewLedger(tmp_path / "reviews.sqlite3")
    with pytest.raises(ValueError, match="verdict"):
        ledger.record(claim=claim, document=doc, reviewer="x", verdict="predicted")
    with pytest.raises(ValueError, match="reviewer"):
        ledger.record(claim=claim, document=doc, reviewer="", verdict="supported")


def test_markdown_and_json_artifacts(tmp_path):
    doc, anns = sample()
    data = derive_candidates(doc, anns)
    path = tmp_path / "claim_candidates.json"
    save_candidates(path, data)
    assert json.loads(path.read_text())["claims"][0]["claim_id"] == data["claims"][0]["claim_id"]
    md = render_markdown(data)
    assert "needs_review" in md
    assert "arxiv.org/abs/1706.03762" in md
    assert "chars 0" in md


def test_empty_annotations_yield_empty_manifest():
    doc, _ = sample()
    result = derive_candidates(doc, [])
    assert result["claims"] == []
    assert result["schema_version"] == "claim-candidates-v1"



def test_tampered_claim_identity_and_excerpt_fail_closed():
    doc, anns = sample()
    claim = derive_candidates(doc, anns)["claims"][0]
    with pytest.raises(ValueError, match="Candidate ID"):
        check_binding(dict(claim, text="A different unsupported statement"), doc)
    with pytest.raises(ValueError, match="excerpt"):
        check_binding(dict(claim, quote=claim["quote"][1:], start=1,
                           end=claim["end"]), doc)
