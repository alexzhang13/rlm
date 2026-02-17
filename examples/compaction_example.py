"""
Compaction example: run RLM with compaction enabled and a low threshold
to trigger summarization on gpt-5-nano.

Uses a low compaction_threshold_pct so compaction runs after several iterations.
The task forces many separate REPL turns with substantial output so the root
context grows and compaction definitely triggers. The REPL variable `history`
holds trajectory segments and summaries.
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# Low threshold so compaction triggers after a few iterations (~2% of context).
# Use 0.85 in production.
COMPACTION_THRESHOLD_PCT = 0.03

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
    max_iterations=10,
    compaction=True,
    compaction_threshold_pct=COMPACTION_THRESHOLD_PCT,
    verbose=True,
    logger=logger,
)

# Hard task that forces many iterations: find the 50th prime using at least 8
# separate REPL blocks, one per turn. Each block must produce visible output.
# This grows message history (long reasoning + code + execution results) so
# compaction triggers.
prompt = (
    "Find the 50th prime number. You MUST use at least 8 separate REPL blocks, "
    "each in its own response (one block per message). Do NOT combine steps.\n\n"
    "Required structure: "
    "Block 1: Define a function is_prime(n) and test it on a few numbers; print the results. "
    "Block 2: Write a loop that counts primes and print the first 10 primes. "
    "Block 3: Extend to count up to 20 primes and print them. "
    "Block 4: Count up to 30 primes and print the 25th. "
    "Block 5: Count up to 40 primes and print the 35th. "
    "Block 6: Count up to 50 primes and print the 45th. "
    "Block 7: Print the full list of the first 50 primes (so we see all 50). "
    "Block 8: Set answer = (the 50th prime) and call FINAL_VAR(answer).\n\n"
    "Each block must run alone. Show your reasoning briefly before each block. "
    "After each block, wait for the execution result before writing the next block."
)

result = rlm.completion(prompt, root_prompt=prompt)

print("Response:", result.response)
print("Execution time:", result.execution_time)
print("Metadata:", result.metadata)
