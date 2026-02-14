import pytest
from unittest.mock import MagicMock, patch
from rlm.clients.openai import OpenAIClient

class TestOpenAIResponsesAPI:
    def test_init_defaults_to_responses_api(self):
        with patch("openai.OpenAI"), patch("openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key")
            assert client.use_responses_api is True

    def test_parse_responses_response_with_reasoning(self):
        with patch("openai.OpenAI"), patch("openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key")
            
            # Mock the response object structure for Responses API
            mock_item_reasoning = MagicMock()
            mock_item_reasoning.type = "message"
            mock_item_reasoning.content = "The result is 42."
            mock_item_reasoning.reasoning_content = "Thinking: 21 * 2 = 42."
            
            mock_response = MagicMock()
            mock_response.output = [mock_item_reasoning]
            
            parsed = client._parse_responses_response(mock_response)
            
            assert parsed["content"] == "The result is 42."
            assert parsed["thought"] == "Thinking: 21 * 2 = 42."
            assert parsed["tool_calls"] is None

    def test_parse_responses_response_with_tools(self):
        with patch("openai.OpenAI"), patch("openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key")
            
            mock_item_tool = MagicMock()
            mock_item_tool.type = "function_call"
            mock_item_tool.id = "call_123"
            mock_item_tool.name = "get_weather"
            mock_item_tool.arguments = '{"location": "San Francisco"}'
            
            mock_response = MagicMock()
            mock_response.output = [mock_item_tool]
            
            parsed = client._parse_responses_response(mock_response)
            
            assert parsed["content"] == ""
            assert parsed["thought"] is None
            assert len(parsed["tool_calls"]) == 1
            assert parsed["tool_calls"][0]["name"] == "get_weather"

    def test_prepare_responses_request(self):
        with patch("openai.OpenAI"), patch("openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key")
            
            prompt = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
            
            kwargs = client._prepare_responses_request(prompt, model="gpt-4o")
            
            assert kwargs["model"] == "gpt-4o"
            assert kwargs["instructions"] == "You are a helpful assistant."
            assert len(kwargs["input"]) == 1
            assert kwargs["input"][0]["role"] == "user"
            assert kwargs["input"][0]["content"] == "Hello!"

    def test_prepare_responses_request_with_chaining(self):
        with patch("openai.OpenAI"), patch("openai.AsyncOpenAI"):
            client = OpenAIClient(api_key="test-key")
            
            prompt = [{"role": "user", "content": "Next step"}]
            previous_id = "resp_123"
            
            kwargs = client._prepare_responses_request(prompt, model="gpt-4o", previous_response_id=previous_id)
            
            assert kwargs["model"] == "gpt-4o"
            assert kwargs["previous_response_id"] == "resp_123"
            assert len(kwargs["input"]) == 1
            assert kwargs["input"][0]["content"] == "Next step"
