"""
IPython REPL environment. Executes code inside a real IPython session.

Two kernel modes:

- ``kernel_mode="in_process"`` (default): Uses ``IPython.core.interactiveshell.
  InteractiveShell`` in the same Python process as RLM. Fast, zero-overhead
  subcalls via direct Python callables. Same timeout limitation as LocalREPL:
  Python cannot interrupt blocking user code from another thread.

- ``kernel_mode="subprocess"``: Uses ``jupyter_client.KernelManager`` to spawn
  an ``ipykernel`` subprocess. Supports hard per-cell timeouts via
  ``kc.execute_interactive(timeout=...)`` + ``km.interrupt_kernel()``. LLM
  and RLM subcalls route over a TCP broker using the existing 4-byte-prefix
  JSON protocol from ``rlm.core.comms_utils``.
"""

from __future__ import annotations

import copy
import io
import json
import os
import re
import shutil
import signal
import socketserver
import sys
import tempfile
import textwrap
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from typing import Any, Literal

from rlm.core.comms_utils import (
    LMRequest,
    send_lm_request,
    send_lm_request_batched,
    socket_recv,
    socket_send,
)
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import (
    RESERVED_TOOL_NAMES,
    NonIsolatedEnv,
    extract_tool_value,
    validate_custom_tools,
)

KernelMode = Literal["in_process", "subprocess"]

# IPython populates user_ns with these. We strip them before returning locals
# so REPLResult.locals stays clean and comparable to LocalREPL.
_IPYTHON_INTERNAL_NAMES: frozenset[str] = frozenset(
    {
        "In",
        "Out",
        "exit",
        "quit",
        "get_ipython",
        "open",
        "_oh",
        "_dh",
        "_ih",
        "_i",
        "_ii",
        "_iii",
        "_",
        "__",
        "___",
    }
)

# Matches the most common terminal escape forms emitted by IPython tracebacks:
# CSI (``ESC[…``), OSC (``ESC]…BEL`` or ``ESC]…ESC\``), and the 2-byte
# ``ESC <char>`` form. The previous CSI-only regex left OSC/ST sequences in
# place when the surrounding terminal supported them.
_ANSI_RE = re.compile(
    r"\x1b(?:"
    r"\[[0-9;?]*[ -/]*[@-~]"  # CSI
    r"|\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC, BEL- or ST-terminated
    r"|[@-Z\\-_]"  # 2-byte escape
    r")"
)


# =============================================================================
# Subcall broker (subprocess kernel mode)
# =============================================================================


