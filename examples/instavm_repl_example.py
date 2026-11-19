"""
Example usage of InstaVM REPL with code execution and LLM queries.

InstaVM (https://instavm.io) provides Firecracker microVMs with sub-second
cold starts. This example uses the same shape as the other isolated
environments (modal/e2b/daytona).

Run with:
    export INSTAVM_API_KEY=...
    export OPENAI_API_KEY=...
    python -m examples.instavm_repl_example
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="openai",
    backend_kwargs={
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-5-nano",
    },
    environment="instavm",
    environment_kwargs={
        "api_key": os.getenv("INSTAVM_API_KEY"),
        "timeout": 300,
    },
    max_depth=1,
    logger=logger,
    verbose=True,
)

result = rlm.completion("Using your code, solve 2^(2^(2^(2))). Show your work in Python.")
print(result.response)
