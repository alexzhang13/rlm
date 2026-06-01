import ast
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from datasets import load_dataset
from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv(Path.cwd() / ".env")

QUESTION_INSTRUCTION = (
    "The context contains thousands of general-knowledge questions, one per "
    "line. Each line has a User ID and a question, and each question's answer "
    "falls into one of 6 categories: 'numeric value', 'entity', 'location', "
    "'description and abstract concept', 'abbreviation', 'human being'. "
    "Answer the following aggregate question."
)
COMPARISON_PHRASES = ("more common than", "less common than", "same frequency as")


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def find_comparison_phrase(output: str) -> str | None:
    out_low = output.lower()
    hits = [(out_low.rfind(phrase), phrase) for phrase in COMPARISON_PHRASES if phrase in out_low]
    return max(hits)[1] if hits else None


def attempt_answer_parse(answer: str) -> str:
    comparison = find_comparison_phrase(answer)
    if comparison is not None:
        return comparison
    if ":" not in answer:
        return answer if len(answer) < 20 else answer.split()[-1]
    candidate = answer.split(":")[-1].strip().replace("*", "").replace("[", "").replace("]", "")
    return candidate if len(candidate) < 20 else candidate


def score(example: dict[str, Any], output: str) -> float:
    answer = str(example.get("answer", ""))
    try:
        if "datetime" in answer:
            gold = datetime.strptime(answer, "[datetime.date(%Y, %m, %d)]")
        else:
            gold = ast.literal_eval(answer)[0]
    except Exception:
        gold = answer

    trimmed = attempt_answer_parse(output)
    gold_s = str(gold)
    if str(trimmed) == gold_s or str(trimmed).lower() == gold_s.lower():
        return 1.0

    if example.get("answer_type") == "ANSWER_TYPE.NUMERIC":
        try:
            return 0.75 ** abs(int(gold) - int(trimmed))
        except Exception:
            return 0.0

    if gold_s and gold_s.lower() not in [p.lower() for p in COMPARISON_PHRASES]:
        if gold_s.lower() in output.lower():
            return 1.0
    return 0.0


def load_examples(num_examples: int, context_len: int) -> list[dict[str, Any]]:
    log(f"Loading {num_examples} OOLONG trec_coarse examples at context_len={context_len}")
    stream = load_dataset("oolongbench/oolong-synth", split="validation", streaming=True)
    examples = []
    for example in stream:
        if example.get("dataset") == "trec_coarse" and example.get("context_len") == context_len:
            examples.append(example)
            log(f"loaded example {len(examples)}/{num_examples}: id={example.get('id')}")
            if len(examples) >= num_examples:
                break
    return examples


def extract_adaptive_stats(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None
    latest = None
    for iteration in metadata.get("iterations", []):
        for block in iteration.get("code_blocks", []):
            locals_snapshot = block.get("result", {}).get("locals", {})
            if "adaptive_metrics" in locals_snapshot:
                latest = locals_snapshot["adaptive_metrics"]
    return latest


def run_one(
    example: dict[str, Any],
    adaptive: bool,
    model: str,
    sub_model: str | None,
    verbose: bool,
) -> dict[str, Any]:
    mode = "adaptive" if adaptive else "vanilla"
    context = example.get("context_window_text", example.get("context", ""))
    root_prompt = f"{QUESTION_INSTRUCTION}\n\nQuestion: {example['question']}"
    sampling_args = {"max_tokens": 4096, "reasoning_effort": "none"}

    logger = RLMLogger(log_dir=f"./logs/oolong_{mode}", file_name=f"oolong_{mode}")
    kwargs: dict[str, Any] = {}
    if sub_model and sub_model != model:
        kwargs["other_backends"] = ["openai"]
        kwargs["other_backend_kwargs"] = [{"model_name": sub_model}]

    rlm = RLM(
        backend="openai",
        backend_kwargs={"model_name": model},
        environment="local",
        max_depth=1,
        max_iterations=12,
        max_concurrent_subcalls=16,
        sampling_args=sampling_args,
        sub_sampling_args=sampling_args,
        logger=logger,
        verbose=verbose,
        adaptive=adaptive,
        adaptive_policy="require",
        **kwargs,
    )

    start = time.perf_counter()
    result = rlm.completion(context, root_prompt=root_prompt)
    wall_time = time.perf_counter() - start
    usage = result.usage_summary
    calls = sum(summary.total_calls for summary in usage.model_usage_summaries.values())
    return {
        "mode": mode,
        "response": result.response,
        "score": score(example, result.response),
        "wall_time": wall_time,
        "calls": calls,
        "input_tokens": usage.total_input_tokens,
        "output_tokens": usage.total_output_tokens,
        "provider_cost": usage.total_cost,
        "adaptive_stats": extract_adaptive_stats(result.metadata),
        "log_file": logger.log_file_path,
    }


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set in the environment or .env")

    model = os.getenv("RLM_MODEL", "gpt-5.4-mini")
    sub_model = os.getenv("RLM_SUB_MODEL")
    num_examples = int(os.getenv("NUM_EXAMPLES", "2"))
    context_len = int(os.getenv("CONTEXT_LEN", "131072"))
    run_vanilla = os.getenv("RUN_VANILLA", "1") != "0"
    run_adaptive = os.getenv("RUN_ADAPTIVE", "1") != "0"
    verbose = os.getenv("VERBOSE", "1") != "0"

    examples = load_examples(num_examples, context_len)
    if not examples:
        raise SystemExit("No matching examples loaded")

    summaries = []
    for idx, example in enumerate(examples, start=1):
        print("\n" + "=" * 80, flush=True)
        log(f"Example {idx}/{len(examples)} id={example.get('id')}")
        print(f"Question: {example['question'][:500]}", flush=True)
        print(f"Gold: {example.get('answer')}", flush=True)

        for adaptive in ([False] if run_vanilla else []) + ([True] if run_adaptive else []):
            log(f"starting {'adaptive' if adaptive else 'vanilla'} run with model={model}")
            summary = run_one(
                example,
                adaptive=adaptive,
                model=model,
                sub_model=sub_model,
                verbose=verbose,
            )
            summaries.append(summary)
            print("\nRESULT", flush=True)
            print(summary["response"], flush=True)
            print("\nMETRICS", flush=True)
            for key in (
                "mode",
                "score",
                "wall_time",
                "calls",
                "input_tokens",
                "output_tokens",
                "provider_cost",
                "adaptive_stats",
                "log_file",
            ):
                print(f"{key}={summary[key]}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("SUMMARY", flush=True)
    for mode in sorted({summary["mode"] for summary in summaries}):
        rows = [summary for summary in summaries if summary["mode"] == mode]
        costs = [row["provider_cost"] for row in rows if row["provider_cost"] is not None]
        provider_cost = sum(costs) if costs else None
        print(
            f"{mode}: examples={len(rows)} avg_score={sum(r['score'] for r in rows) / len(rows):.3f} "
            f"avg_wall_time={sum(r['wall_time'] for r in rows) / len(rows):.2f}s "
            f"total_calls={sum(r['calls'] for r in rows)} "
            f"total_input_tokens={sum(r['input_tokens'] for r in rows)} "
            f"total_output_tokens={sum(r['output_tokens'] for r in rows)} "
            f"provider_cost={provider_cost}",
            flush=True,
        )


if __name__ == "__main__":
    main()
