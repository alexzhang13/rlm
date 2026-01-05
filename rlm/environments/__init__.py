from typing import Any, Literal

from rlm.environments.base_env import BaseEnv
from rlm.environments.local_repl import LocalREPL


def get_environment(
    environment: Literal["local", "modal", "docker", "cloudflare"],
    environment_kwargs: dict[str, Any],
) -> BaseEnv:
    """
    Routes a specific environment and the args (as a dict) to the appropriate environment if supported.
    Currently supported environments: ['local', 'modal', 'docker', 'cloudflare']
    """
    if environment == "local":
        return LocalREPL(**environment_kwargs)
    elif environment == "modal":
        from rlm.environments.modal_repl import ModalREPL

        return ModalREPL(**environment_kwargs)
    elif environment == "docker":
        from rlm.environments.docker_repl import DockerREPL

        return DockerREPL(**environment_kwargs)
    elif environment == "cloudflare":
        from rlm.environments.cloudflare_repl import CloudflareREPL

        return CloudflareREPL(**environment_kwargs)
    else:
        raise ValueError(
            f"Unknown environment: {environment}. Supported: ['local', 'modal', 'docker', 'cloudflare']"
        )
