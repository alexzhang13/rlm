"""Tests for Anthropic client cost estimation and prefix caching."""

from unittest.mock import MagicMock, patch

from rlm.clients.anthropic import (
    _ANTHROPIC_PRICING,
    _CACHE_CREATION_MULTIPLIER,
    _CACHE_READ_MULTIPLIER,
    AnthropicClient,
)


def _mock_usage(input_tokens=100, output_tokens=50, cache_creation=0, cache_read=0):
    """Create a mock Anthropic usage object."""
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    usage.cache_creation_input_tokens = cache_creation
    usage.cache_read_input_tokens = cache_read
    return usage


def _mock_response(input_tokens=100, output_tokens=50, cache_creation=0, cache_read=0):
    """Create a mock Anthropic Message response."""
    response = MagicMock()
    response.usage = _mock_usage(input_tokens, output_tokens, cache_creation, cache_read)
    response.content = [MagicMock(text="test response")]
    return response


class TestAnthropicPricingTable:
    """Tests for the pricing table."""

    def test_known_models_present(self):
        assert "claude-sonnet-4-20250514" in _ANTHROPIC_PRICING
        assert "claude-opus-4-20250514" in _ANTHROPIC_PRICING
        assert "claude-3-5-sonnet-latest" in _ANTHROPIC_PRICING
        assert "claude-3-haiku-20240307" in _ANTHROPIC_PRICING

    def test_pricing_format(self):
        for model, (input_price, output_price) in _ANTHROPIC_PRICING.items():
            assert isinstance(input_price, (int, float)), f"Bad input price for {model}"
            assert isinstance(output_price, (int, float)), f"Bad output price for {model}"
            assert input_price > 0, f"Non-positive input price for {model}"
            assert output_price > 0, f"Non-positive output price for {model}"


class TestAnthropicCostEstimation:
    """Tests for cost tracking in _track_cost."""

    @patch("rlm.clients.anthropic.anthropic")
    def test_known_model_cost_positive(self, mock_anthropic):
        """Cost should be > 0 for a known model."""
        client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
        response = _mock_response(input_tokens=1000, output_tokens=500)

        client._track_cost(response, "claude-sonnet-4-20250514")

        assert client.last_cost is not None
        assert client.last_cost > 0
        # Verify: (1000 * 3.0 + 500 * 15.0) / 1_000_000 = 0.0105
        expected = (1000 * 3.0 + 500 * 15.0) / 1_000_000
        assert abs(client.last_cost - expected) < 1e-10

    @patch("rlm.clients.anthropic.anthropic")
    def test_unknown_model_cost_none(self, mock_anthropic):
        """Cost should be None for an unknown model."""
        client = AnthropicClient(api_key="test-key", model_name="unknown-model-xyz")
        response = _mock_response(input_tokens=100, output_tokens=50)

        client._track_cost(response, "unknown-model-xyz")

        assert client.last_cost is None

    @patch("rlm.clients.anthropic.anthropic")
    def test_cache_token_cost(self, mock_anthropic):
        """Cache creation and read tokens should affect cost."""
        client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
        response = _mock_response(
            input_tokens=1000,
            output_tokens=500,
            cache_creation=200,
            cache_read=300,
        )

        client._track_cost(response, "claude-sonnet-4-20250514")

        assert client.last_cost is not None
        input_price, output_price = _ANTHROPIC_PRICING["claude-sonnet-4-20250514"]
        expected = (
            1000 * input_price
            + 500 * output_price
            + 200 * input_price * _CACHE_CREATION_MULTIPLIER
            + 300 * input_price * _CACHE_READ_MULTIPLIER
        ) / 1_000_000
        assert abs(client.last_cost - expected) < 1e-10

    @patch("rlm.clients.anthropic.anthropic")
    def test_cache_tokens_tracked(self, mock_anthropic):
        """Cache tokens should be accumulated in model_cache_* dicts."""
        client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
        model = "claude-sonnet-4-20250514"

        client._track_cost(_mock_response(cache_creation=100, cache_read=200), model)
        client._track_cost(_mock_response(cache_creation=50, cache_read=80), model)

        assert client.model_cache_creation_tokens[model] == 150
        assert client.model_cache_read_tokens[model] == 280

    @patch("rlm.clients.anthropic.anthropic")
    def test_usage_summary_includes_cost(self, mock_anthropic):
        """get_usage_summary should include total_cost for known models."""
        client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
        client._track_cost(
            _mock_response(input_tokens=1000, output_tokens=500),
            "claude-sonnet-4-20250514",
        )

        summary = client.get_usage_summary()
        model_summary = summary.model_usage_summaries["claude-sonnet-4-20250514"]
        assert model_summary.total_cost is not None
        assert model_summary.total_cost > 0

    @patch("rlm.clients.anthropic.anthropic")
    def test_last_usage_includes_cost(self, mock_anthropic):
        """get_last_usage should include total_cost."""
        client = AnthropicClient(api_key="test-key", model_name="claude-sonnet-4-20250514")
        client._track_cost(
            _mock_response(input_tokens=1000, output_tokens=500),
            "claude-sonnet-4-20250514",
        )

        last = client.get_last_usage()
        assert last.total_cost is not None
        assert last.total_cost > 0

    @patch("rlm.clients.anthropic.anthropic")
    def test_pricing_override(self, mock_anthropic):
        """pricing_override should allow custom per-model pricing."""
        custom_pricing = {"my-custom-model": (1.0, 2.0)}
        client = AnthropicClient(
            api_key="test-key",
            model_name="my-custom-model",
            pricing_override=custom_pricing,
        )
        client._track_cost(
            _mock_response(input_tokens=1000, output_tokens=500),
            "my-custom-model",
        )
        expected = (1000 * 1.0 + 500 * 2.0) / 1_000_000
        assert abs(client.last_cost - expected) < 1e-10


