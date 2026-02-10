"""Tests for the Gemini client."""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from rlm.clients.gemini import GeminiClient
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


class TestGeminiClientUnit:
    """Unit tests that don't require API calls."""

    def test_init_with_api_key(self):
        """Test client initialization with explicit API key."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
            assert client.model_name == "gemini-2.5-flash"

    def test_init_default_model(self):
        """Test client uses default model name."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            assert client.model_name == "gemini-2.5-flash"

    def test_init_requires_api_key(self):
        """Test client raises error when no API key provided."""
        with patch.dict(os.environ, {}, clear=True):
            with (
                patch("rlm.clients.gemini.DEFAULT_GEMINI_API_KEY", None),
                patch("rlm.clients.gemini.DEFAULT_PROJECT", None),
                patch("rlm.clients.gemini.DEFAULT_LOCATION", None),
            ):
                with pytest.raises(ValueError, match="Gemini API key is required"):
                    GeminiClient(api_key=None)

    def test_usage_tracking_initialization(self):
        """Test that usage tracking is properly initialized."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            assert client.model_call_counts == {}
            assert client.model_input_tokens == {}
            assert client.model_output_tokens == {}
            assert client.last_prompt_tokens == 0
            assert client.last_completion_tokens == 0

    def test_get_usage_summary_empty(self):
        """Test usage summary when no calls have been made."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            summary = client.get_usage_summary()
            assert isinstance(summary, UsageSummary)
            assert summary.model_usage_summaries == {}

    def test_get_last_usage(self):
        """Test last usage returns correct format."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            client.last_prompt_tokens = 100
            client.last_completion_tokens = 50
            usage = client.get_last_usage()
            assert isinstance(usage, ModelUsageSummary)
            assert usage.total_calls == 1
            assert usage.total_input_tokens == 100
            assert usage.total_output_tokens == 50

    def test_prepare_contents_string(self):
        """Test _prepare_contents with string input."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            contents, system = client._prepare_contents("Hello world")
            assert contents == "Hello world"
            assert system is None

    def test_prepare_contents_messages_with_system(self):
        """Test _prepare_contents extracts system message."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
            ]
            contents, system = client._prepare_contents(messages)
            assert system == "You are helpful"
            assert len(contents) == 1
            assert contents[0].role == "user"

    def test_prepare_contents_role_mapping(self):
        """Test _prepare_contents maps assistant to model."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "How are you?"},
            ]
            contents, system = client._prepare_contents(messages)
            assert system is None
            assert len(contents) == 3
            assert contents[0].role == "user"
            assert contents[1].role == "model"  # assistant -> model
            assert contents[2].role == "user"

    def test_prepare_contents_invalid_type(self):
        """Test _prepare_contents raises on invalid input."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key")
            with pytest.raises(ValueError, match="Invalid prompt type"):
                client._prepare_contents(12345)

    def test_completion_requires_model(self):
        """Test completion raises when no model specified."""
        with patch("rlm.clients.gemini.genai.Client"):
            client = GeminiClient(api_key="test-key", model_name=None)
            with pytest.raises(ValueError, match="Model name is required"):
                client.completion("Hello")

    def test_completion_with_mocked_response(self):
        """Test completion with mocked API response."""
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini!"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5

        with patch("rlm.clients.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
            result = client.completion("Hello")

            assert result == "Hello from Gemini!"
            assert client.model_call_counts["gemini-2.5-flash"] == 1
            assert client.model_input_tokens["gemini-2.5-flash"] == 10
            assert client.model_output_tokens["gemini-2.5-flash"] == 5

    @pytest.mark.asyncio
    async def test_acompletion_mocked(self):
        """Test async completion with mocked API response."""
        mock_response = MagicMock()
        mock_response.text = "Hello from async Gemini!"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5

        async def mock_call(*args, **kwargs):
            return mock_response

        with patch("rlm.clients.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content.side_effect = mock_call
            mock_client_class.return_value = mock_client

            client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
            result = await client.acompletion("Hello")

            assert result == "Hello from async Gemini!"
            assert client.model_call_counts["gemini-2.5-flash"] == 1
            assert client.model_input_tokens["gemini-2.5-flash"] == 10
            assert client.model_output_tokens["gemini-2.5-flash"] == 5

    @pytest.mark.asyncio
    async def test_acompletion_stream_mocked(self):
        """Test acompletion_stream with mocked API response."""
        mock_chunk = MagicMock()
        mock_chunk.text = "Hello"
        mock_chunk.usage_metadata.prompt_token_count = 10
        mock_chunk.usage_metadata.candidates_token_count = 5

        async def mock_stream():
            yield mock_chunk

        async def mock_call(*args, **kwargs):
            return mock_stream()

        with patch("rlm.clients.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            # The async client method is a coroutine that returns an async iterator
            mock_client.aio.models.generate_content_stream.side_effect = mock_call
            mock_client_class.return_value = mock_client

            client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
            chunks = []
            async for chunk in client.acompletion_stream("Hello"):
                chunks.append(chunk)

            assert chunks == ["Hello"]
            assert client.model_call_counts["gemini-2.5-flash"] == 1
            assert client.model_input_tokens["gemini-2.5-flash"] == 10
            assert client.model_output_tokens["gemini-2.5-flash"] == 5

    def test_completion_stream_mocked(self):
        """Test completion_stream with mocked API response."""
        mock_chunk = MagicMock()
        mock_chunk.text = "Hello"
        mock_chunk.usage_metadata.prompt_token_count = 10
        mock_chunk.usage_metadata.candidates_token_count = 5

        def mock_stream():
            yield mock_chunk

        with patch("rlm.clients.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content_stream.return_value = mock_stream()
            mock_client_class.return_value = mock_client

            client = GeminiClient(api_key="test-key", model_name="gemini-2.5-flash")
            chunks = list(client.completion_stream("Hello"))

            assert chunks == ["Hello"]
            assert client.model_call_counts["gemini-2.5-flash"] == 1
            assert client.model_input_tokens["gemini-2.5-flash"] == 10
            assert client.model_output_tokens["gemini-2.5-flash"] == 5

    def test_init_vertexai_mocked(self):
        """Test client initialization with Vertex AI."""
        with patch("rlm.clients.gemini.genai.Client") as mock_client_class:
            client = GeminiClient(
                vertexai=True,
                project="test-project",
                location="us-central1",
                model_name="gemini-2.5-flash",
            )
            mock_client_class.assert_called_once()
            args, kwargs = mock_client_class.call_args
            assert kwargs["vertexai"] is True
            assert kwargs["project"] == "test-project"
            assert kwargs["location"] == "us-central1"
            assert client.model_name == "gemini-2.5-flash"

    def test_safety_settings_mocked(self):
        """Test that safety settings are correctly passed to the config."""
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_LOW_AND_ABOVE"}
        ]
        mock_response = MagicMock()
        mock_response.text = "Safe response"
        mock_response.usage_metadata.prompt_token_count = 5
        mock_response.usage_metadata.candidates_token_count = 5

        with patch("rlm.clients.gemini.genai.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GeminiClient(api_key="test-key", safety_settings=safety_settings)
            assert client.safety_settings == safety_settings

            client.completion("Hello")

            # Verify GenerateContentConfig was called with safety_settings
            call_args = mock_client.models.generate_content.call_args
            config = call_args.kwargs["config"]
            assert config.safety_settings == safety_settings


class TestGeminiClientIntegration:
    """Integration tests that require a real API key."""

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    def test_simple_completion(self):
        """Test a simple completion with real API."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        result = client.completion("What is 2+2? Reply with just the number.")
        assert "4" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "gemini-2.5-flash" in usage.model_usage_summaries
        assert usage.model_usage_summaries["gemini-2.5-flash"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    def test_message_list_completion(self):
        """Test completion with message list format."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        messages = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is 5 * 5? Reply with just the number."},
        ]
        result = client.completion(messages)
        assert "25" in result

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    @pytest.mark.asyncio
    async def test_async_completion(self):
        """Test async completion."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        result = await client.acompletion("What is 3+3? Reply with just the number.")
        assert "6" in result

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    def test_streaming_completion(self):
        """Test streaming completion."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        chunks = list(client.completion_stream("Count to 3. Reply with just numbers."))
        result = "".join(chunks)
        assert "1" in result
        assert "2" in result
        assert "3" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "gemini-2.5-flash" in usage.model_usage_summaries
        assert usage.model_usage_summaries["gemini-2.5-flash"].total_calls == 1

    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY not set",
    )
    @pytest.mark.asyncio
    async def test_async_streaming_completion(self):
        """Test async streaming completion."""
        client = GeminiClient(model_name="gemini-2.5-flash")
        chunks = []
        async for chunk in client.acompletion_stream("Count from 4 to 6. Reply with just numbers."):
            chunks.append(chunk)
        result = "".join(chunks)
        assert "4" in result
        assert "5" in result
        assert "6" in result

        # Verify usage was tracked
        usage = client.get_usage_summary()
        assert "gemini-2.5-flash" in usage.model_usage_summaries
        assert usage.model_usage_summaries["gemini-2.5-flash"].total_calls == 1


if __name__ == "__main__":
    # Run integration tests directly
    test = TestGeminiClientIntegration()
    print("Testing simple completion...")
    test.test_simple_completion()
    print("Testing message list completion...")
    test.test_message_list_completion()
    print("Testing async completion...")
    asyncio.run(test.test_async_completion())
    print("Testing streaming completion...")
    test.test_streaming_completion()
    print("Testing async streaming completion...")
    asyncio.run(test.test_async_streaming_completion())
    print("All integration tests passed!")
