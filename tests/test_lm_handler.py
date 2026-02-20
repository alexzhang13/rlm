"""Tests for LMHandler.

Tests the LMHandler class which routes LLM requests from
the RLM process and environment subprocesses.
"""

from rlm.clients.base_lm import BaseLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import ModelUsageSummary, UsageSummary
from tests.mock_lm import MockLM

# Test Fixtures


class AnotherMockLM(BaseLM):
    """Another mock LM for testing multiple clients."""

    def __init__(self, model_name: str = "another-mock-model"):
        super().__init__(model_name=model_name)

    def completion(self, prompt):
        return f"Another mock response to: {prompt[:50]}"

    async def acompletion(self, prompt):
        return self.completion(prompt)

    def get_usage_summary(self):
        return UsageSummary(
            model_usage_summaries={
                self.model_name: ModelUsageSummary(
                    total_calls=2, total_input_tokens=20, total_output_tokens=20
                )
            }
        )

    def get_last_usage(self):
        return ModelUsageSummary(total_calls=1, total_input_tokens=10, total_output_tokens=10)


# LMHandler Initialization Tests


class TestLMHandlerInit:
    """Tests for LMHandler initialization."""

    def test_basic_init(self):
        """Test basic initialization with default values."""
        client = MockLM()
        handler = LMHandler(client)

        assert handler.default_client is client
        assert handler.other_backend_client is None
        assert handler.host == "127.0.0.1"
        assert handler._port == 0

    def test_init_with_custom_host_port(self):
        """Test initialization with custom host and port."""
        client = MockLM()
        handler = LMHandler(client, host="0.0.0.0", port=8080)

        assert handler.host == "0.0.0.0"
        assert handler._port == 8080

    def test_init_with_other_backend(self):
        """Test initialization with other_backend_client."""
        default_client = MockLM()
        other_client = AnotherMockLM()
        handler = LMHandler(default_client, other_backend_client=other_client)

        assert handler.default_client is default_client
        assert handler.other_backend_client is other_client

    def test_default_client_auto_registered(self):
        """Test that default client is auto-registered by model name."""
        client = MockLM()
        handler = LMHandler(client)

        assert "mock-model" in handler.clients
        assert handler.clients["mock-model"] is client


# get_client Routing Tests


class TestGetClientRouting:
    """Tests for get_client routing logic."""

    def test_get_client_default_no_args(self):
        """Test get_client returns default_client when no args provided."""
        client = MockLM()
        handler = LMHandler(client)

        result = handler.get_client()
        assert result is client

    def test_get_client_depth_0_returns_default(self):
        """Test depth=0 returns default_client."""
        default_client = MockLM()
        other_client = AnotherMockLM()
        handler = LMHandler(default_client, other_backend_client=other_client)

        result = handler.get_client(depth=0)
        assert result is default_client

    def test_get_client_depth_1_with_other_backend(self):
        """Test depth=1 returns other_backend_client when available."""
        default_client = MockLM()
        other_client = AnotherMockLM()
        handler = LMHandler(default_client, other_backend_client=other_client)

        result = handler.get_client(depth=1)
        assert result is other_client

    def test_get_client_depth_1_without_other_backend(self):
        """Test depth=1 returns default_client when other_backend not set."""
        default_client = MockLM()
        handler = LMHandler(default_client)

        result = handler.get_client(depth=1)
        assert result is default_client

    def test_get_client_by_model_name(self):
        """Test get_client returns registered client by model name."""
        default_client = MockLM()
        handler = LMHandler(default_client)

        result = handler.get_client(model="mock-model")
        assert result is default_client

    def test_get_client_model_overrides_depth(self):
        """Test that model name lookup overrides depth routing."""
        default_client = MockLM()
        other_client = AnotherMockLM()
        handler = LMHandler(default_client, other_backend_client=other_client)

        # Register another client with a specific name
        special_client = AnotherMockLM(model_name="special-model")
        handler.register_client("special-model", special_client)

        # Even with depth=1, should return special_client when model matches
        result = handler.get_client(model="special-model", depth=1)
        assert result is special_client

    def test_get_client_unknown_model_falls_back(self):
        """Test unknown model name falls back to depth routing."""
        default_client = MockLM()
        other_client = AnotherMockLM()
        handler = LMHandler(default_client, other_backend_client=other_client)

        # Unknown model with depth=1 should use other_backend
        result = handler.get_client(model="unknown-model", depth=1)
        assert result is other_client

        # Unknown model with depth=0 should use default
        result = handler.get_client(model="unknown-model", depth=0)
        assert result is default_client


# register_client Tests


class TestRegisterClient:
    """Tests for register_client method."""

    def test_register_new_client(self):
        """Test registering a new client."""
        default_client = MockLM()
        handler = LMHandler(default_client)

        new_client = AnotherMockLM(model_name="new-model")
        handler.register_client("new-model", new_client)

        assert "new-model" in handler.clients
        assert handler.clients["new-model"] is new_client

    def test_register_overwrites_existing(self):
        """Test registering a client with existing name overwrites it."""
        default_client = MockLM()
        handler = LMHandler(default_client)

        new_client = AnotherMockLM(model_name="mock-model")
        handler.register_client("mock-model", new_client)

        assert handler.clients["mock-model"] is new_client


# Completion Tests


