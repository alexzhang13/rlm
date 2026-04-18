"""The 8 methods in our experiment matrix.

Each method exposes a `run(query) -> RunResult` interface matching
baselines.base.Baseline. The RLM arms all use the same RLM scaffold with
a different system prompt suffix appended to RLM_SYSTEM_PROMPT.
"""
from __future__ import annotations

import pathlib
import time

from rlm import RLM
from rlm.utils.prompts import RLM_SYSTEM_PROMPT

from experiments.baselines.base import Baseline, RunResult
from experiments.baselines.codeact_bm25 import CodeActBM25Baseline
from experiments.baselines.direct import DirectBaseline
from experiments.baselines.summary_agent import SummaryAgentBaseline
from experiments.benchmarks.base import Query


PROMPT_DIR = pathlib.Path(__file__).resolve().parent.parent / "prompts"


def _load_arm_suffix(arm: str) -> str:
    """arm in {'A0','A1','A3','A4','A6','A7',...}. Maps to prompts/<arm>_*.txt."""
    name_map = {
        "A0": "A0_vanilla.txt",
        "A1": "A1_lru.txt",
        "A3": "A3_s3fifo.txt",
        "A4": "A4_sieve.txt",
        "A6": "A6_theory.txt",
        "A7": "A7_arc.txt",
        "A8": "A8_tinylfu.txt",
        "A9": "A9_clock.txt",
        "A10": "A10_two_queue.txt",
        "A11": "A11_slru.txt",
        "A12": "A12_victim.txt",
        "A13": "A13_bloom.txt",
        "A14": "A14_prefetch.txt",
        "A15": "A15_oblivious.txt",
        "A16": "A16_cdc.txt",
        "A17": "A17_writeback.txt",
        "A18": "A18_mru.txt",
        "A19": "A19_belady.txt",
        "A20": "A20_lfu.txt",
        "A21": "A21_lirs.txt",
        "A22": "A22_hotcold.txt",
        "A23": "A23_clockpro.txt",
        "A24": "A24_markov.txt",
        "A25": "A25_lruk.txt",
        "A26": "A26_partitioning.txt",
        "A27": "A27_linelocking.txt",
        "A28": "A28_pin_clean.txt",
        "A29": "A29_s3fifo_clean.txt",
        "A30": "A30_one_sentence.txt",
        "A31": "A31_additive_structural.txt",
        "A32": "A32_plan_and_pin.txt",
    }
    return (PROMPT_DIR / name_map[arm]).read_text(encoding="utf-8")


class RLMArm(Baseline):
    """One of the RLM arms — wraps RLM(custom_system_prompt=...).

    RLM's completion() returns an RLMChatCompletion-like object; we extract
    the response + usage and flatten into RunResult.
    """

    def __init__(self, arm: str, max_iterations: int = 10):
        self.arm = arm
        self.name = f"rlm_{arm.lower()}"
        self.max_iterations = max_iterations
        suffix = _load_arm_suffix(arm).strip()
        if suffix:
            self.system_prompt = RLM_SYSTEM_PROMPT + "\n\n---\n\n" + suffix
        else:
            self.system_prompt = RLM_SYSTEM_PROMPT

    def run(self, query: Query) -> RunResult:
        t0 = time.perf_counter()
        try:
            rlm = RLM(
                backend="agent_sdk",
                backend_kwargs={"model_name": "claude-sonnet-4-6"},
                environment="local",
                max_iterations=self.max_iterations,
                custom_system_prompt=self.system_prompt,
                verbose=False,
            )
            result = rlm.completion(query.prompt)
            prediction = str(result.response or "")

            # Pull token/cost aggregates
            usage_by_model = result.usage_summary.model_usage_summaries or {}
            in_tok = sum(u.total_input_tokens for u in usage_by_model.values())
            out_tok = sum(u.total_output_tokens for u in usage_by_model.values())
            cost = sum((u.total_cost or 0.0) for u in usage_by_model.values())

            return RunResult(
                benchmark=query.metadata.get("benchmark", "unknown"),
                method=self.name,
                query_id=query.id,
                prediction=prediction,
                duration_sec=time.perf_counter() - t0,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cache_read_tokens=0,  # RLM's UsageSummary rolls cache into input
                cache_creation_tokens=0,
                cost_usd=cost,
                num_iterations=getattr(result, "num_iterations", 0) or 0,
                num_subcalls=getattr(result, "num_subcalls", 0) or 0,
                extras={"arm": self.arm},
            )
        except Exception as e:
            return RunResult(
                benchmark=query.metadata.get("benchmark", "unknown"),
                method=self.name,
                query_id=query.id,
                prediction="",
                duration_sec=time.perf_counter() - t0,
                error=f"{type(e).__name__}: {e}",
                extras={"arm": self.arm},
            )


def all_methods() -> list[Baseline]:
    """Return the 8 methods in Table 1 order."""
    return [
        DirectBaseline(),
        SummaryAgentBaseline(),
        CodeActBM25Baseline(),
        RLMArm("A0"),
        RLMArm("A1"),
        RLMArm("A3"),
        RLMArm("A4"),
        RLMArm("A6"),
        RLMArm("A7"),
        RLMArm("A8"),
        RLMArm("A9"),
        RLMArm("A10"),
        RLMArm("A11"),
        RLMArm("A12"),
        RLMArm("A13"),
        RLMArm("A14"),
        RLMArm("A15"),
        RLMArm("A16"),
        RLMArm("A17"),
        RLMArm("A18"),
        RLMArm("A19"),
        RLMArm("A20"),
        RLMArm("A21"),
        RLMArm("A22"),
        RLMArm("A23"),
        RLMArm("A24"),
        RLMArm("A25"),
        RLMArm("A26"),
        RLMArm("A27"),
        RLMArm("A28"),
        RLMArm("A29"),
        RLMArm("A30"),
        RLMArm("A31"),
        RLMArm("A32"),
    ]


def method_by_name(name: str) -> Baseline:
    """Look up by method name — "direct", "summary_agent", "codeact_bm25",
    "rlm_a0" / "rlm_a1" / "rlm_a3" / "rlm_a4" / "rlm_a6"."""
    for m in all_methods():
        if m.name == name:
            return m
    raise ValueError(f"Unknown method: {name}")
