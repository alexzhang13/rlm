import copy
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv

# Rate limit detection markers for error strings returned by the LM handler
_RATE_LIMIT_MARKERS = ("rate_limit", "rate limit", "ratelimit", "429", "[rate_limited]")

# Markers for error text that leaks into "successful" response content
_LEAKED_ERROR_MARKERS = (
    "[rate_limited]",
    "[llm_error]",
    "[generation_failed]",
    "error: request failed",
    "error: lm query failed",
)

# Maximum iterations for tool-calling loop (prevents infinite loops)
MAX_TOOL_ITERATIONS = 10


def _is_rate_limit_error(error_str: str) -> bool:
    """Check if an error string indicates a rate limit failure."""
    lower = error_str.lower()
    return any(marker in lower for marker in _RATE_LIMIT_MARKERS)


def _content_is_leaked_error(content: str) -> bool:
    """Check if response content contains error text that leaked through as 'successful'.

    Long responses (>5000 chars) are assumed to be real content.
    """
    if not content or len(content) > 5000:
        return False
    lower = content.lower()
    return any(marker in lower for marker in _LEAKED_ERROR_MARKERS)


# =============================================================================
# Safe Builtins
# =============================================================================

# Safe builtins - blocks dangerous operations like eval/exec/input
_SAFE_BUILTINS = {
    # Core types and functions
    "print": print,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "bool": bool,
    "type": type,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "reversed": reversed,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "any": any,
    "all": all,
    "pow": pow,
    "divmod": divmod,
    "chr": chr,
    "ord": ord,
    "hex": hex,
    "bin": bin,
    "oct": oct,
    "repr": repr,
    "ascii": ascii,
    "format": format,
    "hash": hash,
    "id": id,
    "iter": iter,
    "next": next,
    "slice": slice,
    "callable": callable,
    "hasattr": hasattr,
    "getattr": getattr,
    "setattr": setattr,
    "delattr": delattr,
    "dir": dir,
    "vars": vars,
    "bytes": bytes,
    "bytearray": bytearray,
    "memoryview": memoryview,
    "complex": complex,
    "object": object,
    "super": super,
    "property": property,
    "staticmethod": staticmethod,
    "classmethod": classmethod,
    "__import__": __import__,
    "open": open,
    # Exceptions
    "Exception": Exception,
    "BaseException": BaseException,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "AttributeError": AttributeError,
    "FileNotFoundError": FileNotFoundError,
    "OSError": OSError,
    "IOError": IOError,
    "RuntimeError": RuntimeError,
    "NameError": NameError,
    "ImportError": ImportError,
    "StopIteration": StopIteration,
    "AssertionError": AssertionError,
    "NotImplementedError": NotImplementedError,
    "ArithmeticError": ArithmeticError,
    "LookupError": LookupError,
    "Warning": Warning,
    # Blocked
    "input": None,
    "eval": None,
    "exec": None,
    "compile": None,
    "globals": None,
    "locals": None,
}


