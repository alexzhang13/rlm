import os
from collections import defaultdict
from collections.abc import AsyncIterator, Iterator
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")
DEFAULT_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
DEFAULT_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
DEFAULT_MODEL_NAME = "gemini-2.5-flash"


class GeminiClient(BaseLM):
    """
    LM Client for running models with the Google Gemini API.
    Uses the official google-genai SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = DEFAULT_MODEL_NAME,
        vertexai: bool = False,
        project: str | None = None,
        location: str | None = None,
        **kwargs,
    ):
        """
        Initialize the Gemini Client.

        Args:
            model_name: The ID of the model to use.
            api_key: API key for Gemini API.
            vertexai: If True, use Vertex AI.
            project: Google Cloud project ID (required if vertexai=True).
            location: Google Cloud location (required if vertexai=True).
            **kwargs: Additional arguments passed to the genai.Client.
                Supported kwargs:
                - safety_settings: Optional safety settings configuration for content filtering.
        """

        super().__init__(model_name=model_name, **kwargs)

        api_key = api_key or DEFAULT_GEMINI_API_KEY
        vertexai = vertexai or DEFAULT_VERTEXAI
        project = project or DEFAULT_PROJECT
        location = location or DEFAULT_LOCATION

        # Optional safety settings configuration
        self.safety_settings = kwargs.pop("safety_settings", None)

        # Try Gemini API first (unless vertexai is explicitly True)
        if not vertexai and api_key:
            self.client = genai.Client(api_key=api_key, **kwargs)
        # If vertexai=True or we don't have a Gemini API key, try Vertex AI
        elif vertexai or (not api_key and (project or location)):
            if not project or not location:
                raise ValueError(
                    "Vertex AI requires a project ID and location. "
                    "Set it via `project` and `location` arguments or `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` environment variables."
                )
            self.client = genai.Client(
                vertexai=True,
                project=project,
                location=location,
                **kwargs,
            )
        # No valid configuration found
        else:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var or pass api_key."
                " For Vertex AI, ensure GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are set."
            )

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

        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction

        # Apply safety settings if configured
        if self.safety_settings:
            config.safety_settings = self.safety_settings

        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        self._track_cost(response, model)
        return response.text

    def completion_stream(
        self,
        prompt: str | list[dict[str, Any]],
        model: str | None = None,
    ) -> Iterator[str]:
        """
        Stream completion tokens from the Gemini model.

        Args:
            prompt: The prompt (string or message list)
            model: Optional model override

        Yields:
            Token chunks as they arrive
        """

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        contents, system_instruction = self._prepare_contents(prompt)

        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction

        if self.safety_settings:
            config.safety_settings = self.safety_settings

        response_stream = self.client.models.generate_content_stream(
            model=model, contents=contents, config=config
        )

        # Track the last chunk for usage metadata
        last_chunk = None
        for chunk in response_stream:
            last_chunk = chunk
            if chunk.text:
                yield chunk.text

        # Track usage from the final chunk if available
        if last_chunk:
            self._track_cost(last_chunk, model)

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        contents, system_instruction = self._prepare_contents(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction

        if self.safety_settings:
            config.safety_settings = self.safety_settings

        # google-genai SDK supports async via aio interface
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        self._track_cost(response, model)
        return response.text

    async def acompletion_stream(
        self,
        prompt: str | list[dict[str, Any]],
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Async stream completion tokens from the Gemini model.

        Args:
            prompt: The prompt (string or message list)
            model: Optional model override

        Yields:
            Token chunks as they arrive
        """

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        contents, system_instruction = self._prepare_contents(prompt)

        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction

        if self.safety_settings:
            config.safety_settings = self.safety_settings

        response_stream = await self.client.aio.models.generate_content_stream(
            model=model, contents=contents, config=config
        )

        # Track the last chunk for usage metadata
        last_chunk = None
        async for chunk in response_stream:
            last_chunk = chunk
            if chunk.text:
                yield chunk.text

        # Track usage from the final chunk if available
        if last_chunk:
            self._track_cost(last_chunk, model)

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
                    if system_instruction:
                        system_instruction += "\n" + content
                    else:
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
            total_tokens = usage.total_token_count or (input_tokens + output_tokens)

            self.model_input_tokens[model] += input_tokens
            self.model_output_tokens[model] += output_tokens
            self.model_total_tokens[model] += total_tokens

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
