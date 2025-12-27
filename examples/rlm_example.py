from rlm.logger import RLMLogger
from rlm import RLM

import os
from dotenv import load_dotenv

load_dotenv()

logger = RLMLogger(log_dir="./logs")
rlm = RLM(
    backend="portkey",
    backend_kwargs={
        "api_key": os.getenv("PORTKEY_API_KEY"),
        "model_name": "@openai/gpt-5-nano",
    },
    environment="local",
    environment_kwargs={},
    max_depth=1,
    logger=logger,
)

result = rlm.completion(
    "Using your code, solve 2^(2^(2^(2))). Show your work in Python."
)
print(result)
