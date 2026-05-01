"""Phase 8a — quantitative aggregation.

Reads every results/{benchmark}/{method}/{query_id}.jsonl and produces:
  - results/summary.csv      (long format: benchmark, method, query_id, score, cost, dur)
  - results/table1.md        (markdown Table 1 — methods × benchmarks)
  - results/table1.tex       (LaTeX version for the report)
  - paired bootstrap confidence intervals (arm vs A0) printed to stderr

Usage:
    uv run python -m experiments.analysis.aggregate
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import random
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass

RESULTS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "results"


METHOD_ORDER = [
    "direct",
    "summary_agent",
    "codeact_bm25",
    "rlm_a0",
    "rlm_a1",
    "rlm_a3",
    "rlm_a4",
    "rlm_a6",
    "rlm_a7",
    "rlm_a8",
    "rlm_a9",
    "rlm_a10",
    "rlm_a11",
    "rlm_a12",
    "rlm_a13",
    "rlm_a14",
    "rlm_a15",
    "rlm_a16",
    "rlm_a17",
    "rlm_a18",
    "rlm_a19",
    "rlm_a20",
    "rlm_a21",
    "rlm_a22",
    "rlm_a23",
    "rlm_a24",
    "rlm_a25",
    "rlm_a26",
    "rlm_a27",
    "rlm_a28",
    "rlm_a29",
    "rlm_a30",
    "rlm_a31",
    "rlm_a32",
]

BENCHMARK_ORDER = [
    "sniah",
    "longbench_codeqa",
    "oolong_pairs",
]


@dataclass
class Row:
    benchmark: str
    method: str
    query_id: str
    score: float | None
    cost_usd: float
    duration_sec: float
    input_tokens: int
    output_tokens: int
    prediction: str
    error: str | None


def load_all() -> list[Row]:
    rows: list[Row] = []
    for path in RESULTS_DIR.rglob("*.jsonl"):
        try:
            rec = json.loads(path.read_text().splitlines()[-1])
        except Exception:
            continue
        rows.append(
            Row(
                benchmark=rec.get("benchmark", ""),
                method=rec.get("method", ""),
                query_id=rec.get("query_id", ""),
                score=rec.get("score"),
                cost_usd=float(rec.get("cost_usd", 0.0) or 0.0),
                duration_sec=float(rec.get("duration_sec", 0.0) or 0.0),
                input_tokens=int(rec.get("input_tokens", 0) or 0),
                output_tokens=int(rec.get("output_tokens", 0) or 0),
                prediction=str(rec.get("prediction", "")),
                error=rec.get("error"),
            )
        )
    return rows


def _mean_std(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    m = statistics.mean(xs)
    s = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return m, s


def aggregate_cells(rows: list[Row]) -> dict:
    """cells[benchmark][method] = {score_mean, score_std, cost_mean, cost_std, n}"""
    by: dict[str, dict[str, list[Row]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r.benchmark][r.method].append(r)
    cells: dict = {}
    for bench, method_rows in by.items():
        cells[bench] = {}
        for method, rs in method_rows.items():
            scores = [r.score for r in rs if r.score is not None]
            costs = [r.cost_usd for r in rs]
            sm, ss = _mean_std(scores)
            cm, cs = _mean_std(costs)
            cells[bench][method] = {
                "score_mean": sm,
                "score_std": ss,
                "cost_mean": cm,
                "cost_std": cs,
                "n": len(rs),
                "n_errors": sum(1 for r in rs if r.error),
            }
    return cells


def render_markdown(cells: dict) -> str:
    lines = ["| Method | " + " | ".join(BENCHMARK_ORDER) + " |"]
    lines.append("|" + "---|" * (len(BENCHMARK_ORDER) + 1))
    for method in METHOD_ORDER:
        cell_strs = []
        for bench in BENCHMARK_ORDER:
            c = cells.get(bench, {}).get(method)
            if c is None or c["n"] == 0:
                cell_strs.append("-")
                continue
            cell_strs.append(
                f"{c['score_mean']:.2f} (${c['cost_mean']:.3f}±${c['cost_std']:.3f})"
            )
        lines.append(f"| {method} | " + " | ".join(cell_strs) + " |")
    return "\n".join(lines)


def render_latex(cells: dict) -> str:
    header = "\\begin{tabular}{l" + "r" * len(BENCHMARK_ORDER) + "}\n\\toprule\n"
    header += "Method & " + " & ".join(b.replace("_", " ") for b in BENCHMARK_ORDER) + " \\\\\n\\midrule\n"
    body = ""
    for method in METHOD_ORDER:
        cells_str = []
        for bench in BENCHMARK_ORDER:
            c = cells.get(bench, {}).get(method)
            if c is None or c["n"] == 0:
                cells_str.append("--")
            else:
                cells_str.append(
                    f"{c['score_mean']:.2f} ($\\$ {c['cost_mean']:.3f} \\pm \\$ {c['cost_std']:.3f}$)"
                )
        body += method.replace("_", "\\_") + " & " + " & ".join(cells_str) + " \\\\\n"
    return header + body + "\\bottomrule\n\\end{tabular}\n"


def write_long_csv(rows: list[Row], out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "benchmark", "method", "query_id", "score", "cost_usd",
                "duration_sec", "input_tokens", "output_tokens", "error",
            ]
        )
        for r in rows:
            w.writerow(
                [r.benchmark, r.method, r.query_id, r.score, r.cost_usd,
                 r.duration_sec, r.input_tokens, r.output_tokens, r.error or ""]
            )


def paired_bootstrap(
    rows: list[Row],
    baseline_method: str = "rlm_a0",
    n_resamples: int = 10_000,
    seed: int = 2640,
) -> dict:
    """For each (benchmark, arm) vs baseline_method, compute a 95% CI on the
    paired score difference via bootstrap over queries seen by both."""
    by = defaultdict(dict)  # (bench, method) -> qid -> score
    for r in rows:
        if r.score is None:
            continue
        by[(r.benchmark, r.method)][r.query_id] = r.score
    rng = random.Random(seed)
    result: dict = {}
    benches = sorted({k[0] for k in by.keys()})
    for bench in benches:
        baseline = by.get((bench, baseline_method), {})
        for method in METHOD_ORDER:
            if method == baseline_method:
                continue
            other = by.get((bench, method), {})
            shared = sorted(set(baseline) & set(other))
            if len(shared) < 2:
                continue
            diffs = [other[q] - baseline[q] for q in shared]
            boot_means: list[float] = []
            for _ in range(n_resamples):
                sample = [diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))]
                boot_means.append(sum(sample) / len(sample))
            boot_means.sort()
            lo = boot_means[int(0.025 * len(boot_means))]
            hi = boot_means[int(0.975 * len(boot_means))]
            mean = sum(diffs) / len(diffs)
            result[(bench, method)] = {"mean": mean, "lo": lo, "hi": hi, "n": len(shared)}
    return result


def main():
    rows = load_all()
    if not rows:
        print("No results yet — run the experiment first.", file=sys.stderr)
        return
    print(f"Loaded {len(rows)} result rows", file=sys.stderr)

    cells = aggregate_cells(rows)

    # Write outputs
    md_path = RESULTS_DIR / "table1.md"
    tex_path = RESULTS_DIR / "table1.tex"
    csv_path = RESULTS_DIR / "summary.csv"
    md_path.write_text(render_markdown(cells) + "\n")
    tex_path.write_text(render_latex(cells))
    write_long_csv(rows, csv_path)
    print(f"Wrote {md_path}, {tex_path}, {csv_path}", file=sys.stderr)

    # Paired bootstrap vs A0
    print("\nPaired bootstrap (arm − rlm_a0), 95% CI:", file=sys.stderr)
    boot = paired_bootstrap(rows)
    for (bench, method), d in sorted(boot.items()):
        print(
            f"  {bench:20s} {method:15s} Δ={d['mean']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}] (n={d['n']})",
            file=sys.stderr,
        )

    # Print the table to stdout for convenience
    print(render_markdown(cells))


if __name__ == "__main__":
    main()
