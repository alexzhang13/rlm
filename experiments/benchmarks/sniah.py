"""S-NIAH (Short Needle-in-a-Haystack) — synthetic generator.

RULER's S-NIAH task: inject a single "SECRET KEY IS <n>" line into a haystack
of filler sentences, then ask the model to retrieve the secret.

The RLM paper reports 50 queries spread across context lengths 2K, 4K, 8K,
16K, 32K, 64K, 128K, 256K, 512K, 1M tokens. We match that distribution but
with n=10 total (one per length tier, skipping the largest two to keep
total cost low) plus two repeats at the two tiers where the baseline most
struggles (adjustable).

No HuggingFace dep — fully synthetic, seeded deterministic.
"""
from __future__ import annotations

import random
import string

import tiktoken

from experiments.benchmarks.base import Benchmark, Query, exact_match

# Sentences per chunk chosen so 1 sentence ≈ 15 tokens (cl100k_base).
_FILLER_VOCAB = (
    "the quick brown fox jumps over a lazy dog while contemplating existence "
    "amid scattered leaves drifting across a quiet autumn meadow".split()
)

_DEFAULT_LENGTH_TIERS = [2_000, 4_000, 8_000, 16_000, 32_000, 64_000, 131_072, 262_144]


def _filler_sentence(rng: random.Random) -> str:
    return " ".join(rng.choices(_FILLER_VOCAB, k=12)) + "."


def _haystack_at_token_length(rng: random.Random, target_tokens: int, enc) -> str:
    """Build a filler haystack of ~target_tokens cl100k tokens."""
    parts: list[str] = []
    total = 0
    while total < target_tokens:
        chunk = " ".join(_filler_sentence(rng) for _ in range(50))
        parts.append(chunk)
        total += len(enc.encode(chunk))
    text = " ".join(parts)
    # Trim back to target length by truncating tokens
    toks = enc.encode(text)
    if len(toks) > target_tokens:
        text = enc.decode(toks[:target_tokens])
    return text


def _inject(haystack: str, needle: str, rng: random.Random) -> str:
    words = haystack.split()
    insert_pos = rng.randrange(len(words) // 3, 2 * len(words) // 3)
    return " ".join(words[:insert_pos] + [needle] + words[insert_pos:])


class SNIAH(Benchmark):
    name = "sniah"

    def __init__(self, length_tiers: list[int] | None = None):
        self.length_tiers = length_tiers or _DEFAULT_LENGTH_TIERS
        self.enc = tiktoken.get_encoding("cl100k_base")

    def load_queries(self, n: int = 10, seed: int = 2640) -> list[Query]:
        """Generate n S-NIAH queries, rotating through the length tiers.

        Queries are deterministic w.r.t. (n, seed) — same inputs produce the
        same queries.
        """
        rng = random.Random(seed)
        queries: list[Query] = []
        for i in range(n):
            tier = self.length_tiers[i % len(self.length_tiers)]
            # Per-query RNG seeded from (seed, i) so each query is stable
            # whether we request 3 or 30 of them.
            q_rng = random.Random(f"sniah:{seed}:{i}:{tier}")
            secret = q_rng.randint(10_000_000, 99_999_999)
            needle = f"SECRET_KEY_IS_{secret}"
            haystack = _haystack_at_token_length(q_rng, tier, self.enc)
            haystack = _inject(haystack, needle, q_rng)
            prompt = (
                "The context contains lines of random text with exactly one "
                "line matching the pattern SECRET_KEY_IS_<digits>. Find and "
                "return ONLY the numeric value.\n\n"
                f"{haystack}"
            )
            queries.append(
                Query(
                    id=f"sniah::tier{tier}::i{i}",
                    prompt=prompt,
                    gold=str(secret),
                    context_tokens=tier,
                    metadata={"tier": tier},
                )
            )
        return queries

    def score(self, prediction: str, query: Query) -> float:
        return exact_match(prediction, str(query.gold))


# CLI smoke — python -m experiments.benchmarks.sniah
if __name__ == "__main__":
    import sys

    bench = SNIAH(length_tiers=[2_000, 4_000])
    qs = bench.load_queries(n=2, seed=2640)
    for q in qs:
        print(
            f"{q.id} tier={q.metadata['tier']} "
            f"gold={q.gold} prompt_len={len(q.prompt)} "
            f"actual_tokens≈{len(bench.enc.encode(q.prompt))}"
        )
        # sanity check scoring
        right = bench.score(str(q.gold), q)
        wrong = bench.score("999", q)
        print(f"  score(right)={right:.2f} score(wrong)={wrong:.2f}")
    print("ok", file=sys.stderr)
