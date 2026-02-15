from typing import Any

from dotenv import load_dotenv

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ClientBackend

load_dotenv()

__all__ = ["BaseLM", "OpenAIClient", "get_client"]


def get_client(
    backend: ClientBackend,
    backend_kwargs: dict[str, Any],
) -> BaseLM:
    """
    Routes a specific backend and the args (as a dict) to the appropriate client if supported.
    Currently supported backends: ['openai']
    """
    if backend == "openai":
        from rlm.clients.openai import OpenAIClient

        return OpenAIClient(**backend_kwargs)
    raise ValueError("Unknown backend: openai is the only supported backend")
