"""Tests for LMHandler using MockLM (no real LM required)."""

import json
import socket

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.lm_handler import LMHandler
from rlm.core.types import UsageSummary
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


def test_lm_handler_batched_partial_failure():
    """One failing call returns an error for that slot; the rest still succeed."""

    def response_fn(prompt):
        if prompt == "prompt-1":
            raise RuntimeError("boom")
        return f"ok {prompt}"

    mock = MockLM(response_fn=response_fn)
    with LMHandler(client=mock, batch_max_concurrent=3) as handler:
        prompts = ["prompt-0", "prompt-1", "prompt-2"]
        result = send_lm_request_batched(handler.address, prompts)

    assert len(result) == 3
    assert result[0].success
    assert result[0].chat_completion.response == "ok prompt-0"
    assert not result[1].success
    assert "boom" in result[1].error
    assert result[2].success
    assert result[2].chat_completion.response == "ok prompt-2"


def test_lm_handler_batched_many_prompts_semaphore_cap():
    """Many prompts complete successfully with semaphore limiting concurrency."""
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


def test_lm_handler_routing_and_clients():
    """Test client registration, depth-based routing, and usage summary aggregation."""
    client_default = MockLM(model_name="default-model", responses=["default"])
    client_other = MockLM(model_name="other-model", responses=["other"])
    client_custom = MockLM(model_name="custom-model", responses=["custom"])

    with LMHandler(
        client=client_default,
        other_backend_client=client_other,
    ) as handler:
        handler.register_client("custom-model", client_custom)

        assert handler.get_client(depth=0).model_name == "default-model"
        assert handler.get_client(depth=1).model_name == "other-model"
        assert handler.get_client(depth=2).model_name == "default-model"

        assert handler.get_client(model="custom-model", depth=0).model_name == "custom-model"
        assert handler.get_client(model="unknown-model", depth=0).model_name == "default-model"

        res = handler.completion("hello", model="custom-model")
        assert res == "custom"

        usage = handler.get_usage_summary()
        assert isinstance(usage, UsageSummary)
        assert "custom-model" in usage.model_usage_summaries


def test_lm_handler_invalid_request_payload():
    """Sending valid JSON list instead of dict returns a proper error response."""
    mock = MockLM(responses=["ok"])
    with LMHandler(client=mock) as handler:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(handler.address)
        try:
            # Send valid JSON list instead of dict
            raw_data = json.dumps(["not", "a", "dict"]).encode("utf-8")
            s.sendall(len(raw_data).to_bytes(4, byteorder="big") + raw_data)

            length_bytes = s.recv(4)
            assert len(length_bytes) == 4
            length = int.from_bytes(length_bytes, byteorder="big")
            resp_data = json.loads(s.recv(length).decode("utf-8"))

            assert "error" in resp_data
            assert "Request must be a JSON object" in resp_data["error"]
        finally:
            s.close()
