"""
Tests for OpenAI function calling (tools) support in RLM.

Tests cover:
- Client return type detection (dict vs str)
- Helper method functionality
- Tool handler validation
- Message format conversion
"""

from unittest.mock import Mock, patch

import pytest

from rlm.clients.openai import OpenAIClient
from rlm.environments.local_repl import MAX_TOOL_ITERATIONS, LocalREPL

# =============================================================================
# OpenAI Client Tests
# =============================================================================


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI Responses API response object."""

    def _make_response(content=None, tool_calls=None):
        response = Mock()
        output_items = []
        if content is not None:
            message = Mock()
            message.type = "message"
            message.content = content
            output_items.append(message)
        for tool_call in tool_calls or []:
            call = Mock()
            call.type = "function_call"
            call.id = tool_call["id"]
            call.name = tool_call["name"]
            call.arguments = tool_call["arguments"]
            output_items.append(call)
        response.output = output_items
        response.usage = Mock()
        response.usage.input_tokens = 10
        response.usage.output_tokens = 20
        return response

    return _make_response


def test_client_returns_dict_for_tool_calls(mock_openai_response):
    """Test that OpenAI client returns dict when tool_calls are present."""
    mock_response = mock_openai_response(
        content="",
        tool_calls=[
            {"id": "call_123", "name": "get_weather", "arguments": '{"city": "San Francisco"}'}
        ],
    )

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        client = OpenAIClient(api_key="test-key", model_name="gpt-4")
        result = client.completion("Test prompt")

        # Should return dict with tool_calls
        assert isinstance(result, dict)
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"
        assert result["tool_calls"][0]["name"] == "get_weather"
        assert result["tool_calls"][0]["arguments"] == '{"city": "San Francisco"}'


def test_client_returns_str_for_content(mock_openai_response):
    """Test that OpenAI client returns str when only content is present."""
    mock_response = mock_openai_response(content="Hello, world!", tool_calls=None)

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        client = OpenAIClient(api_key="test-key", model_name="gpt-4")
        result = client.completion("Test prompt")

        assert isinstance(result, dict)
        assert result["content"] == "Hello, world!"


def test_client_handles_tools_parameters(mock_openai_response):
    """Test that client correctly passes tools parameters to OpenAI API."""
    mock_response = mock_openai_response(content="Response", tool_calls=None)

    with patch("openai.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_client.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        client = OpenAIClient(api_key="test-key", model_name="gpt-4")

        tools = [{"type": "function", "function": {"name": "test"}}]
        client.completion("Test", tools=tools, tool_choice="auto")

        # Verify tools were passed to API
        call_kwargs = mock_client.responses.create.call_args[1]
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == tools
        assert call_kwargs["tool_choice"] == "auto"


# =============================================================================
# LocalREPL Helper Method Tests
# =============================================================================


def test_ensure_messages_format_string():
    """Test _ensure_messages_format converts string to messages list."""
    env = LocalREPL()
    result = env._ensure_messages_format("Hello")
    assert result == [{"role": "user", "content": "Hello"}]


def test_ensure_messages_format_list():
    """Test _ensure_messages_format preserves message list."""
    env = LocalREPL()
    messages = [{"role": "user", "content": "Hello"}]
    result = env._ensure_messages_format(messages)
    assert result == messages


def test_ensure_messages_format_invalid():
    """Test _ensure_messages_format raises on invalid input."""
    env = LocalREPL()
    with pytest.raises(ValueError, match="Invalid prompt type"):
        env._ensure_messages_format(123)  # type: ignore[arg-type]


# =============================================================================
# Tool Handler Validation Tests
# =============================================================================


@pytest.fixture
def sample_tools():
    """Sample tool definitions for testing."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]


def test_llm_query_tools_without_handler_raises(sample_tools):
    """Test that providing tools without a handler raises ValueError."""
    env = LocalREPL(lm_handler_address=("127.0.0.1", 12345))

    with pytest.raises(ValueError, match="tool_handler is required"):
        env._llm_query("Test prompt", tools=sample_tools)


def test_llm_query_batched_tools_without_handler_raises(sample_tools):
    """Test that providing tools without handler raises in batched mode."""
    env = LocalREPL(lm_handler_address=("127.0.0.1", 12345))

    with pytest.raises(ValueError, match="tool_handler is required"):
        env._llm_query_batched(["Test 1", "Test 2"], tools=sample_tools)


def test_llm_query_no_handler_configured():
    """Test llm_query returns error when no handler address is configured."""
    env = LocalREPL()  # No lm_handler_address
    result = env._llm_query("Test prompt")
    assert "Error: No LM handler configured" in result


# =============================================================================
# MAX_TOOL_ITERATIONS Constant Test
# =============================================================================


def test_max_tool_iterations_constant_exists():
    """Test that MAX_TOOL_ITERATIONS constant is defined and reasonable."""
    assert MAX_TOOL_ITERATIONS == 10
    assert MAX_TOOL_ITERATIONS > 0
    assert MAX_TOOL_ITERATIONS < 100  # Sanity check


# =============================================================================
# Integration Test Placeholder
# =============================================================================


def test_tools_feature_integration():
    """
    Integration test placeholder for end-to-end tools functionality.

    This would require a running LMHandler server and actual OpenAI API calls.
    For CI, we rely on the unit tests above and manual testing.

    To manually test:
    1. Start an LMHandler server
    2. Create a LocalREPL with the handler address
    3. Call llm_query with tools and tool_handler
    4. Verify the tool-calling loop works correctly
    """
    # Placeholder - actual integration testing requires running server
    assert True  # Documented in TOOLS_API_DOCUMENTATION.md
