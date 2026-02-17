from collections import defaultdict
from typing import Any

import litellm

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary


class LiteLLMClient(BaseLM):
    """
    LM Client for running models with LiteLLM.
    LiteLLM provides a unified interface to 100+ LLM providers.
    """

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for LiteLLM client.")

        kwargs = {"model": model, "messages": messages, "timeout": self.timeout}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        response = litellm.completion(**kwargs)
        self._track_cost(response, model)
        return response.choices[0].message.content

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for LiteLLM client.")

        kwargs = {"model": model, "messages": messages, "timeout": self.timeout}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        response = await litellm.acompletion(**kwargs)
        self._track_cost(response, model)
        return response.choices[0].message.content

    def _track_cost(self, response, model: str):
        self.model_call_counts[model] += 1
        self.model_input_tokens[model] += response.usage.prompt_tokens
        self.model_output_tokens[model] += response.usage.completion_tokens
        self.model_total_tokens[model] += response.usage.total_tokens

        # Track last call for handler to read
        self.last_prompt_tokens = response.usage.prompt_tokens
        self.last_completion_tokens = response.usage.completion_tokens

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
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
        )
