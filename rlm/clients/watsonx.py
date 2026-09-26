import os
from collections import defaultdict
from typing import Any

from dotenv import load_dotenv

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

# Load API keys from environment variables
DEFAULT_WATSONX_API_KEY = os.getenv("WATSONX_APIKEY")
DEFAULT_WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
DEFAULT_WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")


class WatsonXClient(BaseLM):
    """
    LM Client for running models with IBM WatsonX AI using LangChain integration.
    
    Requires langchain-ibm package to be installed:
        pip install langchain-ibm
    
    Environment variables:
        - WATSONX_APIKEY: Your IBM Cloud API key
        - WATSONX_PROJECT_ID: Your WatsonX project ID
        - WATSONX_URL: WatsonX service URL (optional, defaults to us-south)
    
    This client uses the LangChain ChatWatsonx integration which provides:
        - Tool calling support
        - Streaming capabilities
        - Structured output
        - Better message handling
    """

    def __init__(
        self,
        api_key: str | None = None,
        project_id: str | None = None,
        url: str | None = None,
        model_name: str | None = None,
        watsonx_client: Any | None = None,
        params: dict[str, Any] | None = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name or "", **kwargs)

        # Import here to make it optional
        try:
            from langchain_ibm import ChatWatsonx
        except ImportError:
            raise ImportError(
                "langchain-ibm package is required for WatsonX client. "
                "Install it with: pip install langchain-ibm"
            )

        # Use provided values or fall back to environment variables
        self.api_key = api_key or DEFAULT_WATSONX_API_KEY
        self.project_id = project_id or DEFAULT_WATSONX_PROJECT_ID
        self.url = url or DEFAULT_WATSONX_URL
        self.model_name = model_name

        # Build kwargs for ChatWatsonx
        chat_kwargs: dict[str, Any] = {}
        
        # If a custom watsonx_client (APIClient) is provided, use it
        if watsonx_client:
            chat_kwargs["watsonx_client"] = watsonx_client
        else:
            # Otherwise, use credentials
            if not self.api_key:
                raise ValueError(
                    "WatsonX API key is required. Set WATSONX_APIKEY environment variable "
                    "or pass api_key parameter."
                )
            if not self.project_id:
                raise ValueError(
                    "WatsonX project ID is required. Set WATSONX_PROJECT_ID environment variable "
                    "or pass project_id parameter."
                )
            
            chat_kwargs["url"] = self.url
            chat_kwargs["apikey"] = self.api_key
            chat_kwargs["project_id"] = self.project_id

        # Add model_id if provided
        if model_name:
            chat_kwargs["model_id"] = model_name

        # Add custom parameters if provided
        if params:
            chat_kwargs["params"] = params

        # Initialize the LangChain ChatWatsonx client
        self.client = ChatWatsonx(**chat_kwargs)

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

        # Last call tracking
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def _format_messages(self, prompt: str | dict[str, Any] | list[dict[str, Any]]) -> list[tuple[str, str]]:
        """Convert prompt to LangChain message format."""
        if isinstance(prompt, str):
            return [("human", prompt)]
        elif isinstance(prompt, list):
            # Handle list of message dicts
            messages = []
            for msg in prompt:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        messages.append(("system", content))
                    elif role == "assistant":
                        messages.append(("assistant", content))
                    else:
                        messages.append(("human", content))
            return messages
        elif isinstance(prompt, dict):
            # Handle single message dict
            role = prompt.get("role", "user")
            content = prompt.get("content", "")
            if role == "system":
                return [("system", content)]
            elif role == "assistant":
                return [("assistant", content)]
            else:
                return [("human", content)]
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def completion(self, prompt: str | dict[str, Any] | list[dict[str, Any]], model: str | None = None) -> str:
        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for WatsonX client.")

        # Format messages for LangChain
        messages = self._format_messages(prompt)

        # If a different model is requested, create a new client instance
        if model != self.model_name:
            from langchain_ibm import ChatWatsonx
            
            temp_client = ChatWatsonx(
                model_id=model,
                url=self.url,  # type: ignore
                apikey=self.api_key,  # type: ignore
                project_id=self.project_id,
            )
            response = temp_client.invoke(messages)
        else:
            response = self.client.invoke(messages)

        # Track usage
        self._track_usage(model, response)
        
        # Ensure we return a string (LangChain may return list for some models)
        content = response.content
        if isinstance(content, list):
            # Join list items if content is a list
            return " ".join(str(item) for item in content)
        return str(content)

    async def acompletion(
        self, prompt: str | dict[str, Any] | list[dict[str, Any]], model: str | None = None
    ) -> str:
        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for WatsonX client.")

        # Format messages for LangChain
        messages = self._format_messages(prompt)

        # If a different model is requested, create a new client instance
        if model != self.model_name:
            from langchain_ibm import ChatWatsonx
            
            temp_client = ChatWatsonx(
                model_id=model,
                url=self.url,  # type: ignore
                apikey=self.api_key,  # type: ignore
                project_id=self.project_id,
            )
            response = await temp_client.ainvoke(messages)
        else:
            response = await self.client.ainvoke(messages)

        # Track usage
        self._track_usage(model, response)
        
        # Ensure we return a string (LangChain may return list for some models)
        content = response.content
        if isinstance(content, list):
            # Join list items if content is a list
            return " ".join(str(item) for item in content)
        return str(content)

    def _track_usage(self, model: str, response: Any):
        """Track usage statistics from the LangChain response."""
        self.model_call_counts[model] += 1

        # Extract token usage from response metadata
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata:
            prompt_tokens = usage_metadata.get("input_tokens", 0)
            completion_tokens = usage_metadata.get("output_tokens", 0)
        else:
            # Fallback to response_metadata
            response_metadata = getattr(response, "response_metadata", {})
            token_usage = response_metadata.get("token_usage", {})
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)

        total_tokens = prompt_tokens + completion_tokens

        self.model_input_tokens[model] += prompt_tokens
        self.model_output_tokens[model] += completion_tokens
        self.model_total_tokens[model] += total_tokens

        # Track last call
        self.last_prompt_tokens = prompt_tokens
        self.last_completion_tokens = completion_tokens

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
                total_cost=None,  # WatsonX doesn't provide cost info in API responses
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
            total_cost=None,
        )

