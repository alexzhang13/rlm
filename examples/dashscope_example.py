"""Example: RLM with DashScope (Qwen models)"""

import os

from rlm import RLM
from rlm.logger import RLMLogger

# DashScope API key from environment
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY environment variable is not set")

# DashScope OpenAI-compatible base URL
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Initialize RLM with DashScope backend
rlm = RLM(
    backend="openai",  # Uses OpenAI-compatible API
    backend_kwargs={
        "model_name": "qwen3.6-flash",
        "api_key": DASHSCOPE_API_KEY,
        "base_url": DASHSCOPE_BASE_URL,
    },
    environment="local",
    max_iterations=10,
    logger=RLMLogger(log_dir="./logs"),
    verbose=True,
)

# Example 1: Simple completion
print("=" * 60)
print("Example 1: Simple RLM Completion")
print("=" * 60)

result = rlm.completion("What are the top 3 benefits of RLMs? Give a concise answer.")

print(f"\nResponse: {result.response}")

# Example 2: Context-heavy task (finding information in large context)
print("\n" + "=" * 60)
print("Example 2: Context-heavy Task - Finding Hidden Information")
print("=" * 60)

# Create a context with a hidden value
context_lines = []
for i in range(100):
    context_lines.append(f"Line {i}: This is filler text with no important information.")

# Insert a secret at a random position
import random

secret_line = random.randint(30, 70)
context_lines[secret_line] = f"Line {secret_line}: IMPORTANT: The answer to life is 42."

context = "\n".join(context_lines)

prompt = f"""The context contains 100 lines of text. One line contains an important message.
Find and return ONLY the important message.

Context:
{context}
"""

result = rlm.completion(prompt)

print(f"\nResponse: {result.response}")
print(f"\nActual secret was at line {secret_line}: {context_lines[secret_line]}")
print(f"Found it: {'42' in result.response}")

print("\n" + "=" * 60)
print("Examples completed! Check ./logs for trajectory visualization data.")
print("=" * 60)
