from abc import ABC, abstractmethod
from typing import Any

from rlm.core.types import ModelUsageSummary, UsageSummary
from rlm.utils.token_utils import validate_prompt_fits_context_window

# Default timeout for LM API calls (in seconds)
DEFAULT_TIMEOUT: float = 300.0


class BaseLM(ABC):
    """
    Base class for all language model routers / clients. When the RLM makes sub-calls, it currently
    does so in a model-agnostic way, so this class provides a base interface for all language models.
    """

    def __init__(self, model_name: str, timeout: float = DEFAULT_TIMEOUT, **kwargs):
        self.model_name = model_name
        self.timeout = timeout
        self.kwargs = kwargs

    def validate_prompt_context_window(
        self, prompt: str | list[dict[str, Any]], model_name: str
    ) -> None:
        """Fail fast when a prompt is too large for the target model."""
        validate_prompt_fits_context_window(prompt, model_name)

    @abstractmethod
    def completion(self, prompt: str | list[dict[str, Any]]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def acompletion(self, prompt: str | list[dict[str, Any]]) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_usage_summary(self) -> UsageSummary:
        """Get cost summary for all model calls."""
        raise NotImplementedError

    @abstractmethod
    def get_last_usage(self) -> ModelUsageSummary:
        """Get the last cost summary of the model."""
        raise NotImplementedError
