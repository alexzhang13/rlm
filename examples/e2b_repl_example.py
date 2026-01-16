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
    environment="e2b",
    environment_kwargs={
        "timeout": 300,
    },
    max_depth=1,
    logger=logger,
    verbose=True,
)

result = rlm.completion("Using your code, solve 2^(2^(2^(2))). Show your work in Python.")
print(result.response)
