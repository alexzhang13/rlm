"""Tests for the Anthropic client."""

import os
from unittest.mock import MagicMock, patch

import pytest

from rlm.clients.anthropic import AnthropicClient
from rlm.core.types import ModelUsageSummary, UsageSummary


class TestAnthropicClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        with patch("rlm.clients.anthropic.anthropic.Anthropic"):
            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key", model_name="claude-3-5-sonnet")
                assert client.model_name == "claude-3-5-sonnet"

    def test_completion_empty_content(self):
        """Test completion returns empty string when response.content is empty."""
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 0

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key", model_name="claude-3-5-sonnet")
                result = client.completion("Hello")

                assert result == ""

    def test_completion_with_text_content(self):
        """Test completion returns text when response.content has text blocks."""
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Hello from Claude!"

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.anthropic.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
                client = AnthropicClient(api_key="test-key", model_name="claude-3-5-sonnet")
                result = client.completion("Hello")

                assert result == "Hello from Claude!"
