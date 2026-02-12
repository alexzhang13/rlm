import os
from collections import defaultdict
from typing import Any

import anthropic
from dotenv import load_dotenv

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

DEFAULT_FOUNDRY_API_KEY = os.getenv("ANTHROPIC_FOUNDRY_API_KEY")
DEFAULT_FOUNDRY_RESOURCE = os.getenv("ANTHROPIC_FOUNDRY_RESOURCE")
DEFAULT_FOUNDRY_BASE_URL = os.getenv("ANTHROPIC_FOUNDRY_BASE_URL")

ANTHROPIC_PATH_SUFFIX = "/anthropic/v1"


def _resolve_base_url(base_url: str | None, resource: str | None) -> str:
    """Derive the Foundry base URL from explicit URL or resource name.

    Accepts either:
      - A resource name  → https://{resource}.services.ai.azure.com/anthropic/v1
      - A Foundry endpoint URL (resource- or project-scoped)
        e.g. https://res.services.ai.azure.com
             https://res.services.ai.azure.com/api/projects/my-proj

    The /anthropic/v1 suffix is always appended (unless already present).
    """
    if base_url:
        url = base_url.rstrip("/")
        if not url.endswith(ANTHROPIC_PATH_SUFFIX):
            url = url + ANTHROPIC_PATH_SUFFIX
        return url
    if resource:
        return f"https://{resource}.services.ai.azure.com{ANTHROPIC_PATH_SUFFIX}"
    raise ValueError(
        "Azure Anthropic Foundry endpoint is required. "
        "Set ANTHROPIC_FOUNDRY_BASE_URL, ANTHROPIC_FOUNDRY_RESOURCE, "
        "or pass base_url/resource as an argument."
    )


class AzureAnthropicClient(BaseLM):
    """
    LM Client for running Anthropic models hosted on Azure AI Foundry.

    Follows the ANTHROPIC_FOUNDRY_* env-var convention used by Claude Code:
        ANTHROPIC_FOUNDRY_API_KEY      - API key
        ANTHROPIC_FOUNDRY_RESOURCE     - Azure resource name (derives base URL)
        ANTHROPIC_FOUNDRY_BASE_URL     - Explicit base URL (overrides resource)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        resource: str | None = None,
        max_tokens: int = 4096,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        if api_key is None:
            api_key = DEFAULT_FOUNDRY_API_KEY

        if base_url is None:
            base_url = DEFAULT_FOUNDRY_BASE_URL

        if resource is None:
            resource = DEFAULT_FOUNDRY_RESOURCE

        resolved_url = _resolve_base_url(base_url, resource)

        self.client = anthropic.Anthropic(api_key=api_key, base_url=resolved_url)
        self.async_client = anthropic.AsyncAnthropic(api_key=api_key, base_url=resolved_url)
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
            raise ValueError("Model name is required for Azure Anthropic client.")

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
            raise ValueError("Model name is required for Azure Anthropic client.")

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
