"""
Observability and Tracing utilities for RLM.
Supports propagation of trace IDs and integration with tools like Langfuse and OpenTelemetry.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceContext:
    """Container for tracing metadata."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"trace_id": self.trace_id, "parent_id": self.parent_id, **self.metadata}


class TracingLogger:
    """
    A helper to bridge RLM hooks to observability platforms.

    Example with Langfuse:
        logger = TracingLogger(on_trace=lambda data: langfuse.trace(**data))
        rlm = RLM(..., on_request=logger.on_request)
        await rlm.acompletion(..., on_iteration=logger.on_iteration)
    """

    def __init__(
        self,
        on_trace: Callable[[dict[str, Any]], None] | None = None,
        on_step: Callable[[dict[str, Any]], None] | None = None,
    ):
        self.on_trace = on_trace
        self.on_step = on_step

    def on_request(self, request: Any, response: Any):
        """Hook for LMHandler.on_request."""
        if self.on_step:
            metadata = request.metadata or {}
            self.on_step(
                {
                    "name": "rlm_sub_query",
                    "metadata": metadata,
                    "input": request.prompt,
                    "output": response.chat_completion.response
                    if response.success
                    else response.error,
                    "usage": response.chat_completion.usage_summary.to_dict()
                    if response.success
                    else {},
                }
            )

    async def on_iteration(self, iteration: Any, index: int):
        """Hook for RLM.on_iteration."""
        if self.on_step:
            # Iteration is RLMIteration object
            self.on_step(
                {
                    "name": f"rlm_iteration_{index}",
                    "input": iteration.prompt,
                    "output": iteration.response,
                    "final_answer": iteration.final_answer,
                    "iteration_time": iteration.iteration_time,
                }
            )
