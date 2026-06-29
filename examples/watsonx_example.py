"""
Example demonstrating how to use IBM WatsonX AI with RLM using LangChain integration.

Prerequisites:
1. Install langchain-ibm: pip install langchain-ibm
2. Set environment variables:
   - WATSONX_APIKEY: Your IBM Cloud API key
   - WATSONX_PROJECT_ID: Your WatsonX project ID
   - WATSONX_URL (optional): WatsonX service URL (defaults to us-south)

You can also pass these values directly to the RLM constructor.

This integration uses LangChain's ChatWatsonx which provides:
- Tool calling support
- Streaming capabilities
- Structured output
- Better message handling
- Multi-turn conversation support
"""

from rlm import RLM


rlm = RLM(
    backend="watsonx",
    backend_kwargs={
        "api_key": "<APIKEY HERE>",
        "project_id": "<PROJECT ID HERE>",
        "url": "https://us-south.ml.cloud.ibm.com",  # optional
        "model_name": "openai/gpt-oss-120b",
    },
)

# Example 1: Simple string query
print("=== Example 1: Simple Query ===")
print(rlm.completion("Print me the first 100 powers of two, each on a newline.").response)



