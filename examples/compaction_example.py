"""
Compaction example: run RLM with compaction enabled and a low threshold
to trigger summarization.

The task uses random data so earlier results are impossible to recompute —
the model *must* recover them from `history` after compaction fires.

Phase 1: Generate random datasets and compute statistics (fills context).
Phase 2: Compaction fires, summarizing the conversation.
Phase 3: Combine the earlier statistics into a final answer. Since the data
          was random, the model cannot just re-derive the numbers.

Usage:
    PORTKEY_API_KEY=... python examples/compaction_example.py
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# Low threshold so compaction triggers after a few iterations.
# Use 0.85 in production.
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
    max_iterations=12,
    compaction=True,
    compaction_threshold_pct=COMPACTION_THRESHOLD_PCT,
    verbose=True,
    logger=logger,
)

prompt = (
    "Complete the following steps, each in its own REPL block (one block per message). "
    "Do NOT combine steps.\n\n"
    "Step 1: Use `import random; random.seed(42)` then generate a list of 50 random "
    "integers between 1 and 1000. Print ALL of them. Store as `data_a`.\n\n"
    "Step 2: Generate another 50 random integers (continuing the same RNG stream) "
    "between 1 and 1000. Print ALL of them. Store as `data_b`.\n\n"
    "Step 3: Compute and print the mean, median, min, max, and standard deviation "
    "of `data_a`. Store the mean as `mean_a`.\n\n"
    "Step 4: Compute and print the mean, median, min, max, and standard deviation "
    "of `data_b`. Store the mean as `mean_b`.\n\n"
    "Step 5: You previously computed `mean_a` and `mean_b`. "
    "Compute final_answer = round(mean_a + mean_b, 2) and call FINAL_VAR(final_answer)."
)

result = rlm.completion(prompt, root_prompt=prompt)

print("\n" + "=" * 60)
print("RESULT")
print("=" * 60)
print(f"Response: {result.response}")
print(f"Execution time: {result.execution_time:.2f}s")
