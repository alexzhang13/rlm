"""Tests for the Anthropic client."""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.anthropic import AnthropicClient
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


class TestAnthropicClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                assert client.model_name == "claude-sonnet-4-20250514"
                assert client.max_tokens == 32768

    def test_init_with_custom_max_tokens(self):
        """Test client initialization with custom max_tokens."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(
                    api_key="test-key",
                    model_name="claude-sonnet-4-20250514",
                    max_tokens=4096,
                )
                assert client.max_tokens == 4096

    def test_usage_tracking_initialization(self):
        """Test that usage tracking is properly initialized."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                assert dict(client.model_call_counts) == {}
                assert dict(client.model_input_tokens) == {}
                assert dict(client.model_output_tokens) == {}
                assert dict(client.model_total_tokens) == {}

    def test_get_usage_summary_empty(self):
        """Test usage summary when no calls have been made."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                summary = client.get_usage_summary()
                assert isinstance(summary, UsageSummary)
                assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        """Test last usage returns correct format."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                client.last_prompt_tokens = 100
                client.last_completion_tokens = 50
                usage = client.get_last_usage()
                assert isinstance(usage, ModelUsageSummary)
                assert usage.total_calls == 1
                assert usage.total_input_tokens == 100
                assert usage.total_output_tokens == 50

    def test_completion_requires_model(self):
        """Test completion raises when no model specified."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key", model_name=None)
                with pytest.raises(ValueError, match="Model name is required"):
                    client.completion("Hello")

    def test_completion_invalid_prompt_type(self):
        """Test completion raises on invalid prompt type."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                with pytest.raises(ValueError, match="Invalid prompt type"):
                    client.completion(12345)


