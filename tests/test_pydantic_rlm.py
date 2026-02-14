import pytest
import asyncio
from typing import List
from pydantic import BaseModel, Field
from rlm import RLM
from rlm.environments.local_repl import DirectREPL
from unittest.mock import MagicMock

class Insight(BaseModel):
    theme: str = Field(description="The main theme")
    confidence: float = Field(description="Confidence score 0-1")

class Report(BaseModel):
    title: str
    insights: List[Insight]

def test_pydantic_to_response_format():
    from rlm.utils.openai_utils import pydantic_to_response_format
    fmt = pydantic_to_response_format(Report)
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "Report"
    assert "insights" in fmt["json_schema"]["schema"]["properties"]

@pytest.mark.asyncio
async def test_llm_query_pydantic_response_model():
    """Test that llm_query supports response_model and returns a Pydantic object."""
    mock_handler = MagicMock()
    repl = DirectREPL(lm_handler=mock_handler)
    
    # Mock successful JSON response
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.chat_completion.response = '{"title": "Test Report", "insights": [{"theme": "AI", "confidence": 0.9}]}'
    mock_response.chat_completion.error = None
    mock_handler.handle_request.return_value = mock_response
    
    result = repl._llm_query("Tell me about AI", response_model=Report)
    
    assert isinstance(result, Report)
    assert result.title == "Test Report"
    assert result.insights[0].theme == "AI"

@pytest.mark.asyncio
async def test_llm_query_pydantic_tools():
    """Test that llm_query supports Pydantic classes as tools."""
    mock_handler = MagicMock()
    repl = DirectREPL(lm_handler=mock_handler)
    
    class SearchTool(BaseModel):
        """Search for information"""
        query: str
    
    def tool_handler(name, args):
        return "Search results"

    # Mock tool call response
    import json
    
    # First response: tool call
    mock_cc1 = MagicMock()
    mock_cc1.response = json.dumps({
        "tool_calls": [{"id": "1", "name": "SearchTool", "arguments": {"query": "test"}}]
    })
    mock_cc1.error = None
    
    mock_res1 = MagicMock()
    mock_res1.success = True
    mock_res1.chat_completion = mock_cc1
    
    # Second response: final content
    mock_cc2 = MagicMock()
    mock_cc2.response = "Final answer"
    mock_cc2.error = None
    
    mock_res2 = MagicMock()
    mock_res2.success = True
    mock_res2.chat_completion = mock_cc2
    
    mock_handler.handle_request.side_effect = [mock_res1, mock_res2]
    
    result = repl._llm_query("Search for test", tools=[SearchTool], tool_handler=tool_handler)
    
    assert result == "Final answer"
    # Verify tools were converted correctly in the first request
    args, _ = mock_handler.handle_request.call_args_list[0]
    req = args[0]
    assert req.tools[0]["function"]["name"] == "SearchTool"
    assert "query" in req.tools[0]["function"]["parameters"]["properties"]
