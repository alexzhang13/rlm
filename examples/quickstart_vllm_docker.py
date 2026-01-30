"""
Quickstart: Local vLLM backend with Docker execution.

Setup:
    1. Start vLLM OpenAI-compatible server, e.g.:
       python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3-70b --port 8000
    2. Ensure Docker is running.
    3. Run: python -m examples.quickstart_vllm_docker
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

logger = RLMLogger(log_dir="./logs")

# OpenAI client requires an api_key; vLLM ignores it unless configured server-side.
api_key = os.getenv("VLLM_API_KEY", "EMPTY")

rlm = RLM(
    backend="vllm",
    backend_kwargs={
        "base_url": "http://localhost:8000/v1",
        "model_name": "meta-llama/Llama-3-70b",
        "api_key": api_key,
    },
    environment="docker",
    environment_kwargs={},
    recursive_max_depth=3,
    max_iterations=4,
    other_backends=["vllm", "vllm"],  # depth 1 and depth 2
    other_backend_kwargs=[
        {
            "base_url": "http://localhost:8001/v1",
            "model_name": "meta-llama/Llama-3-8b",
            "api_key": api_key,
        },
        {
            "base_url": "http://localhost:8002/v1",
            "model_name": "mistralai/Mistral-7B-Instruct-v0.2",
            "api_key": api_key,
        },
    ],
    logger=logger,
    verbose=True,
)

prompts = [
    "Summarize the key idea of recursive language models in 2 sentences.",
    "Given a list of numbers [3, 7, 2, 9], return the max and min.",
]

for prompt in prompts:
    result = rlm.completion(prompt)
    print("=" * 60)
    print(f"Prompt: {prompt}")
    print(f"Response: {result.response}")
