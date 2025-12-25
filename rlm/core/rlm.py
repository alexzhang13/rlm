from rlm.clients import get_client
from rlm.environments import get_environment

from typing import Dict, Any, Literal, Optional


class RLM:
    """
    Recursive Language Model class that the user instantiates.
    """

    def __init__(
        self,
        backend: Literal["openai"] = "openai",
        backend_kwargs: Dict[str, Any] = {},
        environment: Literal["local", "prime", "modal"] = "local",
        environment_kwargs: Dict[str, Any] = {},
        max_depth: int = 1,
        custom_system_prompt: Optional[str] = None,
    ):
        self.client = get_client(backend, backend_kwargs)
        self.environment = get_environment(environment, **environment_kwargs)
        self.max_depth = max_depth

    def completion(self, prompt: str | Dict[str, Any]) -> str:
        return self.client.completion(prompt)
