"""
Example: depth>1 RLM with metadata inspection.

Demonstrates that when a parent RLM spawns child RLMs via rlm_query(),
each child captures its own trajectory metadata. The metadata flows back
through RLMChatCompletion.metadata on the rlm_calls recorded in each
code block's REPLResult.

Usage:
    PORTKEY_API_KEY=... python examples/depth_metadata_example.py

Prints a structured tree of the metadata at all depth levels.
"""

import json
import os
import sys

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()


def print_separator(char="─", width=80):
    print(char * width)


def print_metadata_tree(result, depth=0):
    """Recursively print metadata from an RLMChatCompletion and its sub-calls."""
    indent = "  " * depth
    prefix = f"{'└─ ' if depth > 0 else ''}"

    print(
        f"{indent}{prefix}[Depth {depth}] model={result.root_model}  "
        f"time={result.execution_time:.2f}s  response_len={len(result.response)}"
    )

    # Print usage
    usage = result.usage_summary
    if usage and usage.model_usage_summaries:
        for _model, summary in usage.model_usage_summaries.items():
            print(
                f"{indent}   tokens: in={summary.total_input_tokens} out={summary.total_output_tokens} "
                f"calls={summary.total_calls}"
                + (f" cost=${summary.total_cost:.6f}" if summary.total_cost else "")
            )

    # Print trajectory metadata
    if result.metadata:
        traj = result.metadata
        n_iters = len(traj.get("iterations", []))
        print(f"{indent}   metadata: {n_iters} iteration(s) captured")

        # Dig into iterations to find sub-calls with their own metadata
        for i, iteration in enumerate(traj.get("iterations", [])):
            for cb in iteration.get("code_blocks", []):
                repl_result = cb.get("result", {})
                for j, sub_call in enumerate(repl_result.get("rlm_calls", [])):
                    sub_response = sub_call.get("response", "")[:80]
                    print(
                        f"{indent}   iter {i + 1} sub-call {j + 1}: "
                        f"model={sub_call.get('root_model', '?')}  "
                        f"response={sub_response!r}..."
                    )
                    if sub_call.get("metadata"):
                        sub_n = len(sub_call["metadata"].get("iterations", []))
                        print(f"{indent}     ^ has nested metadata: {sub_n} iteration(s)")
    else:
        print(f"{indent}   metadata: (none)")

    print()


def main():
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        print("Error: PORTKEY_API_KEY not set. Set it and re-run.")
        sys.exit(1)

    model = "@openai/gpt-5-nano"

    print_separator("=")
    print("  Depth>1 RLM Metadata Example")
    print(f"  Model: {model}  |  max_depth=2  |  max_iterations=3")
    print_separator("=")
    print()

    logger = RLMLogger()

    rlm = RLM(
        backend="portkey",
        backend_kwargs={
            "model_name": model,
            "api_key": api_key,
        },
        environment="local",
        max_depth=2,
        max_iterations=3,
        logger=logger,
        verbose=True,
    )

    # This prompt forces the model to use rlm_query(), triggering a depth>1 subcall
    prompt = (
        "Use rlm_query() to ask the sub-model: 'What are the first 5 prime numbers? "
        "Reply with just the numbers separated by commas.' "
        "Store the response in a variable called 'primes', then return it with FINAL_VAR('primes')."
    )

    print("Prompt:", prompt)
    print()
    print_separator()

    result = rlm.completion(prompt)

    print_separator("=")
    print("  RESULT")
    print_separator("=")
    print(f"Response: {result.response}")
    print(f"Execution time: {result.execution_time:.2f}s")
    print()

    # ── Metadata tree ──
    print_separator("=")
    print("  METADATA TREE")
    print_separator("=")
    print_metadata_tree(result, depth=0)

    # ── Raw metadata JSON ──
    print_separator("=")
    print("  RAW METADATA (JSON)")
    print_separator("=")
    if result.metadata:
        # Print compactly but readable
        print(json.dumps(result.metadata, indent=2, default=str)[:3000])
        if len(json.dumps(result.metadata, default=str)) > 3000:
            print("... (truncated)")
    else:
        print("(no metadata captured)")

    print()
    print_separator("=")
    print("  SUB-CALL METADATA DETAIL")
    print_separator("=")

    # Walk through iterations and find sub-calls with metadata
    if result.metadata:
        found_subcalls = False
        for i, iteration in enumerate(result.metadata.get("iterations", [])):
            for cb in iteration.get("code_blocks", []):
                repl_result = cb.get("result", {})
                for j, sub_call in enumerate(repl_result.get("rlm_calls", [])):
                    found_subcalls = True
                    print(f"\nIteration {i + 1}, Sub-call {j + 1}:")
                    print(f"  Model: {sub_call.get('root_model', '?')}")
                    print(f"  Response: {sub_call.get('response', '')[:200]}")
                    print(f"  Execution time: {sub_call.get('execution_time', 0):.2f}s")
                    if sub_call.get("metadata"):
                        meta = sub_call["metadata"]
                        print(f"  Trajectory: {len(meta.get('iterations', []))} iterations")
                        print(
                            f"  Run metadata: {json.dumps(meta.get('run_metadata', {}), indent=4, default=str)}"
                        )
                    else:
                        print("  Trajectory: (none — leaf LM call, no REPL)")
                    print()

        if not found_subcalls:
            print("No sub-calls found in iterations (model may not have used llm_query).")
    else:
        print("No metadata to inspect.")


if __name__ == "__main__":
    main()
