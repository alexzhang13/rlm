"""
InstaVM REPL environment that runs Python code in InstaVM Firecracker microVMs.

Uses the InstaVM Python SDK (https://instavm.io/docs/sdks/python/overview).
Follows the same HTTP broker pattern as ModalREPL/E2BREPL for LLM communication,
but uses Python stdlib (http.server, pickle) inside the VM and httpx (preinstalled
in InstaVM images) for the in-VM client, so no `pip install` step is needed at
session setup.
"""

import base64
import json
import textwrap
import threading
import time
from typing import Any

import requests
from instavm import InstaVM

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import IsolatedEnv

# =============================================================================
# Broker server script (runs inside the VM, handles the LLM request queue)
# =============================================================================

_BROKER_SCRIPT = textwrap.dedent(
    """
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Request queue: {request_id: {"request": {...}, "response": None, "event": Event}}
pending_requests = {}
lock = threading.Lock()


def _read_json(handler):
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def _write_json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args, **_kwargs):
        return  # silence access log

    def do_GET(self):
        if self.path == "/health":
            _write_json(self, 200, {"status": "ok"})
            return
        if self.path == "/pending":
            with lock:
                out = [
                    {"id": rid, "request": entry["request"]}
                    for rid, entry in pending_requests.items()
                    if entry["response"] is None
                ]
            _write_json(self, 200, {"pending": out})
            return
        _write_json(self, 404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/enqueue":
            data = _read_json(self)
            request_id = str(uuid.uuid4())
            event = threading.Event()
            with lock:
                pending_requests[request_id] = {
                    "request": data,
                    "response": None,
                    "event": event,
                }
            event.wait(timeout=300)
            with lock:
                entry = pending_requests.pop(request_id, None)
            if entry and entry["response"] is not None:
                _write_json(self, 200, entry["response"])
            else:
                _write_json(self, 504, {"error": "Request timed out"})
            return

        if self.path == "/respond":
            data = _read_json(self)
            request_id = data.get("id")
            response = data.get("response")
            with lock:
                if request_id in pending_requests:
                    pending_requests[request_id]["response"] = response
                    pending_requests[request_id]["event"].set()
                    _write_json(self, 200, {"status": "ok"})
                    return
            _write_json(self, 404, {"error": "Request not found"})
            return

        _write_json(self, 404, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", {PORT}), Handler).serve_forever()
"""
)


# =============================================================================
# Execution script (runs inside the VM for each code block)
# =============================================================================


