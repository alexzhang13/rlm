"""
Example: An example from the Oolong Benchmark from the RLM paper: https://arxiv.org/abs/2512.24601v1
"""

import os
import sys
from itertools import islice

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

try:
    from datasets import load_dataset
except ImportError:
    print(
        "Please install the 'datasets' library to run this example. Run `uv pip install datasets`"
    )
    sys.exit(1)


def load_oolong_row(index: int = 1) -> dict:
    """Load a single row from the Oolong benchmark."""
    streaming_ds = load_dataset("oolongbench/oolong-real", "toy_dnd", split="test", streaming=True)
    row = next(islice(streaming_ds, index, index + 1))
    return row


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    # Load benchmark data
    row = load_oolong_row(index=1)
    context = row["context_window_text"]
    question = row["question"]
    expected_answer = row["answer"]

    print(f"Question: {question}")
    print(f"Expected answer: {expected_answer}")
    print("-" * 50)

    # Create logger
    logger = RLMLogger(log_dir="./logs")

    # Create RLM instance
    rlm = RLM(
        backend="openai",
        backend_kwargs={
            "model_name": "gpt-5-mini",
            "api_key": api_key,
        },
        environment="local",
        max_iterations=30,
        logger=logger,
        verbose=True,
    )

    # Run completion with context and question
    result = rlm.completion(prompt=context, root_prompt=question)

    print("-" * 50)
    print(f"RLM Response: {result.response}")
    print(f"Expected: {expected_answer}")

    # Simple validation (exact match or contained)
    is_correct = (
        expected_answer.lower() in result.response.lower()
        or result.response.lower() in expected_answer.lower()
    )
    print(f"Match: {is_correct}")


if __name__ == "__main__":
    main()
