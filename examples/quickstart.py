import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="gemini",  # or "portkey", etc.
    backend_kwargs={
        "model_name": "gemini-2.5-flash",
        "api_key": os.getenv("GEMINI_API_KEY"),
    },
    environment="local",
    environment_kwargs={},
    max_depth=1,
    logger=logger,
    verbose=True,  # For printing to console with rich, disabled by default.
)

result = rlm.completion("How many r's are there in 'strawberry'")

print(result)
