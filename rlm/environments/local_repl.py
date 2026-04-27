import copy
import io
import json
import multiprocessing as mp
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Any

import dill

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion, UsageSummary
from rlm.environments.base_env import (
    RESERVED_TOOL_NAMES,
    NonIsolatedEnv,
    extract_tool_value,
    validate_custom_tools,
)

# =============================================================================
# Global Subprocess Budget
# =============================================================================
# Bounds the number of concurrent subprocess sub-calls actively doing work
# across the entire Python process, at every depth. A worker holding a slot
# is one that's currently inside child.completion(). When a worker itself
# needs to spawn grandchildren (rlm_query_batched inside its REPL), it
# releases its slot before awaiting them and reacquires after — this keeps
# the cap enforceable without deadlocking on recursion.

_DEFAULT_MAX_SUBPROCESSES = 16
_global_subprocess_semaphore: Any = None

# Per-process flag: set True inside a subprocess worker so _rlm_query_batched_parallel
# knows to release/reacquire the slot when orchestrating grandchildren.
_IN_SUBPROCESS_WORKER: bool = False


def set_max_subprocesses(n: int) -> None:
    """Set the global cap on concurrent subprocess-based RLM sub-calls.

    Must be called before any subprocess-based sub-call runs. Not safe to
    change mid-run.
    """
    global _global_subprocess_semaphore
    _global_subprocess_semaphore = mp.get_context("spawn").BoundedSemaphore(n)


def _get_subprocess_semaphore():
    global _global_subprocess_semaphore
    if _global_subprocess_semaphore is None:
        _global_subprocess_semaphore = mp.get_context("spawn").BoundedSemaphore(
            _DEFAULT_MAX_SUBPROCESSES
        )
    return _global_subprocess_semaphore


def _init_subprocess_worker(semaphore) -> None:
    """ProcessPoolExecutor initializer: install the global semaphore in this worker.

    BoundedSemaphores can't be passed through submit() arguments under the
    spawn start method — only through initargs (or fork inheritance). We set
    the module-level _global_subprocess_semaphore here so workers and any
    grandchild pools they spawn can share the same kernel semaphore.
    """
    global _global_subprocess_semaphore
    _global_subprocess_semaphore = semaphore