class TestAnthropicPrepareMessages:
    """Tests for the _prepare_messages method."""

    def test_prepare_messages_string_prompt(self):
        """Test _prepare_messages converts string to user message."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                messages, system = client._prepare_messages("Hello world")
                assert messages == [{"role": "user", "content": "Hello world"}]
                assert system is None

    def test_prepare_messages_list_without_system(self):
        """Test _prepare_messages with message list, no system message."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                input_messages = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there"},
                    {"role": "user", "content": "How are you?"},
                ]
                messages, system = client._prepare_messages(input_messages)
                assert messages == input_messages
                assert system is None

    def test_prepare_messages_extracts_system_message(self):
        """Test _prepare_messages extracts system message from list."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                input_messages = [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello"},
                ]
                messages, system = client._prepare_messages(input_messages)
                assert system == "You are a helpful assistant"
                assert messages == [{"role": "user", "content": "Hello"}]

    def test_prepare_messages_preserves_non_system_messages(self):
        """Test _prepare_messages preserves all non-system messages."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                input_messages = [
                    {"role": "system", "content": "Be helpful"},
                    {"role": "user", "content": "Question 1"},
                    {"role": "assistant", "content": "Answer 1"},
                    {"role": "user", "content": "Question 2"},
                ]
                messages, system = client._prepare_messages(input_messages)
                assert system == "Be helpful"
                assert len(messages) == 3
                assert messages[0] == {"role": "user", "content": "Question 1"}
                assert messages[1] == {"role": "assistant", "content": "Answer 1"}
                assert messages[2] == {"role": "user", "content": "Question 2"}

    def test_prepare_messages_invalid_type_raises(self):
        """Test _prepare_messages raises on invalid input type."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key")
                with pytest.raises(ValueError, match="Invalid prompt type"):
                    client._prepare_messages(12345)


class TestAnthropicCompletion:
    """Tests for the completion method with mocked API."""

    def test_completion_with_string_prompt(self):
        """Test completion converts string prompt to messages."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Hello from Anthropic!"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                result = client.completion("Hello")

                assert result == "Hello from Anthropic!"
                call_args = mock_client.messages.create.call_args
                assert call_args.kwargs["messages"] == [{"role": "user", "content": "Hello"}]
                assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"
                assert "system" not in call_args.kwargs

    def test_completion_with_message_list(self):
        """Test completion with message list format."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 10

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                messages = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"},
                    {"role": "user", "content": "How are you?"},
                ]
                result = client.completion(messages)

                assert result == "Response"
                call_args = mock_client.messages.create.call_args
                assert call_args.kwargs["messages"] == messages

    def test_completion_with_system_message(self):
        """Test completion passes system message to API."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "I am helpful"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 8

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                messages = [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"},
                ]
                result = client.completion(messages)

                assert result == "I am helpful"
                call_args = mock_client.messages.create.call_args
                assert call_args.kwargs["system"] == "You are helpful"
                assert call_args.kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    def test_completion_with_model_override(self):
        """Test completion uses provided model over default."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                client.completion("Test", model="claude-3-haiku-20240307")

                call_args = mock_client.messages.create.call_args
                assert call_args.kwargs["model"] == "claude-3-haiku-20240307"


class TestAnthropicUsageTracking:
    """Tests for usage tracking functionality."""

    def test_completion_tracks_usage(self):
        """Test completion properly tracks usage statistics."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                client.completion("Test")

                assert client.model_call_counts["claude-sonnet-4-20250514"] == 1
                assert client.model_input_tokens["claude-sonnet-4-20250514"] == 100
                assert client.model_output_tokens["claude-sonnet-4-20250514"] == 50
                assert client.model_total_tokens["claude-sonnet-4-20250514"] == 150
                assert client.last_prompt_tokens == 100
                assert client.last_completion_tokens == 50

    def test_completion_multiple_calls_accumulate_usage(self):
        """Test that multiple completions accumulate usage correctly."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                client.completion("Test 1")
                client.completion("Test 2")
                client.completion("Test 3")

                assert client.model_call_counts["claude-sonnet-4-20250514"] == 3
                assert client.model_input_tokens["claude-sonnet-4-20250514"] == 30
                assert client.model_output_tokens["claude-sonnet-4-20250514"] == 15
                assert client.model_total_tokens["claude-sonnet-4-20250514"] == 45

    def test_completion_with_different_models_tracks_separately(self):
        """Test completion tracks usage separately for different models."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                client.completion("Test 1")
                client.completion("Test 2", model="claude-3-haiku-20240307")
                client.completion("Test 3", model="claude-sonnet-4-20250514")

                assert client.model_call_counts["claude-sonnet-4-20250514"] == 2
                assert client.model_call_counts["claude-3-haiku-20240307"] == 1

    def test_get_usage_summary_after_calls(self):
        """Test usage summary returns correct data after calls."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic_class:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_anthropic_class.return_value = mock_client

                client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
                client.completion("Test")

                summary = client.get_usage_summary()
                assert "claude-sonnet-4-20250514" in summary.model_usage_summaries
                model_summary = summary.model_usage_summaries["claude-sonnet-4-20250514"]
                assert model_summary.total_calls == 1
                assert model_summary.total_input_tokens == 100
                assert model_summary.total_output_tokens == 50


class TestAnthropicClientAsync:
    """Tests for async completion method."""

    def test_acompletion_with_string_prompt(self):
        """Test async completion with string prompt."""
        import asyncio

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Async response"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        async def run_test():
            with patch("rlm.clients.anthropic.anthropic.Anthropic"):
                with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic") as mock_async_class:
                    mock_async_client = MagicMock()

                    async def mock_create(**kwargs):
                        return mock_response

                    mock_async_client.messages.create = mock_create
                    mock_async_class.return_value = mock_async_client

                    client = AnthropicClient(
                        api_key="test-key", model_name="claude-sonnet-4-20250514"
                    )
                    result = await client.acompletion("Hello")

                    assert result == "Async response"

        asyncio.run(run_test())

    def test_acompletion_requires_model(self):
        """Test async completion raises when no model specified."""
        import asyncio

        async def run_test():
            with patch("rlm.clients.anthropic.anthropic.Anthropic"):
                with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                    client = AnthropicClient(api_key="test-key", model_name=None)
                    with pytest.raises(ValueError, match="Model name is required"):
                        await client.acompletion("Hello")

        asyncio.run(run_test())

    def test_acompletion_invalid_prompt_type(self):
        """Test async completion raises on invalid prompt type."""
        import asyncio

        async def run_test():
            with patch("rlm.clients.anthropic.anthropic.Anthropic"):
                with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                    client = AnthropicClient(
                        api_key="test-key", model_name="claude-sonnet-4-20250514"
                    )
                    with pytest.raises(ValueError, match="Invalid prompt type"):
                        await client.acompletion(12345)

        asyncio.run(run_test())

    def test_acompletion_with_system_message(self):
        """Test async completion with system message."""
        import asyncio

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "I am helpful"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 8

        async def run_test():
            with patch("rlm.clients.anthropic.anthropic.Anthropic"):
                with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic") as mock_async_class:
                    mock_async_client = MagicMock()
                    captured_kwargs = {}

                    async def mock_create(**kwargs):
                        captured_kwargs.update(kwargs)
                        return mock_response

                    mock_async_client.messages.create = mock_create
                    mock_async_class.return_value = mock_async_client

                    client = AnthropicClient(
                        api_key="test-key", model_name="claude-sonnet-4-20250514"
                    )
                    messages = [
                        {"role": "system", "content": "You are helpful"},
                        {"role": "user", "content": "Hello"},
                    ]
                    result = await client.acompletion(messages)

                    assert result == "I am helpful"
                    assert captured_kwargs["system"] == "You are helpful"
                    assert captured_kwargs["messages"] == [{"role": "user", "content": "Hello"}]

        asyncio.run(run_test())


class TestAnthropicClientIntegration:
    """Integration tests that require a real API key."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = AnthropicClient(model_name="claude-3-haiku-20240307")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "claude-3-haiku-20240307" in usage.model_usage_summaries
        assert usage.model_usage_summaries["claude-3-haiku-20240307"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = AnthropicClient(model_name="claude-3-haiku-20240307")
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_async_completion(self):
        """Test async completion."""
        import asyncio

        async def run_test():
            client = AnthropicClient(model_name="claude-3-haiku-20240307")
            result = await client.acompletion("What is 3+3? Reply with just the number.")
            assert "6" in result

        asyncio.run(run_test())


if __name__ == "__main__":
    # Run integration tests directly
    test = TestAnthropicClientIntegration()
    print("Testing simple completion...")
    test.test_simple_completion()
    print("Testing message list completion...")
    test.test_message_list_completion()
    print("All integration tests passed!")
