"""
Example: Multimodal RLM - Analyzing Images with Vision

This demonstrates the multimodal capabilities of RLM using the
vision_query() function to analyze images.
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_IMAGE = os.path.join(SCRIPT_DIR, "test_image.png")

logger = RLMLogger(log_dir="./logs")

# Use Gemini which supports vision
rlm = RLM(
    backend="gemini",
    backend_kwargs={
        "model_name": "gemini-2.5-flash",
        "api_key": os.getenv("GEMINI_API_KEY"),
    },
    environment="local",
    environment_kwargs={},
    max_depth=1,
    logger=logger,
    verbose=True,
    enable_multimodal=True,  # Enable multimodal functions (vision_query, audio_query, speak)
)

# Create a context that includes references to images
context = {
    "query": "Analyze the image and tell me what fruits are visible.",
    "images": [TEST_IMAGE],
}

result = rlm.completion(
    prompt=context,
    root_prompt="What fruits are in the image? Use vision_query to analyze the image.",
)

print("\n" + "=" * 50)
print("FINAL RESULT:")
print("=" * 50)
print(result.response)
