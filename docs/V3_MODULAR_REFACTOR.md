# V3 Modular Refactor — Architecture, Migration and Verification

> Branch: refactor/v3-modular-pipeline-20261106
>
> **Stacked on V2 PR #8**. This change should be reviewed against
> feat/ar5iv-parser-v2-20261106, not independently cherry-picked to main.
> Existing imports and Notion production writes remain backward compatible.

## 1. Purpose and source-of-truth boundaries

The previous fetch/ar5iv_extractor.py combined HTTP retries, caching,
LaTeXML DOM walking, formula extraction, table/figure parsing, bibliography
heuristics and document assembly in a single file.

V3 separates those responsibilities without deleting the proven import path:

- fetch/ar5iv_extractor.py: HTTP, per-paper cache and compatibility facade.
- parsing/latexhtml.py: HTML-to-Ar5ivContent orchestration.
- parsing/semantic_blocks.py: section hierarchy, nested semantic roles, order.
- parsing/mathematics.py: inline math and display MathML/TeX preservation.
- parsing/figures.py: source references, image panels and captions.
- parsing/tables.py: caption ownership and rectangular table content.
- parsing/references.py: citation-key and bibliographic heuristics.
- fetch/providers/: ar5iv, official arXiv HTML and explicit nano local artifact.
- domain/scientific_document_v2.py, nodes.py, provenance.py, relations.py:
  versioned, content-addressed IR with explicit identity and source evidence.
- adapters/: existing Ar5ivContent and nano-ar5iv M04 contracts to IR V2.
- quality/: structural acceptance, missing formulas and provider divergence.
- notion/compiler_v2.py: strict typed IR -> Notion block compiler.
- notion/media.py: HTTPS public-address media preflight.
- notion/verifier.py: read-only wrapper over durable_sync remote projection.
- benchmarks/: SHA256-pinned reviewed corpus and per-node precision/recall.
- tests/: network-free modular tests, trusted golden staging and opt-in E2E.

No bulk deletion of caches, historical sample papers or annotations is
performed: those are user-owned artifacts. The former parser implementations
were **moved out of the legacy extractor**, not duplicated in the old module.

## 2. Runtime modes

Legacy behavior (default):

    python main.py 1706.03762 --no-annotate

- Uses existing ar5iv extractor, cache, canonical PaperDocument v1,
  annotations and durable Notion writer.
- Historical imported pages and locally saved cache formats remain readable.
- The V2 cache version marker from PR #8 remains active.

Conservative provider comparison (explicit opt-in):

    python main.py 1706.03762 --source-strategy multi --no-annotate

Alternatively set ARXIV_HTML_SOURCE_STRATEGY=multi.

- Fetches ar5iv and official arXiv HTML separately, parses both, checks
  declared HTML identifiers, builds ScientificDocument V2 and runs a
  structural-only quality report.
- If one candidate is structurally accepted and the other unavailable,
  accepts that candidate and persists both legacy document.json and the
  source-bound document-v2.json.
- If accepted sources disagree structurally, abstains from choosing,
  preserving metadata/PDF fallback rather than silently merging content.
- If a requested revision is not proven by HTML metadata, it is a
  REVIEW_REQUIRED candidate; do not treat URL shape as proof.
- Does not auto-execute nano-ar5iv or unknown TeX sources.
- The opt-in resolver does not reuse the legacy HTML cache yet.

A result named ACCEPTED means **structurally accepted**: scientific fidelity
is not independently verified. This is an intentionally conservative V3
foundation, not the end of scientific gold-corpus validation.

## 3. V2 IR contract

ScientificDocument V2 contains:

- paper_id, source (provider, observed normalized HTML SHA256, URI,
  media type, optional explicit revision/engine);
- nodes with stable canonical node_id, typed kind, parent_id, ordinal,
  source_anchor, payload and inline_spans;
- explicit relations and references;
- status NOT_EVALUATED by default, warnings and deterministic content_hash.

Supported kinds include heading, paragraph, theorem, proof, algorithm,
code, equation, figure, table, footnote, citation, cross_reference, unknown.

Semantic role discovery:
- LaTeXML ltx_theorem, ltx_proof, ltx_algorithm, ltx_listing,
  ltx_verbatim and ltx_note wrappers attach a semantic_role to their
  paragraph items.
