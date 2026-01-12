from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from rlm.core.types import REPLResult


class BaseEnv(ABC):
    """
    Base REPL-like environment that the RLM uses to interact with. The primary types are isolated and non-isolated,
    where isolated environments are on a separate machine from the LM.
    """

    def __init__(self, persistent: bool = False, depth: int = 1, **kwargs):
        self.persistent = persistent
        self.depth = depth
        self.kwargs = kwargs

    @abstractmethod
    def setup(self):
        raise NotImplementedError

    @abstractmethod
    def load_context(self, context_payload: dict | list | str):
        raise NotImplementedError

    @abstractmethod
    def execute_code(self, code: str) -> REPLResult:
        raise NotImplementedError


class IsolatedEnv(BaseEnv, ABC):
    """
    These environments (e.g. Prime Envs, Modal Envs) sit on a completely separate machine from the LM,
    guaranteeing complete isolation from the LM process.
    """

    def __init__(self, persistent: bool = False, **kwargs):
        super().__init__(persistent=persistent, **kwargs)

    @abstractmethod
    def setup(self):
        raise NotImplementedError

    @abstractmethod
    def load_context(self, context_payload: dict | list | str):
        raise NotImplementedError

    @abstractmethod
    def execute_code(self, code: str) -> REPLResult:
        raise NotImplementedError


class NonIsolatedEnv(BaseEnv, ABC):
    """
    These environments run on the same machine as the LM, and provide different levels of isolation
    depending on the choice of environment. The simplest, default is a local Python REPL that runs
    as a subprocess.
    """

    def __init__(self, persistent: bool = False, **kwargs):
        super().__init__(persistent=persistent, **kwargs)

    @abstractmethod
    def setup(self):
        raise NotImplementedError

    @abstractmethod
    def load_context(self, context_payload: dict | list | str):
        raise NotImplementedError

    @abstractmethod
    def execute_code(self, code: str) -> REPLResult:
        raise NotImplementedError


@runtime_checkable
class SupportsPersistence(Protocol):
    """Protocol for environments that support persistent multi-turn sessions.

    CHECKING SUPPORT:
        Use isinstance(env, SupportsPersistence) to check if an environment
        supports persistence capabilities.

    IMPLEMENTING THIS PROTOCOL:
        To add persistence to your environment, implement these 6 methods.
        See tests/test_local_repl_persistent.py for expected behavior.

    SESSION CONTEXT BEHAVIOR:
        Contexts are versioned with numeric suffixes:
        - session_context_0, session_context_1, session_context_2, ...
        - context_history: list of session contexts, overwritten each call

    SESSION HISTORY BEHAVIOR:
        Histories are stored as a list of per-call histories:
        - session_history: list[list[dict[str, Any]]]

    COMPLETION CONTEXT BEHAVIOR:
        Completion calls store a single prompt payload:
        - completion_context

    EXAMPLE IMPLEMENTATION:
        See rlm/environments/local_repl.py for a complete reference.

    TESTS:
        - Unit tests: tests/test_local_repl_persistent.py
        - Integration tests: tests/test_multi_turn_integration.py

        Run: uv run pytest tests/test_local_repl_persistent.py -v
    """

    def update_handler_address(self, address: tuple[str, int]) -> None:
        """Update the LM handler address for nested LLM calls.

        Called by RLM when the handler address changes between completions.
        Store the address so llm_query() calls from executed code can reach
        the LM handler.

        Args:
            address: (host, port) tuple for the LM handler server.
        """
        ...

    def add_context(
        self, context_payload: dict | list | str, context_index: int | None = None
    ) -> int:
        """Add a session context payload, making it available as session_context_N in code.

        Versioning:
            - context_index=None: auto-increment (0, 1, 2, ...)
            - context_index=N: use specific index N

        Storage:
            Must store so executed code can access:
            - session_context_0, session_context_1, etc. (versioned)
            - context_history (list of session contexts, overwritten each call)

        Args:
            context_payload: The context data (string, dict, or list).
            context_index: Optional specific index, or None to auto-increment.

        Returns:
            The index used (for auto-increment, returns the assigned index).
        """
        ...

    def get_context_count(self) -> int:
        """Return the number of session contexts added so far.

        Used by RLM to inform the model how many contexts are available.
        """
        ...

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        """Add a session message history to session_history.

        Storage:
            Must store so executed code can access:
            - session_history (list of per-call message histories)

        IMPORTANT: Store a deep copy, not a reference. The caller may
        modify the list after calling this method.

        Args:
            message_history: List of message dicts (role, content).
            history_index: Optional specific index, or None to auto-increment.

        Returns:
            The index used.
        """
        ...

    def get_history_count(self) -> int:
        """Return the number of histories added so far.

        Used by RLM to inform the model how many session histories
        are available.
        """
        ...

    def set_completion_context(self, context_payload: dict | list | str) -> None:
        """Set the completion_context variable for a completion call."""
        ...