def _build_exec_script(code: str, broker_port: int) -> str:
    """
    Build a script that executes user code with state persistence.
    LLM queries go through the local broker server using httpx (preinstalled).
    Uses stdlib pickle for state — values that don't pickle are silently dropped.
    """
    code_b64 = base64.b64encode(code.encode()).decode()

    return textwrap.dedent(
        f'''
import sys
import io
import json
import base64
import os
import pickle

try:
    import dill as state_serializer
except ImportError:
    state_serializer = pickle
import traceback

import httpx

BROKER_URL = "http://127.0.0.1:{broker_port}"
STATE_FILE = "/tmp/rlm_state.pkl"

def llm_query(prompt, model=None):
    """Query the LM via the local broker server."""
    try:
        response = httpx.post(
            f"{{BROKER_URL}}/enqueue",
            json={{"type": "single", "prompt": prompt, "model": model}},
            timeout=300,
        )
        data = response.json()
        if data.get("error"):
            return f"Error: {{data['error']}}"
        return data.get("response", "Error: No response")
    except Exception as exc:
        return f"Error: LM query failed - {{exc}}"


def llm_query_batched(prompts, model=None):
    """Query the LM with multiple prompts via the local broker server."""
    try:
        response = httpx.post(
            f"{{BROKER_URL}}/enqueue",
            json={{"type": "batched", "prompts": prompts, "model": model}},
            timeout=300,
        )
        data = response.json()
        if data.get("error"):
            return [f"Error: {{data['error']}}"] * len(prompts)
        return data.get("responses", ["Error: No response"] * len(prompts))
    except Exception as exc:
        return [f"Error: LM query failed - {{exc}}"] * len(prompts)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as fh:
                return state_serializer.load(fh)
        except Exception:
            return {{}}
    return {{}}


def save_state(state):
    clean = {{}}
    for key, value in state.items():
        if key.startswith("_"):
            continue
        try:
            state_serializer.dumps(value)
            clean[key] = value
        except Exception:
            continue
    with open(STATE_FILE, "wb") as fh:
        state_serializer.dump(clean, fh)


def serialize_locals(state):
    out = {{}}
    for key, value in state.items():
        if key.startswith("_"):
            continue
        try:
            out[key] = repr(value)
        except Exception:
            out[key] = f"<{{type(value).__name__}}>"
    return out


_locals = load_state()


def FINAL_VAR(variable_name):
    variable_name = variable_name.strip().strip("\\"\\'")
    if variable_name in _locals:
        return str(_locals[variable_name])
    available = {{
        k: type(v).__name__ for k, v in _locals.items() if not k.startswith("_")
    }}
    if available:
        return (
            f"Error: Variable '{{variable_name}}' not found. "
            f"Available variables: {{available}}. "
            "You must create and assign a variable BEFORE calling FINAL_VAR on it."
        )
    return (
        f"Error: Variable '{{variable_name}}' not found. "
        "No variables have been created yet. You must create and assign a variable in a "
        "REPL block BEFORE calling FINAL_VAR on it."
    )


def SHOW_VARS():
    available = {{k: type(v).__name__ for k, v in _locals.items() if not k.startswith("_")}}
    if not available:
        return "No variables created yet. Use ```repl``` blocks to create variables."
    return f"Available variables: {{available}}"


_globals = {{
    "__builtins__": __builtins__,
    "__name__": "__main__",
    "llm_query": llm_query,
    "llm_query_batched": llm_query_batched,
    "FINAL_VAR": FINAL_VAR,
    "SHOW_VARS": SHOW_VARS,
}}

code = base64.b64decode("{code_b64}").decode()

stdout_buf = io.StringIO()
stderr_buf = io.StringIO()
old_stdout, old_stderr = sys.stdout, sys.stderr

try:
    sys.stdout = stdout_buf
    sys.stderr = stderr_buf
    combined = {{**_globals, **_locals}}
    exec(code, combined, combined)
    for key, value in combined.items():
        if key not in _globals and not key.startswith("_"):
            _locals[key] = value
except Exception:
    traceback.print_exc(file=stderr_buf)
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

if "context_0" in _locals:
    _locals["context"] = _locals["context_0"]
if "history_0" in _locals:
    _locals["history"] = _locals["history_0"]

save_state(_locals)

print(json.dumps({{
    "stdout": stdout_buf.getvalue(),
    "stderr": stderr_buf.getvalue(),
    "locals": serialize_locals(_locals),
}}))
'''
    )


# =============================================================================
# InstaVMREPL
# =============================================================================


