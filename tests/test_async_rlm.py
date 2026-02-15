from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.core.types import ModelUsageSummary, UsageSummary


async def create_mock_alm(responses: list[str]) -> MagicMock:
    """Create a mock LM that returns responses in order for acompletion."""
    # Use MagicMock for the client so we can mix sync and async methods
    mock = MagicMock()
    mock.acompletion = AsyncMock(side_effect=list(responses))
    mock.model_name = "mock"
    mock.get_usage_summary.return_value = UsageSummary(
        model_usage_summaries={
            "mock": ModelUsageSummary(total_calls=1, total_input_tokens=100, total_output_tokens=50)
        }
    )
    mock.get_last_usage.return_value = mock.get_usage_summary.return_value
    return mock


@pytest.mark.asyncio
async def test_rlm_acompletion_basic():
    """Test basic async completion."""
    # We need to run some code first, or use a multi-response sequence
    # because of the guard that requires code execution before FINAL.
    responses = ["Thinking...\n```repl\npass\n```", "FINAL(async answer)"]

    with patch.object(rlm_module, "get_client") as mock_get_client:
        mock_lm = await create_mock_alm(responses)
        mock_get_client.return_value = mock_lm

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
        )

        result = await rlm.acompletion("Hello async")
        assert result.response == "async answer"
        assert mock_lm.acompletion.call_count == 2


@pytest.mark.asyncio
async def test_rlm_acompletion_with_hooks():
    """Test async completion with iteration hooks."""
    responses = [
        "Let me think\n```repl\nprint(42)\n```",
        "FINAL(the answer is 42)",
    ]

    with patch.object(rlm_module, "get_client") as mock_get_client:
        mock_lm = await create_mock_alm(responses)
        mock_get_client.return_value = mock_lm

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
        )

        iteration_results = []

        async def on_iteration(iteration, index):
            iteration_results.append((index, iteration))

        result = await rlm.acompletion("Hello async with hooks", on_iteration=on_iteration)

        assert result.response == "the answer is 42"
        assert len(iteration_results) == 2
        assert iteration_results[0][0] == 1
        assert iteration_results[1][0] == 2
        assert "print(42)" in iteration_results[0][1].response


@pytest.mark.asyncio
async def test_rlm_on_request_callback():
    """Test on_request callback for sub-LM calls."""
    responses = [
        "```repl\nresult = llm_query('What is 2+2?')\nprint(result)\n```",
        "FINAL(4)",
    ]

    # Sub-LM response
    sub_responses = ["4"]

    with patch.object(rlm_module, "get_client") as mock_get_client:
        # Mock for main RLM
        mock_lm = await create_mock_alm(responses)

        # Mock for sub-LM call
        mock_sub_lm = await create_mock_alm(sub_responses)

        # get_client will be called twice
        mock_get_client.side_effect = [mock_lm, mock_sub_lm]

        request_data = []

        def on_request(request, response):
            request_data.append((request, response))

        rlm = RLM(backend="openai", backend_kwargs={"model_name": "test"}, on_request=on_request)

        result = await rlm.acompletion("Hello with sub-calls")

        assert result.response == "4"
        # We expect at least one request recorded (the sub-call via socket)
        assert len(request_data) >= 1
        assert "What is 2+2?" in str(request_data[0][0].prompt)
