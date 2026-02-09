from abc import ABC, abstractmethod
from typing import Any

from rlm.core.types import ModelUsageSummary, UsageSummary


class BaseLM(ABC):
    """
    Base class for all language model routers / clients. When the RLM makes sub-calls, it currently
    does so in a model-agnostic way, so this class provides a base interface for all language models.
    """

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs

    @abstractmethod
    def completion(self, prompt: str | dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_usage_summary(self) -> UsageSummary:
        """Get cost summary for all model calls."""
        raise NotImplementedError

    @abstractmethod
    def get_last_usage(self) -> ModelUsageSummary:
        """Get the last cost summary of the model."""
        raise NotImplementedError
