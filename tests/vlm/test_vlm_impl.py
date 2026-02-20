import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

logger = RLMLogger(log_dir="./logs")



TEST_CASES = [
    ("test_one_image", "transaction value"),
    ("test_pdf2image", "aye"),
    ("test_n_images", "sanction"),
    ("test_supported_formats", "oil"),
]

from pathlib import Path
FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize(
    "test_name, expected_keyword",
    TEST_CASES,
    ids=[case[0] for case in TEST_CASES]
)
def test_vlm(test_name, expected_keyword, max_iterations):
    prompt = (FIXTURES_DIR / test_name / "prompt.txt").read_text()

    rlm = RLM(
        backend="openai",  # or "portkey", etc.
        backend_kwargs={
            "model_name": "gpt-5.2",
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        environment="docker",
        environment_kwargs={
            "image": f"rlm-vlm-{test_name}",
            "setup_code": "import shutil; shutil.copytree('/prompt', '/workspace/prompt')"
        },
        max_depth=1,
        max_iterations=max_iterations,
        logger=logger,
        verbose=True,  # For printing to console with rich, disabled by default.
    )

    result = rlm.completion(prompt)
    assert expected_keyword in result.response
