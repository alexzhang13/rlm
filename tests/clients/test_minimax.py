"""Tests for the MiniMax client backend."""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients import get_client
from rlm.clients.openai import (
    DEFAULT_MINIMAX_BASE_URL,
    OpenAIClient,
)
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


class TestMiniMaxClientUnit:
    """Unit tests for MiniMax backend (no API calls required)."""

    def test_get_client_returns_openai_client(self):
        """MiniMax backend should return an OpenAIClient instance."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                assert isinstance(client, OpenAIClient)

    def test_default_base_url(self):
        """MiniMax backend should set the default base URL."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["base_url"] == "https://api.minimax.io/v1"

    def test_custom_base_url_preserved(self):
        """User-provided base_url should not be overwritten."""
        custom_url = "https://custom.minimax.example.com/v1"
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                        "base_url": custom_url,
                    },
                )
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["base_url"] == custom_url

    def test_api_key_passed_through(self):
        """Explicit API key should be passed to the OpenAI client."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "minimax-test-key-123",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["api_key"] == "minimax-test-key-123"

    def test_api_key_from_env(self):
        """MINIMAX_API_KEY env var should be used when no explicit key is given."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "env-minimax-key"}):
            with patch(
                "rlm.clients.openai.DEFAULT_MINIMAX_API_KEY", "env-minimax-key"
            ):
                with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
                    with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                        get_client(
                            backend="minimax",
                            backend_kwargs={
                                "model_name": "MiniMax-M2.7",
                            },
                        )
                        call_kwargs = mock_openai.call_args[1]
                        assert call_kwargs["api_key"] == "env-minimax-key"

    def test_model_name_stored(self):
        """Model name should be stored on the client."""
        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7-highspeed",
                    },
                )
                assert client.model_name == "MiniMax-M2.7-highspeed"

    def test_completion_with_mocked_response(self):
        """Test completion with a mocked API response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from MiniMax!"
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 23
        mock_response.usage.cost = None
        mock_response.usage.model_extra = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                result = client.completion("What is 2+2?")

                assert result == "Hello from MiniMax!"
                assert client.model_call_counts["MiniMax-M2.7"] == 1
                assert client.model_input_tokens["MiniMax-M2.7"] == 15
                assert client.model_output_tokens["MiniMax-M2.7"] == 8

    def test_completion_with_message_list(self):
        """Test completion with a list of messages."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "4"
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 1
        mock_response.usage.total_tokens = 21
        mock_response.usage.cost = None
        mock_response.usage.model_extra = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                messages = [
                    {"role": "system", "content": "You are a math tutor."},
                    {"role": "user", "content": "What is 2+2?"},
                ]
                result = client.completion(messages)
                assert result == "4"

    def test_usage_summary(self):
        """Test usage tracking across multiple calls."""
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].message.content = "Response 1"
        mock_response_1.usage.prompt_tokens = 10
        mock_response_1.usage.completion_tokens = 5
        mock_response_1.usage.total_tokens = 15
        mock_response_1.usage.cost = None
        mock_response_1.usage.model_extra = {}

        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].message.content = "Response 2"
        mock_response_2.usage.prompt_tokens = 20
        mock_response_2.usage.completion_tokens = 10
        mock_response_2.usage.total_tokens = 30
        mock_response_2.usage.cost = None
        mock_response_2.usage.model_extra = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                client.completion("Hello")
                client.completion("World")

                summary = client.get_usage_summary()
                assert isinstance(summary, UsageSummary)
                assert "MiniMax-M2.7" in summary.model_usage_summaries
                model_summary = summary.model_usage_summaries["MiniMax-M2.7"]
                assert model_summary.total_calls == 2
                assert model_summary.total_input_tokens == 30
                assert model_summary.total_output_tokens == 15

    def test_last_usage(self):
        """Test get_last_usage returns the most recent call's usage."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.usage.prompt_tokens = 12
        mock_response.usage.completion_tokens = 7
        mock_response.usage.total_tokens = 19
        mock_response.usage.cost = None
        mock_response.usage.model_extra = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                    },
                )
                client.completion("Test prompt")

                last = client.get_last_usage()
                assert isinstance(last, ModelUsageSummary)
                assert last.total_calls == 1
                assert last.total_input_tokens == 12
                assert last.total_output_tokens == 7

    def test_timeout_passed_to_client(self):
        """Custom timeout should be forwarded to the underlying OpenAI client."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI") as mock_async:
                get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7",
                        "timeout": 60.0,
                    },
                )
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["timeout"] == 60.0

                async_call_kwargs = mock_async.call_args[1]
                assert async_call_kwargs["timeout"] == 60.0

    def test_minimax_base_url_constant(self):
        """DEFAULT_MINIMAX_BASE_URL should be set correctly."""
        assert DEFAULT_MINIMAX_BASE_URL == "https://api.minimax.io/v1"

    def test_client_backend_includes_minimax(self):
        """ClientBackend type should include 'minimax'."""
        from rlm.core.types import ClientBackend

        # Literal types expose __args__
        assert "minimax" in ClientBackend.__args__

    def test_legacy_m25_model_still_works(self):
        """Older MiniMax-M2.5 model should still be usable."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Legacy response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.usage.cost = None
        mock_response.usage.model_extra = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.5",
                    },
                )
                result = client.completion("Test legacy model")
                assert result == "Legacy response"
                assert client.model_name == "MiniMax-M2.5"

    def test_m27_highspeed_model(self):
        """MiniMax-M2.7-highspeed should work correctly."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Highspeed response"
        mock_response.usage.prompt_tokens = 8
        mock_response.usage.completion_tokens = 4
        mock_response.usage.total_tokens = 12
        mock_response.usage.cost = None
        mock_response.usage.model_extra = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = get_client(
                    backend="minimax",
                    backend_kwargs={
                        "api_key": "test-key",
                        "model_name": "MiniMax-M2.7-highspeed",
                    },
                )
                result = client.completion("Test highspeed")
                assert result == "Highspeed response"
                assert client.model_name == "MiniMax-M2.7-highspeed"
                assert client.model_call_counts["MiniMax-M2.7-highspeed"] == 1


class TestMiniMaxClientIntegration:
    """Integration tests that require a real MINIMAX_API_KEY."""

    @pytest.mark.skipif(
        not os.environ.get("MINIMAX_API_KEY"),
        reason="MINIMAX_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with the real MiniMax API."""
        client = get_client(
            backend="minimax",
            backend_kwargs={"model_name": "MiniMax-M2.7"},
        )
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        usage = client.get_usage_summary()
        assert "MiniMax-M2.7" in usage.model_usage_summaries
        assert usage.model_usage_summaries["MiniMax-M2.7"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("MINIMAX_API_KEY"),
        reason="MINIMAX_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = get_client(
            backend="minimax",
            backend_kwargs={"model_name": "MiniMax-M2.7"},
        )
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
    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion with MiniMax."""
        client = get_client(
            backend="minimax",
            backend_kwargs={"model_name": "MiniMax-M2.7"},
        )
        result = await client.acompletion("What is 3+3? Reply with just the number.")
        assert "6" in result