class TestAnthropicPrefixCaching:
    """Tests for enable_prefix_cache message structure."""

    @patch("rlm.clients.anthropic.anthropic")
    def test_prefix_cache_disabled_plain_strings(self, mock_anthropic):
        """With prefix caching disabled, system and content should be plain strings."""
        client = AnthropicClient(
            api_key="test-key",
            model_name="test-model",
            enable_prefix_cache=False,
        )
        prompt = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        messages, system = client._prepare_messages(prompt)

        assert system == "You are helpful."
        assert messages == [{"role": "user", "content": "Hello"}]

    @patch("rlm.clients.anthropic.anthropic")
    def test_prefix_cache_system_as_list_of_blocks(self, mock_anthropic):
        """With prefix caching enabled, system should be a list with cache_control."""
        client = AnthropicClient(
            api_key="test-key",
            model_name="test-model",
            enable_prefix_cache=True,
        )
        prompt = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        messages, system = client._prepare_messages(prompt)

        assert isinstance(system, list)
        assert len(system) == 1
        assert system[0]["type"] == "text"
        assert system[0]["text"] == "You are helpful."
        assert system[0]["cache_control"] == {"type": "ephemeral"}

    @patch("rlm.clients.anthropic.anthropic")
    def test_prefix_cache_last_user_message(self, mock_anthropic):
        """With prefix caching, last user message content should have cache_control."""
        client = AnthropicClient(
            api_key="test-key",
            model_name="test-model",
            enable_prefix_cache=True,
        )
        prompt = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second message"},
        ]
        messages, system = client._prepare_messages(prompt)

        # First user message should be unchanged
        assert messages[0]["content"] == "First message"
        # Last user message should be annotated
        last_user = messages[2]
        assert isinstance(last_user["content"], list)
        assert last_user["content"][0]["type"] == "text"
        assert last_user["content"][0]["text"] == "Second message"
        assert last_user["content"][0]["cache_control"] == {"type": "ephemeral"}

    @patch("rlm.clients.anthropic.anthropic")
    def test_prefix_cache_no_system_prompt(self, mock_anthropic):
        """Prefix caching should work even without a system prompt."""
        client = AnthropicClient(
            api_key="test-key",
            model_name="test-model",
            enable_prefix_cache=True,
        )
        prompt = [{"role": "user", "content": "Hello"}]
        messages, system = client._prepare_messages(prompt)

        assert system is None
        assert isinstance(messages[0]["content"], list)
        assert messages[0]["content"][0]["cache_control"] == {"type": "ephemeral"}

    @patch("rlm.clients.anthropic.anthropic")
    def test_prefix_cache_string_prompt(self, mock_anthropic):
        """Prefix caching with a simple string prompt."""
        client = AnthropicClient(
            api_key="test-key",
            model_name="test-model",
            enable_prefix_cache=True,
        )
        messages, system = client._prepare_messages("Hello world")

        assert system is None
        assert len(messages) == 1
        assert isinstance(messages[0]["content"], list)
        assert messages[0]["content"][0]["text"] == "Hello world"
        assert messages[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
