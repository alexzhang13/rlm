"""Tests for the Azure Anthropic (Foundry) client."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.azure_anthropic import AzureAnthropicClient, _resolve_base_url
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


def _make_client(**overrides):
    """Helper to create a client with mocked Anthropic SDK."""
    defaults = {
        "api_key": "test-key",
        "resource": "my-resource",
        "model_name": "claude-opus-4-6",
    }
    defaults.update(overrides)
    with patch("rlm.clients.azure_anthropic.anthropic.Anthropic"), \
         patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
        return AzureAnthropicClient(**defaults)


class TestResolveBaseUrl:
    """Tests for the _resolve_base_url helper."""

    def test_resource_derives_url(self):
        """Resource name is expanded to the Foundry URL pattern."""
        result = _resolve_base_url(None, "ml-platform-openai-stg-useast-2")
        assert result == "https://ml-platform-openai-stg-useast-2.services.ai.azure.com/anthropic/v1"

    def test_base_url_appends_anthropic_suffix(self):
        """Explicit base_url gets /anthropic/v1 appended."""
        result = _resolve_base_url("https://my-res.services.ai.azure.com", None)
        assert result == "https://my-res.services.ai.azure.com/anthropic/v1"

    def test_base_url_project_scoped(self):
        """Project-scoped Foundry endpoint gets /anthropic/v1 appended."""
        result = _resolve_base_url(
            "https://ml-platform-openai-stg-useast-2.services.ai.azure.com/api/projects/ml-platform-openai-stg-useast-2-project",
            None,
        )
        assert result == (
            "https://ml-platform-openai-stg-useast-2.services.ai.azure.com"
            "/api/projects/ml-platform-openai-stg-useast-2-project/anthropic/v1"
        )

    def test_base_url_already_has_suffix(self):
        """If /anthropic/v1 is already present, don't double it."""
        result = _resolve_base_url("https://my-res.services.ai.azure.com/anthropic/v1", None)
        assert result == "https://my-res.services.ai.azure.com/anthropic/v1"

    def test_base_url_strips_trailing_slash(self):
        result = _resolve_base_url("https://my-res.services.ai.azure.com/", None)
        assert result == "https://my-res.services.ai.azure.com/anthropic/v1"

    def test_base_url_takes_priority_over_resource(self):
        """base_url wins when both are provided."""
        result = _resolve_base_url("https://custom.example.com", "some-resource")
        assert result == "https://custom.example.com/anthropic/v1"

    def test_neither_raises(self):
        """Error when neither base_url nor resource is provided."""
        with pytest.raises(ValueError, match="Foundry endpoint is required"):
            _resolve_base_url(None, None)


class TestAzureAnthropicClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_explicit_base_url(self):
        """Test client initialization with explicit base_url."""
        with patch("rlm.clients.azure_anthropic.anthropic.Anthropic") as mock_cls, \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic") as mock_async_cls:
            client = AzureAnthropicClient(
                api_key="test-key",
                base_url="https://my-resource.services.ai.azure.com",
                model_name="claude-opus-4-6",
            )
            assert client.model_name == "claude-opus-4-6"
            mock_cls.assert_called_once_with(
                api_key="test-key",
                base_url="https://my-resource.services.ai.azure.com/anthropic/v1",
            )
            mock_async_cls.assert_called_once_with(
                api_key="test-key",
                base_url="https://my-resource.services.ai.azure.com/anthropic/v1",
            )

    def test_init_with_resource_name(self):
        """Test client derives base_url from resource name."""
        with patch("rlm.clients.azure_anthropic.anthropic.Anthropic") as mock_cls, \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
            AzureAnthropicClient(
                api_key="test-key",
                resource="ml-platform-openai-stg-useast-2",
                model_name="claude-opus-4-6",
            )
            mock_cls.assert_called_once_with(
                api_key="test-key",
                base_url="https://ml-platform-openai-stg-useast-2.services.ai.azure.com/anthropic/v1",
            )

    def test_init_from_env_vars(self):
        """Test client reads ANTHROPIC_FOUNDRY_* env vars."""
        with patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_API_KEY", "env-key"), \
             patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_RESOURCE", "env-resource"), \
             patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_BASE_URL", None), \
             patch("rlm.clients.azure_anthropic.anthropic.Anthropic") as mock_cls, \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
            AzureAnthropicClient(model_name="claude-opus-4-6")
            mock_cls.assert_called_once_with(
                api_key="env-key",
                base_url="https://env-resource.services.ai.azure.com/anthropic/v1",
            )

    def test_base_url_env_overrides_resource_env(self):
        """Test ANTHROPIC_FOUNDRY_BASE_URL takes priority over RESOURCE."""
        with patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_API_KEY", "key"), \
             patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_RESOURCE", "should-not-use"), \
             patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_BASE_URL", "https://explicit.example.com"), \
             patch("rlm.clients.azure_anthropic.anthropic.Anthropic") as mock_cls, \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
            AzureAnthropicClient(model_name="claude-opus-4-6")
            mock_cls.assert_called_once_with(
                api_key="key",
                base_url="https://explicit.example.com/anthropic/v1",
            )

    def test_init_requires_endpoint_or_resource(self):
        """Test client raises error when no endpoint info provided."""
        with patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_API_KEY", "key"), \
             patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_RESOURCE", None), \
             patch("rlm.clients.azure_anthropic.DEFAULT_FOUNDRY_BASE_URL", None):
            with pytest.raises(ValueError, match="Foundry endpoint is required"):
                AzureAnthropicClient(api_key="test-key")

    def test_default_max_tokens(self):
        """Test default max_tokens value."""
        client = _make_client()
        assert client.max_tokens == 4096

    def test_custom_max_tokens(self):
        """Test custom max_tokens value."""
        client = _make_client(max_tokens=4096)
        assert client.max_tokens == 4096

    def test_usage_tracking_initialization(self):
        """Test that usage tracking is properly initialized."""
        client = _make_client()
        assert client.model_call_counts == {}
        assert client.model_input_tokens == {}
        assert client.model_output_tokens == {}
        assert client.model_total_tokens == {}

    def test_get_usage_summary_empty(self):
        """Test usage summary when no calls have been made."""
        client = _make_client()
        summary = client.get_usage_summary()
        assert isinstance(summary, UsageSummary)
        assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        """Test last usage returns correct format."""
        client = _make_client()
        client.last_prompt_tokens = 100
        client.last_completion_tokens = 50
        usage = client.get_last_usage()
        assert isinstance(usage, ModelUsageSummary)
        assert usage.total_calls == 1
        assert usage.total_input_tokens == 100
        assert usage.total_output_tokens == 50

    def test_prepare_messages_string(self):
        """Test _prepare_messages with string input."""
        client = _make_client()
        messages, system = client._prepare_messages("Hello world")
        assert messages == [{"role": "user", "content": "Hello world"}]
        assert system is None

    def test_prepare_messages_with_system(self):
        """Test _prepare_messages extracts system message."""
        client = _make_client()
        prompt = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        messages, system = client._prepare_messages(prompt)
        assert system == "You are helpful"
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "Hello"}

    def test_prepare_messages_no_system(self):
        """Test _prepare_messages without system message."""
        client = _make_client()
        prompt = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
        ]
        messages, system = client._prepare_messages(prompt)
        assert system is None
        assert len(messages) == 3

    def test_prepare_messages_invalid_type(self):
        """Test _prepare_messages raises on invalid input."""
        client = _make_client()
        with pytest.raises(ValueError, match="Invalid prompt type"):
            client._prepare_messages(12345)

    def test_completion_requires_model(self):
        """Test completion raises when no model specified."""
        client = _make_client(model_name=None)
        with pytest.raises(ValueError, match="Model name is required"):
            client.completion("Hello")

    def test_completion_with_mocked_response(self):
        """Test completion with mocked API response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello from Azure Claude!")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.azure_anthropic.anthropic.Anthropic") as mock_cls, \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            client = AzureAnthropicClient(
                api_key="test-key",
                resource="test-resource",
                model_name="claude-opus-4-6",
            )
            result = client.completion("Hello")

            assert result == "Hello from Azure Claude!"
            assert client.model_call_counts["claude-opus-4-6"] == 1
            assert client.model_input_tokens["claude-opus-4-6"] == 10
            assert client.model_output_tokens["claude-opus-4-6"] == 5
            assert client.model_total_tokens["claude-opus-4-6"] == 15

    def test_completion_passes_system_separately(self):
        """Test that system messages are passed via the system kwarg."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch("rlm.clients.azure_anthropic.anthropic.Anthropic") as mock_cls, \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            client = AzureAnthropicClient(
                api_key="test-key",
                resource="test-resource",
                model_name="claude-opus-4-6",
            )
            prompt = [
                {"role": "system", "content": "Be concise"},
                {"role": "user", "content": "Hello"},
            ]
            client.completion(prompt)

            mock_client.messages.create.assert_called_once_with(
                model="claude-opus-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": "Hello"}],
                system="Be concise",
            )

    def test_usage_accumulates_across_calls(self):
        """Test that usage tracking accumulates across multiple calls."""
        client = _make_client()

        for i in range(3):
            mock_response = MagicMock()
            mock_response.usage.input_tokens = 10 * (i + 1)
            mock_response.usage.output_tokens = 5 * (i + 1)
            client._track_cost(mock_response, "claude-opus-4-6")

        assert client.model_call_counts["claude-opus-4-6"] == 3
        assert client.model_input_tokens["claude-opus-4-6"] == 60  # 10+20+30
        assert client.model_output_tokens["claude-opus-4-6"] == 30  # 5+10+15
        assert client.model_total_tokens["claude-opus-4-6"] == 90
        # last_* should reflect only the final call
        assert client.last_prompt_tokens == 30
        assert client.last_completion_tokens == 15

    @pytest.mark.asyncio
    async def test_acompletion_with_mocked_response(self):
        """Test async completion with mocked API response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Async hello!")]
        mock_response.usage.input_tokens = 8
        mock_response.usage.output_tokens = 3

        with patch("rlm.clients.azure_anthropic.anthropic.Anthropic"), \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic") as mock_async_cls:
            mock_async_client = MagicMock()
            mock_async_client.messages.create = AsyncMock(return_value=mock_response)
            mock_async_cls.return_value = mock_async_client

            client = AzureAnthropicClient(
                api_key="test-key",
                resource="test-resource",
                model_name="claude-opus-4-6",
            )
            result = await client.acompletion("Hello")

            assert result == "Async hello!"
            assert client.model_call_counts["claude-opus-4-6"] == 1


class TestAzureAnthropicClientRouter:
    """Test that the client is properly registered in get_client."""

    def test_get_client_routes_azure_anthropic(self):
        """Test get_client returns AzureAnthropicClient for azure_anthropic backend."""
        with patch("rlm.clients.azure_anthropic.anthropic.Anthropic"), \
             patch("rlm.clients.azure_anthropic.anthropic.AsyncAnthropic"):
            from rlm.clients import get_client

            client = get_client(
                "azure_anthropic",
                {
                    "api_key": "test-key",
                    "resource": "test-resource",
                    "model_name": "claude-opus-4-6",
                },
            )
            assert isinstance(client, AzureAnthropicClient)


class TestAzureAnthropicClientIntegration:
    """Integration tests that require real Azure Foundry credentials."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
        or not (os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE") or os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")),
        reason="ANTHROPIC_FOUNDRY_API_KEY and ANTHROPIC_FOUNDRY_RESOURCE/BASE_URL not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = AzureAnthropicClient(model_name="claude-opus-4-6")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        usage = client.get_usage_summary()
        assert "claude-opus-4-6" in usage.model_usage_summaries
        assert usage.model_usage_summaries["claude-opus-4-6"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
        or not (os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE") or os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")),
        reason="ANTHROPIC_FOUNDRY_API_KEY and ANTHROPIC_FOUNDRY_RESOURCE/BASE_URL not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = AzureAnthropicClient(model_name="claude-opus-4-6")
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
        or not (os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE") or os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")),
        reason="ANTHROPIC_FOUNDRY_API_KEY and ANTHROPIC_FOUNDRY_RESOURCE/BASE_URL not set",
    )
    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion with real API."""
        client = AzureAnthropicClient(model_name="claude-opus-4-6")
        result = await client.acompletion("What is 3+3? Reply with just the number.")
        assert "6" in result
