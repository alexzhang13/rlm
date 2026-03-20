"""AWS Bedrock client for RLM via Project Mantle (OpenAI-compatible endpoint).

Amazon Bedrock provides an OpenAI-compatible API through Project Mantle,
allowing seamless integration with existing OpenAI SDK code.

Environment variables:
    AWS_BEDROCK_API_KEY: Bedrock API key (Bearer token).
                         Generate in AWS Console → Bedrock → API keys.
    AWS_BEDROCK_REGION:  AWS region for Mantle endpoint (default: us-east-1).

Endpoint format:
    https://bedrock-mantle.{region}.api.aws/v1

Supported models (examples):
    - qwen.qwen3-32b-v1:0
    - qwen.qwen3-coder-30b-a3b-v1:0
    - qwen.qwen3-235b-a22b-2507-v1:0
    - amazon.nova-micro-v1:0
    - meta.llama3-2-1b-instruct-v1:0

Usage:
    from rlm import RLM

    rlm = RLM(
        backend="bedrock",
        backend_kwargs={
            "model_name": "qwen.qwen3-coder-30b-a3b-v1:0",
            # api_key and region are optional if env vars are set
        },
    )
    result = rlm.completion("Your prompt here")

See also:
    https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html
    https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html
"""

import os
from collections import defaultdict
from typing import Any

import openai
from dotenv import load_dotenv

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

# Default environment variables
DEFAULT_BEDROCK_API_KEY = os.getenv("AWS_BEDROCK_API_KEY")
DEFAULT_BEDROCK_REGION = os.getenv("AWS_BEDROCK_REGION", "us-east-1")


def _build_mantle_base_url(region: str) -> str:
    """Build the Bedrock Mantle endpoint URL for a given region."""
    return f"https://bedrock-mantle.{region}.api.aws/v1"


class BedrockClient(BaseLM):
    """LM Client for AWS Bedrock via Project Mantle (OpenAI-compatible API).

    Bedrock's Project Mantle provides a native OpenAI-compatible endpoint
    that accepts Bedrock API keys as Bearer tokens. This client uses the
    standard OpenAI SDK under the hood, configured to point at Mantle.

    Args:
        api_key: Bedrock API key. Falls back to AWS_BEDROCK_API_KEY env var.
        model_name: Model ID (e.g., "qwen.qwen3-coder-30b-a3b-v1:0").
        region: AWS region for Mantle endpoint. Falls back to AWS_BEDROCK_REGION
                env var, then defaults to "us-east-1".
        base_url: Override the Mantle endpoint URL. If not provided, it's
                  constructed from the region.
        max_tokens: Maximum tokens for completion (default: 32768).
        **kwargs: Additional arguments passed to BaseLM.

    Raises:
        ValueError: If no API key is provided and AWS_BEDROCK_API_KEY is not set.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        region: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 32768,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        # Resolve API key
        if api_key is None:
            api_key = DEFAULT_BEDROCK_API_KEY
        if api_key is None:
            raise ValueError(
                "Bedrock API key is required. "
                "Set AWS_BEDROCK_API_KEY environment variable or pass api_key parameter."
            )

        # Resolve region and base URL
        region = region or DEFAULT_BEDROCK_REGION
        if base_url is None:
            base_url = _build_mantle_base_url(region)

        # Initialize OpenAI clients pointing to Mantle
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.region = region
        self.base_url = base_url

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)
        self.last_prompt_tokens: int = 0
        self.last_completion_tokens: int = 0

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        """Generate a completion using Bedrock via Mantle.

        Args:
            prompt: Either a string or a list of message dicts with "role" and "content".
            model: Override the model for this request.

        Returns:
            The generated text response.

        Raises:
            ValueError: If no model is specified.
        """
        messages = self._prepare_messages(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Bedrock client.")

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        self._track_cost(response, model)
        return response.choices[0].message.content

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        """Generate a completion asynchronously using Bedrock via Mantle.

        Args:
            prompt: Either a string or a list of message dicts with "role" and "content".
            model: Override the model for this request.

        Returns:
            The generated text response.

        Raises:
            ValueError: If no model is specified.
        """
        messages = self._prepare_messages(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Bedrock client.")

        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        self._track_cost(response, model)
        return response.choices[0].message.content

    def _prepare_messages(self, prompt: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert prompt to OpenAI message format.

        Args:
            prompt: Either a string or a list of message dicts.

        Returns:
            List of message dicts in OpenAI format.

        Raises:
            ValueError: If prompt type is not supported.
        """
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            return prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def _track_cost(self, response: openai.types.chat.ChatCompletion, model: str) -> None:
        """Track token usage for cost monitoring.

        Args:
            response: The completion response from OpenAI SDK.
            model: The model name used for this request.
        """
        self.model_call_counts[model] += 1

        usage = getattr(response, "usage", None)
        if usage is not None:
            self.model_input_tokens[model] += usage.prompt_tokens
            self.model_output_tokens[model] += usage.completion_tokens
            self.model_total_tokens[model] += usage.total_tokens
            self.last_prompt_tokens = usage.prompt_tokens
            self.last_completion_tokens = usage.completion_tokens
        else:
            # Some responses may not include usage; track call count only
            self.last_prompt_tokens = 0
            self.last_completion_tokens = 0

    def get_usage_summary(self) -> UsageSummary:
        """Get aggregated usage summary for all models.

        Returns:
            UsageSummary with per-model token counts and call counts.
        """
        model_summaries = {}
        for model in self.model_call_counts:
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        """Get usage summary for the last API call.

        Returns:
            ModelUsageSummary for the most recent completion.
        """
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
        )
