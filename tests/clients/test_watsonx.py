"""
Tests for WatsonX client implementation.

These tests verify that the WatsonX client properly handles:
- String prompts
- Single message dict prompts
- List of message dicts (multi-turn conversations)
- Message format conversion to LangChain format
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class MockWatsonXResponse:
    """Mock response object that mimics LangChain's ChatWatsonx response."""
    
    def __init__(self, content: str, input_tokens: int = 10, output_tokens: int = 20):
        self.content = content
        self.usage_metadata = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
        self.response_metadata = {
            "token_usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
            }
        }


@pytest.fixture
def mock_watsonx_client():
    """Create a mock WatsonX client for testing."""
    # Patch langchain_ibm.ChatWatsonx at the import location
    with patch("langchain_ibm.ChatWatsonx") as mock_chat:
        # Import here after patching
        from rlm.clients.watsonx import WatsonXClient
        
        # Create a mock client instance
        mock_instance = Mock()
        mock_chat.return_value = mock_instance
        
        # Setup the client
        client = WatsonXClient(
            api_key="test_key",
            project_id="test_project",
            model_name="test_model",
        )
        
        yield client, mock_instance


def test_format_messages_string(mock_watsonx_client):
    """Test that string prompts are formatted correctly."""
    client, _ = mock_watsonx_client
    
    result = client._format_messages("Hello, world!")
    assert result == [("human", "Hello, world!")]


def test_format_messages_single_dict_user(mock_watsonx_client):
    """Test that single user message dict is formatted correctly."""
    client, _ = mock_watsonx_client
    
    result = client._format_messages({"role": "user", "content": "Hello"})
    assert result == [("human", "Hello")]


def test_format_messages_single_dict_system(mock_watsonx_client):
    """Test that single system message dict is formatted correctly."""
    client, _ = mock_watsonx_client
    
    result = client._format_messages({"role": "system", "content": "You are helpful"})
    assert result == [("system", "You are helpful")]


def test_format_messages_single_dict_assistant(mock_watsonx_client):
    """Test that single assistant message dict is formatted correctly."""
    client, _ = mock_watsonx_client
    
    result = client._format_messages({"role": "assistant", "content": "I can help"})
    assert result == [("assistant", "I can help")]


def test_format_messages_list_multi_turn(mock_watsonx_client):
    """Test that list of messages (multi-turn) is formatted correctly."""
    client, _ = mock_watsonx_client
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "What about 3+3?"},
    ]
    
    result = client._format_messages(messages)
    expected = [
        ("system", "You are a helpful assistant"),
        ("human", "What is 2+2?"),
        ("assistant", "4"),
        ("human", "What about 3+3?"),
    ]
    assert result == expected


def test_format_messages_invalid_type(mock_watsonx_client):
    """Test that invalid prompt types raise ValueError."""
    client, _ = mock_watsonx_client
    
    with pytest.raises(ValueError, match="Invalid prompt type"):
        client._format_messages(123)  # Invalid type


def test_completion_with_string(mock_watsonx_client):
    """Test completion with string prompt."""
    client, mock_instance = mock_watsonx_client
    
    # Setup mock response
    mock_response = MockWatsonXResponse("Test response")
    mock_instance.invoke.return_value = mock_response
    
    result = client.completion("Hello")
    
    assert result == "Test response"
    assert mock_instance.invoke.called
    # Verify the messages were formatted correctly
    call_args = mock_instance.invoke.call_args[0][0]
    assert call_args == [("human", "Hello")]


def test_completion_with_list(mock_watsonx_client):
    """Test completion with list of messages."""
    client, mock_instance = mock_watsonx_client
    
    # Setup mock response
    mock_response = MockWatsonXResponse("Multi-turn response")
    mock_instance.invoke.return_value = mock_response
    
    messages = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
        {"role": "user", "content": "Second message"},
    ]
    
    result = client.completion(messages)
    
    assert result == "Multi-turn response"
    assert mock_instance.invoke.called
    # Verify the messages were formatted correctly
    call_args = mock_instance.invoke.call_args[0][0]
    expected = [
        ("human", "First message"),
        ("assistant", "First response"),
        ("human", "Second message"),
    ]
    assert call_args == expected