class TestCompletion:
    """Tests for completion method using MockLM."""

    def test_completion_default_client(self):
        """Test completion uses default client."""
        client = MockLM()
        handler = LMHandler(client)

        result = handler.completion("Hello, world!")
        assert result == "Mock response to: Hello, world!"

    def test_completion_with_model(self):
        """Test completion with specific model."""
        default_client = MockLM()
        other_client = AnotherMockLM(model_name="other-model")
        handler = LMHandler(default_client)
        handler.register_client("other-model", other_client)

        result = handler.completion("Test prompt", model="other-model")
        assert result == "Another mock response to: Test prompt"


# Server Start/Stop Tests


class TestServerLifecycle:
    """Tests for server start/stop methods."""

    def test_start_creates_server(self):
        """Test start creates server and returns address."""
        client = MockLM()
        handler = LMHandler(client)

        try:
            address = handler.start()
            assert handler._server is not None
            assert handler._thread is not None
            assert address[0] == "127.0.0.1"
            assert address[1] > 0  # Auto-assigned port
        finally:
            handler.stop()

    def test_start_idempotent(self):
        """Test calling start multiple times returns same address."""
        client = MockLM()
        handler = LMHandler(client)

        try:
            address1 = handler.start()
            address2 = handler.start()
            assert address1 == address2
        finally:
            handler.stop()

    def test_stop_clears_server(self):
        """Test stop clears server and thread."""
        client = MockLM()
        handler = LMHandler(client)

        handler.start()
        handler.stop()

        assert handler._server is None
        assert handler._thread is None

    def test_port_property_returns_actual_port(self):
        """Test port property returns actual assigned port."""
        client = MockLM()
        handler = LMHandler(client, port=0)

        try:
            handler.start()
            # Port should be > 0 after auto-assignment
            assert handler.port > 0
        finally:
            handler.stop()

    def test_address_property(self):
        """Test address property returns (host, port) tuple."""
        client = MockLM()
        handler = LMHandler(client)

        try:
            handler.start()
            address = handler.address
            assert address == (handler.host, handler.port)
        finally:
            handler.stop()


# Context Manager Tests


class TestContextManager:
    """Tests for context manager protocol."""

    def test_enter_starts_server(self):
        """Test __enter__ starts the server."""
        client = MockLM()
        handler = LMHandler(client)

        with handler as h:
            assert h is handler
            assert handler._server is not None

    def test_exit_stops_server(self):
        """Test __exit__ stops the server."""
        client = MockLM()
        handler = LMHandler(client)

        with handler:
            pass

        assert handler._server is None

    def test_exit_returns_false(self):
        """Test __exit__ returns False (doesn't suppress exceptions)."""
        client = MockLM()
        handler = LMHandler(client)

        result = handler.__exit__(None, None, None)
        assert result is False


# Usage Summary Tests


class TestUsageSummary:
    """Tests for get_usage_summary method."""

    def test_usage_summary_single_client(self):
        """Test usage summary with single client."""
        client = MockLM()
        handler = LMHandler(client)

        summary = handler.get_usage_summary()
        assert "mock-model" in summary.model_usage_summaries

    def test_usage_summary_with_other_backend(self):
        """Test usage summary includes other_backend_client."""
        default_client = MockLM()
        other_client = AnotherMockLM()
        handler = LMHandler(default_client, other_backend_client=other_client)

        summary = handler.get_usage_summary()
        assert "mock-model" in summary.model_usage_summaries
        assert "another-mock-model" in summary.model_usage_summaries

    def test_usage_summary_merges_all_clients(self):
        """Test usage summary merges all registered clients."""
        default_client = MockLM()
        handler = LMHandler(default_client)

        extra_client = AnotherMockLM(model_name="extra-model")
        handler.register_client("extra-model", extra_client)

        summary = handler.get_usage_summary()
        assert "mock-model" in summary.model_usage_summaries
        assert "extra-model" in summary.model_usage_summaries


# Integration Tests (with socket communication)


class TestSocketIntegration:
    """Integration tests for socket-based communication."""

    def test_handler_accepts_connection(self):
        """Test that handler accepts socket connections."""
        client = MockLM()

        with LMHandler(client) as handler:
            # Server should be running and accepting connections
            assert handler._server is not None
            assert handler.port > 0

    def test_full_request_response_cycle(self):
        """Test full request/response cycle through socket."""
        from rlm.core.comms_utils import LMRequest, send_lm_request

        client = MockLM()

        with LMHandler(client) as handler:
            request = LMRequest(prompt="Test prompt")
            response = send_lm_request(handler.address, request)

            assert response.success is True
            assert "Mock response to: Test prompt" in response.chat_completion.response

    def test_request_with_depth_routing(self):
        """Test request with depth parameter routes correctly."""
        from rlm.core.comms_utils import LMRequest, send_lm_request

        default_client = MockLM()
        other_client = AnotherMockLM()

        with LMHandler(default_client, other_backend_client=other_client) as handler:
            # depth=0 should use default
            request0 = LMRequest(prompt="Test", depth=0)
            response0 = send_lm_request(handler.address, request0)
            assert "Mock response" in response0.chat_completion.response

            # depth=1 should use other backend
            request1 = LMRequest(prompt="Test", depth=1)
            response1 = send_lm_request(handler.address, request1)
            assert "Another mock response" in response1.chat_completion.response

    def test_batched_request(self):
        """Test batched request handling."""
        from rlm.core.comms_utils import send_lm_request_batched

        client = MockLM()

        with LMHandler(client) as handler:
            prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
            responses = send_lm_request_batched(handler.address, prompts=prompts)

            assert len(responses) == 3
            assert all(r.success for r in responses)
            for i, response in enumerate(responses):
                assert f"Prompt {i + 1}" in response.chat_completion.response
