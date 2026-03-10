from collections import defaultdict
from typing import Any

import anthropic

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

# Per-1M-token pricing (USD) as of 2025-06. Update as needed or use pricing_override.
_ANTHROPIC_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    # Claude 4 family
    "claude-opus-4-20250514": (15.0, 75.0),
    "claude-opus-4-latest": (15.0, 75.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-sonnet-4-latest": (3.0, 15.0),
    # Claude 3.7
    "claude-3-7-sonnet-20250219": (3.0, 15.0),
    "claude-3-7-sonnet-latest": (3.0, 15.0),
    # Claude 3.5
    "claude-3-5-sonnet-20241022": (3.0, 15.0),
    "claude-3-5-sonnet-20240620": (3.0, 15.0),
    "claude-3-5-sonnet-latest": (3.0, 15.0),
    "claude-3-5-haiku-20241022": (0.80, 4.0),
    "claude-3-5-haiku-latest": (0.80, 4.0),
    # Claude 3
    "claude-3-opus-20240229": (15.0, 75.0),
    "claude-3-opus-latest": (15.0, 75.0),
    "claude-3-sonnet-20240229": (3.0, 15.0),
    "claude-3-haiku-20240307": (0.25, 1.25),
}

_CACHE_CREATION_MULTIPLIER = 1.25
_CACHE_READ_MULTIPLIER = 0.10


class AnthropicClient(BaseLM):
    """
    LM Client for running models with the Anthropic API.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str | None = None,
        max_tokens: int = 32768,
        enable_prefix_cache: bool = False,
        pricing_override: dict[str, tuple[float, float]] | None = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.client = anthropic.Anthropic(api_key=api_key, timeout=self.timeout)
        self.async_client = anthropic.AsyncAnthropic(api_key=api_key, timeout=self.timeout)
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.enable_prefix_cache = enable_prefix_cache
        self._pricing = {**_ANTHROPIC_PRICING, **(pricing_override or {})}

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)
        self.model_costs: dict[str, float] = defaultdict(float)
        self.model_cache_creation_tokens: dict[str, int] = defaultdict(int)
        self.model_cache_read_tokens: dict[str, int] = defaultdict(int)

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
    ) -> tuple[list[dict[str, Any]], str | list[dict[str, Any]] | None]:
        """Prepare messages and extract system prompt for Anthropic API.

        When enable_prefix_cache is True, annotates the system prompt and the
        last user message with cache_control for Anthropic prompt caching.
        """
        system: str | list[dict[str, Any]] | None = None

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

        if self.enable_prefix_cache:
            # Annotate system prompt with cache_control
            if system is not None:
                if isinstance(system, str):
                    system = [
                        {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
                    ]
                elif isinstance(system, list) and system:
                    # System is already a list of content blocks; annotate the last block
                    last = system[-1]
                    if isinstance(last, dict):
                        system = system[:-1] + [{**last, "cache_control": {"type": "ephemeral"}}]

            # Annotate last user message content with cache_control
            if messages:
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get("role") == "user":
                        content = messages[i].get("content", "")
                        if isinstance(content, str):
                            messages[i] = {
                                **messages[i],
                                "content": [
                                    {
                                        "type": "text",
                                        "text": content,
                                        "cache_control": {"type": "ephemeral"},
                                    }
                                ],
                            }
                        break

        return messages, system

    def _track_cost(self, response: anthropic.types.Message, model: str):
        self.model_call_counts[model] += 1
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        self.model_input_tokens[model] += input_tokens
        self.model_output_tokens[model] += output_tokens
        self.model_total_tokens[model] += input_tokens + output_tokens

        # Cache token tracking (Anthropic extended usage fields)
        cache_creation = getattr(response.usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(response.usage, "cache_read_input_tokens", 0) or 0
        self.model_cache_creation_tokens[model] += cache_creation
        self.model_cache_read_tokens[model] += cache_read

        # Track last call for handler to read
        self.last_prompt_tokens = input_tokens
        self.last_completion_tokens = output_tokens

        # Compute USD cost if pricing is known.
        # Anthropic usage fields decompose input tokens into three disjoint groups:
        #   input_tokens: non-cached input tokens (charged at base rate)
        #   cache_creation_input_tokens: tokens written to cache (1.25x base rate)
        #   cache_read_input_tokens: tokens read from cache (0.10x base rate)
        self.last_cost: float | None = None
        pricing = self._pricing.get(model)
        if pricing is not None:
            input_price, output_price = pricing
            cost = (
                input_tokens * input_price
                + output_tokens * output_price
                + cache_creation * input_price * _CACHE_CREATION_MULTIPLIER
                + cache_read * input_price * _CACHE_READ_MULTIPLIER
            ) / 1_000_000
            self.last_cost = cost
            self.model_costs[model] += cost

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            cost = self.model_costs.get(model)
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
                total_cost=cost if cost else None,
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
            total_cost=getattr(self, "last_cost", None),
        )
