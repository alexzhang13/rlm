"""Tests for client timeout functionality."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from rlm.clients.base_lm import DEFAULT_TIMEOUT


class TestDefaultTimeout:
    """Tests for the default timeout constant."""

    def test_default_timeout_value(self):
        """Default timeout should be 300 seconds."""
        assert DEFAULT_TIMEOUT == 300.0

    def test_base_lm_stores_timeout(self):
        """BaseLM should store timeout in instance."""
        from rlm.clients.openai import OpenAIClient

        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name="gpt-4o")
                assert client.timeout == DEFAULT_TIMEOUT

    def test_custom_timeout_override(self):
        """Custom timeout should override default."""
        from rlm.clients.openai import OpenAIClient

        with patch("rlm.clients.openai.openai.OpenAI"):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name="gpt-4o", timeout=60.0)
                assert client.timeout == 60.0


class TestOpenAIClientTimeout:
    """Tests for OpenAI client timeout."""

    def test_timeout_passed_to_client(self):
        """Timeout should be passed to OpenAI client."""
        from rlm.clients.openai import OpenAIClient

        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.openai.openai.AsyncOpenAI") as mock_async:
                OpenAIClient(api_key="test-key", model_name="gpt-4o", timeout=120.0)

                # Check sync client received timeout
                mock_openai.assert_called_once()
                call_kwargs = mock_openai.call_args[1]
                assert call_kwargs["timeout"] == 120.0

                # Check async client received timeout
                mock_async.assert_called_once()
                async_call_kwargs = mock_async.call_args[1]
                assert async_call_kwargs["timeout"] == 120.0

    def test_timeout_raises_exception(self):
        """Timeout should raise appropriate exception."""
        from rlm.clients.openai import OpenAIClient

        # Create a mock client that raises timeout
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = httpx.TimeoutException(
            "Connection timed out"
        )

        with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
            with patch("rlm.clients.openai.openai.AsyncOpenAI"):
                client = OpenAIClient(api_key="test-key", model_name="gpt-4o", timeout=0.001)

                with pytest.raises(httpx.TimeoutException):
                    client.completion("Hello")


class TestAnthropicClientTimeout:
    """Tests for Anthropic client timeout."""

    def test_timeout_passed_to_client(self):
        """Timeout should be passed to Anthropic client."""
        from rlm.clients.anthropic import AnthropicClient

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic:
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic") as mock_async:
                AnthropicClient(
                    api_key="test-key", model_name="claude-sonnet-4-20250514", timeout=120.0
                )

                mock_anthropic.assert_called_once()
                call_kwargs = mock_anthropic.call_args[1]
                assert call_kwargs["timeout"] == 120.0

                mock_async.assert_called_once()
                async_call_kwargs = mock_async.call_args[1]
                assert async_call_kwargs["timeout"] == 120.0


class TestAzureOpenAIClientTimeout:
    """Tests for Azure OpenAI client timeout."""

    def test_timeout_passed_to_client(self):
        """Timeout should be passed to Azure OpenAI client."""
        from rlm.clients.azure_openai import AzureOpenAIClient

        with patch("rlm.clients.azure_openai.openai.AzureOpenAI") as mock_azure:
            with patch("rlm.clients.azure_openai.openai.AsyncAzureOpenAI") as mock_async:
                AzureOpenAIClient(
                    api_key="test-key",
                    model_name="gpt-4o",
                    azure_endpoint="https://test.openai.azure.com",
                    timeout=120.0,
                )

                mock_azure.assert_called_once()
                call_kwargs = mock_azure.call_args[1]
                assert call_kwargs["timeout"] == 120.0

                mock_async.assert_called_once()
                async_call_kwargs = mock_async.call_args[1]
                assert async_call_kwargs["timeout"] == 120.0


class TestPortkeyClientTimeout:
    """Tests for Portkey client timeout."""

    def test_timeout_passed_to_client(self):
        """Timeout should be passed to Portkey client."""
        from rlm.clients.portkey import PortkeyClient

        with patch("rlm.clients.portkey.Portkey") as mock_portkey:
            with patch("rlm.clients.portkey.AsyncPortkey") as mock_async:
                PortkeyClient(api_key="test-key", model_name="gpt-4o", timeout=120.0)

                mock_portkey.assert_called_once()
                call_kwargs = mock_portkey.call_args[1]
                assert call_kwargs["timeout"] == 120.0

                mock_async.assert_called_once()
                async_call_kwargs = mock_async.call_args[1]
                assert async_call_kwargs["timeout"] == 120.0


class TestLiteLLMClientTimeout:
    """Tests for LiteLLM client timeout."""

    def test_timeout_passed_to_completion(self):
        """Timeout should be passed to litellm.completion call."""
        pytest.importorskip("litellm")
        from rlm.clients.litellm import LiteLLMClient

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch(
            "rlm.clients.litellm.litellm.completion", return_value=mock_response
        ) as mock_completion:
            client = LiteLLMClient(model_name="gpt-4o", timeout=120.0)
            client.completion("Hello")

            mock_completion.assert_called_once()
            call_kwargs = mock_completion.call_args[1]
            assert call_kwargs["timeout"] == 120.0


class TestGeminiClientTimeout:
    """Tests for Gemini client timeout."""

    def test_timeout_passed_to_client(self):
        """Timeout should be passed to Gemini client via http_options."""
        from rlm.clients.gemini import GeminiClient

        with patch("rlm.clients.gemini.genai.Client") as mock_genai:
            GeminiClient(api_key="test-key", model_name="gemini-2.5-flash", timeout=120.0)

            mock_genai.assert_called_once()
            call_kwargs = mock_genai.call_args[1]
            # Gemini uses milliseconds
            assert call_kwargs["http_options"].timeout == 120000
