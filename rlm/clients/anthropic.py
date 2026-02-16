from collections import defaultdict
from typing import Any

import anthropic

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary


class AnthropicClient(BaseLM):
    """
    LM Client for running models with the Anthropic API.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str | None = None,
        max_tokens: int = 32768,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.client = anthropic.Anthropic(api_key=api_key, timeout=self.timeout)
        self.async_client = anthropic.AsyncAnthropic(api_key=api_key, timeout=self.timeout)
        self.model_name = model_name
        self.max_tokens = max_tokens

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        messages, system = self._prepare_messages(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Anthropic client.")

        kwargs = {"model": model, "max_tokens": self.max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        self._track_cost(response, model)
        return response.content[0].text

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        messages, system = self._prepare_messages(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Anthropic client.")

        kwargs = {"model": model, "max_tokens": self.max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system

        response = await self.async_client.messages.create(**kwargs)
        self._track_cost(response, model)
        return response.content[0].text

    def _prepare_messages(
        self, prompt: str | list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Prepare messages and extract system prompt for Anthropic API."""
        system = None

        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            # Extract system message if present (Anthropic handles system separately)
            messages = []
            for msg in prompt:
                if msg.get("role") == "system":
                    system = msg.get("content")
                else:
                    messages.append(msg)
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        return messages, system

    def _track_cost(self, response: anthropic.types.Message, model: str):
        self.model_call_counts[model] += 1
        self.model_input_tokens[model] += response.usage.input_tokens
        self.model_output_tokens[model] += response.usage.output_tokens
        self.model_total_tokens[model] += response.usage.input_tokens + response.usage.output_tokens

        # Track last call for handler to read
        self.last_prompt_tokens = response.usage.input_tokens
        self.last_completion_tokens = response.usage.output_tokens

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
