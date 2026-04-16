"""Shared types for the 3 non-RLM baselines.

Each baseline exposes:
    run(query: Query) -> RunResult

The runner logs `RunResult` fields to JSONL in the same shape as RLM logs,
so aggregation can pool across methods.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from experiments.benchmarks.base import Query


@dataclass
class RunResult:
    """Outcome of running one method on one query.

    Intentionally flat so JSONL lines aggregate easily. `extras` holds
    method-specific detail (e.g. number of summary rounds).
    """

    benchmark: str
    method: str
    query_id: str
    prediction: str
    duration_sec: float
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: float = 0.0
    num_iterations: int = 0
    num_subcalls: int = 0
    score: float | None = None  # filled in by runner using benchmark.score
    error: str | None = None
    extras: dict = field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class Baseline:
    """Base class for non-RLM methods."""

    name: str = "UNSET"

    def run(self, query: Query) -> RunResult:
        raise NotImplementedError
