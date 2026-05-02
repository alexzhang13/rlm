from typing import Any, Literal

from rlm.environments.base_env import (
    RESERVED_TOOL_NAMES,
    BaseEnv,
    SupportsCustomTools,
    SupportsPersistence,
    ToolInfo,
    extract_tool_value,
    format_tools_for_prompt,
    parse_custom_tools,
    parse_tool_entry,
    validate_custom_tools,
)
from rlm.environments.local_repl import LocalREPL


def __getattr__(name: str) -> Any:
    # Lazy-load environments with optional dependencies so that the package
    # imports cleanly even when those extras aren't installed.
    if name == "IPythonREPL":
        from rlm.environments.ipython_repl import IPythonREPL

        return IPythonREPL
    if name == "InstaVMREPL":
        from rlm.environments.instavm_repl import InstaVMREPL

        return InstaVMREPL
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseEnv",
    "IPythonREPL",
    "InstaVMREPL",
    "LocalREPL",
    "RESERVED_TOOL_NAMES",
    "SupportsCustomTools",
    "SupportsPersistence",
    "ToolInfo",
    "extract_tool_value",
    "format_tools_for_prompt",
    "get_environment",
    "parse_custom_tools",
    "parse_tool_entry",
    "validate_custom_tools",
]


def get_environment(
    environment: Literal[
        "local", "ipython", "modal", "docker", "daytona", "prime", "e2b", "instavm"
    ],
    environment_kwargs: dict[str, Any],
) -> BaseEnv:
    """
    Routes a specific environment and the args (as a dict) to the appropriate environment if supported.
    Currently supported environments: ['local', 'ipython', 'modal', 'docker', 'daytona', 'prime', 'e2b', 'instavm']
    """
    if environment == "local":
        return LocalREPL(**environment_kwargs)
    elif environment == "ipython":
        from rlm.environments.ipython_repl import IPythonREPL

        return IPythonREPL(**environment_kwargs)
    elif environment == "modal":
        from rlm.environments.modal_repl import ModalREPL

        return ModalREPL(**environment_kwargs)
    elif environment == "docker":
        from rlm.environments.docker_repl import DockerREPL

        return DockerREPL(**environment_kwargs)
    elif environment == "daytona":
        from rlm.environments.daytona_repl import DaytonaREPL

        return DaytonaREPL(**environment_kwargs)
    elif environment == "prime":
        from rlm.environments.prime_repl import PrimeREPL

        return PrimeREPL(**environment_kwargs)
    elif environment == "e2b":
        from rlm.environments.e2b_repl import E2BREPL

        return E2BREPL(**environment_kwargs)
    elif environment == "instavm":
        from rlm.environments.instavm_repl import InstaVMREPL

        return InstaVMREPL(**environment_kwargs)
    else:
        raise ValueError(
            f"Unknown environment: {environment}. Supported: ['local', 'ipython', 'modal', 'docker', 'daytona', 'prime', 'e2b', 'instavm']"
        )
