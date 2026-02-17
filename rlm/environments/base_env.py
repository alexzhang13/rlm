from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from rlm.core.types import REPLResult

# =============================================================================
# Custom Tools Support
# =============================================================================

# Reserved names: cannot be overridden by custom tools, and are restored after each
# code execution to prevent namespace corruption (e.g. context = "...", llm_query = ...).
RESERVED_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "llm_query",
        "llm_query_batched",
        "rlm_query",
        "rlm_query_batched",
        "FINAL_VAR",
        "SHOW_VARS",
        "context",
        "history",
    }
)


@dataclass
class ToolInfo:
    """Parsed information about a custom tool."""

    name: str
    value: Any
    description: str | None = None

    @property
    def is_callable(self) -> bool:
        """Check if the tool value is callable."""
        return callable(self.value)


def parse_tool_entry(name: str, entry: Any) -> ToolInfo:
    """
    Parse a custom tool entry into its components.

    Supports two formats:
    1. Just the value: {"name": callable_or_value}
    2. Dict with description: {"name": {"tool": callable_or_value, "description": "..."}}

    Args:
        name: The tool name.
        entry: The tool entry (value or dict with "tool" and "description" keys).

    Returns:
        ToolInfo with parsed components.
    """
    if isinstance(entry, dict) and "tool" in entry:
        value = entry["tool"]
        description = entry.get("description")
        if description is not None and isinstance(description, str):
            return ToolInfo(name=name, value=value, description=description)
        return ToolInfo(name=name, value=value, description=None)
    # No description - treat as plain value
    return ToolInfo(name=name, value=entry, description=None)


def parse_custom_tools(custom_tools: dict[str, Any] | None) -> list[ToolInfo]:
    """
    Parse all custom tools into ToolInfo objects.

    Args:
        custom_tools: Dictionary of tool names to values or {"tool": ..., "description": ...} dicts.

    Returns:
        List of ToolInfo objects.
    """
    if custom_tools is None:
        return []
    return [parse_tool_entry(name, entry) for name, entry in custom_tools.items()]


def extract_tool_value(entry: Any) -> Any:
    """
    Extract the actual value from a tool entry.

    Args:
        entry: The tool entry (value or {"tool": ..., "description": ...} dict).

    Returns:
        The tool value (callable or data).
    """
    if isinstance(entry, dict) and "tool" in entry:
        return entry["tool"]
    return entry


def format_tools_for_prompt(custom_tools: dict[str, Any] | None) -> str | None:
    """
    Format custom tools for inclusion in the system prompt.

    Args:
        custom_tools: Dictionary of tool names to values or {"tool": ..., "description": ...} dicts.

    Returns:
        Formatted string describing available tools, or None if no tools.
    """
    if not custom_tools:
        return None

    tool_infos = parse_custom_tools(custom_tools)
    if not tool_infos:
        return None

    lines = []
    for tool in tool_infos:
        if tool.is_callable:
            if tool.description:
                lines.append(f"- `{tool.name}`: {tool.description}")
            else:
                lines.append(f"- `{tool.name}`: A custom function")
        else:
            if tool.description:
                lines.append(f"- `{tool.name}`: {tool.description}")
            else:
                type_name = type(tool.value).__name__
                lines.append(f"- `{tool.name}`: A custom {type_name} value")

    return "\n".join(lines)


def validate_custom_tools(custom_tools: dict[str, Any] | None) -> None:
    """
    Validate that custom tools don't override reserved REPL functions.

    Args:
        custom_tools: Dictionary of custom tool names to their implementations.

    Raises:
        ValueError: If any tool name conflicts with reserved names.
    """
    if custom_tools is None:
        return

    conflicts = set(custom_tools.keys()) & RESERVED_TOOL_NAMES
    if conflicts:
        raise ValueError(
            f"Custom tools cannot override reserved REPL functions: {sorted(conflicts)}. "
            f"Reserved names: {sorted(RESERVED_TOOL_NAMES)}"
        )


@runtime_checkable
class SupportsCustomTools(Protocol):
    """Protocol for environments that support custom tools.

    Custom tools allow users to inject their own functions and data into the
    REPL environment, making them available to code executed by the RLM.

    CHECKING SUPPORT:
        Use isinstance(env, SupportsCustomTools) to check if an environment
        supports custom tools.

    TOOL TYPES:
        - Callable values: Injected as functions the model can call
        - Non-callable values: Injected as data/variables

    TOOL FORMAT:
        Tools can be specified in two formats:
        1. Plain value: {"name": callable_or_value}
        2. With description: {"name": {"tool": callable_or_value, "description": "..."}}

    NOTE ON llm_query:
        llm_query() calls are single LM completions and do NOT have access to
        custom tools. Only the main RLM execution context has tool access.

    RESERVED NAMES:
        The following names cannot be used as custom tool names:
        - llm_query, llm_query_batched: Single LM completion functions (no tool access)
        - rlm_query, rlm_query_batched: Recursive RLM calls for deeper thinking subtasks
        - FINAL_VAR, SHOW_VARS: Built-in helper functions
        - context, history: The input context and conversation history variables

    EXAMPLE:
        custom_tools = {
            "fetch_data": my_fetch_function,  # Plain callable
            "API_KEY": "sk-...",              # Plain value
            "calculator": {                   # With description
                "tool": calc_function,
                "description": "Performs arithmetic calculations",
            },
        }
    """

    custom_tools: dict[str, Any]


class BaseEnv(ABC):
    """
    Base REPL-like environment that the RLM uses to interact with. The primary types are isolated and non-isolated,
    where isolated environments are on a separate machine from the LM.

    Custom Tools:
        Environments can accept `custom_tools` kwargs:
        - custom_tools: Dict[str, Any] - Functions/values available in the REPL.
          Callable values are added to globals, non-callable to locals.

        Note: llm_query() calls are single LM completions without tool access.

        Example:
            custom_tools = {
                "fetch_data": my_fetch_function,
                "API_KEY": "sk-...",  # Non-callable, added to locals
            }
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
        To add persistence to your environment, implement these 5 methods.
        See tests/test_local_repl_persistent.py for expected behavior.

    VERSIONING BEHAVIOR:
        Contexts and histories are versioned with numeric suffixes:
        - First context  -> context_0, context_1, context_2, ...
        - First history  -> history_0, history_1, history_2, ...

    ALIASING BEHAVIOR:
        The unversioned names always point to index 0:
        - context  -> context_0 (first context)
        - history  -> history_0 (first history)

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
        """Add a context payload, making it available as context_N in code.

        Versioning:
            - context_index=None: auto-increment (0, 1, 2, ...)
            - context_index=N: use specific index N

        Storage:
            Must store so executed code can access:
            - context_0, context_1, etc. (versioned)
            - context (alias to context_0)

        Args:
            context_payload: The context data (string, dict, or list).
            context_index: Optional specific index, or None to auto-increment.

        Returns:
            The index used (for auto-increment, returns the assigned index).
        """
        ...

    def get_context_count(self) -> int:
        """Return the number of contexts added so far.

        Used by RLM to inform the model how many contexts are available.
        """
        ...

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        """Add a message history, making it available as history_N in code.

        Versioning:
            - history_index=None: auto-increment (0, 1, 2, ...)
            - history_index=N: use specific index N

        Storage:
            Must store so executed code can access:
            - history_0, history_1, etc. (versioned)
            - history (alias to history_0)

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

        Used by RLM to inform the model how many conversation histories
        are available.
        """
        ...
