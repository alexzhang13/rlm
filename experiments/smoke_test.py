#!/usr/bin/env python3
"""Phase 0 smoke test: verify Agent-SDK backend drives the RLM scaffold
end-to-end on a small needle-in-haystack query. Expected cost ≈ $0.10.

Run:
    OAUTH from ~/.claude/sensitive/oauth-tokens.md (wzhu@college.harvard.edu)
    uv run python experiments/smoke_test.py
"""
import os
import random
import string

from rlm import RLM
from rlm.logger import RLMLogger

if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
    raise SystemExit(
        "CLAUDE_CODE_OAUTH_TOKEN not set. Export it before running:\n"
        "  export CLAUDE_CODE_OAUTH_TOKEN='sk-ant-oat01-...'"
    )

rng = random.Random(2640)
secret = rng.randint(100_000_000, 999_999_999)
lines = [
    "".join(rng.choices(string.ascii_lowercase + " ", k=80))
    for _ in range(500)
]
lines.insert(rng.randrange(200, 400), f"SECRET_NUMBER={secret}")
haystack = "\n".join(lines)

rlm = RLM(
    backend="agent_sdk",
    backend_kwargs={"model_name": "claude-sonnet-4-6"},
    environment="local",
    max_iterations=6,
    logger=RLMLogger(log_dir="./logs/smoke"),
    verbose=True,
)

result = rlm.completion(
    "The context contains ~500 lines of random text with exactly one line matching "
    "SECRET_NUMBER=<digits>. Return ONLY the numeric value.\n\n" + haystack
)

print()
print(f"Model returned: {result.response!r}")
print(f"Actual secret:  {secret}")
print(f"PASS: {str(secret) in str(result.response)}")
print(f"Usage: {result.usage_summary.to_dict() if hasattr(result, 'usage_summary') else 'n/a'}")
