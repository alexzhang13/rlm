"""
Example script to test Prime Intellect Sandboxes.

Requirements:
1. Install the Prime SDK:
   pip install prime
   # or for lightweight SDK only:
   pip install prime-sandboxes

2. Authenticate with Prime:
   prime login
   # or set environment variable:
   export PRIME_API_KEY="your-api-key"

3. Set your LLM API key (OpenAI in this example):
   export OPENAI_API_KEY="your-api-key"
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
    environment="prime",
    environment_kwargs={
        "name": "rlm-prime-demo",
        "docker_image": "python:3.11-slim",
        "timeout_minutes": 30,
    },
    max_depth=1,
    logger=logger,
    verbose=True,
)

result = rlm.completion("Using your code, solve 2^(2^(2^(2))). Show your work in Python.")
print(result.response)
