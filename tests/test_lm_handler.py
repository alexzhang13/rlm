"""Tests for LMHandler using MockLM (no real LM required)."""

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.lm_handler import LMHandler
from rlm.utils.exceptions import ContextWindowExceededError
from tests.mock_lm import MockLM


def test_lm_handler_single_request():
    """Single prompt request returns success and echo-style content."""
    mock = MockLM(responses=["hello back"])
    with LMHandler(client=mock) as handler:
        request = LMRequest(prompt="hello")
        response = send_lm_request(handler.address, request)
    assert response.success
    assert response.chat_completion is not None
    assert response.chat_completion.response == "hello back"


def test_lm_handler_batched_request():
    """Batched prompts return one response per prompt in order."""
    responses = [f"r{i}" for i in range(5)]
    mock = MockLM(responses=responses)
    with LMHandler(client=mock, batch_max_concurrent=3) as handler:
        prompts = [f"prompt-{i}" for i in range(5)]
        result = send_lm_request_batched(handler.address, prompts)
    assert len(result) == 5
    for i, resp in enumerate(result):
        assert resp.success, resp.error
        assert resp.chat_completion is not None
        assert resp.chat_completion.response == f"r{i}"


def test_lm_handler_batched_many_prompts_semaphore_cap():
    """Many prompts complete successfully with semaphore limiting concurrency."""
    # 50 prompts, max 4 concurrent: should still all complete
    count = 50
    responses = [f"resp-{i}" for i in range(count)]
    mock = MockLM(responses=responses)
    with LMHandler(client=mock, batch_max_concurrent=4) as handler:
        prompts = [f"p-{i}" for i in range(count)]
        result = send_lm_request_batched(handler.address, prompts)
    assert len(result) == count
    for i, resp in enumerate(result):
        assert resp.success, (i, resp.error)
        assert resp.chat_completion.response == f"resp-{i}"


def test_lm_handler_single_request_propagates_context_window_error():
    """Client preflight errors should be returned as handler error responses."""

    def raise_context_window_error(_prompt):
        raise ContextWindowExceededError(
            model_name="gpt-4",
            estimated_input_tokens=9_000,
            context_limit=8_192,
            prompt_kind="string",
            estimation_method="character estimate (4 chars/token)",
        )

    mock = MockLM(model_name="gpt-4", response_fn=raise_context_window_error)
    with LMHandler(client=mock) as handler:
        response = send_lm_request(handler.address, LMRequest(prompt="too big"))

    assert not response.success
    assert response.error is not None
    assert "Context window exceeded" in response.error


def test_lm_handler_batched_request_propagates_context_window_error():
    """Batched handler failures should fan out as one error response per prompt."""

    def raise_context_window_error(_prompt):
        raise ContextWindowExceededError(
            model_name="gpt-4",
            estimated_input_tokens=9_000,
            context_limit=8_192,
            prompt_kind="string",
            estimation_method="character estimate (4 chars/token)",
        )

    mock = MockLM(model_name="gpt-4", response_fn=raise_context_window_error)
    with LMHandler(client=mock) as handler:
        responses = send_lm_request_batched(handler.address, ["a", "b", "c"])

    assert len(responses) == 3
    assert all(not response.success for response in responses)
    assert all(response.error is not None for response in responses)
    assert all("Context window exceeded" in response.error for response in responses)
