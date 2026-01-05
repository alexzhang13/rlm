import os
from collections import defaultdict
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiClient(BaseLM):
    """
    LM Client for running models with the Google Gemini API.
    Uses the official google-genai SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = "gemini-2.5-flash",
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        if api_key is None:
            api_key = DEFAULT_GEMINI_API_KEY

        if api_key is None:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var or pass api_key."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

        # Last call tracking
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        contents, system_instruction = self._prepare_contents(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(system_instruction=system_instruction)

        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        self._track_cost(response, model)
        return response.text

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        contents, system_instruction = self._prepare_contents(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(system_instruction=system_instruction)

        # google-genai SDK supports async via aio interface
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        self._track_cost(response, model)
        return response.text

    def _prepare_contents(
        self, prompt: str | list[dict[str, Any]]
    ) -> tuple[list[types.Content] | str, str | None]:
        """Prepare contents and extract system instruction for Gemini API."""
        system_instruction = None

        if isinstance(prompt, str):
            return prompt, None

        if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            # Convert OpenAI-style messages to Gemini format
            contents = []
            for msg in prompt:
                role = msg.get("role")
                content = msg.get("content", "")

                if role == "system":
                    # Gemini handles system instruction separately
                    system_instruction = content
                elif role == "user":
                    contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
                elif role == "assistant":
                    # Gemini uses "model" instead of "assistant"
                    contents.append(types.Content(role="model", parts=[types.Part(text=content)]))
                else:
                    # Default to user role for unknown roles
                    contents.append(types.Content(role="user", parts=[types.Part(text=content)]))

            return contents, system_instruction

        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def _track_cost(self, response: types.GenerateContentResponse, model: str):
        self.model_call_counts[model] += 1

        # Extract token usage from response
        usage = response.usage_metadata
        if usage:
            input_tokens = usage.prompt_token_count or 0
            output_tokens = usage.candidates_token_count or 0

            self.model_input_tokens[model] += input_tokens
            self.model_output_tokens[model] += output_tokens
            self.model_total_tokens[model] += input_tokens + output_tokens

            # Track last call for handler to read
            self.last_prompt_tokens = input_tokens
            self.last_completion_tokens = output_tokens
        else:
            self.last_prompt_tokens = 0
            self.last_completion_tokens = 0

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
