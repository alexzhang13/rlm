"""E2E test for depth>1 with real LLM via OpenRouter."""

import os

import pytest

from rlm import RLM


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)
def test_depth_2_real_llm():
    """Test depth=2 recursion with google/gemini-3-flash-preview."""
    rlm = RLM(
        backend="openrouter",
        backend_kwargs={"model_name": "google/gemini-3-flash-preview"},
        max_iterations=2,
        max_depth=2,
    )
    result = rlm.completion("What is 2+2? Answer with just the number.")
    assert result.response is not None
    assert len(result.response) > 0
    print(f"Response: {result.response}")
