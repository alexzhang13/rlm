"""
Docker REPL environment that runs Python code in a Docker container.

The container is fully isolated from the host LM process. An HTTP proxy on the
host bridges the gap so code running in the container can:

    - llm_query / llm_query_batched : single LM completions (no recursion)
    - rlm_query  / rlm_query_batched : recursive RLM sub-calls (spawns a child
                                       RLM on the host when max_depth > 1)
    - SHOW_VARS                      : list REPL variables
    - custom tools                  : user-supplied functions/data
    - answer                        : answer["ready"] = True signals completion

Setup:
    docker build -t rlm-sandbox -f Dockerfile.sandbox .

Or use any Python 3.11+ image with: pip install dill requests
"""

import base64
import copy
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import (
    NonIsolatedEnv,
    extract_tool_value,
    validate_custom_tools,
)


class LLMProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler for LLM/RLM requests from the container.

    Class attributes are overridden per-environment via a dynamically created
    subclass (see DockerREPL.setup). Each DockerREPL gets its own handler class
    bound to its own ``pending_calls`` list, lock, depth, and subcall callback.
    """

    lm_handler_address: tuple[str, int] | None = None
    pending_calls: list[RLMChatCompletion] = []
    lock: threading.Lock = threading.Lock()
    depth: int = 1
    # Callback for recursive RLM sub-calls. ``None`` means recursion is not
    # configured, so rlm_query falls back to a plain llm_query.
    subcall_fn: Callable[[str, str | None], RLMChatCompletion] | None = None
    max_concurrent_subcalls: int = 4

    def log_message(self, *args):
        pass

    def _resolve_address(self) -> tuple[str, int] | None:
        """Read the LM handler address dynamically.

        In persistent (multi-turn) mode each completion() spawns a new LMHandler
        on a new port, so the live address is stored on the server instance and
        updated via DockerREPL.update_handler_address. Fall back to the class
        attribute for the non-persistent case.
        """
        return getattr(self.server, "lm_handler_address", None) or self.lm_handler_address

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except Exception as e:
            self._respond(400, {"error": f"Bad request: {e}"})
            return

        try:
            if self.path == "/llm_query":
                result = self._handle_single(body)
            elif self.path == "/llm_query_batched":
                result = self._handle_batched(body)
            elif self.path == "/rlm_query":
                result = self._handle_rlm_single(body)
            elif self.path == "/rlm_query_batched":
                result = self._handle_rlm_batched(body)
            else:
                self._respond(404, {"error": "Not found"})
                return
        except Exception as e:
            # Never let a handler crash leave the container waiting on a dropped
            # connection; always return a structured error it can surface.
            self._respond(500, {"error": f"Proxy handler error: {e}"})
            return

        self._respond(200, result)

    def _respond(self, status: int, data: dict):
        try:
            payload = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionError, OSError):
            # Container-side request closed early (e.g. timeout). Nothing to do.
            pass

    # ------------------------------------------------------------------ #
    # Single-completion LM calls (no recursion)
    # ------------------------------------------------------------------ #
    def _handle_single(self, body: dict) -> dict:
        address = self._resolve_address()
        if not address:
            return {"error": "No LM handler configured"}

        request = LMRequest(prompt=body.get("prompt"), model=body.get("model"), depth=self.depth)
        response = send_lm_request(address, request)

        if not response.success:
            return {"error": response.error}

        with self.lock:
            self.pending_calls.append(response.chat_completion)

        return {"response": response.chat_completion.response}

    def _handle_batched(self, body: dict) -> dict:
        address = self._resolve_address()
        if not address:
            return {"error": "No LM handler configured"}

        prompts = body.get("prompts", [])
        responses = send_lm_request_batched(
            address, prompts, model=body.get("model"), depth=self.depth
        )

        results = []
        for resp in responses:
            if not resp.success:
                results.append(f"Error: {resp.error}")
            else:
                with self.lock:
                    self.pending_calls.append(resp.chat_completion)
                results.append(resp.chat_completion.response)

        return {"responses": results}

    # ------------------------------------------------------------------ #
    # Recursive RLM sub-calls (spawns child RLMs on the host)
    # ------------------------------------------------------------------ #
    def _handle_rlm_single(self, body: dict) -> dict:
        # No recursive capability configured -> behave like a plain llm_query.
        if self.subcall_fn is None:
            return self._handle_single(body)

        prompt = body.get("prompt")
        model = body.get("model")
        try:
            completion = self.subcall_fn(prompt, model)
        except Exception as e:
            return {"error": f"RLM query failed - {e}"}

        # Read .response before tracking so a malformed completion isn't recorded.
        result = {"response": completion.response}
        with self.lock:
            self.pending_calls.append(completion)
        return result

    def _handle_rlm_batched(self, body: dict) -> dict:
        if self.subcall_fn is None:
            return self._handle_batched(body)

        prompts = body.get("prompts", [])
        model = body.get("model")
        n = len(prompts)
        if n == 0:
            return {"responses": []}

        # Pre-allocate to preserve input order regardless of completion order.
        results: list[str] = [""] * n
        completions: list[tuple[int, RLMChatCompletion]] = []
        comp_lock = threading.Lock()

        def _run(index: int, prompt: str) -> None:
            try:
                completion = self.subcall_fn(prompt, model)
                with comp_lock:
                    completions.append((index, completion))
                results[index] = completion.response
            except Exception as e:
                results[index] = f"Error: RLM query failed - {e}"

        if n == 1:
            _run(0, prompts[0])
        else:
            max_workers = min(self.max_concurrent_subcalls, n)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_run, i, p) for i, p in enumerate(prompts)]
                for future in as_completed(futures):
                    future.result()

        # Record completions in prompt order for deterministic metadata.
        completions.sort(key=lambda x: x[0])
        with self.lock:
            for _, completion in completions:
                self.pending_calls.append(completion)

        return {"responses": results}


def _build_custom_tools_code(custom_tools: dict[str, Any] | None) -> str:
    """Build the in-container injection code for custom tools.

    Mirrors DaytonaREPL semantics for out-of-process environments:
        - String values that look like code (def/class/lambda/multiline) are
          executed directly to define a function/class.
        - Everything else is JSON-serialized and loaded as data.
    Arbitrary host callables cannot cross the process boundary and are skipped.
    """
    if not custom_tools:
        return ""

    lines: list[str] = []
    for name, entry in custom_tools.items():
        value = extract_tool_value(entry)

        if isinstance(value, str) and (
            value.strip().startswith("def ")
            or value.strip().startswith("class ")
            or value.strip().startswith("lambda")
            or "\n" in value
        ):
            lines.append(f"# Custom tool: {name}")
            lines.append(value)
            lines.append(f"_globals['{name}'] = {name}")
        elif callable(value):
            # Host callable - cannot be serialized into the container.
            lines.append(
                f"# Warning: custom tool '{name}' is a host callable and is not "
                f"available in the docker environment. Pass it as a code string instead."
            )
        else:
            try:
                json_value = json.dumps(value)
                lines.append(f"_locals['{name}'] = json.loads({json_value!r})")
            except (TypeError, ValueError):
                lines.append(f"# Warning: Could not serialize tool '{name}'")

    return "\n".join(lines)


def _build_exec_script(
    code: str,
    proxy_port: int,
    depth: int = 1,
    custom_tools: dict[str, Any] | None = None,
    compaction: bool = False,
) -> str:
    """Build the per-cell execution script that runs inside the container."""
    code_b64 = base64.b64encode(code.encode()).decode()
    custom_tools_code = _build_custom_tools_code(custom_tools)
    # In compaction mode the running summary list owns `history`; don't let the
    # versioned history_0 alias clobber it (the host re-injects it each turn).
    history_alias = (
        ""
        if compaction
        else 'if "history_0" in _locals:\n    _locals["history"] = _locals["history_0"]'
    )

    return textwrap.dedent(
        f'''
import sys, io, json, base64, traceback, os, requests
try:
    import dill
except ImportError:
    import pickle as dill

PROXY = "http://host.docker.internal:{proxy_port}"
STATE = "/workspace/state.dill"
DEPTH = {depth}

# Generous timeouts: plain LM calls can be slow; recursive RLM calls slower still.
_LLM_TIMEOUT = 600
_RLM_TIMEOUT = 3600

def _post(path, payload, timeout):
    r = requests.post(f"{{PROXY}}{{path}}", json=payload, timeout=timeout)
    return r.json()

def llm_query(prompt, model=None):
    try:
        d = _post("/llm_query", {{"prompt": prompt, "model": model, "depth": DEPTH}}, _LLM_TIMEOUT)
        return d.get("response") or f"Error: {{d.get('error')}}"
    except Exception as e:
        return f"Error: {{e}}"

def llm_query_batched(prompts, model=None):
    try:
        d = _post("/llm_query_batched", {{"prompts": prompts, "model": model, "depth": DEPTH}}, _LLM_TIMEOUT)
        return d.get("responses") or [f"Error: {{d.get('error')}}"] * len(prompts)
    except Exception as e:
        return [f"Error: {{e}}"] * len(prompts)

def rlm_query(prompt, model=None):
    try:
        d = _post("/rlm_query", {{"prompt": prompt, "model": model, "depth": DEPTH}}, _RLM_TIMEOUT)
        return d.get("response") or f"Error: {{d.get('error')}}"
    except Exception as e:
        return f"Error: {{e}}"

def rlm_query_batched(prompts, model=None):
    try:
        d = _post("/rlm_query_batched", {{"prompts": prompts, "model": model, "depth": DEPTH}}, _RLM_TIMEOUT)
        return d.get("responses") or [f"Error: {{d.get('error')}}"] * len(prompts)
    except Exception as e:
        return [f"Error: {{e}}"] * len(prompts)

def load_state():
    if os.path.exists(STATE):
        try:
            with open(STATE, "rb") as f:
                return dill.load(f)
        except Exception:
            pass
    return {{}}

def save_state(s):
    clean = {{}}
    for k, v in s.items():
        if k.startswith("_"):
            continue
        try:
            dill.dumps(v)
            clean[k] = v
        except Exception:
            pass
    with open(STATE, "wb") as f:
        dill.dump(clean, f)

_locals = load_state()

# Default answer dict on the first invocation; preserved across calls via state.
if "answer" not in _locals or not isinstance(_locals.get("answer"), dict):
    _locals["answer"] = {{"content": "", "ready": False}}

def SHOW_VARS():
    available = {{k: type(v).__name__ for k, v in _locals.items() if not k.startswith("_") and k != "answer"}}
    if not available:
        return "No variables created yet. Use ```repl``` blocks to create variables."
    return f"Available variables: {{available}}"

_globals = {{
    "__builtins__": __builtins__,
    "__name__": "__main__",
    "llm_query": llm_query,
    "llm_query_batched": llm_query_batched,
    "rlm_query": rlm_query,
    "rlm_query_batched": rlm_query_batched,
    "SHOW_VARS": SHOW_VARS,
}}

# --- Custom tools injection ---
{custom_tools_code}
# --- End custom tools ---

code = base64.b64decode("{code_b64}").decode()
stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
old_stdout, old_stderr = sys.stdout, sys.stderr

try:
    sys.stdout, sys.stderr = stdout_buf, stderr_buf
    combined = {{**_globals, **_locals}}
    exec(code, combined, combined)
    for k, v in combined.items():
        if k not in _globals and not k.startswith("_"):
            _locals[k] = v
except Exception:
    # combined is mutated in place by exec, so variables assigned before the
    # exception are present -- salvage them instead of discarding paid-for
    # work (e.g. sub-call results from a loop that raised late).
    for k, v in combined.items():
        if k not in _globals and not k.startswith("_"):
            _locals[k] = v
    traceback.print_exc(file=stderr_buf)
    print("\\n(variables assigned before the error were preserved)", file=stderr_buf)
finally:
    sys.stdout, sys.stderr = old_stdout, old_stderr

# Restore scaffold aliases if overwritten by executed code
if "context_0" in _locals:
    _locals["context"] = _locals["context_0"]
{history_alias}

save_state(_locals)
_ans = _locals.get("answer") if isinstance(_locals.get("answer"), dict) else None
_final = None
if _ans is not None and _ans.get("ready"):
    _final = str(_ans.get("content", ""))
print(json.dumps({{
    "stdout": stdout_buf.getvalue(),
    "stderr": stderr_buf.getvalue(),
    "locals": {{k: repr(v) for k, v in _locals.items() if not k.startswith("_")}},
    "final_answer": _final,
}}, ensure_ascii=False))
'''
    )


class DockerREPL(NonIsolatedEnv):
    """
    Docker REPL - runs Python in a Docker container with LLM and recursive RLM support.

    Requires: Docker with a Python 3.11+ image (default: python:3.11-slim).

    Supports:
        - llm_query / llm_query_batched : single LM completions
        - rlm_query  / rlm_query_batched : recursive RLM sub-calls (needs subcall_fn)
        - custom_tools / custom_sub_tools : injected functions/data
        - answer["ready"] = True : final-answer signaling
        - persistent multi-turn sessions : versioned context_N / history_N reuse
          across completion() calls (the container and its dill state are kept
          alive for the lifetime of the env)
        - compaction : auto-summarized running `history` when context fills up
    """

    def __init__(
        self,
        image: str = "python:3.11-slim",
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        subcall_fn: Callable[[str, str | None], RLMChatCompletion] | None = None,
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

        self.image = image
        self.lm_handler_address = lm_handler_address
        self.subcall_fn = subcall_fn
        self.compaction = compaction
        self.container_id: str | None = None
        self.proxy_server: ThreadingHTTPServer | None = None
        self.proxy_thread: threading.Thread | None = None
        self.proxy_port: int = 0
        self._cleaned_up = False

        # Multi-turn persistence bookkeeping (context_N / history_N versioning).
        self._context_count: int = 0
        self._history_count: int = 0
        # Compaction keeps the canonical running history host-side and re-injects
        # it into the container as `history` on each update (see local_repl.py).
        self._compaction_history: list[Any] = []

        # Custom tools: functions/data available in the REPL.
        self.custom_tools = custom_tools or {}
        # Sub-tools inherit from custom_tools unless explicitly provided.
        self.custom_sub_tools = (
            custom_sub_tools if custom_sub_tools is not None else self.custom_tools
        )
        validate_custom_tools(self.custom_tools)

        base_dir = os.environ.get(
            "RLM_DOCKER_WORKSPACE_DIR", os.path.join(os.getcwd(), ".rlm_workspace")
        )
        os.makedirs(base_dir, exist_ok=True)
        self.temp_dir = tempfile.mkdtemp(prefix="docker_repl_", dir=base_dir)
        self.pending_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        self.setup()

        # In compaction mode the model reads the accumulated trajectory via the
        # `history` REPL variable; seed it as an empty list up front.
        if self.compaction:
            self._inject_history(self._compaction_history)

        if context_payload is not None:
            self.load_context(context_payload)
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Start the proxy server and Docker container."""
        # Start LLM/RLM proxy server (multi-threaded so concurrent sub-calls
        # don't serialize or deadlock behind a single in-flight handler).
        handler = type(
            "Handler",
            (LLMProxyHandler,),
            {
                "lm_handler_address": self.lm_handler_address,
                "pending_calls": self.pending_calls,
                "lock": self._calls_lock,
                "depth": self.depth,
                "subcall_fn": staticmethod(self.subcall_fn) if self.subcall_fn else None,
                "max_concurrent_subcalls": self.max_concurrent_subcalls,
            },
        )
        # Bind on all interfaces so the container can reach the proxy via
        # host.docker.internal. On macOS/Docker Desktop loopback works, but on
        # native Linux host.docker.internal resolves to the bridge gateway IP
        # (e.g. 172.17.0.1), which cannot reach a server bound to 127.0.0.1 -
        # the connection is refused. The port is an ephemeral, short-lived one
        # serving only LM/RLM proxy calls for this env's container.
        self.proxy_server = ThreadingHTTPServer(("0.0.0.0", 0), handler)
        self.proxy_server.daemon_threads = True
        # Store the address on the server so handlers read it live; this is what
        # makes update_handler_address work across persistent multi-turn calls.
        self.proxy_server.lm_handler_address = self.lm_handler_address
        self.proxy_port = self.proxy_server.server_address[1]
        self.proxy_thread = threading.Thread(target=self.proxy_server.serve_forever, daemon=True)
        self.proxy_thread.start()

        # Start Docker container
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "-v",
                f"{self.temp_dir}:/workspace",
                "--add-host",
                "host.docker.internal:host-gateway",
                self.image,
                "tail",
                "-f",
                "/dev/null",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.cleanup()
            raise RuntimeError(f"Failed to start container: {result.stderr}")

        self.container_id = result.stdout.strip()

        # Install dependencies. dill is optional (falls back to pickle), but
        # requests is required for llm_query/rlm_query, so verify it imports.
        subprocess.run(
            ["docker", "exec", self.container_id, "pip", "install", "-q", "dill", "requests"],
            capture_output=True,
        )
        check = subprocess.run(
            ["docker", "exec", self.container_id, "python", "-c", "import requests"],
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            self.cleanup()
            raise RuntimeError(
                "Failed to install 'requests' in the docker image; llm_query/rlm_query "
                f"would not work. Use an image with requests preinstalled. Error: {check.stderr}"
            )

    def load_context(self, context_payload: dict | list | str):
        """Load context as ``context_0`` (with ``context`` aliased to it)."""
        self.add_context(context_payload, 0)

    # ------------------------------------------------------------------ #
    # Persistence protocol (SupportsPersistence) - multi-turn sessions
    # ------------------------------------------------------------------ #
    def update_handler_address(self, address: tuple[str, int]) -> None:
        """Point the proxy at a new LM handler (each completion() spawns one).

        This is the per-turn entry point in persistent mode, so it also resets
        the ``answer`` signal. Unlike the local env (which detects the
        False->True transition via a callback), the container reads
        ``answer["ready"]`` from persisted state at the end of each cell, so a
        stale ``ready=True`` from a previous turn would otherwise short-circuit
        the next turn immediately.
        """
        self.lm_handler_address = address
        if self.proxy_server is not None:
            self.proxy_server.lm_handler_address = address
        self.execute_code("answer = {'content': '', 'ready': False}")

    def add_context(
        self, context_payload: dict | list | str, context_index: int | None = None
    ) -> int:
        """Add a context as ``context_N`` (auto-incrementing unless given).

        ``context`` aliases ``context_0`` for backward compatibility, matching
        the versioning behavior of the local environment.
        """
        if context_index is None:
            context_index = self._context_count

        var_name = f"context_{context_index}"
        if isinstance(context_payload, str):
            fname = f"context_{context_index}.txt"
            with open(os.path.join(self.temp_dir, fname), "w") as f:
                f.write(context_payload)
            code = f"with open('/workspace/{fname}', 'r') as _f:\n    {var_name} = _f.read()"
        else:
            fname = f"context_{context_index}.json"
            with open(os.path.join(self.temp_dir, fname), "w") as f:
                json.dump(context_payload, f)
            code = (
                "import json\n"
                f"with open('/workspace/{fname}', 'r') as _f:\n"
                f"    {var_name} = json.load(_f)"
            )
        if context_index == 0:
            code += "\ncontext = context_0"
        self.execute_code(code)

        self._context_count = max(self._context_count, context_index + 1)
        return context_index

    def get_context_count(self) -> int:
        """Return the number of contexts loaded."""
        return self._context_count

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        """Store a conversation's message history as ``history_N`` in the REPL.

        The list is JSON round-tripped into the container, which also gives the
        deep-copy semantics required by the persistence protocol. ``history``
        aliases ``history_0`` (unless compaction owns ``history``).
        """
        if history_index is None:
            history_index = self._history_count

        var_name = f"history_{history_index}"
        fname = f"history_{history_index}.json"
        with open(os.path.join(self.temp_dir, fname), "w") as f:
            json.dump(message_history, f)
        code = (
            "import json\n"
            f"with open('/workspace/{fname}', 'r') as _f:\n"
            f"    {var_name} = json.load(_f)"
        )
        if history_index == 0 and not self.compaction:
            code += "\nhistory = history_0"
        self.execute_code(code)

        self._history_count = max(self._history_count, history_index + 1)
        return history_index

    def get_history_count(self) -> int:
        """Return the number of conversation histories stored."""
        return self._history_count

    # ------------------------------------------------------------------ #
    # Compaction - running, auto-summarized trajectory exposed as `history`
    # ------------------------------------------------------------------ #
    def _inject_history(self, history: list[Any]) -> None:
        """Refresh the container's ``history`` variable from a host-side list."""
        fname = "_compaction_history.json"
        with open(os.path.join(self.temp_dir, fname), "w") as f:
            json.dump(history, f)
        self.execute_code(
            f"import json\nwith open('/workspace/{fname}', 'r') as _f:\n    history = json.load(_f)"
        )

    def append_compaction_entry(self, entry: list[dict[str, Any]] | dict[str, Any]) -> None:
        """Append a trajectory segment or summary to the compaction history.

        The host keeps the canonical list and re-injects it into the container
        as ``history`` so model overwrites can't corrupt the accumulated state.
        """
        if not self.compaction:
            return
        self._compaction_history.append(copy.deepcopy(entry))
        self._inject_history(self._compaction_history)

    def execute_code(self, code: str) -> REPLResult:
        start = time.perf_counter()

        with self._calls_lock:
            self.pending_calls.clear()

        # Write the exec script into the mounted workspace and run it as a file.
        # This avoids ARG_MAX / shell-quoting limits from passing huge scripts
        # via `python -c`.
        script = _build_exec_script(
            code,
            self.proxy_port,
            self.depth,
            custom_tools=self.custom_tools,
            compaction=self.compaction,
        )
        script_path = os.path.join(self.temp_dir, "_exec.py")
        with open(script_path, "w") as f:
            f.write(script)

        result = subprocess.run(
            ["docker", "exec", self.container_id, "python", "/workspace/_exec.py"],
            capture_output=True,
            text=True,
        )

        with self._calls_lock:
            calls = self.pending_calls.copy()
            self.pending_calls.clear()

        try:
            lines = result.stdout.strip().split("\n")
            data = json.loads(lines[-1]) if lines and lines[-1] else {}
            return REPLResult(
                stdout=data.get("stdout", ""),
                stderr=data.get("stderr", "") + result.stderr,
                locals=data.get("locals", {}),
                execution_time=time.perf_counter() - start,
                rlm_calls=calls,
                final_answer=data.get("final_answer"),
            )
        except json.JSONDecodeError:
            return REPLResult(
                stdout=result.stdout,
                stderr=result.stderr or "Parse error",
                locals={},
                execution_time=time.perf_counter() - start,
                rlm_calls=calls,
            )

    def cleanup(self):
        """Tear down the container, proxy server, and workspace. Idempotent."""
        if getattr(self, "_cleaned_up", False):
            return
        self._cleaned_up = True

        # Force-remove the container (fast; --rm cleans the rest). Best-effort
        # removal of root-owned workspace files from inside the container first,
        # so the host rmtree below doesn't leave permission-denied garbage.
        if getattr(self, "container_id", None):
            subprocess.run(
                [
                    "docker",
                    "exec",
                    self.container_id,
                    "sh",
                    "-c",
                    "rm -rf /workspace/* /workspace/.[!.]* 2>/dev/null || true",
                ],
                capture_output=True,
            )
            subprocess.run(["docker", "rm", "-f", self.container_id], capture_output=True)
            self.container_id = None

        if getattr(self, "proxy_server", None):
            self.proxy_server.shutdown()
            self.proxy_server.server_close()
            self.proxy_server = None
        if getattr(self, "proxy_thread", None):
            self.proxy_thread.join(timeout=2)
            self.proxy_thread = None

        if getattr(self, "temp_dir", None) and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
