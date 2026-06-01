import os
import re
import time
from pathlib import Path
from typing import Any

from datasets import load_dataset
from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv(Path.cwd() / ".env")


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def extract_choice(text: str) -> str | None:
    text = str(text).strip()
    patterns = [
        r"\bAnswer\s*[:\-]\s*([ABCD])\b",
        r"\bfinal answer\s*(?:is|:)?\s*([ABCD])\b",
        r"\boption\s*([ABCD])\b",
        r"^\s*([ABCD])\s*$",
        r"\b([ABCD])\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def score(row: dict[str, Any], response: str) -> float:
    prediction = extract_choice(response)
    return 1.0 if prediction == str(row.get("answer", "")).upper() else 0.0


def root_prompt(row: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Answer the multiple-choice question using the stored context.",
            "Return exactly one answer choice: A, B, C, or D.",
            "",
            f"Question: {row.get('question', '')}",
            f"A: {row.get('choice_A', '')}",
            f"B: {row.get('choice_B', '')}",
            f"C: {row.get('choice_C', '')}",
            f"D: {row.get('choice_D', '')}",
        ]
    )


def load_examples(
    dataset_name: str,
    num_examples: int,
    domain_filter: str,
    subdomain_filter: str | None,
    sample_seed: int | None,
    shuffle_buffer_size: int,
) -> list[dict[str, Any]]:
    log(
        f"Loading {num_examples} LongBench-v2 examples from {dataset_name} "
        f"domain={domain_filter!r} subdomain={subdomain_filter!r}"
    )
    stream = load_dataset(dataset_name, split="train", streaming=True)
    if sample_seed is not None:
        stream = stream.shuffle(seed=sample_seed, buffer_size=shuffle_buffer_size)
    rows = []
    for row in stream:
        if domain_filter and row.get("domain") != domain_filter:
            continue
        if subdomain_filter and row.get("sub_domain") != subdomain_filter:
            continue
        rows.append(row)
        log(
            f"loaded example {len(rows)}/{num_examples}: id={row.get('_id')} "
            f"length={row.get('length')} difficulty={row.get('difficulty')}"
        )
        if len(rows) >= num_examples:
            break
    return rows


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
    row: dict[str, Any],
    adaptive: bool,
    model: str,
    sub_model: str | None,
    verbose: bool,
    max_iterations: int,
    max_concurrent_subcalls: int,
    reasoning_effort: str,
) -> dict[str, Any]:
    mode = "adaptive_search_tree" if adaptive else "vanilla"
    sampling_args = {"max_tokens": 4096, "reasoning_effort": reasoning_effort}
    logger = RLMLogger(log_dir=f"./logs/longbench_{mode}", file_name=f"longbench_{mode}")

    kwargs: dict[str, Any] = {}
    if sub_model and sub_model != model:
        kwargs["other_backends"] = ["openai"]
        kwargs["other_backend_kwargs"] = [{"model_name": sub_model}]

    if adaptive:
        user_prologue = os.getenv("ADAPTIVE_SEARCH_TREE_PROLOGUE", "").strip()
        if user_prologue:
            kwargs["user_prologue"] = user_prologue

    rlm = RLM(
        backend="openai",
        backend_kwargs={"model_name": model},
        environment="local",
        max_depth=1,
        max_iterations=max_iterations,
        max_concurrent_subcalls=max_concurrent_subcalls,
        sampling_args=sampling_args,
        sub_sampling_args=sampling_args,
        logger=logger,
        verbose=verbose,
        adaptive=adaptive,
        adaptive_policy="require",
        required_adaptive_helper="adaptive_search_tree" if adaptive else None,
        **kwargs,
    )

    start = time.perf_counter()
    result = rlm.completion(row.get("context", ""), root_prompt=root_prompt(row))
    wall_time = time.perf_counter() - start
    usage = result.usage_summary
    calls = sum(summary.total_calls for summary in usage.model_usage_summaries.values())
    prediction = extract_choice(result.response)

    return {
        "mode": mode,
        "response": result.response,
        "prediction": prediction,
        "gold": str(row.get("answer", "")).upper(),
        "score": score(row, result.response),
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

    dataset_name = os.getenv("LONGBENCH_DATASET", "zai-org/LongBench-v2")
    num_examples = int(os.getenv("NUM_EXAMPLES", "2"))
    model = os.getenv("RLM_MODEL", "gpt-5.4-mini")
    sub_model = os.getenv("RLM_SUB_MODEL")
    domain_filter = os.getenv("DOMAIN_FILTER", "Code Repository Understanding")
    subdomain_filter = os.getenv("SUBDOMAIN_FILTER") or None
    run_vanilla = os.getenv("RUN_VANILLA", "1") != "0"
    run_adaptive = os.getenv("RUN_ADAPTIVE", "1") != "0"
    verbose = os.getenv("VERBOSE", "1") != "0"
    max_iterations = int(os.getenv("MAX_ITERATIONS", "12"))
    max_concurrent_subcalls = int(os.getenv("MAX_CONCURRENT_SUBCALLS", "16"))
    reasoning_effort = os.getenv("REASONING_EFFORT", "none")
    sample_seed_raw = os.getenv("SAMPLE_SEED")
    sample_seed = int(sample_seed_raw) if sample_seed_raw else None
    shuffle_buffer_size = int(os.getenv("SHUFFLE_BUFFER_SIZE", "1000"))

    rows = load_examples(
        dataset_name,
        num_examples,
        domain_filter,
        subdomain_filter,
        sample_seed,
        shuffle_buffer_size,
    )
    if not rows:
        raise SystemExit("No matching LongBench-v2 examples loaded")

    summaries = []
    for idx, row in enumerate(rows, start=1):
        print("\n" + "=" * 80, flush=True)
        log(f"Example {idx}/{len(rows)} id={row.get('_id')}")
        print(f"Domain: {row.get('domain')} / {row.get('sub_domain')}", flush=True)
        print(f"Question: {row.get('question', '')[:600]}", flush=True)
        print(
            f"Choices: A={row.get('choice_A')} | B={row.get('choice_B')} | "
            f"C={row.get('choice_C')} | D={row.get('choice_D')}",
            flush=True,
        )
        print(f"Gold: {row.get('answer')}", flush=True)

        for adaptive in ([False] if run_vanilla else []) + ([True] if run_adaptive else []):
            log(f"starting {'adaptive_search_tree' if adaptive else 'vanilla'} run")
            summary = run_one(
                row=row,
                adaptive=adaptive,
                model=model,
                sub_model=sub_model,
                verbose=verbose,
                max_iterations=max_iterations,
                max_concurrent_subcalls=max_concurrent_subcalls,
                reasoning_effort=reasoning_effort,
            )
            summaries.append(summary)
            print("\nRESULT", flush=True)
            print(summary["response"], flush=True)
            print("\nMETRICS", flush=True)
            for key in (
                "mode",
                "prediction",
                "gold",
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
        rows_for_mode = [summary for summary in summaries if summary["mode"] == mode]
        costs = [row["provider_cost"] for row in rows_for_mode if row["provider_cost"] is not None]
        provider_cost = sum(costs) if costs else None
        print(
            f"{mode}: examples={len(rows_for_mode)} "
            f"avg_score={sum(r['score'] for r in rows_for_mode) / len(rows_for_mode):.3f} "
            f"avg_wall_time={sum(r['wall_time'] for r in rows_for_mode) / len(rows_for_mode):.2f}s "
            f"total_calls={sum(r['calls'] for r in rows_for_mode)} "
            f"total_input_tokens={sum(r['input_tokens'] for r in rows_for_mode)} "
            f"total_output_tokens={sum(r['output_tokens'] for r in rows_for_mode)} "
            f"provider_cost={provider_cost}",
            flush=True,
        )


if __name__ == "__main__":
    main()
