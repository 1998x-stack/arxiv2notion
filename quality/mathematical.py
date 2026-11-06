"""Check presence of original scientific formula representations."""
from domain.scientific_document_v2 import ScientificDocument

def formula_warnings(document: ScientificDocument) -> list[str]:
    warnings = []
    for node in document.nodes:
        if node.kind != "equation":
            continue
        if not (node.payload.get("latex") or node.payload.get("source_tex")
                or node.payload.get("mathml")
                or node.payload.get("presentation_mathml") or node.text):
            warnings.append(f"empty_equation:{node.node_id}")
    return warnings
