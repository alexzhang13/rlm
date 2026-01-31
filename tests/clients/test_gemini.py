"""Tests for the Gemini client."""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.gemini import GeminiClient
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


@patch("rlm.clients.gemini.genai.Client")
class TestGeminiClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self, mock_client_class):
        """Test client initialization with explicit API key."""
        client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
        mock_client_class.assert_called_with(api_key="test-key")
        assert client.model_name == "gemini-2.5-flash"

    def test_init_default_model(self, mock_client_class):
        """Test client uses default model name."""
        client = GeminiClient(api_key="test-key")
        assert client.model_name == "gemini-2.5-flash"

    def test_init_requires_api_key(self, mock_client_class):
        """Test client raises error when no API key provided."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("rlm.clients.gemini.DEFAULT_GEMINI_API_KEY", None):
                with pytest.raises(ValueError, match="Gemini API key is required"):
                    GeminiClient(api_key=None)

    def test_usage_tracking_initialization(self, mock_client_class):
        """Test that usage tracking is properly initialized."""
        client = GeminiClient(api_key="test-key")
        assert client.model_call_counts == {}
        assert client.model_input_tokens == {}
        assert client.model_output_tokens == {}
        assert client.last_prompt_tokens == 0
        assert client.last_completion_tokens == 0

    def test_get_usage_summary_empty(self, mock_client_class):
        """Test usage summary when no calls have been made."""
        client = GeminiClient(api_key="test-key")
        summary = client.get_usage_summary()
        assert isinstance(summary, UsageSummary)
        assert summary.model_usage_summaries == {}

    def test_get_last_usage(self, mock_client_class):
        """Test last usage returns correct format."""
        client = GeminiClient(api_key="test-key")
        client.last_prompt_tokens = 100
        client.last_completion_tokens = 50
        usage = client.get_last_usage()
        assert isinstance(usage, ModelUsageSummary)
        assert usage.total_calls == 1
        assert usage.total_input_tokens == 100
        assert usage.total_output_tokens == 50

    def test_prepare_contents_string(self, mock_client_class):
        """Test _prepare_contents with string input."""
        client = GeminiClient(api_key="test-key")
        contents, system = client._prepare_contents("Hello world")
        assert contents == "Hello world"
        assert system is None

    def test_prepare_contents_messages_with_system(self, mock_client_class):
        """Test _prepare_contents extracts system message."""
        client = GeminiClient(api_key="test-key")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        contents, system = client._prepare_contents(messages)
        assert system == "You are helpful"
        assert len(contents) == 1
        assert contents[0]["role"] == "user"
        assert contents[0]["parts"][0]["text"] == "Hello"

    def test_prepare_contents_role_mapping(self, mock_client_class):
        """Test _prepare_contents maps assistant to model."""
        client = GeminiClient(api_key="test-key")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]
        contents, system = client._prepare_contents(messages)
        assert system is None
        assert len(contents) == 3
        assert contents[0]["role"] == "user"
        assert contents[1]["role"] == "model"
        assert contents[2]["role"] == "user"

    def test_prepare_contents_invalid_type(self, mock_client_class):
        """Test _prepare_contents raises on invalid input."""
        client = GeminiClient(api_key="test-key")
        with pytest.raises(ValueError, match="Invalid prompt type"):
            client._prepare_contents(12345)

    def test_completion_requires_model(self, mock_client_class):
        """Test completion raises when no model specified."""
        client = GeminiClient(api_key="test-key", model_name=None)
        with pytest.raises(ValueError, match="Model name is required"):
            client.completion("Hello")

    def test_completion_with_mocked_response(self, mock_client_class):
        """Test completion with mocked API response."""
        mock_client = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini!"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5

        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
        result = client.completion("Hello")

        assert result == "Hello from Gemini!"
        assert client.model_call_counts["gemini-2.5-flash"] == 1
        assert client.model_input_tokens["gemini-2.5-flash"] == 10
        assert client.model_output_tokens["gemini-2.5-flash"] == 5


class TestGeminiClientIntegration:
    """Integration tests that require a real API key."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "gemini-2.5-flash" in usage.model_usage_summaries
        assert usage.model_usage_summaries["gemini-2.5-flash"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        result = await client.acompletion("What is 3+3? Reply with just the number.")
        assert "6" in result
