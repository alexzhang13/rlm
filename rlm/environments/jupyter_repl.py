import contextlib
import copy
import os
import threading
import time
import traceback
from typing import Any

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv
from rlm.environments.local_repl import _SAFE_BUILTINS


class JupyterREPL(NonIsolatedEnv):
    """
    Notebook-friendly REPL environment with persistent Python namespace.
    Executes code in the notebook kernel and captures stdout/stderr safely.
    """

    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        context_scope: str = "completion",
        setup_code: str | None = None,
        workdir: str | None = None,
        allow_builtin_imports: bool = True,
        sync_to_user_ns: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        try:
            from IPython.utils.capture import capture_output
        except Exception as exc:
            raise ValueError("JupyterREPL requires IPython to be installed.") from exc

        if context_scope not in {"completion", "session"}:
            raise ValueError("context_scope must be 'completion' or 'session'")

        self.capture_output_func = capture_output
        self.lm_handler_address = lm_handler_address
        self.context_scope = context_scope
        self.workdir = workdir or os.getcwd()
        self.allow_builtin_imports = allow_builtin_imports
        self.sync_to_user_ns = sync_to_user_ns
        self.lock = threading.Lock()

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)

        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Setup the environment."""
        safe_builtins = _SAFE_BUILTINS.copy()
        if not self.allow_builtin_imports:
            safe_builtins.pop("__import__", None)

        self.globals: dict[str, Any] = {
            "__builtins__": safe_builtins,
            "__name__": "__main__",
        }
        self.locals: dict[str, Any] = {}
        self.session_context_count = 0
        self.session_history_count = 0

        self.pending_llm_calls: list[RLMChatCompletion] = []

        self.globals["FINAL_VAR"] = self.final_var
        self.globals["llm_query"] = self.llm_query
        self.globals["llm_query_batched"] = self.llm_query_batched

    def final_var(self, variable_name: str) -> str:
        """Return the value of a variable as a final answer."""
        variable_name = variable_name.strip().strip("\"'")
        if variable_name in self.locals:
            return str(self.locals[variable_name])
        return f"Error: Variable '{variable_name}' not found"

    def llm_query(self, prompt: str, model: str | None = None) -> str:
        """Query the LM via socket connection to the handler."""
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            request = LMRequest(prompt=prompt, model=model)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            self.pending_llm_calls.append(response.chat_completion)

            return response.chat_completion.response
        except Exception as exc:
            return f"Error: LM query failed - {exc}"

    def llm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Query the LM with multiple prompts concurrently."""
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)

        try:
            responses = send_lm_request_batched(self.lm_handler_address, prompts, model=model)

            results = []
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                else:
                    self.pending_llm_calls.append(response.chat_completion)
                    results.append(response.chat_completion.response)

            return results
        except Exception as exc:
            return [f"Error: LM query failed - {exc}"] * len(prompts)

    def load_context(self, context_payload: dict | list | str):
        """Load context into the environment based on the context scope."""
        if self.context_scope == "session":
            self.add_context(context_payload, 0)
        else:
            self.set_completion_context(context_payload)

    def add_context(
        self,
        context_payload: dict | list | str,
        context_index: int | None = None,
    ) -> int:
        if context_index is None:
            context_index = self.session_context_count

        var_name = f"session_context_{context_index}"
        self.locals[var_name] = copy.deepcopy(context_payload)

        self.session_context_count = max(self.session_context_count, context_index + 1)
        self.locals["context_history"] = [
            self.locals[f"session_context_{index}"]
            for index in range(self.session_context_count)
        ]
        self.sync_user_namespace()
        return context_index

    def get_context_count(self) -> int:
        return self.session_context_count

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        if history_index is not None and history_index != self.session_history_count:
            raise ValueError("history_index is not supported for session_history ordering")

        session_history = self.locals.setdefault("session_history", [])
        session_history.append(copy.deepcopy(message_history))
        self.session_history_count = len(session_history)
        self.sync_user_namespace()
        return self.session_history_count - 1

    def get_history_count(self) -> int:
        return self.session_history_count

    def set_completion_context(self, context_payload: dict | list | str) -> None:
        self.locals["completion_context"] = copy.deepcopy(context_payload)
        self.sync_user_namespace()

    def update_handler_address(self, address: tuple[str, int]) -> None:
        self.lm_handler_address = address

    @contextlib.contextmanager
    def capture_output(self):
        """Thread-safe context manager to capture stdout/stderr."""
        with self.lock:
            with self.capture_output_func() as captured:
                yield captured

    @contextlib.contextmanager
    def temp_cwd(self):
        """Temporarily change to workdir for execution."""
        if not self.workdir:
            yield
            return

        old_cwd = os.getcwd()
        try:
            os.chdir(self.workdir)
            yield
        finally:
            os.chdir(old_cwd)

    def execute_code(self, code: str) -> REPLResult:
        """Execute code in the persistent namespace and return result."""
        start_time = time.perf_counter()
        self.pending_llm_calls = []

        with self.capture_output() as captured:
            with self.temp_cwd():
                try:
                    combined = {**self.globals, **self.locals}
                    exec(code, combined, combined)

                    for key, value in combined.items():
                        if key not in self.globals and not key.startswith("_"):
                            self.locals[key] = value
                except Exception:
                    traceback.print_exc()

        self.sync_user_namespace()

        return REPLResult(
            stdout=captured.stdout,
            stderr=captured.stderr,
            locals=self.locals.copy(),
            execution_time=time.perf_counter() - start_time,
            rlm_calls=self.pending_llm_calls.copy(),
        )

    def sync_user_namespace(self) -> None:
        if not self.sync_to_user_ns:
            return
        try:
            from IPython import get_ipython
        except Exception:
            return

        ip = get_ipython()
        if ip is None:
            return

        for key, value in self.locals.items():
            if key.startswith("_") or key in self.globals:
                continue
            ip.user_ns[key] = value

    def cleanup(self):
        """Clean up state."""
        self.globals.clear()
        self.locals.clear()
        self.session_context_count = 0
        self.session_history_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
