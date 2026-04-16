"""OOLONG adapter.

Source: `oolongbench/oolong-synth` on HuggingFace.

Note — the RLM paper's "OOLONG trec_coarse" row doesn't match the public
dataset: oolong-synth contains agnews/app_reviews/formality/imdb/metaphors/
multinli/negation/yahoo, not trec_coarse. We substitute `agnews` (4-way
coarse-grained news topic classification) as the closest in-spirit task —
same type (LABEL), similar category count (4 vs TREC-coarse 6), same 131K
context length. This substitution is noted in the report's Limitations.

Filter: dataset == "agnews" AND context_len == 131072.
Paper-level: 2 context windows × 25 questions each = 50 at this length.

Fields we use:
    context_window_text + "\n" + question   — input to model
    answer                                    — gold label string
"""
from __future__ import annotations

from experiments.benchmarks.base import Benchmark, Query, exact_match, seeded_sample


class OOLONGAGNews(Benchmark):
    name = "oolong_agnews"

    def __init__(self, context_len: int = 131_072):
        self.context_len = context_len
        self._cache: list[dict] | None = None

    def _load(self) -> list[dict]:
        if self._cache is not None:
            return self._cache
        from datasets import load_dataset
        ds = load_dataset("oolongbench/oolong-synth", split="test")
        filtered = ds.filter(
            lambda x: x["dataset"] == "agnews" and x["context_len"] == self.context_len
        )
        self._cache = list(filtered)
        return self._cache

    def load_queries(self, n: int = 10, seed: int = 2640) -> list[Query]:
        rows = self._load()
        idx = seeded_sample(list(range(len(rows))), n, seed)
        queries: list[Query] = []
        for i in idx:
            row = rows[i]
            prompt = (
                f"{row['context_window_text']}\n\n{row['question']}\n\n"
                "Respond with ONLY the single-word class label, nothing else."
            )
            queries.append(
                Query(
                    id=f"oolong_agnews::{row.get('id', i)}",
                    prompt=prompt,
                    gold=str(row["answer"]).strip(),
                    context_tokens=self.context_len,
                    metadata={
                        "benchmark": self.name,
                        "context_window_id": row.get("context_window_id"),
                        "task": row.get("task"),
                        "answer_type": row.get("answer_type"),
                    },
                )
            )
        return queries

    def score(self, prediction: str, query: Query) -> float:
        return exact_match(prediction, str(query.gold))


if __name__ == "__main__":
    import sys
    bench = OOLONGAGNews()
    qs = bench.load_queries(n=2, seed=2640)
    for q in qs:
        print(f"{q.id} gold={q.gold!r} tokens≈{q.context_tokens} prompt_chars={len(q.prompt)}")
    print("ok", file=sys.stderr)