- Legacy Section.paragraphs and Section.ordered_content types stay
  unchanged. The V2 adapter changes the corresponding node **kind**, not its
  identity or text; there is no duplicate paragraph.
- Richer equation, figure, table and bibliography payloads remain available
  in the existing canonical data.
- New inline spans and citation edges are modelled but not fully extracted
  from arbitrary HTML. Do not claim complete cross-reference fidelity.

nano-ar5iv M04 compatibility:
- An allowlisted, size-bounded local normalization artifact is read with
  explicit expected SHA256 and a declared paper ID.
- Its section/subsection nodes map to headings; paragraph_text to paragraph;
  math and assets to typed semantic nodes.
- M04 quality_status NOT_EVALUATED is retained; no synthetic VERIFIED.
- A full nano remote conversion service remains outside this release.

## 4. Notion compilation and verification

The existing NotionConverter + DurableNotionWriter remain the production
default. This is deliberate to avoid silently losing reference pages or
AI reading annotations during the IR migration.

For consumers explicitly using V2:
- compile_document(document) maps typed nodes to existing NotionBlockBuilder
  blocks; supports equation, figure, table, theorem, proof, algorithm and
  code.
- Unknown/unrenderable nodes, missing renderable math or invalid media
  URLs raise ScientificCompileError rather than silently disappear.
- It uses validate_notion_blocks() for request-size and rich text limits.
- CompiledPage.node_block_map tracks which output blocks belong to source IDs.
- NotionReadbackVerifier checks the writer's complete remote projection,
  returns MATCH/INCOMPLETE/MISMATCH and performs no writes itself.

Not implemented:
- a fully promoted V2 writer replacing all existing Notion annotation and
  reference-page features;
- full media upload life-cycle and expiry tracking;
- live, credentialed Notion read-back integration validation;
- publication-quality reconstruction of merged table styling.

## 5. Golden benchmark contract

A reviewed manifest is required to declare ground truth:

    {
      "reviewed": true,
      "paper_id": "...",
      "source_file": "source.html",
      "source_sha256": "<64 hex chars>",
      "labels": {
        "paragraph": [
          {"source_anchor": "...", "text": "..."}
        ]
      }
    }

benchmarks/corpus.py verifies the pinned snapshot and rejects unreviewed
manifests; benchmarks/evaluate.py reports per-kind TP/FP/FN, precision,
recall. Duplicate nodes are handled by a multiset. compare.py reports
before/after deltas without changing labels.

No synthetic regression fixture is described as a real manually annotated
paper. The first 40-paper independent gold corpus is **future work**.

## 6. Regression and release commands

    python -m compileall -q main.py config.py models.py utils.py \
      fetch parsing domain adapters quality notion benchmarks process \
      storage research tests
    python -m pytest tests/ -q

New V3 tests verify:
- the old Ar5ivExtractor API remains available with its semantic methods
  inherited from focused parsers;
- canonical node IDs, parent relationships and serialized hashes;
- compiler ordering, explicit failures and media URL denial;
- fake-provider fallback, source conflict abstention and arXiv version check;
- M04 node kind mapping and artifact SHA256 tamper checks;
- content-addressed document-v2.json persistence;
- reviewed-only benchmark pinning, exact TP/FP/FN and metric comparison.

## 7. Follow-up work with hard acceptance criteria

1. **Real provider gold corpus**: manually reviewed HTML/PDF/TeX snapshots,
   precise block recall and precision; fail if critical science content
   changes silently.
2. **Cross-reference AST**: parse inline anchors, citation target IDs,
   subfigure caption ownership and semantic theorem numbering.
3. **Real Notion workspace certification**: create, paginate, verify every
   node, retry uncertain writes and inspect media availability.
4. **nano-ar5iv M05/M06**: finish scientific fidelity gate and a sandboxed
   service contract before enabling automated untrusted conversion.
5. **Promotion of V2 compiler**: migrate annotations and child references
   and deprecate legacy converter only after back-to-back golden and
   integration evidence confirms equal or better fidelity.

No configuration, test or documentation claims that successful parsing is
equivalent to scientific correctness.
