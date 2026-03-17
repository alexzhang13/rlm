"""Tests for the MiniMax client."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.minimax import MinimaxClient
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


def _make_mock_response(content="Hello", prompt_tokens=10, completion_tokens=5):
    """Create a properly structured mock API response."""
    mock_usage = MagicMock(spec=[
        "prompt_tokens", "completion_tokens", "total_tokens",
    ])
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens
    mock_usage.total_tokens = prompt_tokens + completion_tokens

    mock_choice = MagicMock()
    mock_choice.message.content = content

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    return mock_response


class TestMinimaxClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5")
        assert client.model_name == "MiniMax-M2.5"

    def test_init_default_model(self):
        """Test client uses default model name."""
        client = MinimaxClient(api_key="test-key")
        assert client.model_name == "MiniMax-M2.5"

    def test_init_default_base_url(self):
        """Test client uses MiniMax base URL by default."""
        client = MinimaxClient(api_key="test-key")
        assert str(client.base_url) == "https://api.minimax.io/v1"

    def test_init_custom_base_url(self):
        """Test client accepts custom base URL."""
        client = MinimaxClient(api_key="test-key", base_url="https://api.minimaxi.com/v1")
        assert str(client.base_url) == "https://api.minimaxi.com/v1"

    def test_init_custom_model(self):
        """Test client accepts custom model name."""
        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5-highspeed")
        assert client.model_name == "MiniMax-M2.5-highspeed"

    def test_init_env_api_key(self):
        """Test client picks up MINIMAX_API_KEY from environment."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "env-test-key"}):
            with patch("rlm.clients.minimax.DEFAULT_MINIMAX_API_KEY", "env-test-key"):
                client = MinimaxClient()
                assert client.model_name == "MiniMax-M2.5"

    def test_usage_tracking_initialization(self):
        """Test that usage tracking is properly initialized."""
        client = MinimaxClient(api_key="test-key")
        assert dict(client.model_call_counts) == {}
        assert dict(client.model_input_tokens) == {}
        assert dict(client.model_output_tokens) == {}

    def test_get_usage_summary_empty(self):
        """Test usage summary when no calls have been made."""
        client = MinimaxClient(api_key="test-key")
        summary = client.get_usage_summary()
        assert isinstance(summary, UsageSummary)
        assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        """Test last usage returns correct format."""
        client = MinimaxClient(api_key="test-key")
        client.last_prompt_tokens = 100
        client.last_completion_tokens = 50
        usage = client.get_last_usage()
        assert isinstance(usage, ModelUsageSummary)
        assert usage.total_calls == 1
        assert usage.total_input_tokens == 100
        assert usage.total_output_tokens == 50

    def test_completion_with_string_prompt(self):
        """Test completion with string input sends correct temperature."""
        mock_response = _make_mock_response("Hello from MiniMax!", 10, 5)

        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5")
        client.client.chat.completions.create = MagicMock(return_value=mock_response)

        result = client.completion("Hello")
        assert result == "Hello from MiniMax!"

        # Verify temperature=1.0 is passed
        call_kwargs = client.client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("temperature") == 1.0

    def test_completion_with_message_list(self):
        """Test completion with message list format."""
        mock_response = _make_mock_response("Hi there!", 20, 10)

        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5")
        client.client.chat.completions.create = MagicMock(return_value=mock_response)

        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        result = client.completion(messages)
        assert result == "Hi there!"

        # Verify messages are passed through correctly
        call_kwargs = client.client.chat.completions.create.call_args
        assert call_kwargs.kwargs["messages"] == messages

    def test_completion_invalid_prompt(self):
        """Test completion raises on invalid prompt type."""
        client = MinimaxClient(api_key="test-key")
        with pytest.raises(ValueError, match="Invalid prompt type"):
            client.completion(12345)

    def test_completion_requires_model(self):
        """Test completion raises when no model specified."""
        client = MinimaxClient(api_key="test-key", model_name=None)
        client.model_name = None  # Override the default
        with pytest.raises(ValueError, match="Model name is required"):
            client.completion("Hello")

    def test_completion_tracks_usage(self):
        """Test that completion tracks usage correctly."""
        mock_response = _make_mock_response("Response", 15, 8)

        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5")
        client.client.chat.completions.create = MagicMock(return_value=mock_response)

        client.completion("Test prompt")
        assert client.model_call_counts["MiniMax-M2.5"] == 1
        assert client.model_input_tokens["MiniMax-M2.5"] == 15
        assert client.model_output_tokens["MiniMax-M2.5"] == 8

    @pytest.mark.asyncio
    async def test_acompletion_with_string_prompt(self):
        """Test async completion with string input."""
        mock_response = _make_mock_response("Async response", 10, 5)

        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5")

        async def mock_create(**kwargs):
            return mock_response

        client.async_client.chat.completions.create = mock_create

        result = await client.acompletion("Hello async")
        assert result == "Async response"

    @pytest.mark.asyncio
    async def test_acompletion_invalid_prompt(self):
        """Test async completion raises on invalid prompt type."""
        client = MinimaxClient(api_key="test-key")
        with pytest.raises(ValueError, match="Invalid prompt type"):
            await client.acompletion(12345)

    def test_completion_with_model_override(self):
        """Test completion with explicit model override."""
        mock_response = _make_mock_response("Highspeed response", 10, 5)

        client = MinimaxClient(api_key="test-key", model_name="MiniMax-M2.5")
        client.client.chat.completions.create = MagicMock(return_value=mock_response)

        result = client.completion("Hello", model="MiniMax-M2.5-highspeed")
        assert result == "Highspeed response"

        call_kwargs = client.client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "MiniMax-M2.5-highspeed"


class TestMinimaxClientIntegration:
    """Integration tests that require a real API key."""

    @pytest.mark.skipif(
        not os.environ.get("MINIMAX_API_KEY"),
        reason="MINIMAX_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = MinimaxClient(model_name="MiniMax-M2.5")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "MiniMax-M2.5" in usage.model_usage_summaries
        assert usage.model_usage_summaries["MiniMax-M2.5"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("MINIMAX_API_KEY"),
        reason="MINIMAX_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = MinimaxClient(model_name="MiniMax-M2.5")
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("MINIMAX_API_KEY"),
        reason="MINIMAX_API_KEY not set",
    )
    def test_highspeed_model(self):
        """Test completion with MiniMax-M2.5-highspeed model."""
        client = MinimaxClient(model_name="MiniMax-M2.5-highspeed")
        result = client.completion("What is 3+3? Reply with just the number.")
        assert "6" in result


if __name__ == "__main__":
    # Run integration tests directly
    test = TestMinimaxClientIntegration()
    print("Testing simple completion...")
    test.test_simple_completion()
    print("Testing message list completion...")
    test.test_message_list_completion()
    print("Testing highspeed model...")
    test.test_highspeed_model()
    print("All integration tests passed!")
