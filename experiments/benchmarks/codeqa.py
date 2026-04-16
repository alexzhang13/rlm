"""LongBench-v2 CodeQA adapter.

Source: `zai-org/LongBench-v2` (THUDM alias works too). 503 total rows.
Filter `domain == "Code"` yields ~50 CodeQA-style examples, matching the
RLM paper's 50-query sample.

Schema: multiple-choice A/B/C/D. Gold is a letter. We score by exact match
on the letter only (ignoring anything else the model says).
"""
from __future__ import annotations

import re

from experiments.benchmarks.base import Benchmark, Query, seeded_sample


_ANSWER_RE = re.compile(r"\b([ABCD])\b")


def _extract_letter(text: str) -> str | None:
    """Pull the first ABCD letter from the model's answer."""
    if not text:
        return None
    m = _ANSWER_RE.search(text.strip().upper())
    return m.group(1) if m else None


class LongBenchCodeQA(Benchmark):
    name = "longbench_codeqa"

    def __init__(self):
        self._cache: list[dict] | None = None

    def _load(self) -> list[dict]:
        if self._cache is not None:
            return self._cache
        from datasets import load_dataset
        ds = load_dataset("zai-org/LongBench-v2", split="train")
        # Actual domain value is "Code Repository Understanding"
        # (research agent's original guess "Code" was wrong).
        filtered = ds.filter(lambda x: x["domain"] == "Code Repository Understanding")
        self._cache = list(filtered)
        return self._cache

    def load_queries(self, n: int = 10, seed: int = 2640) -> list[Query]:
        rows = self._load()
        idx = seeded_sample(list(range(len(rows))), n, seed)
        queries: list[Query] = []
        for i in idx:
            row = rows[i]
            prompt = (
                f"{row['context']}\n\n"
                f"QUESTION: {row['question']}\n\n"
                f"A) {row['choice_A']}\n"
                f"B) {row['choice_B']}\n"
                f"C) {row['choice_C']}\n"
                f"D) {row['choice_D']}\n\n"
                "Respond with ONLY the single letter (A, B, C, or D) of the correct answer."
            )
            queries.append(
                Query(
                    id=f"longbench_codeqa::{row['_id']}",
                    prompt=prompt,
                    gold=row["answer"].strip().upper(),
                    context_tokens=row.get("length", 0) or 0,
                    metadata={
                        "benchmark": self.name,
                        "sub_domain": row.get("sub_domain"),
                        "difficulty": row.get("difficulty"),
                    },
                )
            )
        return queries

    def score(self, prediction: str, query: Query) -> float:
        letter = _extract_letter(prediction)
        if letter is None:
            return 0.0
        return 1.0 if letter == str(query.gold).strip().upper() else 0.0


if __name__ == "__main__":
    import sys
    bench = LongBenchCodeQA()
    qs = bench.load_queries(n=2, seed=2640)
    for q in qs:
        print(f"{q.id} gold={q.gold} prompt_len={len(q.prompt)}")
    print("ok", file=sys.stderr)
