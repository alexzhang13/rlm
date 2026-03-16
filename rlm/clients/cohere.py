import os
from collections import defaultdict
from typing import Any, Optional

import cohere
from dotenv import load_dotenv
import openai

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

# Load API keys from environment variables
DEFAULT_COHERE_API_KEY = os.getenv("COHERE_API_KEY")

class CohereClient(BaseLM):
    """
    LM Client for running models with the Cohere API.

    Supports both string prompts and message list formats compatible with
    the Cohere chat API.
    """

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = DEFAULT_COHERE_API_KEY,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        client_kwargs = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": self.timeout,
            **{k: v for k, v in self.kwargs.items() if k != "model_name"},
        }

        self.client = cohere.ClientV2(
            **client_kwargs
        )
        self.async_client = openai.AsyncOpenAI(
            **client_kwargs
        )
        self.model_name = model_name
        self.base_url = base_url

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)

        # Last call tracking
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def completion(self, prompt: str | list[dict[str, Any]]) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        response = self.client.chat(
            model=self.model_name,
            messages=messages,
        )
        self._track_cost(response, self.model_name)
        return response.message.content[0].text

    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        response = await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        self._track_cost(response, self.model_name)
        return response.message.content[0].text

    def _track_cost(self, response: cohere.ChatResponse, model: str):
        self.model_call_counts[model] += 1

        usage = getattr(response, "usage", None)
        if usage is None:
            raise ValueError("No usage data received. Tracking tokens not possible.")

        self.model_input_tokens[model] += usage.billed_units.input_tokens
        self.model_output_tokens[model] += usage.billed_units.output_tokens
        self.last_prompt_tokens = usage.billed_units.input_tokens
        self.last_completion_tokens = usage.billed_units.output_tokens

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
                total_cost=None,
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
            total_cost=None,
        )
