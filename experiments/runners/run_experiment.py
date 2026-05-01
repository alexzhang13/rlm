"""Main experiment orchestrator.

For each (benchmark, method, query), run the method on the query and log
a JSONL line to results/{benchmark}/{method}/{query_id}.jsonl.

Invocation:

    uv run python -m experiments.runners.run_experiment --pilot
    uv run python -m experiments.runners.run_experiment --full
    uv run python -m experiments.runners.run_experiment --benchmark sniah --method rlm_a0 --n 1
    uv run python -m experiments.runners.run_experiment --benchmark sniah --method all --n 3

JSONL files are append-only; re-runs skip queries that already have a
result unless --overwrite is passed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import traceback

from experiments.baselines.base import RunResult
from experiments.benchmarks.base import Benchmark, Query
from experiments.benchmarks.browsecomp_plus import BrowseCompPlus1K
from experiments.benchmarks.codeqa import LongBenchCodeQA
from experiments.benchmarks.oolong import OOLONGAGNews
from experiments.benchmarks.oolong_pairs import OOLONGPairs
from experiments.benchmarks.sniah import SNIAH
from experiments.runners.methods import all_methods, method_by_name


RESULTS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "results"


# 2026-04-16 scope change #2: BrowseComp+ dropped from the pilot matrix.
# Agent SDK CLI has an undocumented stdin-line-length cap that kills the
# subprocess (exit 1, no stderr) on any single-call prompt > ~40K tokens,
# even with max_buffer_size=16MB. BrowseComp+ 100-doc = 400K tokens, way
# over. Revisit by either (a) routing BrowseComp+ via anthropic.Anthropic
# fallback with a real API key, or (b) forcing RLM's own chunking so the
# large prompt never goes in one single LM call. Leaving the adapter in
# the repo for the report/appendix.
BENCHMARK_REGISTRY: dict[str, tuple[type[Benchmark], dict]] = {
    "sniah": (SNIAH, {}),
    "longbench_codeqa": (LongBenchCodeQA, {}),
    "oolong_pairs": (OOLONGPairs, {}),
    "oolong_agnews": (OOLONGAGNews, {}),
}


# Locked sample sizes per the plan
PILOT_N = {b: 3 for b in BENCHMARK_REGISTRY}
FULL_N = {
    "sniah": 10,
    "longbench_codeqa": 10,
    "oolong_pairs": 4,
    "oolong_agnews": 4,
}


def _results_path(benchmark: str, method: str, query_id: str) -> pathlib.Path:
    safe = query_id.replace("/", "_").replace(":", "_")
    return RESULTS_DIR / benchmark / method / f"{safe}.jsonl"


def _already_done(path: pathlib.Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def _write_result(path: pathlib.Path, result: RunResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(result.to_jsonl() + "\n")


def _run_with_timeout(method, q: Query, timeout_s: float) -> RunResult:
    """Run method.run(q) on a background thread with a hard deadline.

    If it doesn't return in `timeout_s`, we stop waiting and record a
    timeout error. The underlying worker may keep running (can't cleanly
    kill a blocking Agent SDK subprocess from here), but future cells
    continue on a new call path.
    """
    import threading
    slot: dict = {}

    def worker():
        try:
            slot["result"] = method.run(q)
        except Exception as e:  # noqa: BLE001
            slot["error"] = f"{type(e).__name__}: {e}"

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        return RunResult(
            benchmark=q.metadata.get("benchmark", "unknown"),
            method=method.name,
            query_id=q.id,
            prediction="",
            duration_sec=timeout_s,
            error=f"TIMEOUT after {timeout_s:.0f}s",
        )
    if "error" in slot:
        return RunResult(
            benchmark=q.metadata.get("benchmark", "unknown"),
            method=method.name,
            query_id=q.id,
            prediction="",
            duration_sec=0.0,
            error=slot["error"],
        )
    return slot["result"]


def _run_one(method, benchmark, q: Query, overwrite: bool, timeout_s: float) -> tuple[str, float | None]:
    out = _results_path(benchmark.name, method.name, q.id)
    if _already_done(out) and not overwrite:
        try:
            rec = json.loads(out.read_text().splitlines()[-1])
            return "skip", rec.get("score")
        except Exception:
            return "skip", None
    try:
        result = _run_with_timeout(method, q, timeout_s=timeout_s)
        if result.error is None:
            result.score = benchmark.score(result.prediction, q)
    except Exception as e:
        traceback.print_exc()
        result = RunResult(
            benchmark=benchmark.name,
            method=method.name,
            query_id=q.id,
            prediction="",
            duration_sec=0.0,
            error=f"{type(e).__name__}: {e}",
        )
    _write_result(out, result)
    return "ok" if result.error is None else "err", result.score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--benchmark", default=None, help="specific benchmark, or all")
    parser.add_argument("--method", default=None, help="specific method, or all")
    parser.add_argument("--n", type=int, default=None, help="override sample count")
    parser.add_argument("--seed", type=int, default=2640)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--cell-timeout", type=float, default=1200.0,
        help="max seconds for one (method, query) cell (default 480)",
    )
    args = parser.parse_args()

    if args.pilot:
        n_map = PILOT_N
    elif args.full:
        n_map = FULL_N
    else:
        if args.n is None:
            parser.error("Specify --pilot, --full, or --n")
        n_map = {b: args.n for b in BENCHMARK_REGISTRY}

    # Filter to requested benchmarks/methods
    benchmarks = (
        [args.benchmark] if args.benchmark and args.benchmark != "all"
        else list(BENCHMARK_REGISTRY.keys())
    )
    if args.method and args.method != "all":
        methods = [method_by_name(args.method)]
    else:
        methods = all_methods()

    # Load queries per benchmark once
    query_sets: dict[str, tuple[Benchmark, list[Query]]] = {}
    for bname in benchmarks:
        if bname not in BENCHMARK_REGISTRY:
            print(f"  skip unknown benchmark: {bname}", file=sys.stderr)
            continue
        bench_cls, kwargs = BENCHMARK_REGISTRY[bname]
        bench = bench_cls(**kwargs)
        n = args.n if args.n is not None else n_map[bname]
        print(f"[{bname}] loading {n} queries…", file=sys.stderr)
        qs = bench.load_queries(n=n, seed=args.seed)
        # Tag queries with benchmark name in metadata (used by RunResult)
        for q in qs:
            q.metadata.setdefault("benchmark", bench.name)
        query_sets[bname] = (bench, qs)

    # Run matrix
    grand_start = time.perf_counter()
    total = sum(len(qs) for (_, qs) in query_sets.values()) * len(methods)
    done = 0
    print(f"=== Running {total} (benchmark × method × query) cells ===", file=sys.stderr)
    for bname, (bench, qs) in query_sets.items():
        for method in methods:
            for q in qs:
                t0 = time.perf_counter()
                status, score = _run_one(
                    method, bench, q,
                    overwrite=args.overwrite, timeout_s=args.cell_timeout,
                )
                done += 1
                elapsed = time.perf_counter() - t0
                print(
                    f"[{done}/{total}] {bname} × {method.name} × {q.id} "
                    f"→ {status} score={score} ({elapsed:.1f}s)",
                    file=sys.stderr,
                    flush=True,
                )
    grand = time.perf_counter() - grand_start
    print(f"=== Done in {grand:.1f}s ({grand/60:.1f}m) ===", file=sys.stderr)


if __name__ == "__main__":
    main()
