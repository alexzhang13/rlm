import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="openai",  # or "portkey", etc.
    backend_kwargs={
        "model_name": "gpt-5",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    environment="docker",
    environment_kwargs={},
    recursive_max_depth=2,
    max_iterations=4,
    other_backends=["openai", "openai"],  # depth 1 and depth 2 (leaf)
    other_backend_kwargs=[
        {"model_name": "gpt-5-nano", "api_key": os.getenv("OPENAI_API_KEY")},
        {"model_name": "gpt-5-nano", "api_key": os.getenv("OPENAI_API_KEY")},
    ],
    logger=logger,
    verbose=True,  # For printing to console with rich, disabled by default.
)

prompt = "Let ${\\triangle ABC}$ be a right triangle with $\\angle A = 90^{\\circ}$ and $BC = 38.$ There exist points $K$ and $L$ inside the triangle such that $AK = AL = BK = CL = KL = 14.$ The area of the quadrilateral $BKLC$ can be expressed as $n\\sqrt{3}$ for some positive integer $n.$ Find $n.$"

result = rlm.completion(prompt)

print(result)
