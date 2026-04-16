"""Shared types for the 5 benchmark adapters.

Each adapter exposes:
    load_queries(n: int, seed: int) -> list[Query]
    score(prediction: str, query: Query) -> float
    name: str  (class attribute)

Sample sizing is deterministic: a seeded random.sample over a fixed index
list, so the same N queries are seen by all 8 methods (paired design).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Query:
    """One benchmark question.

    Attributes:
        id: Stable identifier for logs — include benchmark prefix, e.g.
            "oolong_trec_coarse::0042".
        prompt: The full user-facing question to feed to an RLM / baseline.
        gold: Reference answer. Type depends on benchmark (str, dict, list).
        context_tokens: Rough token count of the input context, for reporting.
        metadata: Free-form (dataset subset, difficulty tier, etc.).
    """

    id: str
    prompt: str
    gold: Any
    context_tokens: int = 0
    metadata: dict = field(default_factory=dict)


class Benchmark:
    """Base class — subclass to implement a benchmark adapter."""

    name: str = "UNSET"

    def load_queries(self, n: int, seed: int = 2640) -> list[Query]:
        raise NotImplementedError

    def score(self, prediction: str, query: Query) -> float:
        raise NotImplementedError


def seeded_sample(indices: list[int], n: int, seed: int) -> list[int]:
    """Deterministic sample used by all adapters.

    Using a fresh Random instance so we don't perturb global state.
    """
    rng = random.Random(seed)
    if n >= len(indices):
        return list(indices)
    return rng.sample(list(indices), n)


# --------------------- common scoring primitives ---------------------

def _normalize_gold(gold: Any) -> list[str]:
    """Return list of acceptable gold strings.

    OOLONG stores answers as stringified lists ("['World']", "['yes', 'no']").
    Unwrap those to the raw label(s); accept any."""
    if gold is None:
        return []
    if isinstance(gold, list):
        return [str(g).strip().lower() for g in gold if g]
    s = str(gold).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            import ast as _ast
            parsed = _ast.literal_eval(s)
            if isinstance(parsed, (list, tuple)):
                return [str(g).strip().lower() for g in parsed if g]
        except Exception:
            pass
    return [s.lower()]


def exact_match(pred: str, gold: Any) -> float:
    """1.0 if pred stripped/lowercased contains ANY of the gold strings,
    else 0.0. Handles stringified-list OOLONG golds."""
    golds = _normalize_gold(gold)
    if not golds:
        return 0.0
    p = (pred or "").strip().lower()
    for g in golds:
        if p == g or g in p:
            return 1.0
    return 0.0


def tokenized_f1(pred: str, gold: str) -> float:
    """Standard SQuAD-style F1 over whitespace tokens."""
    def toks(s: str) -> list[str]:
        return (s or "").strip().lower().split()

    p_toks = toks(pred)
    g_toks = toks(gold)
    if not p_toks or not g_toks:
        return 0.0

    common: dict[str, int] = {}
    for t in p_toks:
        common[t] = common.get(t, 0) + 1
    overlap = 0
    for t in g_toks:
        if common.get(t, 0) > 0:
            overlap += 1
            common[t] -= 1
    if overlap == 0:
        return 0.0
    precision = overlap / len(p_toks)
    recall = overlap / len(g_toks)
    return 2 * precision * recall / (precision + recall)


def numeric_score(pred: str, gold_num: float, base: float = 0.75) -> float:
    """RLM paper's BrowseComp-style score: base ** |y - ŷ|."""
    import re as _re
    m = _re.search(r"-?\d+(?:\.\d+)?", pred or "")
    if not m:
        return 0.0
    try:
        y_hat = float(m.group())
    except ValueError:
        return 0.0
    return float(base) ** abs(gold_num - y_hat)
