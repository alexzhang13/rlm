from collections import defaultdict
from typing import Any

import httpx
from dotenv import load_dotenv

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


class OllamaClient(BaseLM):
    """
    LM Client for running models with Ollama or llama.cpp.

    Works with local Ollama servers via the OpenAI-compatible API endpoint.
    Requires Ollama to be running with the server started:
        ollama serve

    And models pulled:
        ollama pull llama3
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model_name: str | None = None,
        api_key: str | None = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "ollama"
        self.timeout = kwargs.get("timeout", httpx.Timeout(60.0, connect=10.0))

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        self.async_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_cost: float | None = None

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Ollama client.")

        response = self.client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        self._track_usage(data, model)
        return data["choices"][0]["message"]["content"]

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
            raise ValueError("Model name is required for Ollama client.")

        response = await self.async_client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        self._track_usage(data, model)
        return data["choices"][0]["message"]["content"]

    def _track_usage(self, data: dict, model: str) -> None:
        self.model_call_counts[model] += 1

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        self.model_input_tokens[model] += prompt_tokens
        self.model_output_tokens[model] += completion_tokens
        self.last_prompt_tokens = prompt_tokens
        self.last_completion_tokens = completion_tokens

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

    def get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available models from Ollama server."""
        try:
            response = self.client.get("/models")
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception:
            return []

    def check_connection(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            response = self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        self.client.close()

    async def aclose(self) -> None:
        await self.async_client.aclose()