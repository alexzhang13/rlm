import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="openai",  # or "portkey", etc.
    backend_kwargs={
        "model_name": "gpt-5-nano",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    environment="docker",
    environment_kwargs={},
    max_depth=1,
    logger=logger,
    verbose=True,  # For printing to console with rich, disabled by default.
)

result = rlm.completion("Print me the first 5 powers of two, each on a newline.")

print(result)
