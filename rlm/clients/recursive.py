import asyncio
from collections import defaultdict
from typing import Any

from rlm.clients.base_lm import BaseLM
from rlm.core.recursion_utils import select_backend_for_depth
from rlm.core.types import ClientBackend, ModelUsageSummary, UsageSummary
from rlm.core.rlm import RLM
from rlm.clients import get_client


class RecursiveRLMClient(BaseLM):
    """
    A BaseLM wrapper that spawns an RLM at a specific depth, enabling recursive sub-calls.
    """

    def __init__(
        self,
        depth: int,
        backend: ClientBackend,
        backend_kwargs: dict[str, Any],
        environment: str,
        environment_kwargs: dict[str, Any],
        recursive_max_depth: int,
        parent_max_iterations: int,
        other_backends: list[ClientBackend] | None = None,
        other_backend_kwargs: list[dict[str, Any]] | None = None,
        custom_system_prompt: str | None = None,
        model_name: str | None = None,
    ):
        super().__init__(model_name=model_name or f"rlm_depth_{depth}")

        if depth < 0:
            raise ValueError("depth must be >= 0")
        if recursive_max_depth < 0:
            raise ValueError("recursive_max_depth must be >= 0")

        self.depth = depth
        self.recursive_max_depth = recursive_max_depth
        self.parent_max_iterations = parent_max_iterations
        self.environment = environment
        self.environment_kwargs = environment_kwargs
        self.custom_system_prompt = custom_system_prompt
        self.other_backends = other_backends
        self.other_backend_kwargs = other_backend_kwargs

        # Backend for this depth
        self.backend, self.backend_kwargs = select_backend_for_depth(
            depth=depth,
            backend=backend,
            backend_kwargs=backend_kwargs,
            other_backends=other_backends,
            other_backend_kwargs=other_backend_kwargs,
        )
        self.base_client = get_client(self.backend, self.backend_kwargs)

        # Aggregate usage across recursive calls
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.depth_call_counts: dict[int, int] = defaultdict(int)
        self.last_usage = ModelUsageSummary(
            total_calls=0, total_input_tokens=0, total_output_tokens=0
        )

    def completion(self, prompt: str | dict[str, Any]) -> str:
        if self.recursive_max_depth <= 0:
            response = self.base_client.completion(prompt)
            usage_summary = UsageSummary(
                model_usage_summaries={
                    self.base_client.model_name: self.base_client.get_last_usage()
                }
            )
            self.record_usage_summary(usage_summary)
            return response

        nested_max_iterations = max(1, self.parent_max_iterations // 2)
        rlm = RLM(
            backend=self.backend,
            backend_kwargs=self.backend_kwargs,
            environment=self.environment,
            environment_kwargs=self.environment_kwargs,
            depth=self.depth,
            recursive_max_depth=self.recursive_max_depth,
            max_iterations=nested_max_iterations,
            custom_system_prompt=self.custom_system_prompt,
            other_backends=self.other_backends,
            other_backend_kwargs=self.other_backend_kwargs,
            verbose=False,
            logger=None,
            persistent=False,
        )
        completion = rlm.completion(prompt)
        self.record_usage_summary(completion.usage_summary)
        self.record_depth_call_counts(completion.depth_call_counts)
        return completion.response

    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        return await asyncio.to_thread(self.completion, prompt)

    def record_usage_summary(self, usage_summary: UsageSummary) -> None:
        for model, usage in usage_summary.model_usage_summaries.items():
            self.model_call_counts[model] += usage.total_calls
            self.model_input_tokens[model] += usage.total_input_tokens
            self.model_output_tokens[model] += usage.total_output_tokens
        self.last_usage = aggregate_usage(usage_summary)

    def record_depth_call_counts(self, depth_call_counts: dict[int, int]) -> None:
        for depth, count in depth_call_counts.items():
            self.depth_call_counts[depth] += count

    def get_depth_call_counts(self) -> dict[int, int]:
        return dict(self.depth_call_counts)

    def get_usage_summary(self) -> UsageSummary:
        summaries: dict[str, ModelUsageSummary] = {}
        for model in self.model_call_counts:
            summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
            )
        return UsageSummary(model_usage_summaries=summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return self.last_usage


def aggregate_usage(usage_summary: UsageSummary) -> ModelUsageSummary:
    total_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0

    for summary in usage_summary.model_usage_summaries.values():
        total_calls += summary.total_calls
        total_input_tokens += summary.total_input_tokens
        total_output_tokens += summary.total_output_tokens

    return ModelUsageSummary(
        total_calls=total_calls,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
    )
