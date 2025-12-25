from typing import Dict, Any, Literal

from rlm.environments.base_env import BaseEnv
from rlm.environments.local_repl import LocalREPL


def get_environment(
    environment: Literal["local"],
    environment_kwargs: Dict[str, Any],
) -> BaseEnv:
    """
    Routes a specific environment and the args (as a dict) to the appropriate environment if supported.
    Currently supported environments: ['local']
    """
    if environment == "local":
        return LocalREPL(**environment_kwargs)
    else:
        raise ValueError(
            f"Unknown environment: {environment}. Supported environments: ['local']"
        )
