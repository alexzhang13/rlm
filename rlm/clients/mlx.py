import asyncio
from collections import defaultdict
from functools import lru_cache
from typing import Any

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary


@lru_cache(maxsize=4)
def _load_mlx_model(model_path: str) -> tuple[Any, Any]:
    try:
        import mlx_vlm
    except ImportError as exc:
        raise ImportError(
            "Install the optional MLX dependencies with `pip install 'rlms[mlx]'`."
        ) from exc
    return mlx_vlm.load(model_path)


def generate_mlx(
    prompt: str,
    model_path: str,
    image_path: str | list[str] | None = None,
    audio_path: str | list[str] | None = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    enable_thinking: bool = False,
    **kwargs,
) -> str:
    """Run a local MLX-VLM generation, importing heavy optional deps lazily."""
    try:
        from mlx_vlm.generate.dispatch import generate
        from mlx_vlm.prompt_utils import apply_chat_template
    except ImportError as exc:
        raise ImportError(
            "Install the optional MLX dependencies with `pip install 'rlms[mlx]'`."
        ) from exc

    model, processor = _load_mlx_model(model_path)
    num_images = len(image_path) if isinstance(image_path, list) else (1 if image_path else 0)
    num_audios = len(audio_path) if isinstance(audio_path, list) else (1 if audio_path else 0)
    formatted_prompt = apply_chat_template(
        processor,
        model.config,
        prompt,
        num_images=num_images,
        num_audios=num_audios,
        enable_thinking=enable_thinking,
    )
    output = generate(
        model,
        processor,
        formatted_prompt,
        image=image_path,
        audio=audio_path,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs,
    )
    return output.text if hasattr(output, "text") else str(output)


class MLXClient(BaseLM):
    """Local offline LM client for Apple Silicon models served through MLX."""

    def __init__(
        self,
        model_name: str | None = None,
        model_path: str | None = None,
        sampling_args: dict[str, Any] | None = None,
        **kwargs,
    ):
        if model_name is None and model_path is None:
            raise ValueError("MLX client requires model_name or model_path.")
        super().__init__(model_name=model_name or model_path, sampling_args=sampling_args, **kwargs)
        self.model_path = model_path or model_name
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def completion(
        self,
        prompt: str | list[dict[str, Any]] | dict[str, Any],
        model: str | None = None,
        **kwargs,
    ) -> str:
        prompt_text = self._prompt_to_text(prompt)
        generation_args = {**self.sampling_args, **kwargs}
        model_path_override = generation_args.pop("model_path", None)
        model_path = model_path_override or model or self.model_path
        usage_model = model or model_path_override or self.model_name or model_path
        image_path = generation_args.pop("image_path", generation_args.pop("image", None))
        audio_path = generation_args.pop("audio_path", generation_args.pop("audio", None))
        max_tokens = generation_args.pop("max_tokens", 512)
        temperature = generation_args.pop("temperature", 0.0)

        response = generate_mlx(
            prompt=prompt_text,
            model_path=model_path,
            image_path=image_path,
            audio_path=audio_path,
            max_tokens=max_tokens,
            temperature=temperature,
            **generation_args,
        )
        self._track_usage(usage_model, prompt_text, response)
        return response

    async def acompletion(
        self,
        prompt: str | list[dict[str, Any]] | dict[str, Any],
        model: str | None = None,
        **kwargs,
    ) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.completion(prompt, model=model, **kwargs),
        )

    def _prompt_to_text(self, prompt: str | list[dict[str, Any]] | dict[str, Any]) -> str:
        if isinstance(prompt, str):
            return prompt
        if isinstance(prompt, dict):
            return str(prompt.get("content", prompt))
        if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            return "\n".join(
                f"{message.get('role', 'user')}: {message.get('content', '')}" for message in prompt
            )
        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def _track_usage(self, model: str, prompt: str, response: str) -> None:
        input_tokens = max(1, len(prompt) // 4) if prompt else 0
        output_tokens = max(1, len(response) // 4) if response else 0
        self.model_call_counts[model] += 1
        self.model_input_tokens[model] += input_tokens
        self.model_output_tokens[model] += output_tokens
        self.last_prompt_tokens = input_tokens
        self.last_completion_tokens = output_tokens

    def get_usage_summary(self) -> UsageSummary:
        return UsageSummary(
            model_usage_summaries={
                model: ModelUsageSummary(
                    total_calls=self.model_call_counts[model],
                    total_input_tokens=self.model_input_tokens[model],
                    total_output_tokens=self.model_output_tokens[model],
                    total_cost=0.0,
                )
                for model in self.model_call_counts
            }
        )

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
            total_cost=0.0,
        )