def _subprocess_worker_entry(job_bytes: bytes) -> bytes:
    """Top-level entry for subprocess-based sub-calls.

    Unpacks a dill-pickled (kind, data, prompt) tuple and either constructs a
    child RLM and runs its completion, or makes a plain LM call at max-depth.
    Acquires the global semaphore (set by _init_subprocess_worker) while doing
    work and sets _IN_SUBPROCESS_WORKER so recursive rlm_query_batched inside
    this worker can release/reacquire the slot.
    """
    global _IN_SUBPROCESS_WORKER
    semaphore = _global_subprocess_semaphore
    kind, data, prompt = dill.loads(job_bytes)

    semaphore.acquire()
    _IN_SUBPROCESS_WORKER = True
    try:
        if kind == "rlm":
            from rlm.core.rlm import RLM

            child = RLM(**data)
            try:
                result = child.completion(prompt, root_prompt=None)
            finally:
                child.close()
            return dill.dumps(result)

        if kind == "plain_lm":
            from rlm.clients import get_client

            backend, backend_kwargs, root_model = data
            client = get_client(backend, backend_kwargs)
            start = time.perf_counter()
            try:
                response = client.completion(prompt)
                end = time.perf_counter()
                model_usage = client.get_last_usage()
                result = RLMChatCompletion(
                    root_model=root_model,
                    prompt=prompt,
                    response=response,
                    usage_summary=UsageSummary(model_usage_summaries={root_model: model_usage}),
                    execution_time=end - start,
                )
            except Exception as e:
                end = time.perf_counter()
                result = RLMChatCompletion(
                    root_model=root_model,
                    prompt=prompt,
                    response=f"Error: LM query failed at max depth - {e}",
                    usage_summary=UsageSummary(model_usage_summaries={}),
                    execution_time=end - start,
                )
            return dill.dumps(result)

        raise ValueError(f"Unknown subprocess job kind: {kind!r}")
    finally:
        _IN_SUBPROCESS_WORKER = False
        semaphore.release()


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
        subcall_fn: Callable[[str, str | None], RLMChatCompletion] | None = None,
        subcall_preamble_fn: Callable[..., tuple] | None = None,
        subcall_finalize_fn: Callable[..., None] | None = None,
        custom_tools: dict[str, Any] | None = None,
        custom_sub_tools: dict[str, Any] | None = None,
        compaction: bool = False,
        max_concurrent_subcalls: int = 4,
        **kwargs,
    ):
        super().__init__(
            persistent=persistent,
            depth=depth,
            max_concurrent_subcalls=max_concurrent_subcalls,
            **kwargs,
        )

        self.lm_handler_address = lm_handler_address
        self.subcall_fn = subcall_fn  # Callback for recursive RLM calls (depth > 1 support)
        self.subcall_preamble_fn = subcall_preamble_fn
        self.subcall_finalize_fn = subcall_finalize_fn
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix=f"repl_env_{uuid.uuid4()}_")
        self._lock = threading.Lock()
        self._context_count: int = 0
        self._history_count: int = 0
        self.compaction = compaction

        # Custom tools: functions available in the REPL
        self.custom_tools = custom_tools or {}
        # Sub-tools: inherited from custom_tools if not specified
        self.custom_sub_tools = (
            custom_sub_tools if custom_sub_tools is not None else self.custom_tools
        )

        # Validate custom tools don't override reserved names
        validate_custom_tools(self.custom_tools)

        # Setup globals, locals, and modules in environment.
        self.setup()

        if compaction:
            self._compaction_history: list[Any] = []
            self.locals["history"] = self._compaction_history

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
        # When FINAL_VAR is called inside a REPL block, we store the value here for the main loop
        self._last_final_answer: str | None = None

        # Add helper functions
        self.globals["FINAL_VAR"] = self._final_var
        self.globals["SHOW_VARS"] = self._show_vars
        self.globals["llm_query"] = self._llm_query
        self.globals["llm_query_batched"] = self._llm_query_batched
        self.globals["rlm_query"] = self._rlm_query
        self.globals["rlm_query_batched"] = self._rlm_query_batched

        # Add custom tools to globals
        # Tools can be either plain values or (value, description) tuples
        for name, entry in self.custom_tools.items():
            value = extract_tool_value(entry)
            if callable(value):
                self.globals[name] = value
            else:
                # For non-callable values (constants, data), add to locals
                self.locals[name] = value

    def _final_var(self, variable_name: str | Any) -> str:
        """Return the value of a variable as a final answer for the main model, or stringify a direct value."""
        if not isinstance(variable_name, str):
            answer = str(variable_name)
            self._last_final_answer = answer
            return answer
        variable_name = variable_name.strip().strip("\"'")
        if variable_name in self.locals:
            answer = str(self.locals[variable_name])
            self._last_final_answer = answer
            return answer

        # Provide helpful error message with available variables (do not set _last_final_answer)
        available = [k for k in self.locals.keys() if not k.startswith("_")]
        if available:
            return (
                f"Error: Variable '{variable_name}' not found. "
                f"Available variables: {available}. "
                f"You must create and assign a variable BEFORE calling FINAL_VAR on it."
            )
        return (
            f"Error: Variable '{variable_name}' not found. "
            f"No variables have been created yet. "
            f"You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."
        )

    def _show_vars(self) -> str:
        """Show all available variables in the REPL environment."""
        available = {k: type(v).__name__ for k, v in self.locals.items() if not k.startswith("_")}
        if not available:
            return "No variables created yet. Use ```repl``` blocks to create variables."
        return f"Available variables: {available}"

    def _llm_query(self, prompt: str, model: str | None = None) -> str:
        """Query the LM with a single plain completion (no REPL, no recursion).

        This always makes a direct LM call via the handler, regardless of depth.

        Args:
            prompt: The prompt to send to the LM.
            model: Optional model name to use (if handler has multiple clients).
        """
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            request = LMRequest(prompt=prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            self._pending_llm_calls.append(response.chat_completion)
            return response.chat_completion.response
        except Exception as e:
            return f"Error: LM query failed - {e}"

    def _llm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Query the LM with multiple prompts concurrently (no REPL, no recursion).

        This always makes direct LM calls via the handler, regardless of depth.

        Args:
            prompts: List of prompts to send to the LM.
            model: Optional model name to use (if handler has multiple clients).

        Returns:
            List of responses in the same order as input prompts.
        """
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)
        try:
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
            )

            results = []
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                else:
                    self._pending_llm_calls.append(response.chat_completion)
                    results.append(response.chat_completion.response)

            return results
        except Exception as e:
            return [f"Error: LM query failed - {e}"] * len(prompts)

    def _rlm_query(self, prompt: str, model: str | None = None) -> str:
        """Spawn a recursive RLM sub-call for deeper thinking on a subtask.

        When a subcall callback is available (max_depth > 1), this spawns a child
        RLM with its own REPL that can reason over the prompt iteratively.
        Falls back to a plain llm_query if no recursive capability is configured.

        Args:
            prompt: The prompt to send to the child RLM.
            model: Optional model name override for the child.
        """
        if self.subcall_fn is not None:
            try:
                completion = self.subcall_fn(prompt, model)
                self._pending_llm_calls.append(completion)
                return completion.response
            except Exception as e:
                return f"Error: RLM query failed - {e}"

        # Fall back to plain LM call if no recursive capability
        return self._llm_query(prompt, model)

    def _rlm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Spawn recursive RLM sub-calls for multiple prompts in parallel.

        Each prompt gets its own child RLM for deeper thinking. When multiple
        prompts are provided and max_concurrent_subcalls > 1, subcalls run
        concurrently using a thread pool. Results are returned in the same
        order as input prompts.

        Falls back to llm_query_batched if no recursive capability is configured.

        Args:
            prompts: List of prompts for child RLMs.
            model: Optional model name override for the children.

        Returns:
            List of responses in the same order as input prompts.
        """
        if self.subcall_fn is not None:
            if not prompts:
                return []

            # Parallel execution: multiple prompts + concurrency enabled
            if self.max_concurrent_subcalls > 1 and len(prompts) > 1:
                return self._rlm_query_batched_parallel(prompts, model)

            # Sequential execution (default): zero overhead, identical to previous behavior
            results = []
            for prompt in prompts:
                try:
                    completion = self.subcall_fn(prompt, model)
                    self._pending_llm_calls.append(completion)
                    results.append(completion.response)
                except Exception as e:
                    results.append(f"Error: RLM query failed - {e}")
            return results

        # Fall back to plain batched LM call if no recursive capability
        return self._llm_query_batched(prompts, model)

    def _rlm_query_batched_parallel(
        self, prompts: list[str], model: str | None = None
    ) -> list[str]:
        """
        Spawn recursive RLM sub-calls for multiple prompts in parallel subprocesses.

        Each sub-call runs in its own subprocess so it has its own cwd (via
        _temp_cwd) and file-system state without racing with siblings. Global
        concurrency is bounded by a module-level BoundedSemaphore; see
        set_max_subprocesses.
        """
        if self.subcall_preamble_fn is None or self.subcall_finalize_fn is None:
            # Missing wiring — fall back to sequential sub-calls via subcall_fn.
            # The subprocess path requires preamble/finalize callbacks that RLM
            # installs at completion-time.
            results = []
            for prompt in prompts:
                try:
                    completion = self.subcall_fn(prompt, model)
                    self._pending_llm_calls.append(completion)
                    results.append(completion.response)
                except Exception as e:
                    results.append(f"Error: RLM query failed - {e}")
            return results

        semaphore = _get_subprocess_semaphore()
        global _IN_SUBPROCESS_WORKER
        is_reentrant = _IN_SUBPROCESS_WORKER

        # If we're inside a subprocess worker, release our slot while orchestrating
        # grandchildren to prevent deadlock; reclaim on the way out.
        if is_reentrant:
            semaphore.release()

        try:
            # Plan each sub-call in the parent process (synchronous, cheap)
            preambles = [self.subcall_preamble_fn(prompt, model) for prompt in prompts]
            # preamble = (kind, data, start_time, next_depth, resolved_model)

            # Collect jobs that need a subprocess (rlm or plain_lm)
            pool_jobs: list[tuple[int, tuple]] = []
            for idx, preamble in enumerate(preambles):
                if preamble[0] != "short_circuit":
                    pool_jobs.append((idx, preamble))

            results_by_idx: dict[int, tuple[RLMChatCompletion, str | None]] = {}

            if pool_jobs:
                max_workers = min(self.max_concurrent_subcalls, len(pool_jobs))
                ctx = mp.get_context("spawn")
                with ProcessPoolExecutor(
                    max_workers=max_workers,
                    mp_context=ctx,
                    initializer=_init_subprocess_worker,
                    initargs=(semaphore,),
                ) as executor:
                    fut_to_idx: dict[Any, int] = {}
                    for idx, preamble in pool_jobs:
                        kind, data, _, _, resolved_model = preamble
                        prompt = prompts[idx]
                        job_bytes = dill.dumps((kind, data, prompt))
                        fut = executor.submit(_subprocess_worker_entry, job_bytes)
                        fut_to_idx[fut] = idx

                    for fut in as_completed(fut_to_idx):
                        idx = fut_to_idx[fut]
                        preamble = preambles[idx]
                        resolved_model = preamble[4]
                        try:
                            completion = dill.loads(fut.result())
                            error_msg = None
                        except Exception as e:
                            error_msg = f"Subprocess sub-call failed - {e}"
                            completion = RLMChatCompletion(
                                root_model=resolved_model,
                                prompt=prompts[idx],
                                response=f"Error: {error_msg}",
                                usage_summary=UsageSummary(model_usage_summaries={}),
                                execution_time=0.0,
                            )
                        results_by_idx[idx] = (completion, error_msg)

            # Build response list and fire finalize callbacks in prompt order
            responses: list[str | None] = [None] * len(prompts)
            ordered_completions: list[RLMChatCompletion] = []
            for idx, preamble in enumerate(preambles):
                kind, data, start_time, next_depth, resolved_model = preamble
                if kind == "short_circuit":
                    completion = data  # completion stored in slot 1 for short-circuit
                    error_msg = None
                    cost_already_tracked = True  # short-circuit completions carry no cost
                else:
                    completion, error_msg = results_by_idx[idx]
                    cost_already_tracked = False
                self.subcall_finalize_fn(
                    completion,
                    start_time,
                    next_depth,
                    resolved_model,
                    error_msg,
                    cost_already_tracked,
                )
                responses[idx] = completion.response
                ordered_completions.append(completion)

            for completion in ordered_completions:
                self._pending_llm_calls.append(completion)

            return responses  # type: ignore[return-value]
        finally:
            if is_reentrant:
                semaphore.acquire()

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

    def append_compaction_entry(self, entry: list[dict[str, Any]] | dict[str, Any]) -> None:
        """
        Append a trajectory segment or a summary to the compaction history.

        Entry is either a list of message dicts (trajectory segment) or
        a dict with "type": "summary" and "content": str.
        """
        if not self.compaction:
            return
        self._compaction_history.append(copy.deepcopy(entry))

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
        """chdir into temp_dir for the duration of exec().

        Safe because this process is single-threaded for its own execute_code:
        parallel RLM sub-calls run in subprocesses, not threads, so no other
        thread can race on os.chdir.
        """
        try:
            os.chdir(self.temp_dir)
            yield
        finally:
            try:
                os.chdir(self.original_cwd)
            except OSError:
                pass

    def _restore_scaffold(self) -> None:
        """Restore scaffold names after execution so overwrites (e.g. context = 'x') don't persist."""
        for name in RESERVED_TOOL_NAMES:
            if name == "llm_query":
                self.globals["llm_query"] = self._llm_query
            elif name == "llm_query_batched":
                self.globals["llm_query_batched"] = self._llm_query_batched
            elif name == "rlm_query":
                self.globals["rlm_query"] = self._rlm_query
            elif name == "rlm_query_batched":
                self.globals["rlm_query_batched"] = self._rlm_query_batched
            elif name == "FINAL_VAR":
                self.globals["FINAL_VAR"] = self._final_var
            elif name == "SHOW_VARS":
                self.globals["SHOW_VARS"] = self._show_vars
            elif name == "context" and "context_0" in self.locals:
                self.locals["context"] = self.locals["context_0"]
            elif name == "history" and "history_0" in self.locals and not self.compaction:
                self.locals["history"] = self.locals["history_0"]
            elif name == "history" and self.compaction:
                self.locals["history"] = self._compaction_history

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

                # Restore scaffold so model overwrites (context = ..., llm_query = ...) don't persist
                self._restore_scaffold()

                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue()
            except Exception as e:
                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue() + f"\n{type(e).__name__}: {e}"

        final_answer = self._last_final_answer
        self._last_final_answer = None

        return REPLResult(
            stdout=stdout,
            stderr=stderr,
            locals=self.locals.copy(),
            execution_time=time.perf_counter() - start_time,
            rlm_calls=self._pending_llm_calls.copy(),
            final_answer=final_answer,
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
        if hasattr(self, "globals"):
            self.globals.clear()
        if hasattr(self, "locals"):
            self.locals.clear()

    def __del__(self):
        self.cleanup()
