"""Quickstart example for using RLM with AWS Bedrock.

This example demonstrates how to use RLM with AWS Bedrock via Project Mantle,
Amazon's OpenAI-compatible endpoint for Bedrock models.

Prerequisites:
    1. Generate a Bedrock API key in AWS Console → Bedrock → API keys
    2. Set environment variables:
        export AWS_BEDROCK_API_KEY=your-bedrock-api-key
        export AWS_BEDROCK_REGION=us-east-1  # optional, defaults to us-east-1

Usage:
    python examples/bedrock_quickstart.py
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# Initialize logger for debugging
logger = RLMLogger(log_dir="./logs")

# Create RLM instance with Bedrock backend
rlm = RLM(
    backend="bedrock",
    backend_kwargs={
        "model_name": "qwen.qwen3-coder-30b-a3b-v1:0",  # Qwen3 Coder for code tasks
        # api_key and region are read from environment variables:
        # - AWS_BEDROCK_API_KEY
        # - AWS_BEDROCK_REGION (defaults to us-east-1)
    },
    environment="docker",  # or "local" for direct execution
    environment_kwargs={},
    max_depth=1,
    logger=logger,
    verbose=True,
)

# Run a simple RLM completion
result = rlm.completion("Print me the first 5 powers of two, each on a newline.")

print("\n" + "=" * 50)
print("RLM Result:")
print("=" * 50)
print(result)
