"""OOLONG-Pairs adapter (MultiNLI @ 32K context).

There is no official "pairs" split in oolong-synth. The RLM paper's
"OOLONG-Pairs (20 × 32K)" corresponds to the MultiNLI entries in the main
dataset at context_len=32768 — MultiNLI is inherently pairwise (premise /
hypothesis) and is the only pairwise dataset in OOLONG.

We use 4/20 queries (20% cap per plan), sampled deterministically.
"""
from __future__ import annotations

from experiments.benchmarks.base import Benchmark, Query, exact_match, seeded_sample


class OOLONGPairs(Benchmark):
    name = "oolong_pairs"

    def __init__(self, context_len: int = 32_768):
        self.context_len = context_len
        self._cache: list[dict] | None = None

    def _load(self) -> list[dict]:
        if self._cache is not None:
            return self._cache
        from datasets import load_dataset
        ds = load_dataset("oolongbench/oolong-synth", split="test")
        filtered = ds.filter(
            lambda x: x["dataset"] == "multinli" and x["context_len"] == self.context_len
        )
        self._cache = list(filtered)
        return self._cache

    def load_queries(self, n: int = 4, seed: int = 2640) -> list[Query]:
        rows = self._load()
        idx = seeded_sample(list(range(len(rows))), n, seed)
        queries: list[Query] = []
        for i in idx:
            row = rows[i]
            prompt = (
                f"{row['context_window_text']}\n\n{row['question']}\n\n"
                "Respond with ONLY the required label."
            )
            queries.append(
                Query(
                    id=f"oolong_pairs::{row.get('id', i)}",
                    prompt=prompt,
                    gold=str(row["answer"]).strip(),
                    context_tokens=self.context_len,
                    metadata={
                        "benchmark": self.name,
                        "context_window_id": row.get("context_window_id"),
                        "answer_type": row.get("answer_type"),
                    },
                )
            )
        return queries

    def score(self, prediction: str, query: Query) -> float:
        return exact_match(prediction, str(query.gold))


if __name__ == "__main__":
    import sys
    bench = OOLONGPairs()
    qs = bench.load_queries(n=2, seed=2640)
    for q in qs:
        print(f"{q.id} gold={q.gold!r} prompt_tokens≈{q.context_tokens}")
    print("ok", file=sys.stderr)
