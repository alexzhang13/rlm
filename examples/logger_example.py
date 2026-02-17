"""
Logger example: same structure as quickstart, with a different prompt.
Shows trajectory capture in completion.metadata (and optional save to disk).
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# In-memory only: trajectory on completion.metadata (no disk write)
logger = RLMLogger()
# To also save JSONL for the visualizer: logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="portkey",
    backend_kwargs={
        "model_name": "@openai/gpt-5-nano",
        "api_key": os.getenv("PORTKEY_API_KEY"),
    },
    environment="local",
    environment_kwargs={},
    max_depth=1,
    logger=logger,
    verbose=True,
)

prompt = "Compute the sum 1 + 2 + 3 + 4 + 5 and print the result using a REPL block, then return it with FINAL_VAR."
result = rlm.completion(prompt)

print("Response:", result.response)
if result.metadata:
    traj = result.metadata
    print("Trajectory: run_metadata +", len(traj.get("iterations", [])), "iterations")
    print("Trajectory:", traj)
    if traj.get("iterations"):
        first = traj["iterations"][0]
        print("  First iteration keys:", list(first.keys()))
else:
    print("Trajectory: (none — no logger or metadata not captured)")

print("Full response:", result)
