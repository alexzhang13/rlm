"""Tests for the OpenAI client."""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.openai import (
    DEFAULT_PRIME_INTELLECT_BASE_URL,
    OpenAIClient,
)
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


class TestOpenAIClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                assert client.model_name == "gpt-4o"

    def test_init_with_base_url(self):
        """Test client initialization with custom base URL."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI") as mock_async:
                client = OpenAIClient(
                    api_key="test-key",
                    model_name="gpt-4o",
                    base_url="https://custom.api.com/v1",
                )
                mock_openai.assert_called_once_with(
                    api_key="test-key", base_url="https://custom.api.com/v1"
                )
                mock_async.assert_called_once_with(
                    api_key="test-key", base_url="https://custom.api.com/v1"
                )
                assert client.model_name == "gpt-4o"

    def test_init_auto_selects_openrouter_key(self):
        """Test client auto-selects OpenRouter API key for OpenRouter base URL."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                with patch("rlm.clients.openai.DEFAULT_OPENROUTER_API_KEY", "openrouter-key"):
                    OpenAIClient(
                        api_key=None,
                        model_name="gpt-4o",
                        base_url="https://openrouter.ai/api/v1",
                    )
                    mock_openai.assert_called_once_with(
                        api_key="openrouter-key", base_url="https://openrouter.ai/api/v1"
                    )

    def test_init_auto_selects_vercel_key(self):
        """Test client auto-selects Vercel API key for AI Gateway base URL."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                with patch("rlm.clients.openai.DEFAULT_VERCEL_API_KEY", "vercel-key"):
                    OpenAIClient(
                        api_key=None,
                        model_name="gpt-4o",
                        base_url="https://ai-gateway.vercel.sh/v1",
                    )
                    mock_openai.assert_called_once_with(
                        api_key="vercel-key", base_url="https://ai-gateway.vercel.sh/v1"
                    )

    def test_usage_tracking_initialization(self):
        """Test that usage tracking is properly initialized."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key")
                assert dict(client.model_call_counts) == {}
                assert dict(client.model_input_tokens) == {}
                assert dict(client.model_output_tokens) == {}
                assert dict(client.model_total_tokens) == {}

    def test_get_usage_summary_empty(self):
        """Test usage summary when no calls have been made."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key")
                summary = client.get_usage_summary()
                assert isinstance(summary, UsageSummary)
                assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        """Test last usage returns correct format."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key")
                client.last_prompt_tokens = 100
                client.last_completion_tokens = 50
                usage = client.get_last_usage()
                assert isinstance(usage, ModelUsageSummary)
                assert usage.total_calls == 1
                assert usage.total_input_tokens == 100
                assert usage.total_output_tokens == 50

    def test_completion_requires_model(self):
        """Test completion raises when no model specified."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name=None)
                with pytest.raises(ValueError, match="Model name is required"):
                    client.completion("Hello")

    def test_completion_invalid_prompt_type(self):
        """Test completion raises on invalid prompt type."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                with pytest.raises(ValueError, match="Invalid prompt type"):
                    client.completion(12345)

    def test_completion_with_string_prompt(self):
        """Test completion converts string prompt to messages."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from OpenAI!"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = "https://api.openai.com/v1"
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                result = client.completion("Hello")

                assert result == "Hello from OpenAI!"
                # Verify the prompt was converted to messages format
                call_args = mock_client.chat.completions.create.call_args
                assert call_args.kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    def test_completion_with_message_list(self):
        """Test completion with message list format."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 30

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = "https://api.openai.com/v1"
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                messages = [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"},
                ]
                result = client.completion(messages)

                assert result == "Response"
                # Verify messages were passed directly
                call_args = mock_client.chat.completions.create.call_args
                assert call_args.kwargs["messages"] == messages

    def test_completion_tracks_usage(self):
        """Test completion properly tracks usage statistics."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = "https://api.openai.com/v1"
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                client.completion("Test")

                assert client.model_call_counts["gpt-4o"] == 1
                assert client.model_input_tokens["gpt-4o"] == 100
                assert client.model_output_tokens["gpt-4o"] == 50
                assert client.model_total_tokens["gpt-4o"] == 150
                assert client.last_prompt_tokens == 100
                assert client.last_completion_tokens == 50

    def test_completion_multiple_calls_accumulate_usage(self):
        """Test that multiple completions accumulate usage correctly."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = "https://api.openai.com/v1"
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                client.completion("Test 1")
                client.completion("Test 2")
                client.completion("Test 3")

                assert client.model_call_counts["gpt-4o"] == 3
                assert client.model_input_tokens["gpt-4o"] == 30
                assert client.model_output_tokens["gpt-4o"] == 15
                assert client.model_total_tokens["gpt-4o"] == 45

    def test_get_usage_summary_after_calls(self):
        """Test usage summary returns correct data after calls."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = "https://api.openai.com/v1"
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                client.completion("Test")

                summary = client.get_usage_summary()
                assert "gpt-4o" in summary.model_usage_summaries
                model_summary = summary.model_usage_summaries["gpt-4o"]
                assert model_summary.total_calls == 1
                assert model_summary.total_input_tokens == 100
                assert model_summary.total_output_tokens == 50

    def test_track_cost_raises_on_missing_usage(self):
        """Test _track_cost raises when response has no usage data."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                mock_response = MagicMock()
                mock_response.usage = None

                with pytest.raises(ValueError, match="No usage data received"):
                    client._track_cost(mock_response, "gpt-4o")

    def test_completion_with_prime_intellect_base_url(self):
        """Test completion adds extra_body for Prime Intellect API."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = DEFAULT_PRIME_INTELLECT_BASE_URL
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(
                    api_key="test-key",
                    model_name="test-model",
                    base_url=DEFAULT_PRIME_INTELLECT_BASE_URL,
                )
                client.completion("Test")

                # Verify extra_body was passed
                call_args = mock_client.chat.completions.create.call_args
                assert call_args.kwargs["extra_body"] == {"usage": {"include": True}}

    def test_completion_with_different_models(self):
        """Test completion tracks usage separately for different models."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_client.base_url = "https://api.openai.com/v1"
                mock_openai_class.return_value = mock_client

                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                client.completion("Test 1")
                client.completion("Test 2", model="gpt-4o-mini")
                client.completion("Test 3", model="gpt-4o")

                assert client.model_call_counts["gpt-4o"] == 2
                assert client.model_call_counts["gpt-4o-mini"] == 1


