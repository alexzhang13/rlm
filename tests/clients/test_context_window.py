"""Tests for client-side prompt-size validation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rlm.clients.anthropic import AnthropicClient
from rlm.clients.azure_openai import AzureOpenAIClient
from rlm.clients.gemini import GeminiClient
from rlm.clients.openai import OpenAIClient
from rlm.clients.portkey import PortkeyClient
from rlm.utils.exceptions import ContextWindowExceededError


def _context_window_error() -> ContextWindowExceededError:
    return ContextWindowExceededError(
        model_name="gpt-4",
        estimated_input_tokens=9_000,
        context_limit=8_192,
        prompt_kind="string",
        estimation_method="character estimate (4 chars/token)",
    )


def test_openai_client_validates_before_sync_sdk_call():
    """OpenAI client should fail before hitting the sync SDK call."""
    mock_client = MagicMock()

    with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
        with patch("rlm.clients.openai.openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key", model_name="gpt-4")

    with patch.object(
        OpenAIClient, "validate_prompt_context_window", side_effect=_context_window_error()
    ) as mock_validate:
        with pytest.raises(ContextWindowExceededError):
            client.completion("too big")

    mock_validate.assert_called_once_with("too big", "gpt-4")
    mock_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_openai_client_validates_before_async_sdk_call():
    """OpenAI async client should fail before hitting the async SDK call."""
    mock_async_client = MagicMock()
    mock_async_client.chat.completions.create = AsyncMock()

    with patch("rlm.clients.openai.openai.OpenAI"):
        with patch("rlm.clients.openai.openai.AsyncOpenAI", return_value=mock_async_client):
            client = OpenAIClient(api_key="test-key", model_name="gpt-4")

    with patch.object(
        OpenAIClient, "validate_prompt_context_window", side_effect=_context_window_error()
    ) as mock_validate:
        with pytest.raises(ContextWindowExceededError):
            await client.acompletion("too big")

    mock_validate.assert_called_once_with("too big", "gpt-4")
    mock_async_client.chat.completions.create.assert_not_awaited()


def test_openai_client_sync_sdk_call_still_runs_for_small_prompt():
    """Small prompts should still reach the provider SDK."""
    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
        usage=SimpleNamespace(
            prompt_tokens=3,
            completion_tokens=2,
            total_tokens=5,
            cost=None,
            model_extra=None,
        ),
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("rlm.clients.openai.openai.OpenAI", return_value=mock_client):
        with patch("rlm.clients.openai.openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key", model_name="gpt-4")

    assert client.completion("small prompt") == "ok"
    mock_client.chat.completions.create.assert_called_once()


def test_anthropic_client_validates_before_sdk_call():
    """Anthropic client should fail before hitting the provider SDK."""
    mock_client = MagicMock()

    with patch("rlm.clients.anthropic.anthropic.Anthropic", return_value=mock_client):
        with patch("rlm.clients.anthropic.anthropic.AsyncAnthropic"):
            client = AnthropicClient(api_key="test-key", model_name="gpt-4")

    with patch.object(
        AnthropicClient, "validate_prompt_context_window", side_effect=_context_window_error()
    ) as mock_validate:
        with pytest.raises(ContextWindowExceededError):
            client.completion("too big")

    mock_validate.assert_called_once_with("too big", "gpt-4")
    mock_client.messages.create.assert_not_called()


def test_gemini_client_validates_before_sdk_call():
    """Gemini client should fail before hitting the provider SDK."""
    mock_client = MagicMock()

    with patch("rlm.clients.gemini.genai.Client", return_value=mock_client):
        client = GeminiClient(api_key="test-key", model_name="gpt-4")

    with patch.object(
        GeminiClient, "validate_prompt_context_window", side_effect=_context_window_error()
    ) as mock_validate:
        with pytest.raises(ContextWindowExceededError):
            client.completion("too big")

    mock_validate.assert_called_once_with("too big", "gpt-4")
    mock_client.models.generate_content.assert_not_called()


def test_azure_openai_client_validates_before_sdk_call():
    """Azure OpenAI client should fail before hitting the provider SDK."""
    mock_client = MagicMock()

    with patch("rlm.clients.azure_openai.openai.AzureOpenAI", return_value=mock_client):
        with patch("rlm.clients.azure_openai.openai.AsyncAzureOpenAI"):
            client = AzureOpenAIClient(
                api_key="test-key",
                model_name="gpt-4",
                azure_endpoint="https://test.openai.azure.com",
            )

    with patch.object(
        AzureOpenAIClient,
        "validate_prompt_context_window",
        side_effect=_context_window_error(),
    ) as mock_validate:
        with pytest.raises(ContextWindowExceededError):
            client.completion("too big")

    mock_validate.assert_called_once_with("too big", "gpt-4")
    mock_client.chat.completions.create.assert_not_called()


def test_portkey_client_validates_before_sdk_call():
    """Portkey client should fail before hitting the provider SDK."""
    mock_client = MagicMock()

    with patch("rlm.clients.portkey.Portkey", return_value=mock_client):
        with patch("rlm.clients.portkey.AsyncPortkey"):
            client = PortkeyClient(api_key="test-key", model_name="gpt-4")

    with patch.object(
        PortkeyClient, "validate_prompt_context_window", side_effect=_context_window_error()
    ) as mock_validate:
        with pytest.raises(ContextWindowExceededError):
            client.completion("too big")

    mock_validate.assert_called_once_with("too big", "gpt-4")
    mock_client.chat.completions.create.assert_not_called()
