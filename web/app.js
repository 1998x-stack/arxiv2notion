/* Local-first, read-only UI: never insert untrusted data as HTML. */
"use strict";
const results = document.getElementById("results");
const detail = document.getElementById("detail");
const count = document.getElementById("count");
const status = document.getElementById("status");
const queryInput = document.getElementById("query");
let activeId = null;

function element(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (cls) node.className = cls;
  return node;
}
function add(parent, tag, text, cls) {
  const node = element(tag, text, cls);
  parent.appendChild(node);
  return node;
}
async function api(path, params = {}) {
  const url = new URL(path, window.location.origin);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  const response = await fetch(url);
  const body = await response.json();
  if (!response.ok) throw Error(body.error || "Request failed");
  return body;
}
function showError(parent, message) { add(parent, "p", message, "error"); }
function refList(parent, citations, direction) {
  const section = add(parent, "section", undefined, "panel");
  add(section, "h2", direction === "out" ? "References" : "Cited by");
  if (!citations.length) { add(section, "p", "None indexed.", "muted"); return; }
  const list = add(section, "ol", undefined, "refs");
  citations.forEach(ref => {
    const item = add(list, "li");
    if (direction === "out") {
      const label = ref.target_kind + ":" + ref.target_id;
      add(item, "strong", (ref.citation_key || "") + " " + label + " ");
      add(item, "span", ref.raw_text || "", "muted");
      if (ref.target_kind === "arxiv") {
        const link = add(item, "a", " View on arXiv");
        link.href = "https://arxiv.org/abs/" + encodeURIComponent(ref.target_id);
        link.rel = "noreferrer";
      }
    } else {
      const button = add(item, "button", ref.title || ref.source_id);
      button.addEventListener("click", () => openPaper(ref.source_id));
      add(item, "small", "  " + (ref.raw_text || ""), "muted");
    }
  });
}
function nodeList(parent, nodes, paperId) {
  const section = add(parent, "section", undefined, "panel");
  add(section, "h2", "Document structure");
  if (!nodes.length) { add(section, "p", "No full-text nodes available.", "muted"); return; }
  nodes.forEach(node => {
    const entry = add(section, "article", undefined, "node");
    if (node.kind === "heading") {
      add(entry, "h3", node.text, "section-title");
    } else {
      add(entry, "span", node.kind, "chip");
      if (node.section_title) add(entry, "span", node.section_title, "chip");
      if (node.kind === "figure" && node.payload && node.payload.src &&
          /^https?:\/\//i.test(node.payload.src)) {
        const link = add(entry, "a", "Figure source");
        link.href = node.payload.src;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
      const text = node.text || JSON.stringify(node.payload || {});
      add(entry, "pre", text);
    }
    if (node.source_anchor) {
      const link = add(entry, "a", "Original section");
      link.href = "https://ar5iv.labs.arxiv.org/html/" +
        encodeURIComponent(paperId) + "#" + encodeURIComponent(node.source_anchor);
      link.rel = "noreferrer";
    }
  });
}
async function claimPanel(parent, paperId) {
  const section = add(parent, "section", undefined, "panel");
  add(section, "h2", "Evidence & review");
  try {
    const data = await api("/api/claims", { id: paperId });
    if (!data.claims || !data.claims.length) {
      add(section, "p", "No AI reading-note candidates available.", "muted");
      return;
    }
    data.claims.forEach(claim => {
      const box = add(section, "article", undefined, "claim");
      const verdict = claim.latest_review ? claim.latest_review.verdict : "needs_review";
      add(box, "span", verdict, "chip");
      if (claim.numeric_warning) add(box, "span", "Check numbers", "chip");
      add(box, "p", claim.text);
      const quote = add(box, "blockquote", undefined, "quote");
      quote.textContent = claim.quote;
      add(box, "small", "Source node " + claim.source_node_id +
        " · characters " + claim.start + "–" + claim.end, "muted");
    });
  } catch (error) { showError(section, "Evidence unavailable: " + error.message); }
}
async function openPaper(paperId) {
  activeId = paperId;
  detail.replaceChildren();
  add(detail, "p", "Loading paper…", "muted");
  try {
    const [paper, cites, backlinks] = await Promise.all([
      api("/api/paper", { id: paperId }),
      api("/api/citations", { id: paperId }),
      api("/api/backlinks", { id: paperId }),
    ]);
    if (activeId !== paperId) return;
    detail.replaceChildren();
    add(detail, "h2", paper.title || paper.arxiv_id, "paper-title");
    add(detail, "span", "arXiv " + paper.arxiv_id, "chip");
    add(detail, "span", "Quality: " + (paper.quality || {}).status, "chip");
    add(detail, "p", "Content fingerprint: " + paper.content_hash.slice(0, 16), "meta");
    const abstract = (paper.metadata || {}).abstract ||
      (paper.nodes || []).find(n => n.kind === "abstract")?.text;
    if (abstract) {
      const section = add(detail, "section", undefined, "panel");
      add(section, "h2", "Abstract");
      add(section, "p", abstract);
    }
    refList(detail, cites, "out");
    refList(detail, backlinks, "in");
    await claimPanel(detail, paperId);
    nodeList(detail, paper.nodes || [], paperId);
    detail.focus();
    [...results.querySelectorAll("button")].forEach(button =>
      button.setAttribute("aria-current", button.dataset.id === paperId ? "true" : "false"));
  } catch (error) {
    detail.replaceChildren();
    showError(detail, "Unable to open paper: " + error.message);
  }
}
async function search() {
  status.textContent = "Searching…";
  try {
    const docs = await api("/api/search", { q: queryInput.value, limit: "40" });
    results.replaceChildren();
    count.textContent = "(" + docs.length + ")";
    docs.forEach(doc => {
      const item = add(results, "li");
      const button = add(item, "button", doc.title || doc.arxiv_id);
      button.dataset.id = doc.arxiv_id;
      button.setAttribute("aria-current", doc.arxiv_id === activeId ? "true" : "false");
      button.addEventListener("click", () => openPaper(doc.arxiv_id));
      add(item, "small", doc.arxiv_id + " · " + doc.quality, "muted");
    });
    status.textContent = docs.length + " papers shown";
    if (!docs.length) add(results, "li", "No matching papers.", "muted");
  } catch (error) { status.textContent = "Search failed"; showError(results, error.message); }
}
document.getElementById("search-form").addEventListener("submit", event => {
  event.preventDefault();
  search();
});
async function init() {
  try {
    const stats = await api("/api/overview");
    status.textContent = stats.papers + " papers · " + stats.citations + " citations";
  } catch (error) { status.textContent = "Catalog unavailable"; }
  await search();
}
init();