class InstaVMREPL(IsolatedEnv):
    """
    InstaVM REPL environment that runs Python code in InstaVM Firecracker microVMs.

    InstaVM provides:
      * Sub-200ms cold-start microVMs.
      * Stateful Python execution between calls (persisted via pickle).
      * Full network access from inside the VM.

    LLM communication uses the same HTTP broker pattern as ModalREPL/E2BREPL:
      * A stdlib http.server runs inside the VM and is exposed publicly via
        ``vm.shares.create(port=BROKER_PORT, is_public=True)``.
      * A poller thread on the host forwards requests from the broker to the
        LM handler and posts responses back.
    """

    BROKER_PORT = 8889

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.instavm.io",
        timeout: int = 300,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        **kwargs: Any,
    ):
        if persistent:
            raise NotImplementedError(
                "Persistent REPLs are currently not supported for environment: InstaVMREPL"
            )
        super().__init__(persistent=persistent, **kwargs)

        if api_key is None:
            import os

            api_key = os.environ.get("INSTAVM_API_KEY")
        if not api_key:
            raise ValueError(
                "InstaVM API key not found. Pass api_key in environment_kwargs or set "
                "the INSTAVM_API_KEY environment variable. Get a key at https://instavm.io"
            )

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.lm_handler_address = lm_handler_address

        self.vm: InstaVM | None = None
        self.broker_url: str | None = None
        self.share_id: str | None = None

        self.poller_thread: threading.Thread | None = None
        self.poller_stop = threading.Event()
        self.pending_llm_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)

        if setup_code:
            self.execute_code(setup_code)

    # ------------------------------------------------------------------ setup

    def setup(self):
        """Boot the InstaVM, start the broker inside it, and expose it publicly."""
        self.vm = InstaVM(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        # Install dill so user-defined functions/classes survive across blocks
        # (matches the persistence semantics of e2b/modal/daytona REPLs).
        # If the install fails for any reason, the in-VM script falls back to
        # stdlib pickle (objects defined in __main__ will be silently dropped).
        self.vm.execute(
            "import subprocess, sys;"
            "subprocess.run([sys.executable,'-m','pip','install','-q','dill>=0.3.7'],"
            " check=False)",
            language="python",
            timeout=120,
        )

        # Write the broker script to /tmp/broker.py via a base64 round-trip so
        # we don't have to worry about heredoc escaping inside vm.execute().
        broker_script = _BROKER_SCRIPT.replace("{PORT}", str(self.BROKER_PORT))
        broker_b64 = base64.b64encode(broker_script.encode()).decode()
        write_cmd = (
            f"import base64;open('/tmp/rlm_broker.py','wb').write(base64.b64decode('{broker_b64}'))"
        )
        self.vm.execute(write_cmd, language="python", timeout=30)

        # Start the broker as a detached background process. preexec_fn=os.setpgrp
        # ensures the process survives across separate vm.execute() invocations.
        bg_cmd = (
            "import subprocess, os;"
            "subprocess.Popen("
            "['nohup','python3','/tmp/rlm_broker.py'],"
            " stdout=open('/tmp/rlm_broker.out','w'),"
            " stderr=subprocess.STDOUT,"
            " preexec_fn=os.setpgrp)"
        )
        self.vm.execute(bg_cmd, language="python", timeout=30)

        # Expose the broker port publicly via InstaVM shares.
        share = self.vm.shares.create(port=self.BROKER_PORT, is_public=True)
        self.broker_url = share["url"].rstrip("/")
        self.share_id = share.get("share_id")

        self._wait_for_broker()

        if self.lm_handler_address is not None:
            self.poller_stop.clear()
            self.poller_thread = threading.Thread(target=self._poll_broker, daemon=True)
            self.poller_thread.start()

    def _wait_for_broker(self, max_attempts: int = 30, interval: float = 1.0):
        """Block until the broker's /health endpoint responds 200."""
        last_err: Exception | None = None
        for _ in range(max_attempts):
            try:
                resp = requests.get(f"{self.broker_url}/health", timeout=5)
                if resp.status_code == 200 and resp.json().get("status") == "ok":
                    return
            except Exception as exc:
                last_err = exc
            time.sleep(interval)
        raise RuntimeError(
            f"InstaVM broker did not become ready within {max_attempts * interval:.0f}s "
            f"(last error: {last_err!r})"
        )

    # --------------------------------------------------------------- polling

    def _poll_broker(self):
        """Forward inside-VM LLM requests to the host LM handler and post back."""
        while not self.poller_stop.is_set():
            try:
                resp = requests.get(f"{self.broker_url}/pending", timeout=5)
                pending = resp.json().get("pending", [])
                for item in pending:
                    request_id = item["id"]
                    req_data = item["request"]
                    response = self._handle_llm_request(req_data)
                    try:
                        requests.post(
                            f"{self.broker_url}/respond",
                            json={"id": request_id, "response": response},
                            timeout=10,
                        )
                    except requests.exceptions.RequestException:
                        pass
            except requests.exceptions.RequestException:
                pass
            except Exception:
                pass
            time.sleep(0.1)

    def _handle_llm_request(self, req_data: dict) -> dict:
        """Forward a single LLM request to the host LM handler."""
        req_type = req_data.get("type")
        model = req_data.get("model")

        if req_type == "single":
            prompt = req_data.get("prompt")
            request = LMRequest(prompt=prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)
            if not response.success:
                return {"error": response.error}
            with self._calls_lock:
                self.pending_llm_calls.append(response.chat_completion)
            return {"response": response.chat_completion.response}

        if req_type == "batched":
            prompts = req_data.get("prompts", [])
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
            )
            results = []
            for resp in responses:
                if not resp.success:
                    results.append(f"Error: {resp.error}")
                    continue
                with self._calls_lock:
                    self.pending_llm_calls.append(resp.chat_completion)
                results.append(resp.chat_completion.response)
            return {"responses": results}

        return {"error": f"Unknown request type: {req_type!r}"}

    # ---------------------------------------------------------------- context

    def load_context(self, context_payload: dict | list | str):
        """Inject ``context = ...`` into the VM's execution namespace."""
        if isinstance(context_payload, str):
            escaped = context_payload.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
            context_code = f'context = """{escaped}"""'
        else:
            context_json = json.dumps(context_payload)
            escaped_json = context_json.replace("\\", "\\\\").replace("'", "\\'")
            context_code = f"import json; context = json.loads('{escaped_json}')"
        self.execute_code(context_code)

    # --------------------------------------------------------------- execute

    def execute_code(self, code: str) -> REPLResult:
        """Execute code inside the InstaVM and return a REPLResult."""
        if self.vm is None:
            raise RuntimeError("InstaVM client not initialized. Call setup() first.")

        start_time = time.perf_counter()

        with self._calls_lock:
            self.pending_llm_calls.clear()

        script = _build_exec_script(code, self.BROKER_PORT)
        script_b64 = base64.b64encode(script.encode()).decode()
        write_cmd = (
            f"import base64;open('/tmp/rlm_run.py','wb').write(base64.b64decode('{script_b64}'))"
        )
        self.vm.execute(write_cmd, language="python", timeout=30)

        run_result = self.vm.execute(
            "import subprocess, sys;"
            "p = subprocess.run([sys.executable, '/tmp/rlm_run.py'],"
            " capture_output=True, text=True);"
            "sys.stdout.write(p.stdout);"
            "sys.stderr.write(p.stderr)",
            language="python",
            timeout=self.timeout,
        )

        stdout = run_result.get("stdout", "") if isinstance(run_result, dict) else ""
        stderr = run_result.get("stderr", "") if isinstance(run_result, dict) else ""

        with self._calls_lock:
            pending_calls = self.pending_llm_calls.copy()
            self.pending_llm_calls.clear()

        execution_time = time.perf_counter() - start_time

        # The exec script prints a single JSON object as its last line of stdout.
        try:
            lines = [ln for ln in stdout.strip().split("\n") if ln.strip()]
            parsed = json.loads(lines[-1]) if lines else {}
            return REPLResult(
                stdout=parsed.get("stdout", ""),
                stderr=parsed.get("stderr", "") + stderr,
                locals=parsed.get("locals", {}),
                execution_time=execution_time,
                rlm_calls=pending_calls,
            )
        except (json.JSONDecodeError, IndexError):
            return REPLResult(
                stdout=stdout,
                stderr=stderr or "Failed to parse execution result",
                locals={},
                execution_time=execution_time,
                rlm_calls=pending_calls,
            )

    # ---------------------------------------------------------------- cleanup

    def update_handler_address(self, address: tuple[str, int]) -> None:
        """Update the LM handler address; RLM calls this between completions."""
        self.lm_handler_address = address
        if self.poller_thread is None and address is not None:
            self.poller_stop.clear()
            self.poller_thread = threading.Thread(target=self._poll_broker, daemon=True)
            self.poller_thread.start()

    def cleanup(self):
        """Stop the poller, revoke the public share, and kill the VM."""
        if self.poller_thread is not None:
            self.poller_stop.set()
            self.poller_thread.join(timeout=2)
            self.poller_thread = None

        if self.vm is not None and self.share_id is not None:
            try:
                self.vm.shares.update(self.share_id, revoke=True)
            except Exception:
                pass
            self.share_id = None

        if self.vm is not None:
            try:
                self.vm.kill()
            except Exception:
                pass
            self.vm = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
