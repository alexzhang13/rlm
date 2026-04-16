"""Diagnose: difference between RLMArm (fails) and smoke_test.py (passes)."""
import os

from rlm import RLM
from rlm.utils.prompts import RLM_SYSTEM_PROMPT

from experiments.benchmarks.sniah import SNIAH
bench = SNIAH()
q = bench.load_queries(n=1, seed=2640)[0]
prompt = q.prompt
secret = q.gold
print(f"prompt_len={len(prompt)} secret={secret} prompt_head={prompt[:200]!r}")

rlm = RLM(
    backend="agent_sdk",
    backend_kwargs={"model_name": "claude-sonnet-4-6"},
    environment="local",
    max_iterations=10,
    custom_system_prompt=RLM_SYSTEM_PROMPT,
    verbose=False,
)
try:
    result = rlm.completion(prompt)
    print(f"response: {result.response!r}")
    print(f"expected: {secret}")
    print(f"PASS: {str(secret) in str(result.response)}")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
