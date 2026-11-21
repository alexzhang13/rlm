"""Measure spec-ptc with scripted models and controlled latency (no API key/cost).

Python 3.12+: uv run --python 3.12 --extra spec-ptc python examples/spec_ptc_example.py
The actual RLM loop, spec-ptc library, REPLs, and LM socket calls all run.
Only model generation and model answers are simulated.
"""

import argparse
import asyncio
import json
import statistics
import threading
import time
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from rlm import RLM
from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary
from rlm.logger import RLMLogger


def repl(body):
    return "```repl\n" + body + "\n```\n"


SCRIPTS = {
    "independent": repl(
        "a = llm_query('one')\nb = llm_query('two')\n"
        "answer['content'] = a + b\nanswer['ready'] = True"
    ),
    "batched": repl(
        "answers = llm_query_batched(['one', 'two', 'three', 'four'])\n"
        "answer['content'] = '|'.join(answers)\nanswer['ready'] = True"
    ),
    "large_batch": repl(
        "answers = llm_query_batched(" + repr([f"item-{i}" for i in range(20)]) + ")\n"
        "answer['content'] = '|'.join(answers)\nanswer['ready'] = True"
    ),
    "long_context": repl(
        "prompts = [str(i) + ':' + 'x' * 100000 for i in range(8)]\n"
        "answers = llm_query_batched(prompts)\n"
        "answer['content'] = str(len(answers))\nanswer['ready'] = True"
    ),
    "dependent": repl(
        "a = llm_query('one')\nb = llm_query(a)\nanswer['content'] = b\nanswer['ready'] = True"
    ),
    "no_tools": repl("answer['content'] = str(sum(range(100)))\nanswer['ready'] = True"),
    "discarded": "```repl\nx = llm_query('unused')\n# unfinished\n# still generating\n# no closing fence\n",  # no closing fence, never executed
    "recursive": repl(
        "x = rlm_query('child-task', context='child-data')\n"
        "answer['content'] = x\nanswer['ready'] = True"
    ),
}


class DemoLM(BaseLM):
    supports_streaming = True

    def __init__(self, model_name, workload):
        super().__init__(model_name=model_name)
        self.workload = workload
        self.calls = 0

    def begin_call(self, prompt):
        self.calls += 1
        with self.workload.lock:
            self.workload.calls[self.model_name] += 1
        if not isinstance(prompt, list):
            return None
        if "child-task" in prompt[1]["content"]:
            return SCRIPTS["independent"]
        if self.workload.scenario == "discarded" and self.calls > 1:
            return repl("answer['content'] = 'done'\nanswer['ready'] = True")
        return SCRIPTS[self.workload.scenario]

    def completion(self, prompt, model=None):
        script = self.begin_call(prompt)
        if script is not None:
            time.sleep(self.workload.token_delay * len(script.splitlines()))
            return script
        time.sleep(self.workload.tool_delay)
        return f"result:{prompt[:40]}"

    async def acompletion(self, prompt, model=None):
        self.begin_call(prompt)
        await asyncio.sleep(self.workload.tool_delay)
        return f"result:{prompt[:40]}"

    def stream_completion(self, prompt, model=None):
        script = self.begin_call(prompt)
        if script is None:
            time.sleep(self.workload.tool_delay)
            yield f"result:{prompt[:40]}"
            return
        for line in script.splitlines(keepends=True):
            time.sleep(self.workload.token_delay)
            yield line

    def get_usage_summary(self):
        return UsageSummary({self.model_name: ModelUsageSummary(self.calls, 0, 0)})

    def get_last_usage(self):
        return ModelUsageSummary(1, 0, 0)


class Workload:
    def __init__(self, scenario, token_delay, tool_delay, spec_inflight_chars=120_000):
        self.scenario = scenario
        self.token_delay = token_delay
        self.tool_delay = tool_delay
        self.calls = Counter()
        self.lock = threading.Lock()
        self.speculation = []
        self.spec_inflight_chars = spec_inflight_chars

    def client(self, backend, kwargs):
        return DemoLM(kwargs["model_name"], self)

    def run(self, mode):
        start = time.perf_counter()
        with (
            patch("rlm.core.rlm.get_client", side_effect=self.client),
            RLM(
                backend_kwargs={"model_name": "root"},
                other_backends=["openai"],
                other_backend_kwargs=[{"model_name": "worker"}],
                stream=mode == "stream",
                experimental_spec_ptc=mode == "spec-ptc",
                environment_kwargs={
                    "speculation_observer": self.speculation.append,
                    "spec_max_inflight_chars": self.spec_inflight_chars,
                }
                if mode == "spec-ptc"
                else {},
                max_depth=2 if self.scenario == "recursive" else 1,
                max_iterations=2,
                logger=RLMLogger(),
                orchestrator=False,
            ) as rlm,
        ):
            result = rlm.completion("demo context", root_prompt="Run the scripted workload")
        return {
            "scenario": self.scenario,
            "mode": mode,
            "wall_s": time.perf_counter() - start,
            "active_s": sum(turn["iteration_time"] for turn in result.metadata["iterations"]),
            "calls": dict(self.calls),
            "dispatch": sum(m["dispatch"] for m in self.speculation),
            "hits": sum(m["claim_hit"] for m in self.speculation),
            "evicted": sum(m["evict"] for m in self.speculation),
            "answer": result.response,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-inflight-chars", type=int, default=120_000)
    parser.add_argument("--scenario", choices=list(SCRIPTS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--token-delay", type=float, default=0.04, help="Seconds per emitted line")
    parser.add_argument("--tool-delay", type=float, default=0.15)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []
    print("Controlled latency simulation; timings are not a real-provider performance claim.")
    print(
        f"{'workload':<14} {'mode':<10} {'active(s)':>10} {'wall(s)':>10} {'LM calls':>9} {'hits':>5} {'evicted':>7}"
    )
    for scenario in [args.scenario] if args.scenario else SCRIPTS:
        answers = set()
        for mode in ("blocking", "stream", "spec-ptc"):
            samples = [
                Workload(scenario, args.token_delay, args.tool_delay, args.spec_inflight_chars).run(
                    mode
                )
                for _ in range(args.repeats)
            ]
            answers.update(sample["answer"] for sample in samples)
            row = samples[0] | {
                "active_s": statistics.median(sample["active_s"] for sample in samples),
                "wall_s": statistics.median(sample["wall_s"] for sample in samples),
                "repeats": args.repeats,
            }
            rows.append(row)
            print(
                f"{scenario:<14} {mode:<10} {row['active_s']:>10.3f} {row['wall_s']:>10.3f} "
                f"{sum(row['calls'].values()):>9} {row['hits']:>5} {row['evicted']:>7}",
                flush=True,
            )
        assert len(answers) == 1, f"Outputs diverged for {scenario}: {answers}"
    if args.output:
        args.output.write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
