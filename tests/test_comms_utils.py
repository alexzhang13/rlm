"""Tests for communication utilities.

Tests the socket protocol and message dataclasses used for
LM Handler <-> Environment subprocess communication.
"""

import json
import struct
from unittest.mock import MagicMock, Mock, patch

import pytest

from rlm.core.comms_utils import (
    LMRequest,
    LMResponse,
    send_lm_request,
    send_lm_request_batched,
    socket_recv,
    socket_request,
    socket_send,
)
from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary


def make_chat_completion(response: str) -> RLMChatCompletion:
    """Helper to create a RLMChatCompletion for tests."""
    return RLMChatCompletion(
        root_model="test-model",
        prompt="test prompt",
        response=response,
        usage_summary=UsageSummary(
            model_usage_summaries={
                "test-model": ModelUsageSummary(
                    total_calls=1,
                    total_input_tokens=10,
                    total_output_tokens=10,
                )
            }
        ),
        execution_time=0.1,
    )


# LMRequest Tests


class TestLMRequest:
    """Tests for LMRequest dataclass."""

    def test_single_prompt_creation(self):
        """Test creating a request with a single prompt."""
        request = LMRequest(prompt="Hello, world!")
        assert request.prompt == "Hello, world!"
        assert request.prompts is None
        assert request.is_batched is False

    def test_batched_prompts_creation(self):
        """Test creating a request with multiple prompts."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        request = LMRequest(prompts=prompts)
        assert request.prompt is None
        assert request.prompts == prompts
        assert request.is_batched is True

    def test_empty_prompts_not_batched(self):
        """Test that empty prompts list is not considered batched."""
        request = LMRequest(prompts=[])
        assert request.is_batched is False

    def test_model_and_depth(self):
        """Test model and depth fields."""
        request = LMRequest(prompt="Test", model="gpt-4", depth=2)
        assert request.model == "gpt-4"
        assert request.depth == 2

    def test_default_depth(self):
        """Test default depth is 0."""
        request = LMRequest(prompt="Test")
        assert request.depth == 0

    def test_to_dict_single_prompt(self):
        """Test converting single prompt request to dict."""
        request = LMRequest(prompt="Hello", model="gpt-4", depth=1)
        d = request.to_dict()
        assert d["prompt"] == "Hello"
        assert d["model"] == "gpt-4"
        assert d["depth"] == 1
        assert "prompts" not in d

    def test_to_dict_batched(self):
        """Test converting batched request to dict."""
        request = LMRequest(prompts=["A", "B"], depth=0)
        d = request.to_dict()
        assert d["prompts"] == ["A", "B"]
        assert d["depth"] == 0
        assert "prompt" not in d
        assert "model" not in d

    def test_from_dict_single_prompt(self):
        """Test creating from dict with single prompt."""
        data = {"prompt": "Hello", "model": "gpt-4", "depth": 1}
        request = LMRequest.from_dict(data)
        assert request.prompt == "Hello"
        assert request.model == "gpt-4"
        assert request.depth == 1

    def test_from_dict_batched(self):
        """Test creating from dict with batched prompts."""
        data = {"prompts": ["A", "B", "C"], "depth": 2}
        request = LMRequest.from_dict(data)
        assert request.prompts == ["A", "B", "C"]
        assert request.depth == 2

    def test_roundtrip(self):
        """Test dict conversion roundtrip."""
        original = LMRequest(prompt="Test", model="gpt-4", depth=3)
        restored = LMRequest.from_dict(original.to_dict())
        assert restored.prompt == original.prompt
        assert restored.model == original.model
        assert restored.depth == original.depth


# LMResponse Tests


class TestLMResponse:
    """Tests for LMResponse dataclass."""

    def test_success_response(self):
        """Test creating a successful response."""
        completion = make_chat_completion("Hello!")
        response = LMResponse.success_response(completion)
        assert response.success is True
        assert response.error is None
        assert response.chat_completion.response == "Hello!"

    def test_error_response(self):
        """Test creating an error response."""
        response = LMResponse.error_response("Something went wrong")
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.chat_completion is None

    def test_batched_success_response(self):
        """Test creating a batched successful response."""
        completions = [
            make_chat_completion("Response 1"),
            make_chat_completion("Response 2"),
        ]
        response = LMResponse.batched_success_response(completions)
        assert response.success is True
        assert response.is_batched is True
        assert len(response.chat_completions) == 2

    def test_is_batched_property(self):
        """Test is_batched property."""
        single = LMResponse.success_response(make_chat_completion("Test"))
        assert single.is_batched is False

        batched = LMResponse.batched_success_response([make_chat_completion("Test")])
        assert batched.is_batched is True

    def test_to_dict_success(self):
        """Test converting successful response to dict."""
        completion = make_chat_completion("Hello!")
        response = LMResponse.success_response(completion)
        d = response.to_dict()
        assert d["error"] is None
        assert d["chat_completion"]["response"] == "Hello!"
        assert d["chat_completions"] is None

    def test_to_dict_error(self):
        """Test converting error response to dict."""
        response = LMResponse.error_response("Failed")
        d = response.to_dict()
        assert d["error"] == "Failed"
        assert d["chat_completion"] is None

    def test_from_dict_success(self):
        """Test creating from dict with successful response."""
        data = {
            "chat_completion": {
                "root_model": "test-model",
                "prompt": "test",
                "response": "Hello!",
                "usage_summary": {"model_usage_summaries": {}},
                "execution_time": 0.1,
            },
            "error": None,
            "chat_completions": None,
        }
        response = LMResponse.from_dict(data)
        assert response.success is True
        assert response.chat_completion.response == "Hello!"

    def test_from_dict_error(self):
        """Test creating from dict with error."""
        data = {"error": "Something failed", "chat_completion": None}
        response = LMResponse.from_dict(data)
        assert response.success is False
        assert response.error == "Something failed"

    def test_empty_response_is_error(self):
        """Test that response with no completion or error produces error dict."""
        response = LMResponse()
        d = response.to_dict()
        assert "No chat completion or error provided" in d["error"]


# Socket Protocol Tests


class TestSocketProtocol:
    """Tests for socket send/recv protocol."""

    def test_socket_send_format(self):
        """Test that socket_send uses correct protocol format."""
        mock_sock = Mock()
        data = {"message": "Hello"}

        socket_send(mock_sock, data)

        # Verify sendall was called once
        mock_sock.sendall.assert_called_once()

        # Get the sent bytes
        sent_bytes = mock_sock.sendall.call_args[0][0]

        # First 4 bytes should be big-endian length
        length = struct.unpack(">I", sent_bytes[:4])[0]
        payload = sent_bytes[4:]

        assert length == len(payload)
        assert json.loads(payload.decode("utf-8")) == data

    def test_socket_recv_success(self):
        """Test receiving a valid message."""
        data = {"response": "World"}
        payload = json.dumps(data).encode("utf-8")
        length_prefix = struct.pack(">I", len(payload))

        mock_sock = Mock()
        # First call returns length, second returns payload
        mock_sock.recv.side_effect = [length_prefix, payload]

        result = socket_recv(mock_sock)
        assert result == data

    def test_socket_recv_empty_returns_empty_dict(self):
        """Test that empty recv (connection closed) returns empty dict."""
        mock_sock = Mock()
        mock_sock.recv.return_value = b""

        result = socket_recv(mock_sock)
        assert result == {}

    def test_socket_recv_partial_payload(self):
        """Test receiving payload in multiple chunks."""
        data = {"large": "x" * 1000}
        payload = json.dumps(data).encode("utf-8")
        length_prefix = struct.pack(">I", len(payload))

        mock_sock = Mock()
        # Simulate receiving in chunks
        chunk1 = payload[:500]
        chunk2 = payload[500:]
        mock_sock.recv.side_effect = [length_prefix, chunk1, chunk2]

        result = socket_recv(mock_sock)
        assert result == data

    def test_socket_recv_connection_closed_mid_message(self):
        """Test that connection closing mid-message raises error."""
        mock_sock = Mock()
        length_prefix = struct.pack(">I", 1000)  # Expect 1000 bytes
        mock_sock.recv.side_effect = [length_prefix, b"short", b""]  # Connection closes

        with pytest.raises(ConnectionError, match="Connection closed before message complete"):
            socket_recv(mock_sock)


# socket_request Tests


class TestSocketRequest:
    """Tests for socket_request function."""

    def test_socket_request_success(self):
        """Test successful request/response cycle."""
        request_data = {"prompt": "Hello"}
        response_data = {"content": "World"}

        with patch("rlm.core.comms_utils.socket.socket") as mock_socket_class:
            mock_sock = MagicMock()
            mock_socket_class.return_value.__enter__.return_value = mock_sock

            # Set up recv to return response
            payload = json.dumps(response_data).encode("utf-8")
            length_prefix = struct.pack(">I", len(payload))
            mock_sock.recv.side_effect = [length_prefix, payload]

            result = socket_request(("localhost", 5000), request_data)

            # Verify connection was made
            mock_sock.connect.assert_called_once_with(("localhost", 5000))
            # Verify timeout was set
            mock_sock.settimeout.assert_called_once_with(300)
            # Verify response
            assert result == response_data


# send_lm_request Tests


class TestSendLMRequest:
    """Tests for send_lm_request function."""

    def test_send_lm_request_success(self):
        """Test successful LM request."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.return_value = {
                "chat_completion": {
                    "root_model": "test",
                    "prompt": "test",
                    "response": "Hello!",
                    "usage_summary": {"model_usage_summaries": {}},
                    "execution_time": 0.1,
                },
                "error": None,
            }

            request = LMRequest(prompt="Test")
            response = send_lm_request(("localhost", 5000), request)

            assert response.success is True
            assert response.chat_completion.response == "Hello!"

    def test_send_lm_request_error(self):
        """Test LM request that returns error."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.return_value = {"error": "Model overloaded"}

            request = LMRequest(prompt="Test")
            response = send_lm_request(("localhost", 5000), request)

            assert response.success is False
            assert response.error == "Model overloaded"

    def test_send_lm_request_exception(self):
        """Test LM request that raises exception."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.side_effect = ConnectionError("Connection refused")

            request = LMRequest(prompt="Test")
            response = send_lm_request(("localhost", 5000), request)

            assert response.success is False
            assert "Connection refused" in response.error

    def test_send_lm_request_depth_override(self):
        """Test that depth parameter overrides request depth."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.return_value = {
                "chat_completion": {
                    "root_model": "test",
                    "prompt": "test",
                    "response": "Test",
                    "usage_summary": {"model_usage_summaries": {}},
                    "execution_time": 0.1,
                },
                "error": None,
            }

            request = LMRequest(prompt="Test", depth=0)
            send_lm_request(("localhost", 5000), request, depth=5)

            # Verify the request was modified
            assert request.depth == 5


# send_lm_request_batched Tests


class TestSendLMRequestBatched:
    """Tests for send_lm_request_batched function."""

    def test_batched_success(self):
        """Test successful batched request."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.return_value = {
                "chat_completions": [
                    {
                        "root_model": "test",
                        "prompt": "test",
                        "response": "Response 1",
                        "usage_summary": {"model_usage_summaries": {}},
                        "execution_time": 0.1,
                    },
                    {
                        "root_model": "test",
                        "prompt": "test",
                        "response": "Response 2",
                        "usage_summary": {"model_usage_summaries": {}},
                        "execution_time": 0.1,
                    },
                ],
                "error": None,
            }

            responses = send_lm_request_batched(
                ("localhost", 5000),
                prompts=["Prompt 1", "Prompt 2"],
            )

            assert len(responses) == 2
            assert all(r.success for r in responses)
            assert responses[0].chat_completion.response == "Response 1"
            assert responses[1].chat_completion.response == "Response 2"

    def test_batched_error(self):
        """Test batched request that returns error."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.return_value = {"error": "Rate limited"}

            responses = send_lm_request_batched(
                ("localhost", 5000),
                prompts=["A", "B", "C"],
            )

            assert len(responses) == 3
            assert all(not r.success for r in responses)
            assert all("Rate limited" in r.error for r in responses)

    def test_batched_exception(self):
        """Test batched request that raises exception."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.side_effect = TimeoutError("Connection timed out")

            responses = send_lm_request_batched(
                ("localhost", 5000),
                prompts=["A", "B"],
            )

            assert len(responses) == 2
            assert all(not r.success for r in responses)
            assert all("Connection timed out" in r.error for r in responses)

    def test_batched_no_completions_returned(self):
        """Test when server returns success but no completions."""
        with patch("rlm.core.comms_utils.socket_request") as mock_request:
            mock_request.return_value = {"error": None, "chat_completions": None}

            responses = send_lm_request_batched(
                ("localhost", 5000),
                prompts=["A", "B"],
            )

            assert len(responses) == 2
            assert all(not r.success for r in responses)
            assert all("No completions returned" in r.error for r in responses)
