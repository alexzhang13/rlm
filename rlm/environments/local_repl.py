import io
import json
import os
import platform
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
from rlm.utils.code_safety import DANGEROUS_MODULES, check_code_safety

# =============================================================================
# Execution Timeout Error
# =============================================================================


class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the timeout limit."""

    pass


# =============================================================================
# Security Helpers
# =============================================================================


def _create_safe_import(blocked_modules: frozenset[str]):
    """Create a restricted import function that blocks dangerous modules.

    Args:
        blocked_modules: Set of module names to block.

    Returns:
        A wrapped __import__ function that raises ImportError for blocked modules.
    """

    def _safe_import(
        name: str,
        globals_: dict | None = None,
        locals_: dict | None = None,
        fromlist: tuple = (),
        level: int = 0,
    ):
        # Check the root module name
        root_module = name.split(".")[0]
        if root_module in blocked_modules:
            raise ImportError(f"Import of '{name}' is blocked for security reasons")

        # Also check fromlist entries if importing submodules
        if fromlist:
            for item in fromlist:
                if item in blocked_modules:
                    raise ImportError(f"Import of '{item}' is blocked for security reasons")

        return __import__(name, globals_, locals_, fromlist, level)

    return _safe_import


def _create_safe_open(allowed_base_path: str):
    """Create a restricted open function that only allows file access within a directory.

    Args:
        allowed_base_path: The base directory path within which file access is allowed.

    Returns:
        A wrapped open function that raises PermissionError for paths outside base.
    """

    def _safe_open(file, mode: str = "r", *args, **kwargs):
        # Resolve the absolute path
        if isinstance(file, (str, bytes)):
            file_str = file.decode() if isinstance(file, bytes) else file
            abs_path = os.path.abspath(file_str)
            base_path = os.path.abspath(allowed_base_path)

            # Ensure the path is within the allowed base path
            # Use os.path.commonpath to prevent path traversal attacks
            try:
                common = os.path.commonpath([abs_path, base_path])
                if common != base_path:
                    raise PermissionError(
                        f"File access denied: path '{file_str}' is outside allowed directory"
                    )
            except ValueError as e:
                # Different drives on Windows
                raise PermissionError(
                    f"File access denied: path '{file_str}' is outside allowed directory"
                ) from e

        return open(file, mode, *args, **kwargs)

    return _safe_open


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

    Security features:
        - Blocked dangerous imports via _safe_import
        - File access restricted to temp_dir via _safe_open
        - Configurable execution timeout (default 30s)
        - Memory limits on Linux/Mac via resource.setrlimit()
    """

    DEFAULT_TIMEOUT: int = 30
    DEFAULT_MEMORY_LIMIT_MB: int = 512

    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        execution_timeout: int | None = None,
        memory_limit_mb: int | None = None,
        **kwargs,
    ):
        """Initialize LocalREPL with security controls.

        Args:
            lm_handler_address: Optional (host, port) tuple for LM handler.
            context_payload: Optional context to load into environment.
            setup_code: Optional code to run during setup.
            execution_timeout: Timeout in seconds for code execution (default 30s).
                Set to None or 0 to disable timeout.
            memory_limit_mb: Memory limit in MB for code execution (default 512MB).
                Only enforced on Linux/Mac. Set to None or 0 to disable.
        """
        super().__init__(**kwargs)

        self.lm_handler_address = lm_handler_address
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix=f"repl_env_{uuid.uuid4()}_")
        self._lock = threading.Lock()

        # Security configuration
        self.execution_timeout = (
            execution_timeout if execution_timeout is not None else self.DEFAULT_TIMEOUT
        )
        self.memory_limit_mb = (
            memory_limit_mb if memory_limit_mb is not None else self.DEFAULT_MEMORY_LIMIT_MB
        )

        # Setup globals, locals, and modules in environment.
        self.setup()

        # Load context if provided
        if context_payload is not None:
            self.load_context(context_payload)

        # Run setup code if provided
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Setup the environment with security-hardened builtins."""
        # Create safe versions of import and open
        safe_import = _create_safe_import(DANGEROUS_MODULES)
        safe_open = _create_safe_open(self.temp_dir)

        # Create hardened builtins with safe import/open
        safe_builtins = _SAFE_BUILTINS.copy()
        safe_builtins["__import__"] = safe_import
        safe_builtins["open"] = safe_open

        # Create sandboxed globals
        self.globals: dict[str, Any] = {
            "__builtins__": safe_builtins,
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

    def _llm_query(self, prompt: str, model: str | None = None) -> str:
        """Query the LM via socket connection to the handler.

        Args:
            prompt: The prompt to send to the LM.
            model: Optional model name to use (if handler has multiple clients).
        """
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            request = LMRequest(prompt=prompt, model=model)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            # Track this LLM call
            self._pending_llm_calls.append(
                response.chat_completion,
            )

            return response.chat_completion.response
        except Exception as e:
            return f"Error: LM query failed - {e}"

    def _llm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Query the LM with multiple prompts concurrently.

        Args:
            prompts: List of prompts to send to the LM.
            model: Optional model name to use (if handler has multiple clients).

        Returns:
            List of responses in the same order as input prompts.
        """
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)

        try:
            responses = send_lm_request_batched(self.lm_handler_address, prompts, model=model)

            results = []
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                else:
                    # Track this LLM call in list of all calls -- we may want to do this hierarchically
                    self._pending_llm_calls.append(response.chat_completion)
                    results.append(response.chat_completion.response)

            return results
        except Exception as e:
            return [f"Error: LM query failed - {e}"] * len(prompts)

    def load_context(self, context_payload: dict | list | str):
        """Load context into the environment."""
        if isinstance(context_payload, str):
            context_path = os.path.join(self.temp_dir, "context.txt")
            with open(context_path, "w") as f:
                f.write(context_payload)
            self.execute_code(f"with open(r'{context_path}', 'r') as f:\n    context = f.read()")
        else:
            context_path = os.path.join(self.temp_dir, "context.json")
            with open(context_path, "w") as f:
                json.dump(context_payload, f)
            self.execute_code(
                f"import json\nwith open(r'{context_path}', 'r') as f:\n    context = json.load(f)"
            )

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
        """Temporarily change to temp directory for execution."""
        old_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            yield
        finally:
            os.chdir(old_cwd)

    def _apply_memory_limit(self):
        """Apply memory limits using resource.setrlimit() on Linux/Mac."""
        if self.memory_limit_mb <= 0:
            return

        current_platform = platform.system()
        if current_platform in ("Linux", "Darwin"):
            try:
                import resource

                # Convert MB to bytes
                limit_bytes = self.memory_limit_mb * 1024 * 1024
                # Set soft and hard limits for address space
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            except (ImportError, ValueError, OSError):
                # resource module not available or limits not supported
                pass

    def _execute_with_timeout(
        self, code: str, combined: dict, stdout_buf: io.StringIO, stderr_buf: io.StringIO
    ) -> tuple[str, str, dict, Exception | None]:
        """Execute code with timeout using threading.

        Returns:
            Tuple of (stdout, stderr, updated_locals, exception_or_none)
        """
        result: dict[str, Any] = {
            "stdout": "",
            "stderr": "",
            "locals": {},
            "exception": None,
            "completed": False,
        }

        def run_code():
            try:
                # Apply memory limits (only affects this thread's children on some platforms)
                self._apply_memory_limit()

                exec(code, combined, combined)

                # Update locals with new variables
                new_locals = {}
                for key, value in combined.items():
                    if key not in self.globals and not key.startswith("_"):
                        new_locals[key] = value

                result["stdout"] = stdout_buf.getvalue()
                result["stderr"] = stderr_buf.getvalue()
                result["locals"] = new_locals
                result["completed"] = True
            except Exception as e:
                result["stdout"] = stdout_buf.getvalue()
                result["stderr"] = stderr_buf.getvalue() + f"\n{type(e).__name__}: {e}"
                result["exception"] = e
                result["completed"] = True

        exec_thread = threading.Thread(target=run_code, daemon=True)
        exec_thread.start()

        # Wait for timeout (0 means no timeout)
        timeout = self.execution_timeout if self.execution_timeout > 0 else None
        exec_thread.join(timeout=timeout)

        if exec_thread.is_alive():
            # Thread is still running - execution timed out
            # Note: We can't forcefully kill the thread in Python, but it's a daemon
            # so it will be cleaned up when the process exits
            return (
                stdout_buf.getvalue(),
                f"ExecutionTimeoutError: Code execution exceeded {self.execution_timeout}s timeout",
                {},
                ExecutionTimeoutError(f"Execution exceeded {self.execution_timeout}s"),
            )

        return (
            result["stdout"],
            result["stderr"],
            result["locals"],
            result["exception"],
        )

    def execute_code(self, code: str) -> REPLResult:
        """Execute code in the persistent namespace and return result.

        Security features:
            - Static analysis blocks dangerous patterns before execution
            - Restricted imports via _safe_import (blocks os, subprocess, etc.)
            - File access restricted to temp_dir via _safe_open
            - Execution timeout (configurable, default 30s)
            - Memory limits on Linux/Mac (configurable, default 512MB)
        """
        start_time = time.perf_counter()

        # Static analysis security check
        safety_result = check_code_safety(code)
        if not safety_result.is_safe:
            return REPLResult(
                stdout="",
                stderr=f"Security: {safety_result.reason}",
                locals=self.locals.copy(),
                execution_time=time.perf_counter() - start_time,
                rlm_calls=[],
            )

        # Clear pending LLM calls from previous execution
        self._pending_llm_calls = []

        with self._capture_output() as (stdout_buf, stderr_buf):
            with self._temp_cwd():
                combined = {**self.globals, **self.locals}

                # Execute with timeout
                stdout, stderr, new_locals, _ = self._execute_with_timeout(
                    code, combined, stdout_buf, stderr_buf
                )

                # Update locals with new variables (only if execution completed)
                for key, value in new_locals.items():
                    self.locals[key] = value

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
