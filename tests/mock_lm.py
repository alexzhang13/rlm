"""Mock LM for testing without a real model."""

from collections.abc import Callable
from typing import Any

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary


class MockLM(BaseLM):
    """
    In-memory mock LM that implements BaseLM for testing.

    - completion() / acompletion(): echo-style response by default, or use
      optional responses list / response_fn if provided.
    - get_usage_summary() / get_last_usage(): return usage suitable for tests.
    """

    def __init__(
        self,
        model_name: str = "mock-model",
        responses: list[str] | None = None,
        response_fn: Callable[[str | dict[str, Any]], str] | None = None,
        **kwargs: Any,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self._responses = list(responses) if responses is not None else None
        self._response_fn = response_fn
        self._call_count = 0

    def completion(self, prompt: str | dict[str, Any]) -> str:
        self._call_count += 1
        if self._responses is not None:
            if not self._responses:
                raise IndexError("MockLM: no more responses in list")
            return self._responses.pop(0)
        if self._response_fn is not None:
            return self._response_fn(prompt)
        prompt_str = prompt if isinstance(prompt, str) else str(prompt)[:80]
        return f"Mock response to: {prompt_str}"

    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        return self.completion(prompt)

    def get_usage_summary(self) -> UsageSummary:
        return UsageSummary(
            model_usage_summaries={
                self.model_name: ModelUsageSummary(
                    total_calls=self._call_count,
                    total_input_tokens=self._call_count * 10,
                    total_output_tokens=self._call_count * 10,
                )
            }
        )

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=10,
            total_output_tokens=10,
        )