class _SubcallBroker:
    """TCP broker that the subprocess kernel calls back into for rlm_query
    and FINAL_VAR results.

    Reuses the 4-byte-length-prefix JSON protocol from ``rlm.core.comms_utils``.

    Request types:
        {"type": "subcall", "prompt": str, "model": str | None}
        {"type": "subcall_batched", "prompts": [str], "model": str | None}
        {"type": "final_var", "value": str}

    Responses:
        subcall:          {"completion": RLMChatCompletion.to_dict()} | {"error": str}
        subcall_batched:  {"responses": [str]}                        | {"error": str}
        final_var:        {"ok": True}
    """

    def __init__(
        self,
        subcall_fn: Callable[[str, str | None], RLMChatCompletion] | None,
        max_concurrent: int = 4,
        host: str = "127.0.0.1",
        port: int = 0,
    ):
        self.subcall_fn = subcall_fn
        self.max_concurrent = max_concurrent
        self.host = host
        self._port = port
        self._server: socketserver.ThreadingTCPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        # Bounds total in-flight ``subcall_fn`` invocations across *all*
        # broker requests (single + batched), regardless of how many
        # connections the kernel opens. Per-request thread pools alone
        # only bound concurrency within a single batched request.
        self._subcall_semaphore = threading.Semaphore(max(1, max_concurrent))
        self._shutting_down = False
        self.completions: list[RLMChatCompletion] = []
        self.final_answer: str | None = None

    def start(self) -> tuple[str, int]:
        parent = self

        class _Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                try:
                    data = socket_recv(self.connection)
                    if not isinstance(data, dict):
                        socket_send(self.connection, {"error": "Request must be a JSON object"})
                        return
                    reply = parent._dispatch(data)
                    socket_send(self.connection, reply)
                except (BrokenPipeError, ConnectionError, ConnectionResetError, OSError):
                    pass
                except Exception as e:
                    try:
                        socket_send(self.connection, {"error": f"{type(e).__name__}: {e}"})
                    except Exception:
                        pass

        class _Server(socketserver.ThreadingTCPServer):
            daemon_threads = True
            allow_reuse_address = True

        self._server = _Server((self.host, self._port), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self.address

    def _run_subcall(self, prompt: str, model: str | None) -> RLMChatCompletion:
        """Invoke ``subcall_fn`` under the global concurrency semaphore.

        Without this gate, kernel-side code that fans out N concurrent
        ``rlm_query`` calls (or runs N independent ``rlm_query_batched``
        requests) would invoke ``subcall_fn`` N times in parallel, ignoring
        ``max_concurrent``.
        """
        assert self.subcall_fn is not None
        with self._subcall_semaphore:
            return self.subcall_fn(prompt, model)

    def _dispatch(self, data: dict[str, Any]) -> dict[str, Any]:
        req_type = data.get("type")

        # Reject new subcall work once cleanup has begun, so we don't kick
        # off API calls (which incur cost) for a kernel that's about to
        # die. ``final_var`` still goes through — it's cheap and we may
        # already have its accumulated answer to drain.
        if self._shutting_down and req_type in ("subcall", "subcall_batched"):
            return {"error": "Broker shutting down"}

        if req_type == "final_var":
            value = data.get("value")
            with self._lock:
                self.final_answer = str(value) if value is not None else None
            return {"ok": True}

        if req_type == "subcall":
            if self.subcall_fn is None:
                return {"error": "No subcall_fn configured; rlm_query unavailable"}
            try:
                completion = self._run_subcall(data.get("prompt", ""), data.get("model"))
                with self._lock:
                    self.completions.append(completion)
                return {"completion": completion.to_dict()}
            except Exception as e:
                return {"error": f"{type(e).__name__}: {e}"}

        if req_type == "subcall_batched":
            if self.subcall_fn is None:
                return {"error": "No subcall_fn configured; rlm_query_batched unavailable"}
            prompts = data.get("prompts") or []
            model = data.get("model")
            responses: list[str | None] = [None] * len(prompts)
            errors: list[str | None] = [None] * len(prompts)
            local_completions: list[tuple[int, RLMChatCompletion]] = []
            local_lock = threading.Lock()

            def _one(i: int, prompt: str) -> None:
                try:
                    # _run_subcall already gates on the global semaphore.
                    completion = self._run_subcall(prompt, model)
                    with local_lock:
                        local_completions.append((i, completion))
                    responses[i] = completion.response
                except Exception as e:
                    errors[i] = f"{type(e).__name__}: {e}"

            # Per-batch pool size is capped at ``max_concurrent`` for
            # symmetry, but the semaphore inside ``_run_subcall`` is what
            # actually bounds total in-flight subcalls across requests.
            max_workers = max(1, min(self.max_concurrent, len(prompts) or 1))
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = [ex.submit(_one, i, p) for i, p in enumerate(prompts)]
                for f in as_completed(futures):
                    f.result()

            with self._lock:
                for _, c in sorted(local_completions, key=lambda t: t[0]):
                    self.completions.append(c)

            return {
                "responses": [
                    (r if r is not None else f"Error: {e or 'Unknown error'}")
                    for r, e in zip(responses, errors, strict=True)
                ]
            }

        return {"error": f"Unknown message type: {req_type!r}"}

    def stop(self) -> None:
        # Flip the flag *before* tearing down the server so any handler
        # threads still inside ``_dispatch`` reject new subcall work
        # instead of starting a fresh ``subcall_fn`` (which can incur API
        # cost). Already-running ``subcall_fn`` invocations will run to
        # completion — we can't cooperatively cancel arbitrary user code.
        self._shutting_down = True
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            self._thread = None

    @property
    def address(self) -> tuple[str, int]:
        if self._server is None:
            return (self.host, self._port)
        return (self.host, self._server.server_address[1])

    def drain(self) -> tuple[list[RLMChatCompletion], str | None]:
        """Atomically snapshot + clear completions and final_answer."""
        with self._lock:
            completions = self.completions.copy()
            self.completions.clear()
            final = self.final_answer
            self.final_answer = None
        return completions, final


# =============================================================================
# Subprocess kernel bootstrap script
# =============================================================================


def _build_kernel_bootstrap(
    lm_address: tuple[str, int] | None,
    subcall_address: tuple[str, int] | None,
    depth: int,
    subcall_timeout: float | None,
) -> str:
    """Code executed once inside the kernel to wire up scaffold helpers."""
    return textwrap.dedent(
        f"""
        import json as _rlm_json
        import socket as _rlm_socket
        import struct as _rlm_struct

        _RLM_LM_ADDRESS = {list(lm_address) if lm_address else None!r}
        _RLM_SUBCALL_ADDRESS = {list(subcall_address) if subcall_address else None!r}
        _RLM_DEPTH = {depth}
        _RLM_SUBCALL_TIMEOUT = {subcall_timeout!r}

        def _rlm_socket_send(sock, data):
            payload = _rlm_json.dumps(data).encode("utf-8")
            sock.sendall(_rlm_struct.pack(">I", len(payload)) + payload)

        def _rlm_socket_recv(sock):
            raw_len = b""
            while len(raw_len) < 4:
                chunk = sock.recv(4 - len(raw_len))
                if not chunk:
                    # Surface EOF as an explicit error so callers don't read
                    # an empty dict as a successful empty completion.
                    return {{"error": "Connection closed before length prefix received"}}
                raw_len += chunk
            length = _rlm_struct.unpack(">I", raw_len)[0]
            payload = b""
            while len(payload) < length:
                chunk = sock.recv(length - len(payload))
                if not chunk:
                    return {{"error": "Connection closed before message complete"}}
                payload += chunk
            return _rlm_json.loads(payload.decode("utf-8"))

        def _rlm_request(address, data, timeout=_RLM_SUBCALL_TIMEOUT):
            if address is None:
                return {{"error": "No address configured"}}
            sock = _rlm_socket.socket(_rlm_socket.AF_INET, _rlm_socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect(tuple(address))
                _rlm_socket_send(sock, data)
                return _rlm_socket_recv(sock)
            finally:
                sock.close()

        def llm_query(prompt, model=None):
            resp = _rlm_request(_RLM_LM_ADDRESS, {{
                "prompt": prompt, "model": model, "depth": _RLM_DEPTH
            }})
            if not isinstance(resp, dict):
                return "Error: LM query failed - malformed response"
            if resp.get("error"):
                return f"Error: {{resp['error']}}"
            cc = resp.get("chat_completion") or {{}}
            return cc.get("response", "")

        def llm_query_batched(prompts, model=None):
            prompts = list(prompts)
            resp = _rlm_request(_RLM_LM_ADDRESS, {{
                "prompts": prompts, "model": model, "depth": _RLM_DEPTH
            }})
            if not isinstance(resp, dict):
                return ["Error: LM query failed - malformed response"] * len(prompts)
            if resp.get("error"):
                return [f"Error: {{resp['error']}}"] * len(prompts)
            ccs = resp.get("chat_completions") or []
            return [c.get("response", "") for c in ccs]

        def rlm_query(prompt, model=None):
            if _RLM_SUBCALL_ADDRESS is None:
                return llm_query(prompt, model=model)
            resp = _rlm_request(_RLM_SUBCALL_ADDRESS, {{
                "type": "subcall", "prompt": prompt, "model": model
            }})
            if not isinstance(resp, dict):
                return "Error: RLM query failed - malformed response"
            if resp.get("error"):
                # Fall back to a plain LM call if the parent has no subcall_fn
                if "No subcall_fn" in resp["error"]:
                    return llm_query(prompt, model=model)
                return f"Error: {{resp['error']}}"
            cc = resp.get("completion") or {{}}
            return cc.get("response", "")

        def rlm_query_batched(prompts, model=None):
            prompts = list(prompts)
            if _RLM_SUBCALL_ADDRESS is None:
                return llm_query_batched(prompts, model=model)
            resp = _rlm_request(_RLM_SUBCALL_ADDRESS, {{
                "type": "subcall_batched", "prompts": prompts, "model": model
            }})
            if not isinstance(resp, dict):
                return ["Error: RLM query failed - malformed response"] * len(prompts)
            if resp.get("error"):
                if "No subcall_fn" in resp["error"]:
                    return llm_query_batched(prompts, model=model)
                return [f"Error: {{resp['error']}}"] * len(prompts)
            return list(resp.get("responses") or [])

        def FINAL_VAR(variable):
            if not isinstance(variable, str):
                answer = str(variable)
                _rlm_request(_RLM_SUBCALL_ADDRESS, {{"type": "final_var", "value": answer}})
                return answer
            name = variable.strip().strip('"\\'')
            ns = get_ipython().user_ns
            if name in ns:
                answer = str(ns[name])
                _rlm_request(_RLM_SUBCALL_ADDRESS, {{"type": "final_var", "value": answer}})
                return answer
            skip = {{"In", "Out", "exit", "quit", "get_ipython"}}
            available = [
                k for k in ns.keys()
                if not k.startswith("_") and k not in skip
            ]
            if available:
                return (
                    f"Error: Variable {{name!r}} not found. "
                    f"Available variables: {{available}}. "
                    "You must create and assign a variable BEFORE calling FINAL_VAR on it."
                )
            return (
                f"Error: Variable {{name!r}} not found. "
                "No variables have been created yet. "
                "You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."
            )

        def SHOW_VARS():
            ns = get_ipython().user_ns
            skip = {{"In", "Out", "exit", "quit", "get_ipython"}}
            available = {{
                k: type(v).__name__
                for k, v in ns.items()
                if not k.startswith("_") and k not in skip
            }}
            if not available:
                return "No variables created yet. Use ```repl``` blocks to create variables."
            return f"Available variables: {{available}}"
        """
    ).strip()


# =============================================================================
# IPythonREPL
# =============================================================================


class IPythonREPL(NonIsolatedEnv):
    """IPython-backed REPL with in-process or subprocess kernel modes.

    Concurrency / isolation:
        * ``execute_code`` is serialized within an instance via an
          :class:`~threading.RLock`, in both modes.
        * Subcall fan-out (``rlm_query`` / ``rlm_query_batched``) is bounded
          *globally* per broker by ``max_concurrent_subcalls``, regardless
          of how many concurrent kernel requests fan in.
        * In-process mode shares the parent Python process: ``sys.stdout``
          /``sys.stderr`` redirection, ``os.chdir``, and ``signal.SIGALRM``
          are process-global, and any other thread in the parent that
          touches them while a cell is running will see the shadowed
          state. Two in-process instances each get a *unique* user
          module so they don't trample each other's ``sys.modules``
          entry, but they still share the surrounding process. Use
          ``kernel_mode="subprocess"`` for true isolation.
        * Subprocess mode runs user code in a separate Python process via
          ``ipykernel`` and is fully isolated from the parent's
          namespace, cwd, and signals.

    Args:
        lm_handler_address: (host, port) of the LM handler socket server.
        context_payload: Initial context to load as ``context``/``context_0``.
        setup_code: Optional code to execute after context is loaded.
        persistent: If True, state survives across multiple ``RLM.completion``
            calls; the env exposes ``add_context``/``add_history`` and the
            ``SupportsPersistence`` protocol.
        depth: RLM depth the environment is running at (used for LM routing).
        subcall_fn: Callback that spawns a child RLM for ``rlm_query``.
        custom_tools: Extra functions/values to inject into the namespace.
        custom_sub_tools: Tools inherited by child RLMs (defaults to custom_tools).
        kernel_mode: ``"in_process"`` (default) or ``"subprocess"``.
        cell_timeout: Max seconds for a single ``execute_code`` call.
            - ``subprocess`` mode: hard guarantee via ``kc.execute_interactive
              (timeout=...)`` + ``km.interrupt_kernel()``. Always enforced.
            - ``in_process`` mode: best-effort via ``SIGALRM`` on Unix when
              called from the main thread. Interrupts Python loops *and*
              C-level blocking calls like ``time.sleep``. Silently no-op on
              Windows or when called off the main thread.
        startup_timeout: Max seconds to wait for a ``subprocess`` kernel to
            become ready.
        subcall_timeout: Per-request timeout (seconds) for the kernel→parent
            socket round-trip used by ``llm_query`` / ``rlm_query`` /
            ``FINAL_VAR`` in subprocess mode. ``None`` (default) disables
            the timeout, which matches in-process behavior where subcalls
            block indefinitely.
        max_concurrent_subcalls: Cap on concurrent ``rlm_query_batched`` calls.
    """

    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        subcall_fn: Callable[[str, str | None], RLMChatCompletion] | None = None,
        custom_tools: dict[str, Any] | None = None,
        custom_sub_tools: dict[str, Any] | None = None,
        kernel_mode: KernelMode = "in_process",
        cell_timeout: float | None = None,
        startup_timeout: float = 60.0,
        subcall_timeout: float | None = None,
        max_concurrent_subcalls: int = 4,
        **kwargs,
    ):
        if kernel_mode not in ("in_process", "subprocess"):
            raise ValueError(
                f"kernel_mode must be 'in_process' or 'subprocess', got {kernel_mode!r}"
            )

        super().__init__(
            persistent=persistent,
            depth=depth,
            max_concurrent_subcalls=max_concurrent_subcalls,
            **kwargs,
        )

        self.lm_handler_address = lm_handler_address
        self.subcall_fn = subcall_fn
        self.kernel_mode: KernelMode = kernel_mode
        # Normalize cell_timeout: 0 or negative is meaningless (subprocess
        # mode would interpret it as "give up immediately"). Treat as
        # disabled to match the in-process ``timeout > 0`` guard.
        self.cell_timeout = cell_timeout if cell_timeout and cell_timeout > 0 else None
        self.startup_timeout = startup_timeout
        self.subcall_timeout = subcall_timeout

        self.custom_tools = custom_tools or {}
        self.custom_sub_tools = (
            custom_sub_tools if custom_sub_tools is not None else self.custom_tools
        )
        validate_custom_tools(self.custom_tools)

        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix=f"ipython_env_{uuid.uuid4()}_")
        # RLock lets ``add_context`` / ``add_history`` hold the lock while
        # invoking ``execute_code`` (which re-acquires it) so the
        # index→assign→count-increment sequence stays atomic across threads.
        self._lock = threading.RLock()
        self._context_count: int = 0
        self._history_count: int = 0

        # Subprocess mode doesn't serialize the kernel's full user_ns back to
        # the parent on every execute. We keep a parent-side shadow of the
        # versioned context_N / history_N data (injected by add_context /
        # add_history) so tests and the RLM loop can inspect them via
        # ``self.locals``.
        self._subprocess_shadow: dict[str, Any] = {}

        # Tracking state for LLM calls / final answer during execute_code.
        self._pending_llm_calls: list[RLMChatCompletion] = []
        self._last_final_answer: str | None = None

        # In-process: IPython shell instance
        self._shell: Any = None
        # Per-instance ``__main__`` substitute used in in-process mode
        # (see ``_setup_in_process``).
        self._user_module: Any = None
        # Subprocess: jupyter_client manager/client
        self._km: Any = None
        self._kc: Any = None
        self._broker: _SubcallBroker | None = None

        # If anything below fails after a kernel/broker has started, we must
        # tear them down explicitly — relying on ``__del__`` is timing-
        # dependent and would leave kernels orphaned on crash.
        try:
            self.setup()

            if context_payload is not None:
                self.load_context(context_payload)

            if setup_code:
                self.execute_code(setup_code)
        except BaseException:
            self.cleanup()
            raise

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    def setup(self) -> None:
        if self.kernel_mode == "in_process":
            self._setup_in_process()
        else:
            self._setup_subprocess()

    def _setup_in_process(self) -> None:
        try:
            from IPython.core.interactiveshell import InteractiveShell
            from traitlets.config import Config
        except ImportError as e:
            raise ImportError(
                "IPython is required for IPythonREPL. Install with: "
                "pip install 'rlms[ipython]' or pip install ipython"
            ) from e

        # Disable IPython's history SQLite database. Without this, every
        # in-process instance opens (and leaks until __del__) a connection
        # to ~/.ipython/profile_default/history.sqlite, even though we
        # already pass ``store_history=False`` to ``run_cell``.
        config = Config()
        config.HistoryAccessor.enabled = False

        # By default, ``InteractiveShell`` names its user module
        # ``__main__`` and writes ``sys.modules['__main__'] = user_module``.
        # Two in-process IPythonREPLs in the same process would overwrite
        # each other's ``__main__``. Use a unique module name per instance
        # so each gets its own ``sys.modules`` slot. (The kernel-side
        # ``__main__`` of the parent process is left untouched.)
        import types as _types

        unique_main = _types.ModuleType(
            f"_rlm_ipython_main_{uuid.uuid4().hex[:8]}",
            doc="Per-instance namespace for an in-process IPythonREPL.",
        )

        # InteractiveShell is a singleton by default; using .instance() would
        # leak state across multiple IPythonREPL objects. Create a fresh one.
        shell = InteractiveShell(config=config, user_module=unique_main)
        self._shell = shell
        self._user_module = unique_main
        ns = shell.user_ns

        # Inject scaffold functions
        ns["llm_query"] = self._llm_query
        ns["llm_query_batched"] = self._llm_query_batched
        ns["rlm_query"] = self._rlm_query
        ns["rlm_query_batched"] = self._rlm_query_batched
        ns["FINAL_VAR"] = self._final_var
        ns["SHOW_VARS"] = self._show_vars

        # Inject custom tools
        for name, entry in self.custom_tools.items():
            ns[name] = extract_tool_value(entry)

    def _setup_subprocess(self) -> None:
        try:
            from jupyter_client.manager import KernelManager
        except ImportError as e:
            raise ImportError(
                "jupyter_client and ipykernel are required for IPythonREPL "
                "in subprocess mode. Install with: pip install 'rlms[ipython]' "
                "or pip install jupyter_client ipykernel"
            ) from e

        # Start broker first so we know its address before bootstrapping kernel
        self._broker = _SubcallBroker(
            subcall_fn=self.subcall_fn,
            max_concurrent=self.max_concurrent_subcalls,
        )
        self._broker.start()

        self._km = KernelManager(kernel_name="python3")
        # Force the kernel to run under the same Python as the parent process,
        # so it inherits the same installed packages (dill, custom imports,
        # etc.). Without this, jupyter_client uses whatever 'python' is on
        # PATH per the default kernelspec.
        self._km.kernel_cmd = [
            sys.executable,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
        self._km.start_kernel(cwd=self.temp_dir)
        self._kc = self._km.client()
        self._kc.start_channels()
        self._kc.wait_for_ready(timeout=self.startup_timeout)

        # Bootstrap scaffold inside the kernel
        bootstrap = _build_kernel_bootstrap(
            lm_address=self.lm_handler_address,
            subcall_address=self._broker.address,
            depth=self.depth,
            subcall_timeout=self.subcall_timeout,
        )
        result = self._execute_in_kernel(
            bootstrap, timeout=self.startup_timeout, drain_broker=False
        )
        if result.stderr:
            raise RuntimeError(f"Kernel bootstrap failed:\n{result.stderr}")

        # Inject custom tools. Only values that pickle cleanly will survive;
        # for arbitrary callables we use dill if available, otherwise we skip
        # with a clear error.
        if self.custom_tools:
            self._inject_custom_tools_subprocess()

    def _inject_custom_tools_subprocess(self) -> None:
        """Ship custom_tools to the subprocess kernel.

        Prefers dill for callables and arbitrary Python objects, falls back to
        JSON for plain data if dill isn't installed. Either path raises with a
        clear message on failure.
        """
        try:
            import dill  # type: ignore

            dill_available = True
        except ImportError:
            dill_available = False

        for name, entry in self.custom_tools.items():
            value = extract_tool_value(entry)

            if dill_available:
                try:
                    # recurse=True pickles functions by value (including their
                    # module globals) so the kernel doesn't need to import the
                    # original defining module — important for locally-defined
                    # closures.
                    payload = dill.dumps(value, recurse=True).hex()
                except Exception as e:
                    raise RuntimeError(
                        f"Custom tool {name!r} could not be pickled with dill: {e}"
                    ) from e
                code = textwrap.dedent(
                    f"""
                    import dill as _rlm_dill
                    {name} = _rlm_dill.loads(bytes.fromhex({payload!r}))
                    """
                ).strip()
                result = self._execute_in_kernel(code, drain_broker=False)
                if result.stderr:
                    raise RuntimeError(
                        f"Failed to inject custom tool {name!r} into kernel: {result.stderr}"
                    )
                continue

            # Fallback: JSON-roundtrip for primitive data
            try:
                json_payload = json.dumps(value)
            except (TypeError, ValueError) as e:
                raise RuntimeError(
                    f"Custom tool {name!r} is not JSON-serializable and dill is not "
                    f"installed. Install dill (pip install dill) to inject arbitrary "
                    f"callables/objects. ({e})"
                ) from e
            code = f"import json as _rlm_json; {name} = _rlm_json.loads({json_payload!r})"
            result = self._execute_in_kernel(code, drain_broker=False)
            if result.stderr:
                raise RuntimeError(
                    f"Failed to inject custom tool {name!r} into kernel: {result.stderr}"
                )

    # -------------------------------------------------------------------------
    # Scaffold helpers (in-process only; subprocess has its own in the kernel)
    # -------------------------------------------------------------------------

    def _final_var(self, variable_name: str | Any) -> str:
        if not isinstance(variable_name, str):
            answer = str(variable_name)
            self._last_final_answer = answer
            return answer
        name = variable_name.strip().strip("\"'")
        ns = self._shell.user_ns if self._shell is not None else {}
        if name in ns:
            answer = str(ns[name])
            self._last_final_answer = answer
            return answer
        available = [
            k for k in ns.keys() if not k.startswith("_") and k not in _IPYTHON_INTERNAL_NAMES
        ]
        if available:
            return (
                f"Error: Variable '{name}' not found. "
                f"Available variables: {available}. "
                f"You must create and assign a variable BEFORE calling FINAL_VAR on it."
            )
        return (
            f"Error: Variable '{name}' not found. "
            f"No variables have been created yet. "
            f"You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."
        )

    def _show_vars(self) -> str:
        ns = self._shell.user_ns if self._shell is not None else {}
        available = {
            k: type(v).__name__
            for k, v in ns.items()
            if not k.startswith("_") and k not in _IPYTHON_INTERNAL_NAMES
        }
        if not available:
            return "No variables created yet. Use ```repl``` blocks to create variables."
        return f"Available variables: {available}"

    def _llm_query(self, prompt: str, model: str | None = None) -> str:
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
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)
        try:
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
            )
            results: list[str] = []
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
        if self.subcall_fn is None:
            return self._llm_query(prompt, model)
        try:
            completion = self.subcall_fn(prompt, model)
            self._pending_llm_calls.append(completion)
            return completion.response
        except Exception as e:
            return f"Error: RLM query failed - {e}"

    def _rlm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        if self.subcall_fn is None:
            return self._llm_query_batched(prompts, model)

        if len(prompts) <= 1:
            results: list[str] = []
            for prompt in prompts:
                try:
                    completion = self.subcall_fn(prompt, model)
                    self._pending_llm_calls.append(completion)
                    results.append(completion.response)
                except Exception as e:
                    results.append(f"Error: RLM query failed - {e}")
            return results

        max_workers = min(self.max_concurrent_subcalls, len(prompts))
        results: list[str] = [""] * len(prompts)
        completions: list[tuple[int, RLMChatCompletion]] = []
        lock = threading.Lock()

        def _run(index: int, prompt: str) -> None:
            try:
                completion = self.subcall_fn(prompt, model)  # type: ignore[misc]
                with lock:
                    completions.append((index, completion))
                results[index] = completion.response
            except Exception as e:
                results[index] = f"Error: RLM query failed - {e}"

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run, i, p) for i, p in enumerate(prompts)]
            for f in as_completed(futures):
                f.result()

        completions.sort(key=lambda x: x[0])
        for _, completion in completions:
            self._pending_llm_calls.append(completion)
        return results

    # -------------------------------------------------------------------------
    # Context
    # -------------------------------------------------------------------------

    def load_context(self, context_payload: dict | list | str) -> None:
        self.add_context(context_payload, 0)

    def add_context(
        self,
        context_payload: dict | list | str,
        context_index: int | None = None,
    ) -> int:
        # Hold the env lock for the whole index → write → increment
        # sequence. Without this, two concurrent ``add_context`` calls with
        # ``context_index=None`` would both pick the same index and
        # silently overwrite each other.
        with self._lock:
            if context_index is None:
                context_index = self._context_count
            var_name = f"context_{context_index}"

            if isinstance(context_payload, str):
                context_path = os.path.join(self.temp_dir, f"context_{context_index}.txt")
                with open(context_path, "w") as f:
                    f.write(context_payload)
                code = (
                    f"with open(r'{context_path}', 'r') as _rlm_f:\n    {var_name} = _rlm_f.read()"
                )
            else:
                context_path = os.path.join(self.temp_dir, f"context_{context_index}.json")
                with open(context_path, "w") as f:
                    json.dump(context_payload, f)
                code = (
                    "import json as _rlm_json\n"
                    f"with open(r'{context_path}', 'r') as _rlm_f:\n"
                    f"    {var_name} = _rlm_json.load(_rlm_f)"
                )

            # Fold the ``context = context_0`` alias into the same cell to
            # save a kernel round-trip in subprocess mode.
            if context_index == 0:
                code += f"\ncontext = {var_name}"

            result = self.execute_code(code)
            if result.stderr:
                raise RuntimeError(f"Failed to load context: {result.stderr}")

            # Shadow for subprocess mode so self.locals can report context_N.
            if self.kernel_mode == "subprocess":
                self._subprocess_shadow[var_name] = copy.deepcopy(context_payload)
                if context_index == 0:
                    self._subprocess_shadow["context"] = self._subprocess_shadow[var_name]

            self._context_count = max(self._context_count, context_index + 1)
            return context_index

    def get_context_count(self) -> int:
        return self._context_count

    def add_history(
        self,
        message_history: list[dict[str, Any]],
        history_index: int | None = None,
    ) -> int:
        """Store a message history as ``history_N`` (and ``history`` for index 0)."""
        # See ``add_context`` for the rationale on holding ``self._lock``.
        with self._lock:
            if history_index is None:
                history_index = self._history_count
            var_name = f"history_{history_index}"
            payload = copy.deepcopy(message_history)

            # In-process: assign directly into user_ns.
            if self.kernel_mode == "in_process":
                assert self._shell is not None
                self._shell.user_ns[var_name] = payload
                if history_index == 0:
                    self._shell.user_ns["history"] = payload
            else:
                # Subprocess: round-trip via a temp JSON file (histories are
                # always JSON-serializable by construction: role/content
                # dicts).
                history_path = os.path.join(self.temp_dir, f"history_{history_index}.json")
                with open(history_path, "w") as f:
                    json.dump(payload, f)
                code = (
                    "import json as _rlm_json\n"
                    f"with open(r'{history_path}', 'r') as _rlm_f:\n"
                    f"    {var_name} = _rlm_json.load(_rlm_f)"
                )
                if history_index == 0:
                    code += f"\nhistory = {var_name}"
                result = self.execute_code(code)
                if result.stderr:
                    raise RuntimeError(f"Failed to load history: {result.stderr}")
                self._subprocess_shadow[var_name] = payload
                if history_index == 0:
                    self._subprocess_shadow["history"] = payload

            self._history_count = max(self._history_count, history_index + 1)
            return history_index

    def get_history_count(self) -> int:
        return self._history_count

    def update_handler_address(self, address: tuple[str, int]) -> None:
        self.lm_handler_address = address
        if self.kernel_mode == "subprocess" and self._kc is not None:
            # Update the kernel's cached address
            update = textwrap.dedent(
                f"""
                _RLM_LM_ADDRESS = {list(address)!r}
                """
            ).strip()
            self._execute_in_kernel(update, drain_broker=False)

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def execute_code(self, code: str) -> REPLResult:
        if self.kernel_mode == "in_process":
            return self._execute_in_process(code)
        return self._execute_in_kernel(code, timeout=self.cell_timeout, drain_broker=True)

    def _execute_in_process(self, code: str) -> REPLResult:
        start_time = time.perf_counter()
        self._pending_llm_calls = []

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        timeout = self.cell_timeout
        use_alarm = (
            timeout is not None
            and timeout > 0
            and sys.platform != "win32"
            and threading.current_thread() is threading.main_thread()
            and hasattr(signal, "SIGALRM")
        )

        def _alarm_handler(signum, frame):
            raise TimeoutError(f"cell execution exceeded {timeout}s and was interrupted")

        prev_handler = None
        prev_timer: tuple[float, float] | None = None

        with self._lock, self._temp_cwd():
            if use_alarm:
                prev_handler = signal.signal(signal.SIGALRM, _alarm_handler)
                prev_timer = signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                    try:
                        result = self._shell.run_cell(code, store_history=False, silent=False)
                    except Exception as e:
                        stderr_buf.write(f"\n{type(e).__name__}: {e}")
                        result = None
            finally:
                if use_alarm:
                    # Clear the pending alarm before restoring the handler, or
                    # a late-firing SIGALRM could escape into unrelated code.
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    if prev_handler is not None:
                        signal.signal(signal.SIGALRM, prev_handler)
                    # Restore any previously-scheduled timer the caller had set.
                    if prev_timer and prev_timer[0] > 0:
                        signal.setitimer(signal.ITIMER_REAL, *prev_timer)

            if result is not None:
                # IPython's own traceback printer doesn't reliably go through
                # ``sys.stderr`` (it binds to ``IPython.utils.io.stderr`` at
                # import time, before our ``redirect_stderr``). Format the
                # exception ourselves so the LLM sees a useful traceback,
                # matching the verbosity of subprocess-mode output.
                if result.error_before_exec is not None:
                    err = result.error_before_exec
                    stderr_buf.write(
                        "\n"
                        + "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    )
                if result.error_in_exec is not None:
                    err = result.error_in_exec
                    stderr_buf.write(
                        "\n"
                        + "".join(traceback.format_exception(type(err), err, err.__traceback__))
                    )

            # Re-inject scaffold in case user code overwrote it
            self._restore_scaffold_in_process()

            locals_snapshot = {
                k: v
                for k, v in self._shell.user_ns.items()
                if not k.startswith("_") and k not in _IPYTHON_INTERNAL_NAMES
            }

        final_answer = self._last_final_answer
        self._last_final_answer = None

        return REPLResult(
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue(),
            locals=locals_snapshot,
            execution_time=time.perf_counter() - start_time,
            rlm_calls=self._pending_llm_calls.copy(),
            final_answer=final_answer,
        )

    def _execute_in_kernel(
        self,
        code: str,
        timeout: float | None = None,
        drain_broker: bool = True,
    ) -> REPLResult:
        """Execute ``code`` in the subprocess kernel.

        ``drain_broker=False`` is for setup paths (bootstrap, custom-tool
        injection, ``update_handler_address``) that must not consume
        completions destined for a future user-facing cell. User-facing
        ``execute_code`` always passes ``drain_broker=True``.

        Acquires ``self._lock`` so concurrent ``execute_code`` calls from
        different threads don't race on ``_kc.execute_interactive`` or on
        broker drain.
        """
        assert self._kc is not None and self._broker is not None

        with self._lock:
            return self._execute_in_kernel_locked(code, timeout, drain_broker)

    def _execute_in_kernel_locked(
        self,
        code: str,
        timeout: float | None,
        drain_broker: bool,
    ) -> REPLResult:
        start_time = time.perf_counter()

        # If a previous cell timed out mid-subcall, ``subcall_fn`` may have
        # finished after we drained, leaving stragglers in the broker.
        # Discard them so they aren't misattributed to *this* cell.
        if drain_broker:
            assert self._broker is not None
            self._broker.drain()

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        error_info: dict[str, Any] | None = None

        def output_hook(msg: dict[str, Any]) -> None:
            nonlocal error_info
            msg_type = msg.get("header", {}).get("msg_type")
            content = msg.get("content", {})
            if msg_type == "stream":
                name = content.get("name")
                text = content.get("text", "")
                if name == "stderr":
                    stderr_parts.append(text)
                else:
                    stdout_parts.append(text)
            elif msg_type == "error":
                error_info = content
            elif msg_type == "execute_result":
                data = content.get("data", {})
                text = data.get("text/plain")
                if text:
                    stdout_parts.append(text + "\n")
            elif msg_type == "display_data":
                data = content.get("data", {})
                text = data.get("text/plain")
                if text:
                    stdout_parts.append(text + "\n")

        timed_out = False
        try:
            self._kc.execute_interactive(
                code,
                timeout=timeout,
                output_hook=output_hook,
                store_history=False,
                stop_on_error=False,
                allow_stdin=False,
            )
        except TimeoutError:
            timed_out = True
            try:
                self._km.interrupt_kernel()
            except Exception:
                pass
            stderr_parts.append(
                f"\nTimeoutError: cell execution exceeded {timeout}s and was interrupted"
            )

        if error_info is not None and not timed_out:
            ename = error_info.get("ename", "Error")
            evalue = error_info.get("evalue", "")
            traceback_lines = error_info.get("traceback") or []
            # Strip ANSI escape codes from tracebacks for cleaner stderr
            tb = "\n".join(self._strip_ansi(line) for line in traceback_lines)
            if tb:
                stderr_parts.append("\n" + tb)
            else:
                stderr_parts.append(f"\n{ename}: {evalue}")

        # Drain broker state (rlm_query completions, FINAL_VAR answer) only on
        # user-facing cells. ``rlm_calls`` reports what was made *during this
        # cell* — never accumulate across cells.
        if drain_broker:
            completions, final_answer = self._broker.drain()
        else:
            completions, final_answer = [], None

        return REPLResult(
            stdout="".join(stdout_parts),
            stderr="".join(stderr_parts),
            locals={},  # serializing arbitrary user_ns through ZMQ is costly; skip for now
            execution_time=time.perf_counter() - start_time,
            rlm_calls=list(completions),
            final_answer=final_answer,
        )

    @staticmethod
    def _strip_ansi(s: str) -> str:
        return _ANSI_RE.sub("", s)

    def _restore_scaffold_in_process(self) -> None:
        if self._shell is None:
            return
        ns = self._shell.user_ns
        ns["llm_query"] = self._llm_query
        ns["llm_query_batched"] = self._llm_query_batched
        ns["rlm_query"] = self._rlm_query
        ns["rlm_query_batched"] = self._rlm_query_batched
        ns["FINAL_VAR"] = self._final_var
        ns["SHOW_VARS"] = self._show_vars
        if "context_0" in ns:
            ns["context"] = ns["context_0"]
        if "history_0" in ns:
            ns["history"] = ns["history_0"]
        # Re-inject custom tools if overwritten
        for name, entry in self.custom_tools.items():
            if name in RESERVED_TOOL_NAMES:
                continue
            ns[name] = extract_tool_value(entry)

    # -------------------------------------------------------------------------
    # Convenience: expose a dict-like 'locals' view for parity with LocalREPL
    # -------------------------------------------------------------------------

    @property
    def locals(self) -> dict[str, Any]:
        """Snapshot of the user-defined namespace.

        In-process mode mirrors the IPython shell's ``user_ns``. Subprocess
        mode only tracks variables we ourselves injected via ``add_context``
        / ``add_history`` (the parent doesn't round-trip the kernel's
        ``user_ns`` on every cell). User-defined variables from
        ``execute_code`` are not visible here in subprocess mode — query the
        kernel directly with another cell instead.
        """
        if self.kernel_mode == "in_process" and self._shell is not None:
            return {
                k: v
                for k, v in self._shell.user_ns.items()
                if not k.startswith("_") and k not in _IPYTHON_INTERNAL_NAMES
            }
        return dict(self._subprocess_shadow)

    @contextmanager
    def _temp_cwd(self):
        old = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            yield
        finally:
            try:
                os.chdir(old)
            except FileNotFoundError:
                os.chdir(self.original_cwd)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def cleanup(self) -> None:
        if self.kernel_mode == "subprocess":
            if self._kc is not None:
                try:
                    self._kc.stop_channels()
                except Exception:
                    pass
                self._kc = None
            if self._km is not None:
                try:
                    self._km.shutdown_kernel(now=True)
                except Exception:
                    pass
                self._km = None
            if self._broker is not None:
                try:
                    self._broker.stop()
                except Exception:
                    pass
                self._broker = None

        if self._shell is not None:
            try:
                self._shell.reset(new_session=False)
            except Exception:
                pass
            self._shell = None

        # Drop the per-instance module from sys.modules so we don't
        # accumulate one slot per IPythonREPL ever created.
        user_module = getattr(self, "_user_module", None)
        if user_module is not None:
            sys.modules.pop(user_module.__name__, None)
            self._user_module = None

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def __enter__(self) -> IPythonREPL:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.cleanup()
        return False

    def __del__(self) -> None:
        try:
            self.cleanup()
        except Exception:
            pass
