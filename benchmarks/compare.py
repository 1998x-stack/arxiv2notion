"""Compare two audited benchmark metric sets without hiding regressions."""
from benchmarks.evaluate import KindMetrics

def compare_metrics(before: dict[str, KindMetrics],
                    after: dict[str, KindMetrics]) -> dict[str, dict[str, float]]:
    if before.keys() != after.keys():
        raise ValueError("Benchmark kinds differ")
    return {
        kind: {
            "precision_delta": after[kind].precision - before[kind].precision,
            "recall_delta": after[kind].recall - before[kind].recall,
        }
        for kind in sorted(before)
    }
