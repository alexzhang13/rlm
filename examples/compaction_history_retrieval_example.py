"""
Compaction + history retrieval example.

Like compaction_example.py but with more intermediate results to recover.
Uses random data across 4 groups so none of the statistics are re-derivable
after compaction — the model must look in `history` to find them.

Usage:
    PORTKEY_API_KEY=... python examples/compaction_history_retrieval_example.py
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# Very low threshold so compaction fires after the first few steps.
COMPACTION_THRESHOLD_PCT = 0.02

logger = RLMLogger()
rlm = RLM(
    backend="portkey",
    backend_kwargs={
        "model_name": "@openai/gpt-5-nano",
        "api_key": os.getenv("PORTKEY_API_KEY"),
    },
    environment="local",
    environment_kwargs={},
    max_depth=1,
    max_iterations=15,
    compaction=True,
    compaction_threshold_pct=COMPACTION_THRESHOLD_PCT,
    verbose=True,
    logger=logger,
)

prompt = (
    "Complete the following steps, each in its own REPL block (one block per message). "
    "Do NOT combine steps.\n\n"
    "Step 1: `import random; random.seed(99)`. Generate 40 random floats in [0, 100). "
    "Print all of them. Store as `group_1`.\n\n"
    "Step 2: Generate another 40 random floats (same RNG stream). Print all. "
    "Store as `group_2`.\n\n"
    "Step 3: Generate another 40 random floats. Print all. Store as `group_3`.\n\n"
    "Step 4: Generate another 40 random floats. Print all. Store as `group_4`.\n\n"
    "Step 5: Compute the mean of each group. Print all four means. "
    "Store as `m1`, `m2`, `m3`, `m4`.\n\n"
    "Step 6: Compute the standard deviation of each group. Print all four. "
    "Store as `s1`, `s2`, `s3`, `s4`.\n\n"
    "Step 7: You previously computed four means and four standard deviations. "
    "Compute final_answer = round((m1 + m2 + m3 + m4) / (s1 + s2 + s3 + s4), 4). "
    "Print the full equation with values and call FINAL_VAR(final_answer)."
)

result = rlm.completion(prompt, root_prompt=prompt)

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)
print(f"Response: {result.response}")
print(f"Execution time: {result.execution_time:.2f}s")
