"""Tests for the AWS Bedrock client."""

import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.bedrock import BedrockClient, _build_mantle_base_url
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

# Default test model - Qwen3 Coder for code generation tasks
TEST_MODEL = "qwen.qwen3-coder-30b-a3b-v1:0"


class TestBedrockClientUnit:
    """Unit tests that don't require API calls."""

    def test_build_mantle_base_url(self):
        """Test Mantle URL construction for different regions."""
        assert _build_mantle_base_url("us-east-1") == "https://bedrock-mantle.us-east-1.api.aws/v1"
        assert _build_mantle_base_url("eu-west-1") == "https://bedrock-mantle.eu-west-1.api.aws/v1"
        assert _build_mantle_base_url("ap-northeast-1") == "https://bedrock-mantle.ap-northeast-1.api.aws/v1"

    def test_init_with_explicit_params(self):
        """Test client initialization with explicit parameters."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(
                    api_key="test-key",
                    model_name=TEST_MODEL,
                    region="us-west-2",
                )
                assert client.model_name == TEST_MODEL
                assert client.region == "us-west-2"
                assert client.base_url == "https://bedrock-mantle.us-west-2.api.aws/v1"

    def test_init_with_custom_base_url(self):
        """Test client initialization with custom base URL override."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                custom_url = "https://custom-endpoint.example.com/v1"
                client = BedrockClient(
                    api_key="test-key",
                    model_name=TEST_MODEL,
                    base_url=custom_url,
                )
                assert client.base_url == custom_url

    def test_init_default_region(self):
        """Test client uses default region (us-east-1)."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                with patch.dict(os.environ, {}, clear=False):
                    # Clear region env var if set
                    os.environ.pop("AWS_BEDROCK_REGION", None)
                    client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                    assert client.region == "us-east-1"

    def test_init_requires_api_key(self):
        """Test client raises error when no API key provided."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("rlm.clients.bedrock.DEFAULT_BEDROCK_API_KEY", None):
                with pytest.raises(ValueError, match="Bedrock API key is required"):
                    BedrockClient(api_key=None)

    def test_init_uses_env_api_key(self):
        """Test client uses API key from environment variable."""
        with patch("rlm.clients.bedrock.openai.OpenAI") as mock_openai:
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                with patch("rlm.clients.bedrock.DEFAULT_BEDROCK_API_KEY", "env-api-key"):
                    client = BedrockClient(model_name=TEST_MODEL)
                    # Verify OpenAI client was called with env key
                    mock_openai.assert_called_once()
                    call_kwargs = mock_openai.call_args[1]
                    assert call_kwargs["api_key"] == "env-api-key"

    def test_usage_tracking_initialization(self):
        """Test that usage tracking is properly initialized."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                assert client.model_call_counts == {}
                assert client.model_input_tokens == {}
                assert client.model_output_tokens == {}
                assert client.last_prompt_tokens == 0
                assert client.last_completion_tokens == 0

    def test_get_usage_summary_empty(self):
        """Test usage summary when no calls have been made."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                summary = client.get_usage_summary()
                assert isinstance(summary, UsageSummary)
                assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        """Test last usage returns correct format."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                client.last_prompt_tokens = 100
                client.last_completion_tokens = 50
                usage = client.get_last_usage()
                assert isinstance(usage, ModelUsageSummary)
                assert usage.total_calls == 1
                assert usage.total_input_tokens == 100
                assert usage.total_output_tokens == 50

    def test_prepare_messages_string(self):
        """Test _prepare_messages with string input."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                messages = client._prepare_messages("Hello world")
                assert messages == [{"role": "user", "content": "Hello world"}]

    def test_prepare_messages_list(self):
        """Test _prepare_messages with message list input."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                input_messages = [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"},
                ]
                messages = client._prepare_messages(input_messages)
                assert messages == input_messages

    def test_prepare_messages_invalid_type(self):
        """Test _prepare_messages raises on invalid input."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                with pytest.raises(ValueError, match="Invalid prompt type"):
                    client._prepare_messages(12345)

    def test_completion_requires_model(self):
        """Test completion raises when no model specified."""
        with patch("rlm.clients.bedrock.openai.OpenAI"):
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                client = BedrockClient(api_key="test-key", model_name=None)
                with pytest.raises(ValueError, match="Model name is required"):
                    client.completion("Hello")

    def test_completion_with_mocked_response(self):
        """Test completion with mocked API response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from Bedrock!"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("rlm.clients.bedrock.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai_class.return_value = mock_client

                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                result = client.completion("Hello")

                assert result == "Hello from Bedrock!"
                assert client.model_call_counts[TEST_MODEL] == 1
                assert client.model_input_tokens[TEST_MODEL] == 10
                assert client.model_output_tokens[TEST_MODEL] == 5

    def test_completion_tracks_usage_across_calls(self):
        """Test that usage is accumulated across multiple calls."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("rlm.clients.bedrock.openai.OpenAI") as mock_openai_class:
            with patch("rlm.clients.bedrock.openai.AsyncOpenAI"):
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai_class.return_value = mock_client

                client = BedrockClient(api_key="test-key", model_name=TEST_MODEL)
                client.completion("Hello 1")
                client.completion("Hello 2")
                client.completion("Hello 3")

                assert client.model_call_counts[TEST_MODEL] == 3
                assert client.model_input_tokens[TEST_MODEL] == 30
                assert client.model_output_tokens[TEST_MODEL] == 15

                summary = client.get_usage_summary()
                assert summary.model_usage_summaries[TEST_MODEL].total_calls == 3