class TestOpenAIClientAsync:
    """Tests for async completion method."""

    def test_acompletion_with_string_prompt(self):
        """Test async completion with string prompt."""
        import asyncio

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Async response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        async def run_test():
            with patch("rlm.clients.openai.openai.OpenAI"):
                with patch("rlm.clients.openai.openai.AsyncOpenAI") as mock_async_class:
                    mock_async_client = MagicMock()

                    # Make the async create method return a coroutine
                    async def mock_create(**kwargs):
                        return mock_response

                    mock_async_client.chat.completions.create = mock_create
                    mock_async_class.return_value = mock_async_client

                    client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                    client.client.base_url = "https://api.openai.com/v1"
                    result = await client.acompletion("Hello")

                    assert result == "Async response"

        asyncio.run(run_test())

    def test_acompletion_requires_model(self):
        """Test async completion raises when no model specified."""
        import asyncio

        async def run_test():
            with patch("rlm.clients.openai.openai.OpenAI"):
                with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                    client = OpenAIClient(api_key="test-key", model_name=None)
                    with pytest.raises(ValueError, match="Model name is required"):
                        await client.acompletion("Hello")

        asyncio.run(run_test())

    def test_acompletion_invalid_prompt_type(self):
        """Test async completion raises on invalid prompt type."""
        import asyncio

        async def run_test():
            with patch("rlm.clients.openai.openai.OpenAI"):
                with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                    client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                    with pytest.raises(ValueError, match="Invalid prompt type"):
                        await client.acompletion(12345)

        asyncio.run(run_test())


class TestOpenAIClientIntegration:
    """Integration tests that require a real API key."""

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = OpenAIClient(model_name="gpt-4o-mini")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "gpt-4o-mini" in usage.model_usage_summaries
        assert usage.model_usage_summaries["gpt-4o-mini"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = OpenAIClient(model_name="gpt-4o-mini")
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    def test_async_completion(self):
        """Test async completion."""
        import asyncio

        async def run_test():
            client = OpenAIClient(model_name="gpt-4o-mini")
            result = await client.acompletion("What is 3+3? Reply with just the number.")
            assert "6" in result

        asyncio.run(run_test())


if __name__ == "__main__":
    # Run integration tests directly
    test = TestOpenAIClientIntegration()
    print("Testing simple completion...")
    test.test_simple_completion()
    print("Testing message list completion...")
    test.test_message_list_completion()
    print("All integration tests passed!")
