"""
Utilities for OpenAI-specific features like Pydantic model conversion.
"""

import json
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel


def pydantic_to_tool(model: Type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic model to an OpenAI tool definition."""
    schema = model.model_json_schema()
    
    # OpenAI expects title and description to be at the top level of the function
    name = schema.pop("title", model.__name__)
    description = schema.pop("description", "")
    
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": schema,
            "strict": True  # Enable Structured Outputs
        }
    }


def pydantic_to_response_format(model: Type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic model to an OpenAI response_format dict."""
    schema = model.model_json_schema()
    name = schema.pop("title", model.__name__)
    
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": schema
        }
    }


def parse_pydantic_response(model: Type[BaseModel], response_text: str) -> BaseModel:
    """Parse a JSON response into a Pydantic model."""
    try:
        data = json.loads(response_text)
        return model.model_validate(data)
    except Exception as e:
        # Fallback or raise
        raise ValueError(f"Failed to parse response into {model.__name__}: {e}")
