"""Tests for the Anthropic client."""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.anthropic import AnthropicClient, _extract_text
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


def _text_block(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _thinking_block() -> MagicMock:
    block = MagicMock(spec=["type", "thinking"])
    block.type = "thinking"
    block.thinking = "reasoning..."
    return block


class TestExtractText:
    """Unit tests for the module-level _extract_text helper."""

    def test_text_only(self):
        assert _extract_text([_text_block("hello")]) == "hello"

    def test_thinking_then_text(self):
        content = [_thinking_block(), _text_block("hello")]
        assert _extract_text(content) == "hello"

    def test_no_text_block_raises(self):
        with pytest.raises(ValueError, match="no text block"):
            _extract_text([_thinking_block()])


class TestAnthropicClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self):
        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic"),
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"),
        ):
            client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-5")
            assert client.model_name == "claude-sonnet-5"

    def test_completion_requires_model(self):
        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic"),
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"),
        ):
            client = AnthropicClient(api_key="test-key", model_name=None)
            with pytest.raises(ValueError, match="Model name is required"):
                client.completion("Hello")

    def test_completion_with_mocked_response(self):
        mock_response = MagicMock()
        mock_response.content = [_text_block("Hello from Claude!")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_client_class,
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-5")
            result = client.completion("Hello")

            assert result == "Hello from Claude!"
            assert client.model_call_counts["claude-sonnet-5"] == 1
            assert client.model_input_tokens["claude-sonnet-5"] == 10
            assert client.model_output_tokens["claude-sonnet-5"] == 5

    def test_completion_with_leading_thinking_block(self):
        """Regression test: a ThinkingBlock preceding the text block must not crash."""
        mock_response = MagicMock()
        mock_response.content = [_thinking_block(), _text_block("Hello from Claude!")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_client_class,
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-5")
            result = client.completion("Hello")

            assert result == "Hello from Claude!"

    @pytest.mark.anyio
    async def test_acompletion_with_leading_thinking_block(self):
        mock_response = MagicMock()
        mock_response.content = [_thinking_block(), _text_block("Hello from Claude!")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic"),
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic") as mock_async_client_class,
        ):
            mock_async_client = MagicMock()

            async def _create(**kwargs):
                return mock_response

            mock_async_client.messages.create = _create
            mock_async_client_class.return_value = mock_async_client

            client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-5")
            result = await client.acompletion("Hello")

            assert result == "Hello from Claude!"

    def test_get_usage_summary_empty(self):
        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic"),
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"),
        ):
            client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-5")
            summary = client.get_usage_summary()
            assert isinstance(summary, UsageSummary)
            assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        with (
            patch("rlm.clients.anthropic.anthropic.Anthropic"),
            patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"),
        ):
            client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-5")
            client.last_prompt_tokens = 100
            client.last_completion_tokens = 50
            usage = client.get_last_usage()
            assert isinstance(usage, ModelUsageSummary)
            assert usage.total_calls == 1
            assert usage.total_input_tokens == 100
            assert usage.total_output_tokens == 50


class TestAnthropicClientIntegration:
    """Integration tests that require a real API key."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    )
    def test_simple_completion(self):
        client = AnthropicClient(model_name="claude-sonnet-5")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result
