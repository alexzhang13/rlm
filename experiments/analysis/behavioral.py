"""Phase 8b — behavioral trace analysis.

Measures how each arm's *behavior* differs (not just its score), via:
  - Strategy-term adoption: per arm, fraction of traces mentioning the
    hinted vocabulary (LRU, probation, SIEVE, reconstruction_cost, …).
  - Code-pattern signatures: del-statement count, comments mentioning
    strategy names, use of rlm_query_batched, etc.
  - Simple behavioral clustering: between-arm vs within-arm feature
    distances.

Outputs:
  - results/behavioral.csv    (long format: arm, query_id, feature, value)
  - results/behavioral.md     (summary table of adoption rates + cluster
                               separation)

For RLM arms we read the per-iteration traces from the RLM logger output
at logs/ — if no logs exist, we fall back to the top-level prediction
string only (still catches final-answer vocabulary but misses REPL code).

Usage:
    uv run python -m experiments.analysis.behavioral
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import statistics
import sys
from collections import defaultdict

RESULTS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "results"
LOGS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "logs"


ARM_TERMS: dict[str, list[str]] = {
    "rlm_a0": [],
    "rlm_a1": ["lru", "last_used", "recently"],
    "rlm_a3": ["probation", "ghost", "promote", "one-hit"],
    "rlm_a4": ["sieve", "lazy promotion", "re-referenced", "re-reference"],
    "rlm_a6": [
        "reconstruction", "admission", "retention_cost",
        "s3-fifo", "sieve", "lru", "lfu",
    ],
}


def _trace_text(benchmark: str, method: str, query_id: str) -> str:
    """Best-effort: combine the prediction + any RLM per-iteration log
    that matches this query."""
    safe = query_id.replace("/", "_").replace(":", "_")
    path = RESULTS_DIR / benchmark / method / f"{safe}.jsonl"
    parts: list[str] = []
    if path.exists():
        try:
            rec = json.loads(path.read_text().splitlines()[-1])
            parts.append(str(rec.get("prediction", "")))
        except Exception:
            pass
    # Try to find matching RLM log (optional)
    for log_path in LOGS_DIR.rglob("*.jsonl"):
        if query_id in log_path.stem:
            try:
                parts.append(log_path.read_text()[:500_000])  # cap to 500K
            except Exception:
                pass
            break
    return "\n\n".join(parts)


def count_features(text: str, arm: str) -> dict[str, float]:
    t = (text or "").lower()
    feats: dict[str, float] = {}
    # Strategy-term presence (0/1) — any of the arm's terms
    terms = ARM_TERMS.get(arm, [])
    feats["uses_any_arm_term"] = float(any(term in t for term in terms))
    feats["n_arm_term_hits"] = float(sum(t.count(term) for term in terms))
    # Universal behavioral counters
    feats["n_del_statements"] = float(len(re.findall(r"\bdel\s+\w", t)))
    feats["n_repl_blocks"] = float(len(re.findall(r"```(?:repl|python)", t)))
    feats["n_llm_query_calls"] = float(len(re.findall(r"llm_query\(", t)))
    feats["n_rlm_query_calls"] = float(len(re.findall(r"rlm_query\(", t)))
    feats["n_batched_calls"] = float(len(re.findall(r"llm_query_batched\(|rlm_query_batched\(", t)))
    feats["trace_len_chars"] = float(len(t))
    return feats


def aggregate_adoption(rows_by_arm: dict[str, list[dict]]) -> dict:
    """Per-arm adoption rate + mean behavioral features."""
    summary: dict = {}
    for arm, rows in rows_by_arm.items():
        if not rows:
            continue
        keys = rows[0].keys()
        summary[arm] = {}
        for k in keys:
            vals = [r[k] for r in rows]
            summary[arm][k] = {
                "mean": statistics.mean(vals) if vals else 0.0,
                "std": statistics.stdev(vals) if len(vals) > 1 else 0.0,
                "n": len(vals),
            }
    return summary


def pairwise_distance(a: list[float], b: list[float]) -> float:
    """Normalized L1 distance between two feature vectors."""
    if not a or not b:
        return 0.0
    parts = []
    for x, y in zip(a, b):
        m = max(abs(x), abs(y), 1.0)
        parts.append(abs(x - y) / m)
    return sum(parts) / len(parts)


def cluster_separation(rows_by_arm: dict[str, list[dict]]) -> dict:
    """Between-arm vs within-arm feature distance.

    Uses a fixed feature ordering so vectors are comparable.
    If between >> within, arms are behaviorally distinct.
    """
    feature_order = [
        "uses_any_arm_term", "n_arm_term_hits", "n_del_statements",
        "n_repl_blocks", "n_llm_query_calls", "n_rlm_query_calls",
        "n_batched_calls", "trace_len_chars",
    ]
    vectors_by_arm: dict[str, list[list[float]]] = {}
    for arm, rows in rows_by_arm.items():
        vectors_by_arm[arm] = [[r.get(f, 0.0) for f in feature_order] for r in rows]

    within: list[float] = []
    between: list[float] = []
    arms = list(vectors_by_arm.keys())
    for a in arms:
        vecs = vectors_by_arm[a]
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                within.append(pairwise_distance(vecs[i], vecs[j]))
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            for va in vectors_by_arm[a]:
                for vb in vectors_by_arm[b]:
                    between.append(pairwise_distance(va, vb))
    return {
        "within_mean": statistics.mean(within) if within else 0.0,
        "between_mean": statistics.mean(between) if between else 0.0,
        "within_n": len(within),
        "between_n": len(between),
        "ratio": (statistics.mean(between) / statistics.mean(within))
                 if within and between and statistics.mean(within) > 0 else 0.0,
    }


def main():
    # Gather per-query feature rows
    rows_by_arm: dict[str, list[dict]] = defaultdict(list)
    long_rows: list[list] = [["arm", "query_id", "feature", "value"]]

    for path in RESULTS_DIR.rglob("*.jsonl"):
        try:
            rec = json.loads(path.read_text().splitlines()[-1])
        except Exception:
            continue
        method = rec.get("method", "")
        if not method.startswith("rlm_"):
            continue
        qid = rec.get("query_id", "")
        text = _trace_text(rec.get("benchmark", ""), method, qid)
        feats = count_features(text, method)
        rows_by_arm[method].append(feats)
        for f, v in feats.items():
            long_rows.append([method, qid, f, v])

    if not any(rows_by_arm.values()):
        print("No RLM traces found — run the experiment first.", file=sys.stderr)
        return

    # Adoption + behavioral summary
    summary = aggregate_adoption(rows_by_arm)

    # Cluster separation
    cluster = cluster_separation(rows_by_arm)

    # Write long CSV
    csv_path = RESULTS_DIR / "behavioral.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w") as f:
        w = csv.writer(f)
        w.writerows(long_rows)

    # Write markdown summary
    md_lines = ["# Behavioral analysis (Phase 8b)", "", "## Adoption rates", ""]
    md_lines.append("| Arm | Uses term | Term hits | del | repl blocks | llm_q | rlm_q | batched | trace len | n |")
    md_lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for arm in sorted(summary.keys()):
        s = summary[arm]
        md_lines.append(
            f"| {arm} | "
            f"{s['uses_any_arm_term']['mean']:.2f} | "
            f"{s['n_arm_term_hits']['mean']:.1f} | "
            f"{s['n_del_statements']['mean']:.1f} | "
            f"{s['n_repl_blocks']['mean']:.1f} | "
            f"{s['n_llm_query_calls']['mean']:.1f} | "
            f"{s['n_rlm_query_calls']['mean']:.1f} | "
            f"{s['n_batched_calls']['mean']:.1f} | "
            f"{s['trace_len_chars']['mean']:.0f} | "
            f"{s['uses_any_arm_term']['n']} |"
        )

    md_lines += [
        "",
        "## Cluster separation",
        "",
        f"- Within-arm mean pairwise distance: {cluster['within_mean']:.3f} (n={cluster['within_n']})",
        f"- Between-arm mean pairwise distance: {cluster['between_mean']:.3f} (n={cluster['between_n']})",
        f"- Ratio (between/within): {cluster['ratio']:.2f}   (>1.5 → arms behaviorally distinct)",
        "",
    ]

    md_path = RESULTS_DIR / "behavioral.md"
    md_path.write_text("\n".join(md_lines))

    print(f"Wrote {csv_path}", file=sys.stderr)
    print(f"Wrote {md_path}", file=sys.stderr)
    print("\n".join(md_lines))


if __name__ == "__main__":
    main()