class LocalREPL(NonIsolatedEnv):
    """
    Local REPL environment with persistent Python namespace.
    Executes code in a sandboxed namespace with access to context data.
    """

    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        **kwargs,
    ):
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        self.lm_handler_address = lm_handler_address
        # Permanent per-instance working directory under a stable base path.
        # No os.chdir() — CWD is process-global and unsafe across threads.
        base_dir = os.path.join(tempfile.gettempdir(), "rlm_repl_envs")
        os.makedirs(base_dir, exist_ok=True)
        self.temp_dir = os.path.join(base_dir, str(uuid.uuid4()))
        os.makedirs(self.temp_dir, exist_ok=True)
        self._lock = threading.Lock()
        self._context_count: int = 0
        self._history_count: int = 0

        # Setup globals, locals, and modules in environment.
        self.setup()

        # Load context if provided
        if context_payload is not None:
            self.load_context(context_payload)

        # Run setup code if provided
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Setup the environment."""
        # Create sandboxed globals
        self.globals: dict[str, Any] = {
            "__builtins__": _SAFE_BUILTINS.copy(),
            "__name__": "__main__",
        }
        self.locals: dict[str, Any] = {}

        # Track LLM calls made during code execution
        self._pending_llm_calls: list[RLMChatCompletion] = []

        # Add helper functions
        self.globals["FINAL_VAR"] = self._final_var
        self.globals["llm_query"] = self._llm_query
        self.globals["llm_query_batched"] = self._llm_query_batched

    def _final_var(self, variable_name: str) -> str:
        """Return the value of a variable as a final answer."""
        variable_name = variable_name.strip().strip("\"'")
        if variable_name in self.locals:
            return str(self.locals[variable_name])
        return f"Error: Variable '{variable_name}' not found"

    def _llm_query(
        self,
        prompt: str | list[dict[str, Any]],
        model: str | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_handler: Any | None = None,
    ) -> str:
        """Query the LM via socket connection to the handler.

        Args:
            prompt: The prompt to send — string or list of message dicts.
            model: Optional model name to use.
            response_format: Optional OpenAI response_format dict for structured output.
            tools: Optional list of OpenAI function calling tool definitions.
            tool_handler: Required if tools provided. Called as handler(tool_name, arguments) -> str.

        Returns:
            String response from the model (after tool execution loop if tools used).
        """
        # Validation
        if tools is not None and tool_handler is None:
            raise ValueError("tool_handler is required when tools are provided")

        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        # If no tools, use simple path (backward compatible)
        if tools is None:
            return self._llm_query_simple(prompt, model, response_format)

        # Tool-calling loop
        messages = self._ensure_messages_format(prompt)

        for _iteration in range(MAX_TOOL_ITERATIONS):
            try:
                request = LMRequest(
                    prompt=messages,
                    model=model,
                    depth=self.depth,
                    response_format=response_format,
                    tools=tools,
                )
                response = send_lm_request(self.lm_handler_address, request)

                if not response.success:
                    return f"__LLM_ERROR__|socket_error|0|{response.error}"

                cc = response.chat_completion
                if cc.error:
                    return f"__LLM_ERROR__|{cc.error_type}|{cc.status_code or 0}|{cc.error}"

                content = cc.response

                # Check if response is a tool_calls dict (JSON string from handler)
                if content.startswith("{") and "tool_calls" in content:
                    tool_response = json.loads(content)
                    tool_calls = tool_response.get("tool_calls", [])

                    if not tool_calls:
                        # Model returned content (final response)
                        self._pending_llm_calls.append(cc)
                        return tool_response.get("content") or ""

                    # Append assistant message with tool_calls to conversation
                    messages.append(
                        {
                            "role": "assistant",
                            "content": tool_response.get("content"),
                            "tool_calls": [
                                {
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": json.dumps(tc["arguments"]),
                                    },
                                }
                                for tc in tool_calls
                            ],
                        }
                    )

                    # Execute each tool and append results
                    for tool_call in tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["arguments"]
                        tool_id = tool_call["id"]

                        # Execute tool handler
                        try:
                            tool_result = tool_handler(tool_name, tool_args)
                        except Exception as e:
                            tool_result = f"Error executing {tool_name}: {str(e)}"

                        # Append tool result message
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": tool_result,
                            }
                        )

                    # Continue loop to call model again with tool results

                else:
                    # Normal completion (no tool calls)
                    if _content_is_leaked_error(content):
                        return f"__LLM_ERROR__|leaked_error|0|LLM returned error content: {content[:200]}"

                    self._pending_llm_calls.append(cc)
                    return content

            except Exception as e:
                return f"__LLM_ERROR__|socket_error|0|LM query failed - {e}"

        # Max iterations reached
        return f"__LLM_ERROR__|tool_loop_error|0|Maximum tool iterations ({MAX_TOOL_ITERATIONS}) exceeded"

    def _ensure_messages_format(self, prompt: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert string prompt to messages format, or return as-is if already messages."""
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            return prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def _llm_query_simple(
        self,
        prompt: str | list[dict[str, Any]],
        model: str | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Simple query path without tools (original implementation)."""
        try:
            request = LMRequest(
                prompt=prompt,
                model=model,
                depth=self.depth,
                response_format=response_format,
            )
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"__LLM_ERROR__|socket_error|0|{response.error}"

            cc = response.chat_completion
            if cc.error:
                return f"__LLM_ERROR__|{cc.error_type}|{cc.status_code or 0}|{cc.error}"

            content = cc.response
            if _content_is_leaked_error(content):
                return f"__LLM_ERROR__|leaked_error|0|LLM returned error content: {content[:200]}"

            self._pending_llm_calls.append(cc)
            return content
        except Exception as e:
            return f"__LLM_ERROR__|socket_error|0|LM query failed - {e}"

    def _llm_query_batched(
        self,
        prompts: list[str | list[dict[str, Any]]],
        model: str | None = None,
        response_formats: list[dict | None] | None = None,
        tools: list[dict] | None = None,
        tool_handler: Any | None = None,
    ) -> list[str]:
        """Query the LM with multiple prompts concurrently.

        Args:
            prompts: List of prompts.
            model: Optional model name.
            response_formats: Optional per-prompt response_format dicts.
            tools: Optional tool definitions (shared across all prompts).
            tool_handler: Required if tools provided (shared handler).

        Returns:
            List of responses in same order as input prompts.
        """
        # Validation
        if tools is not None and tool_handler is None:
            raise ValueError("tool_handler is required when tools are provided")

        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)

        # If no tools, use simple batched path
        if tools is None:
            return self._llm_query_batched_simple(prompts, model, response_formats)

        # With tools: each prompt gets independent tool-calling loop
        results = []
        for i, prompt in enumerate(prompts):
            response_format = response_formats[i] if response_formats else None
            result = self._llm_query(prompt, model, response_format, tools, tool_handler)
            results.append(result)

        return results

    def _llm_query_batched_simple(
        self,
        prompts: list[str | list[dict[str, Any]]],
        model: str | None = None,
        response_formats: list[dict | None] | None = None,
    ) -> list[str]:
        """Simple batched query without tools (original implementation)."""
        try:
            responses = send_lm_request_batched(
                self.lm_handler_address,
                prompts,
                model=model,
                depth=self.depth,
                response_formats=response_formats,
            )

            results = []
            for response in responses:
                if not response.success:
                    results.append(f"__LLM_ERROR__|socket_error|0|{response.error}")
                else:
                    cc = response.chat_completion
                    if cc.error:
                        results.append(
                            f"__LLM_ERROR__|{cc.error_type}|{cc.status_code or 0}|{cc.error}"
                        )
                    else:
                        content = cc.response
                        if _content_is_leaked_error(content):
                            results.append("[GENERATION_FAILED]")
                        else:
                            self._pending_llm_calls.append(cc)
                            results.append(content)

            return results
        except Exception as e:
            return [f"__LLM_ERROR__|socket_error|0|LM query failed - {e}"] * len(prompts)

    def load_context(self, context_payload: dict | list | str):
        """Load context into the environment as context_0 (and 'context' alias)."""
        self.add_context(context_payload, 0)

    def add_context(
        self, context_payload: dict | list | str, context_index: int | None = None
    ) -> int:
        """
        Add a context with versioned variable name.

        Args:
            context_payload: The context data to add
            context_index: Optional explicit index. If None, auto-increments.

        Returns:
            The context index used.
        """
        if context_index is None:
            context_index = self._context_count

        var_name = f"context_{context_index}"

        if isinstance(context_payload, str):
            context_path = os.path.join(self.temp_dir, f"context_{context_index}.txt")
            with open(context_path, "w") as f:
                f.write(context_payload)
            self.execute_code(f"with open(r'{context_path}', 'r') as f:\n    {var_name} = f.read()")
        else:
            context_path = os.path.join(self.temp_dir, f"context_{context_index}.json")
            with open(context_path, "w") as f:
                json.dump(context_payload, f)
            self.execute_code(
                f"import json\nwith open(r'{context_path}', 'r') as f:\n    {var_name} = json.load(f)"
            )

        # Alias context_0 as 'context' for backward compatibility
        if context_index == 0:
            self.execute_code(f"context = {var_name}")

        self._context_count = max(self._context_count, context_index + 1)
        return context_index

    def update_handler_address(self, address: tuple[str, int]) -> None:
        """Update the LM handler address for a new completion call."""
        self.lm_handler_address = address

    def get_context_count(self) -> int:
        """Return the number of contexts loaded."""
        return self._context_count

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        """
        Store a conversation's message history as a versioned variable.

        Args:
            message_history: The list of message dicts from a completion call
            history_index: Optional explicit index. If None, auto-increments.

        Returns:
            The history index used.
        """
        if history_index is None:
            history_index = self._history_count

        var_name = f"history_{history_index}"

        # Store deep copy to avoid reference issues with nested dicts
        self.locals[var_name] = copy.deepcopy(message_history)

        # Alias history_0 as 'history' for convenience
        if history_index == 0:
            self.locals["history"] = self.locals[var_name]

        self._history_count = max(self._history_count, history_index + 1)
        return history_index

    def get_history_count(self) -> int:
        """Return the number of conversation histories stored."""
        return self._history_count

    @contextmanager
    def _capture_output(self):
        """Thread-safe context manager to capture stdout/stderr."""
        with self._lock:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
            try:
                sys.stdout, sys.stderr = stdout_buf, stderr_buf
                yield stdout_buf, stderr_buf
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

    @contextmanager
    def _temp_cwd(self):
        """No-op context manager. CWD is never changed.

        os.chdir() is process-global and fundamentally unsafe in multi-threaded
        code. All file operations use absolute paths via self.temp_dir instead.
        """
        yield

    def execute_code(self, code: str) -> REPLResult:
        """Execute code in the persistent namespace and return result."""
        start_time = time.perf_counter()

        # Clear pending LLM calls from previous execution
        self._pending_llm_calls = []

        with self._capture_output() as (stdout_buf, stderr_buf), self._temp_cwd():
            try:
                combined = {**self.globals, **self.locals}
                exec(code, combined, combined)

                # Update locals with new variables
                for key, value in combined.items():
                    if key not in self.globals and not key.startswith("_"):
                        self.locals[key] = value

                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue()
            except Exception as e:
                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue() + f"\n{type(e).__name__}: {e}"

        return REPLResult(
            stdout=stdout,
            stderr=stderr,
            locals=self.locals.copy(),
            execution_time=time.perf_counter() - start_time,
            rlm_calls=self._pending_llm_calls.copy(),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def cleanup(self):
        """Clean up temp directory and reset state."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        self.globals.clear()
        self.locals.clear()

    def __del__(self):
        self.cleanup()
