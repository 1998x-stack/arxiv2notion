# ar5iv / LaTeXML Extraction Adapter — V2

> This module extracts **already converted HTML**, not LaTeX sources. The adapter sits between ar5iv and the canonical PaperDocument / Notion pipeline.

## Source and scope

ar5iv offers HTML5 articles converted from arXiv TeX sources through LaTeXML. The original source archive may have nonstandard entrypoint names, multiple TeX files, custom styles, figures, and unsupported macros. A downstream HTML parser **cannot reconstruct omitted content** or discover the correct main TeX file.

References:

- [ar5iv service](https://github.com/dginev/ar5iv)
- [LaTeXML](https://github.com/brucemiller/LaTeXML)
- [ar5iv CSS and HTML conventions](https://github.com/dginev/ar5iv-css)
- [HTML papers on arXiv (2402.08954)](https://arxiv.org/abs/2402.08954)
- [1998x-stack/nano-ar5iv: upstream-conversion research](https://github.com/1998x-stack/nano-ar5iv)

Pipeline:

    arXiv paper ID
      +-- arXiv metadata API -----------------> metadata / PDF fallback
      +-- ar5iv HTML (LaTeXML) ---------------> bounded async fetch
                                                  |
                                      BeautifulSoup + lxml
                                                  |
                             structural sections, ordered blocks,
                             MathML, images, tables, references
                                                  |
                              legacy Ar5ivContent dataclasses
                                      |                  |
                             PaperDocument v1      NotionConverter
                             IDs / quality / hash  Notion blocks
                                      |                  |
                             local versioned data  durable sync

## Parser guarantees

### Semantic traversal

LaTeXML pages contain deeply nested wrappers: ltx_para, ltx_theorem, ltx_proof, ltx_itemize and additional layout containers. Searching only immediate children silently loses legitimate body content.

V2 uses a recursive, bounded-by-section DOM walk and emits each recognized block exactly once. It stops at nested sections and at paragraph, equation, figure or table boundaries. Short paragraphs remain valid. A heading belongs to the section whose nearest section ancestor contains it. Removing displayed section numbering must not mutate the original DOM.

The Section model preserves both an ordered_content stream and legacy arrays of paragraphs, figures, tables and equations. It keeps child sections in the existing subsection tree. This is compatible with domain/paper_document.py and notion/converter.py. A future schema version is needed to represent child sections interleaved with their parent's body.

### Math

Priority for recoverable LaTeX:

1. MathML math element alttext attribute.
2. Semantics annotation with encoding application/x-tex.
3. Preserve MathML alone when no LaTeX exists; never invent a formula.

Inline mathematics uses dollar-marked text when LaTeX exists; when only MathML is present, it is preserved as visible literal XML rather than silently dropped. Display formulas are Equation blocks with raw MathML and optional LaTeX. Equation groups must not be double-counted with their children.

Notion requires renderable LaTeX for Equation blocks. Canonical content can preserve MathML when Notion cannot render the formula. Existing no-silent-loss behavior is intentional.

### Figures, tables, bibliography

A figure carries source, caption, alternative text, and source anchor. Image URLs are resolved relative to source HTML and only HTTPS URLs are exported; an unsafe URL is replaced with the empty string. Multi-image figures emit a panel per image, with the parent caption on the first panel and stable source-anchor suffixes for subsequent panels. Subfigure-level captions and exact panel layout remain a future schema extension.

Tables capture the nearest caption, headers, and data rows, excluding rows of nested tabulars. Colspan and rowspan placeholders preserve a rectangular content matrix, but **not merged-cell presentation**. The original HTML/PDF remains authoritative for layout.

Bibliography entries are traversed once, not as body paragraphs. DOI, year, title, and arXiv ID inferred from text are best-effort heuristics; they are not definitive bibliographic identities.

### Full-text export

The legacy full_text field previously serialized body paragraphs only. V2 uses ordered_content, including equations, image links and captions, and table values. The canonical PaperDocument nodes remain the structured source of truth.

### Cache and identity

No public Ar5ivContent field was removed and the PaperDocument schema remains v1.0. The stored extraction cache now includes an internal extractor version of 2. Older caches must be re-fetched because they can contain omissions even when their quality score was considered sufficient.

Document node IDs, duplicate-content handling, source_anchor and content hashes remain managed by domain/paper_document.py. Do not fabricate source byte offsets or claim the output is lossless without golden-fidelity evaluation.

## Network policy

- Validate modern and old-format arXiv IDs **before** filesystem cache or URL use.
- Respect the configured ar5iv base URL.
- Use bounded aiohttp calls; total response payload max 20 MiB, HTML/XHTML only.
- Do not follow HTTP redirects to unknown hosts; reject malformed links and private-network media URLs.
- Retry only 429, 500, 502, 503, 504, timeout and client transport errors.
- Use bounded exponential delays and honor numeric Retry-After when within budget.
- Treat an excessive Retry-After as deferral, **not** permission to retry early.
- 404 and 410 indicate no available upstream HTML and lead to metadata/PDF fallback.
- A 200 response without meaningful abstract or body is not a successful full-text extraction.
- Never cache an abstract-only response as full text.
- Avoid dumping HTML, sensitive tokens or entire paper bodies into logs.

## Explicit limitations and V3 roadmap

| Case | V2 behavior | Future work |
|---|---|---|
| Missing or irregular TeX entrypoint | No HTML conversion performed | Sandboxed LaTeXML worker with root-candidate discovery, include graph and provenance |
| Official arXiv HTML also available | Current configured ar5iv source only | Ordered, quality-aware HTML provider fallback |
| Theorems, proofs, lists | Their body paragraphs preserved | Dedicated node types for semantic presentation |
| Complex algorithms / code listings | Generic text when represented as paragraphs | Typed code and algorithm nodes |
| MathML without LaTeX | Inline XML visible as text; display MathML retained canonically but Notion cannot render it | MathML-to-image or carefully validated conversion |
| Cross-references | Visible link text retained | Inline span/link AST with target anchors |
| Footnotes and margin annotations | Excluded from body traversal | Footnote nodes with backlinks |
| Multiple figure panels | All image URLs emitted as ordered Figure panels; parent caption on first | Individual subpanel captions and exact grid layout |
| Merged cells | Expanded rectangular placeholders | Explicit span metadata |
| Nested section order | Child sections after parent's body | Mixed ordered child block stream |
| Citations | Heuristic DOI/arXiv extraction | Provenance-aware citation graph with confidence |
| Full document fidelity | Structural quality gate only | Manually annotated golden corpus and block-level recall |

The upstream TeX-to-HTML process belongs in a separate trusted worker. Handling unusual files, missing main.tex, custom classes or latexml conversion errors is **not** solved by adding more BeautifulSoup selectors.

## Validation

Run:

    python -m compileall -q fetch domain models.py
    python -m pytest tests/test_ar5iv_semantics_v2.py -q
    python -m pytest tests/ -q

Synthetic tests use no live networking and no Notion credentials. Live integration verification belongs in a dedicated Notion test workspace.

Coverage targets: nested wrappers, subsection isolation, stable canonical nodes, inline and display mathematics, grouped equations, table captions and grid spans, relative image links, invalid protocols, references, 404/429/503, response-body limits, cache migration and idempotent Notion sync.

Before calling an import complete, compare block-level recall against manually inspected ar5iv HTML and verify Notion blocks through the durable sync read-back layer. Track failure counts, partial quality rate, and missing image/equation/table fractions separately.
