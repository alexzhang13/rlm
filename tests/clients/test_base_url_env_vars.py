"""
Unit tests for automatic base URL and API key env var fallbacks
in OpenAI, Anthropic, and Gemini clients.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# OpenAI
# =============================================================================


class TestOpenAIClientBaseUrl:
    """Tests for OPENAI_API_BASE env var fallback in OpenAIClient."""

    def test_base_url_from_env(self):
        """When base_url is not passed, OPENAI_API_BASE is used."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai, patch(
            "rlm.clients.openai.openai.AsyncOpenAI"
        ), patch.dict(
            os.environ,
            {"OPENAI_API_BASE": "https://my-org.example.com/v1", "OPENAI_API_KEY": "test-key"},
        ):
            from rlm.clients.openai import OpenAIClient

            with patch("rlm.clients.openai.DEFAULT_OPENAI_API_BASE", "https://my-org.example.com/v1"):
                _ = OpenAIClient(api_key="test-key")

            _, kwargs = mock_openai.call_args
            assert kwargs.get("base_url") == "https://my-org.example.com/v1"

    def test_explicit_base_url_overrides_env(self):
        """An explicitly passed base_url takes precedence over OPENAI_API_BASE."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai, patch(
            "rlm.clients.openai.openai.AsyncOpenAI"
        ), patch("rlm.clients.openai.DEFAULT_OPENAI_API_BASE", "https://env-base.example.com/v1"):
            from rlm.clients.openai import OpenAIClient

            _ = OpenAIClient(api_key="test-key", base_url="https://explicit.example.com/v1")

            _, kwargs = mock_openai.call_args
            assert kwargs.get("base_url") == "https://explicit.example.com/v1"

    def test_base_url_is_none_when_env_not_set(self):
        """When OPENAI_API_BASE is not set and base_url not passed, base_url is None."""
        with patch("rlm.clients.openai.openai.OpenAI") as mock_openai, patch(
            "rlm.clients.openai.openai.AsyncOpenAI"
        ), patch("rlm.clients.openai.DEFAULT_OPENAI_API_BASE", None):
            from rlm.clients.openai import OpenAIClient

            _ = OpenAIClient(api_key="test-key")

            _, kwargs = mock_openai.call_args
            assert kwargs.get("base_url") is None


# =============================================================================
# Anthropic
# =============================================================================


class TestAnthropicClientEnvVars:
    """Tests for ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL env var fallbacks."""

    def test_api_key_from_env(self):
        """When api_key is not passed, ANTHROPIC_API_KEY env var is used."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic, patch(
            "rlm.clients.anthropic.anthropic.AsyncAnthropic"
        ), patch("rlm.clients.anthropic.DEFAULT_ANTHROPIC_API_KEY", "env-anthropic-key"), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_BASE_URL", None
        ):
            from rlm.clients.anthropic import AnthropicClient

            _ = AnthropicClient()

            _, kwargs = mock_anthropic.call_args
            assert kwargs.get("api_key") == "env-anthropic-key"

    def test_raises_when_no_api_key(self):
        """Raises ValueError when neither api_key arg nor ANTHROPIC_API_KEY env var is set."""
        with patch("rlm.clients.anthropic.DEFAULT_ANTHROPIC_API_KEY", None), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_BASE_URL", None
        ):
            from rlm.clients.anthropic import AnthropicClient

            with pytest.raises(ValueError, match="Anthropic API key is required"):
                AnthropicClient(api_key=None)

    def test_base_url_from_env(self):
        """When base_url is not passed, ANTHROPIC_BASE_URL env var is used."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic, patch(
            "rlm.clients.anthropic.anthropic.AsyncAnthropic"
        ), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_API_KEY", "test-key"
        ), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_BASE_URL", "https://my-org.example.com"
        ):
            from rlm.clients.anthropic import AnthropicClient

            _ = AnthropicClient()

            _, kwargs = mock_anthropic.call_args
            assert kwargs.get("base_url") == "https://my-org.example.com"

    def test_explicit_base_url_overrides_env(self):
        """An explicitly passed base_url takes precedence over ANTHROPIC_BASE_URL."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic, patch(
            "rlm.clients.anthropic.anthropic.AsyncAnthropic"
        ), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_API_KEY", "test-key"
        ), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_BASE_URL", "https://env-base.example.com"
        ):
            from rlm.clients.anthropic import AnthropicClient

            _ = AnthropicClient(base_url="https://explicit.example.com")

            _, kwargs = mock_anthropic.call_args
            assert kwargs.get("base_url") == "https://explicit.example.com"

    def test_base_url_not_passed_when_env_not_set(self):
        """When ANTHROPIC_BASE_URL is not set, base_url key is absent from client kwargs."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_anthropic, patch(
            "rlm.clients.anthropic.anthropic.AsyncAnthropic"
        ), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_API_KEY", "test-key"
        ), patch(
            "rlm.clients.anthropic.DEFAULT_ANTHROPIC_BASE_URL", None
        ):
            from rlm.clients.anthropic import AnthropicClient

            _ = AnthropicClient()

            _, kwargs = mock_anthropic.call_args
            assert "base_url" not in kwargs


# =============================================================================
# Gemini
# =============================================================================


class TestGeminiClientBaseUrl:
    """Tests for GEMINI_API_BASE env var fallback in GeminiClient."""

    def test_base_url_from_env(self):
        """When base_url is not passed, GEMINI_API_BASE is used in HttpOptions."""
        with patch("rlm.clients.gemini.genai.Client"), patch(
            "rlm.clients.gemini.types.HttpOptions"
        ) as mock_http_options, patch(
            "rlm.clients.gemini.DEFAULT_GEMINI_API_BASE", "https://my-org.example.com"
        ):
            from rlm.clients.gemini import GeminiClient

            _ = GeminiClient(api_key="test-key")

            _, kwargs = mock_http_options.call_args
            assert kwargs.get("base_url") == "https://my-org.example.com"

    def test_explicit_base_url_overrides_env(self):
        """An explicitly passed base_url takes precedence over GEMINI_API_BASE."""
        with patch("rlm.clients.gemini.genai.Client"), patch(
            "rlm.clients.gemini.types.HttpOptions"
        ) as mock_http_options, patch(
            "rlm.clients.gemini.DEFAULT_GEMINI_API_BASE", "https://env-base.example.com"
        ):
            from rlm.clients.gemini import GeminiClient

            _ = GeminiClient(api_key="test-key", base_url="https://explicit.example.com")

            _, kwargs = mock_http_options.call_args
            assert kwargs.get("base_url") == "https://explicit.example.com"

    def test_base_url_absent_when_env_not_set(self):
        """When GEMINI_API_BASE is not set, base_url is not passed to HttpOptions."""
        with patch("rlm.clients.gemini.genai.Client"), patch(
            "rlm.clients.gemini.types.HttpOptions"
        ) as mock_http_options, patch(
            "rlm.clients.gemini.DEFAULT_GEMINI_API_BASE", None
        ):
            from rlm.clients.gemini import GeminiClient

            _ = GeminiClient(api_key="test-key")

            _, kwargs = mock_http_options.call_args
            assert "base_url" not in kwargs