class TestBedrockClientIntegration:
    """Integration tests that require a real Bedrock API key.

    These tests are skipped if AWS_BEDROCK_API_KEY is not set.
    Set the environment variable to run integration tests:

        export AWS_BEDROCK_API_KEY=your-bedrock-api-key
        pytest tests/clients/test_bedrock.py -v
    """

    @pytest.mark.skipif(
        not os.environ.get("AWS_BEDROCK_API_KEY"),
        reason="AWS_BEDROCK_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = BedrockClient(model_name=TEST_MODEL)
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert TEST_MODEL in usage.model_usage_summaries
        assert usage.model_usage_summaries[TEST_MODEL].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("AWS_BEDROCK_API_KEY"),
        reason="AWS_BEDROCK_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = BedrockClient(model_name=TEST_MODEL)
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("AWS_BEDROCK_API_KEY"),
        reason="AWS_BEDROCK_API_KEY not set",
    )
    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion."""
        client = BedrockClient(model_name=TEST_MODEL)
        result = await client.acompletion("What is 3+3? Reply with just the number.")
        assert "6" in result

    @pytest.mark.skipif(
        not os.environ.get("AWS_BEDROCK_API_KEY"),
        reason="AWS_BEDROCK_API_KEY not set",
    )
    def test_code_generation(self):
        """Test code generation capability (important for RLM use case)."""
        client = BedrockClient(model_name=TEST_MODEL)
        result = client.completion(
            "Write a Python function that returns the sum of a list of numbers. "
            "Reply with only the function code, no explanation."
        )
        assert "def" in result
        assert "sum" in result.lower() or "return" in result


if __name__ == "__main__":
    # Run integration tests directly
    print("Running Bedrock integration tests...")
    print(f"Using model: {TEST_MODEL}")

    test = TestBedrockClientIntegration()

    print("\n1. Testing simple completion...")
    test.test_simple_completion()
    print("   ✓ Passed")

    print("\n2. Testing message list completion...")
    test.test_message_list_completion()
    print("   ✓ Passed")

    print("\n3. Testing code generation...")
    test.test_code_generation()
    print("   ✓ Passed")

    print("\n✓ All integration tests passed!")
