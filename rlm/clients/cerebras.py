import os
from collections import defaultdict
from typing import Any

from cerebras.cloud.sdk import AsyncCerebras, Cerebras
from dotenv import load_dotenv

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

DEFAULT_CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
DEFAULT_CEREBRAS_BASE_URL = os.getenv("CEREBRAS_BASE_URL")


class CerebrasClient(BaseLM):
    """
    LM client for running models with the Cerebras Cloud SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        if api_key is None:
            api_key = DEFAULT_CEREBRAS_API_KEY

        if base_url is None:
            base_url = DEFAULT_CEREBRAS_BASE_URL

        self.client = Cerebras(api_key=api_key, base_url=base_url, **kwargs)
        self.async_client = AsyncCerebras(api_key=api_key, base_url=base_url, **kwargs)
        self.model_name = model_name
        self.request_kwargs = kwargs

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        messages = self._build_messages(prompt)
        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Cerebras client.")

        request_kwargs = {**self.request_kwargs, "model": model, "messages": messages}
        response = self.client.chat.completions.create(**request_kwargs)
        self._track_cost(response, model)

        return self._extract_content(response)

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        messages = self._build_messages(prompt)
        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Cerebras client.")

        request_kwargs = {**self.request_kwargs, "model": model, "messages": messages}
        response = await self.async_client.chat.completions.create(**request_kwargs)
        self._track_cost(response, model)

        return self._extract_content(response)

    def _build_messages(self, prompt: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            return prompt
        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def _extract_content(self, response: Any) -> str:
        if not getattr(response, "choices", None):
            return ""
        message = response.choices[0].message
        return message.content or ""

    def _track_cost(self, response: Any, model: str):
        self.model_call_counts[model] += 1

        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        self.model_input_tokens[model] += prompt_tokens
        self.model_output_tokens[model] += completion_tokens
        self.model_total_tokens[model] += total_tokens

        # Track last call for handler to read
        self.last_prompt_tokens = prompt_tokens
        self.last_completion_tokens = completion_tokens

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=getattr(self, "last_prompt_tokens", 0),
            total_output_tokens=getattr(self, "last_completion_tokens", 0),
        )
