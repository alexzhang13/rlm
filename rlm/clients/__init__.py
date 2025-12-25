from typing import Dict, Any, Literal

from rlm.clients.base_lm import BaseLM
from rlm.clients.openai import OpenAIClient


def get_client(
    backend: Literal["openai"],
    backend_kwargs: Dict[str, Any],
) -> BaseLM:
    """
    Routes a specific backend and the args (as a dict) to the appropriate client if supported.
    Currently supported backends: ['openai']
    """
    if backend == "openai":
        return OpenAIClient(**backend_kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}. Supported backends: ['openai']")
