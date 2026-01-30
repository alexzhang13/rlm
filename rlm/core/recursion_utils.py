from typing import Any

from rlm.core.types import ClientBackend


def select_backend_for_depth(
    depth: int,
    backend: ClientBackend,
    backend_kwargs: dict[str, Any],
    other_backends: list[ClientBackend] | None,
    other_backend_kwargs: list[dict[str, Any]] | None,
) -> tuple[ClientBackend, dict[str, Any]]:
    if depth < 0:
        raise ValueError("depth must be >= 0")

    if depth == 0 or other_backends is None or other_backend_kwargs is None:
        return backend, backend_kwargs

    index = depth - 1
    if index >= len(other_backends) or index >= len(other_backend_kwargs):
        return backend, backend_kwargs

    return other_backends[index], other_backend_kwargs[index]
