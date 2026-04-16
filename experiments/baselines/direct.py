"""Baseline 1 — "Direct": a single Sonnet call with the full prompt.

Truncates the prompt if it exceeds Sonnet's 200K-token context (RLM paper
does the same for long-context tasks: Table 1 footnote). We use tiktoken's
cl100k_base as a proxy for Anthropic's tokenizer — good enough for sizing.

Truncation strategy: keep the tail (which usually holds the question) and as
many leading tokens as fit, with a dropped-middle marker.
"""
from __future__ import annotations

import time

import tiktoken

from experiments.baselines._llm import sonnet_call
from experiments.baselines.base import Baseline, RunResult
from experiments.benchmarks.base import Query

# Agent SDK's Claude Code preamble adds ~16K tokens on top of our user msg,
# so we keep the user prompt well under 200K−16K−output. Empirically 150K
# is the largest value that reliably doesn't hit a context-overflow error.
_MAX_INPUT_TOKENS = 150_000
_TOK = tiktoken.get_encoding("cl100k_base")


def _truncate_if_needed(prompt: str) -> tuple[str, int]:
    toks = _TOK.encode(prompt)
    if len(toks) <= _MAX_INPUT_TOKENS:
        return prompt, 0
    # Keep last 20K tokens + first (MAX - 20K - 20) tokens, marker in between
    tail_len = 15_000
    head_len = _MAX_INPUT_TOKENS - tail_len - 20
    head = _TOK.decode(toks[:head_len])
    tail = _TOK.decode(toks[-tail_len:])
    truncated = head + "\n\n[...TRUNCATED...]\n\n" + tail
    dropped = len(toks) - _MAX_INPUT_TOKENS + 20
    return truncated, dropped


class DirectBaseline(Baseline):
    name = "direct"

    def run(self, query: Query) -> RunResult:
        t0 = time.perf_counter()
        prompt, dropped = _truncate_if_needed(query.prompt)
        call = sonnet_call(user=prompt)
        return RunResult(
            benchmark=query.metadata.get("benchmark", "unknown"),
            method=self.name,
            query_id=query.id,
            prediction=call.text,
            duration_sec=time.perf_counter() - t0,
            input_tokens=call.input_tokens,
            output_tokens=call.output_tokens,
            cache_read_tokens=call.cache_read_tokens,
            cache_creation_tokens=call.cache_creation_tokens,
            cost_usd=call.cost_usd,
            num_iterations=1,
            num_subcalls=0,
            extras={"dropped_tokens": dropped},
        )