@pytest.mark.anyio
async def test_acompletion_with_list():
    """Test async completion with list of messages."""
    with patch("langchain_ibm.ChatWatsonx") as mock_chat:
        from rlm.clients.watsonx import WatsonXClient
        
        mock_instance = Mock()
        mock_chat.return_value = mock_instance
        
        client = WatsonXClient(
            api_key="test_key",
            project_id="test_project",
            model_name="test_model",
        )
        
        # Setup mock async response
        mock_response = MockWatsonXResponse("Async multi-turn response")
        mock_instance.ainvoke = AsyncMock(return_value=mock_response)
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Help me"},
        ]
        
        result = await client.acompletion(messages)
        
        assert result == "Async multi-turn response"
        assert mock_instance.ainvoke.called
        # Verify the messages were formatted correctly
        call_args = mock_instance.ainvoke.call_args[0][0]
        expected = [
            ("system", "You are helpful"),
            ("human", "Help me"),
        ]
        assert call_args == expected


def test_completion_with_list_content(mock_watsonx_client):
    """Test completion handles list content responses."""
    client, mock_instance = mock_watsonx_client
    
    # Setup mock response with list content
    mock_response = Mock()
    mock_response.content = ["Part 1", "Part 2", "Part 3"]
    mock_response.usage_metadata = {"input_tokens": 10, "output_tokens": 20}
    mock_instance.invoke.return_value = mock_response
    
    result = client.completion("Hello")
    
    # Should join list items
    assert result == "Part 1 Part 2 Part 3"


def test_usage_tracking(mock_watsonx_client):
    """Test that usage statistics are tracked correctly."""
    client, mock_instance = mock_watsonx_client
    
    # Setup mock response
    mock_response = MockWatsonXResponse("Response", input_tokens=15, output_tokens=25)
    mock_instance.invoke.return_value = mock_response
    
    client.completion("Test prompt")
    
    # Check usage tracking
    assert client.model_call_counts["test_model"] == 1
    assert client.model_input_tokens["test_model"] == 15
    assert client.model_output_tokens["test_model"] == 25
    assert client.model_total_tokens["test_model"] == 40
    assert client.last_prompt_tokens == 15
    assert client.last_completion_tokens == 25


def test_get_usage_summary(mock_watsonx_client):
    """Test getting usage summary."""
    client, mock_instance = mock_watsonx_client
    
    # Setup mock response
    mock_response = MockWatsonXResponse("Response", input_tokens=10, output_tokens=20)
    mock_instance.invoke.return_value = mock_response
    
    # Make a few calls
    client.completion("Test 1")
    client.completion("Test 2")
    
    summary = client.get_usage_summary()
    
    assert "test_model" in summary.model_usage_summaries
    model_summary = summary.model_usage_summaries["test_model"]
    assert model_summary.total_calls == 2
    assert model_summary.total_input_tokens == 20
    assert model_summary.total_output_tokens == 40
    assert model_summary.total_cost is None  # WatsonX doesn't provide cost


def test_get_last_usage(mock_watsonx_client):
    """Test getting last usage summary."""
    client, mock_instance = mock_watsonx_client
    
    # Setup mock response
    mock_response = MockWatsonXResponse("Response", input_tokens=15, output_tokens=25)
    mock_instance.invoke.return_value = mock_response
    
    client.completion("Test")
    
    last_usage = client.get_last_usage()
    
    assert last_usage.total_calls == 1
    assert last_usage.total_input_tokens == 15
    assert last_usage.total_output_tokens == 25
    assert last_usage.total_cost is None

