from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from rlm.core.types import ModelUsageSummary, UsageSummary

# Default timeout for LM API calls (in seconds)
DEFAULT_TIMEOUT: float = 300.0


class BaseLM(ABC):
    """
    Base class for all language model routers / clients. When the RLM makes sub-calls, it currently
    does so in a model-agnostic way, so this class provides a base interface for all language models.
    """

    # Streaming is an optional capability. Clients that implement a real
    # ``stream_completion`` set this to True; everything else inherits the
    # single-chunk fallback below and keeps working unchanged.
    supports_streaming: bool = False

    def __init__(
        self,
        model_name: str,
        timeout: float = DEFAULT_TIMEOUT,
        sampling_args: dict[str, Any] | None = None,
        **kwargs,
    ):
        self.model_name = model_name
        self.timeout = timeout
        # Sampling args forwarded to the underlying completion API
        # (e.g. temperature, top_p, max_tokens, seed). Forwarded by
        # subclasses as **self.sampling_args.
        self.sampling_args: dict[str, Any] = dict(sampling_args or {})
        self.kwargs = kwargs

    @abstractmethod
    def completion(self, prompt: str | dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        raise NotImplementedError

    def stream_completion(
        self, prompt: str | dict[str, Any], model: str | None = None
    ) -> Iterator[str]:
        """Yield the response incrementally as text deltas.

        Not abstract: the default implementation makes one blocking
        ``completion()`` call and yields the whole response as a single delta,
        so every client is usable through the streaming interface whether or
        not it can really stream. Concatenating the deltas always reproduces
        exactly what ``completion()`` would have returned.

        Clients that override this with a real stream must also set
        ``supports_streaming = True`` so callers that only benefit from
        incremental output (e.g. speculative tool calling) can detect it.
        """
        yield self.completion(prompt)

    @abstractmethod
    def get_usage_summary(self) -> UsageSummary:
        """Get cost summary for all model calls."""
        raise NotImplementedError

    @abstractmethod
    def get_last_usage(self) -> ModelUsageSummary:
        """Get the last cost summary of the model."""
        raise NotImplementedError
