import os
from typing import Any

import openai
from dotenv import load_dotenv

from rlm.clients.openai import OpenAIClient

load_dotenv()

DEFAULT_MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
DEFAULT_MINIMAX_BASE_URL = "https://api.minimax.io/v1"
DEFAULT_MINIMAX_MODEL = "MiniMax-M2.5"


class MinimaxClient(OpenAIClient):
    """
    LM Client for running models with the MiniMax API (OpenAI-compatible).

    Supported models:
      - MiniMax-M2.5 (default): 204K context, peak performance
      - MiniMax-M2.5-highspeed: 204K context, same performance, faster

    Uses the MiniMax OpenAI-compatible endpoint at https://api.minimax.io/v1.
    Set MINIMAX_API_KEY environment variable or pass api_key directly.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ):
        if api_key is None:
            api_key = DEFAULT_MINIMAX_API_KEY
        if base_url is None:
            base_url = DEFAULT_MINIMAX_BASE_URL
        if model_name is None:
            model_name = DEFAULT_MINIMAX_MODEL

        super().__init__(
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            **kwargs,
        )

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for MiniMax client.")

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.0,
        )
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
            raise ValueError("Model name is required for MiniMax client.")

        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.0,
        )
        self._track_cost(response, model)
        return response.choices[0].message.content
