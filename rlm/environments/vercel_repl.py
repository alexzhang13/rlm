"""
Vercel REPL environment that runs Python code in Vercel Sandboxes.

Uses a lightweight HTTP broker inside the sandbox for LLM communication:
- Sandbox code posts LM requests to the broker
- VercelREPL polls the broker for pending requests
- VercelREPL forwards requests to the host LM handler
- Responses are posted back to the broker
"""

import base64
import json
import textwrap
import threading
import time
from typing import Any

import requests
from vercel.sandbox import Sandbox

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import IsolatedEnv

_BROKER_SCRIPT = textwrap.dedent(
    """
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

pending_requests = {}
lock = threading.Lock()


def _json_response(handler, payload, status=200):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class BrokerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/health":
            _json_response(self, {"status": "ok"})
            return

        if self.path == "/pending":
            with lock:
                pending = [
                    {"id": rid, "request": entry["request"]}
                    for rid, entry in pending_requests.items()
                    if entry["response"] is None
                ]
            _json_response(self, {"pending": pending})
            return

        _json_response(self, {"error": "Not found"}, status=404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            _json_response(self, {"error": "Invalid JSON"}, status=400)
            return

        if self.path == "/enqueue":
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
                _json_response(self, entry["response"])
                return

            _json_response(self, {"error": "Request timed out"}, status=504)
            return

        if self.path == "/respond":
            request_id = data.get("id")
            response = data.get("response")

            with lock:
                if request_id in pending_requests:
                    pending_requests[request_id]["response"] = response
                    pending_requests[request_id]["event"].set()
                    _json_response(self, {"status": "ok"})
                    return

            _json_response(self, {"error": "Request not found"}, status=404)
            return

        _json_response(self, {"error": "Not found"}, status=404)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), BrokerHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
"""
)


def _build_exec_script(code: str, broker_port: int = 8080, depth: int = 1) -> str:
    code_b64 = base64.b64encode(code.encode()).decode()

    return textwrap.dedent(
        f"""
import base64
import io
import json
import os
import sys
import traceback
import urllib.error
import urllib.request

try:
    import dill
except ImportError:
    import pickle as dill

BROKER_URL = "http://127.0.0.1:{broker_port}"
STATE_FILE = "/tmp/rlm_state.dill"


def _post_json(url, payload, timeout=300):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={{"Content-Type": "application/json"}},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            raise


def llm_query(prompt, model=None):
    try:
        data = _post_json(
            f"{{BROKER_URL}}/enqueue",
            {{"type": "single", "prompt": prompt, "model": model, "depth": {depth}}},
        )
        if data.get("error"):
            return f"Error: {{data['error']}}"
        return data.get("response", "Error: No response")
    except Exception as exc:
        return f"Error: LM query failed - {{exc}}"


def llm_query_batched(prompts, model=None):
    try:
        data = _post_json(
            f"{{BROKER_URL}}/enqueue",
            {{"type": "batched", "prompts": prompts, "model": model, "depth": {depth}}},
        )
        if data.get("error"):
            return [f"Error: {{data['error']}}"] * len(prompts)
        return data.get("responses", ["Error: No response"] * len(prompts))
    except Exception as exc:
        return [f"Error: LM query failed - {{exc}}"] * len(prompts)


def rlm_query(prompt, model=None):
    return llm_query(prompt, model=model)


def rlm_query_batched(prompts, model=None):
    return llm_query_batched(prompts, model=model)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as f:
                return dill.load(f)
        except Exception:
            pass
    return {{}}


def save_state(state):
    clean_state = {{}}
    for key, value in state.items():
        if key.startswith("_"):
            continue
        try:
            dill.dumps(value)
            clean_state[key] = value
        except Exception:
            pass
    with open(STATE_FILE, "wb") as f:
        dill.dump(clean_state, f)


def serialize_locals(state):
    result = {{}}
    for key, value in state.items():
        if key.startswith("_"):
            continue
        try:
            result[key] = repr(value)
        except Exception:
            result[key] = f"<{{type(value).__name__}}>"
    return result


_locals = load_state()


def FINAL_VAR(variable_name):
    variable_name = variable_name.strip().strip("\\"\\'")
    if variable_name in _locals:
        return str(_locals[variable_name])
    available = [key for key in _locals.keys() if not key.startswith("_")]
    if available:
        return (
            f"Error: Variable '{{variable_name}}' not found. Available variables: "
            f"{{available}}. You must create and assign a variable BEFORE calling "
            f"FINAL_VAR on it."
        )
    return (
        f"Error: Variable '{{variable_name}}' not found. No variables have been "
        "created yet. You must create and assign a variable in a REPL block "
        "BEFORE calling FINAL_VAR on it."
    )


def SHOW_VARS():
    available = {{key: type(value).__name__ for key, value in _locals.items() if not key.startswith("_")}}
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

print(
    json.dumps(
        {{
            "stdout": stdout_buf.getvalue(),
            "stderr": stderr_buf.getvalue(),
            "locals": serialize_locals(_locals),
        }}
    )
)
"""
    )


class VercelREPL(IsolatedEnv):
    """
    Vercel Sandbox-backed REPL environment.

    Uses the same HTTP broker pattern as the other isolated environments:
    - sandbox code talks to a broker on localhost
    - the host polls the public broker URL
    - requests are forwarded to LMHandler
    """

    BROKER_PORT = 8080
    BROKER_STARTUP_TIMEOUT = 15.0
    WORKDIR = "/vercel/sandbox"
    BROKER_SCRIPT_PATH = f"{WORKDIR}/rlm_broker.py"
    EXEC_SCRIPT_PATH = f"{WORKDIR}/rlm_exec.py"

    def __init__(
        self,
        timeout: int = 600,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        **kwargs,
    ):
        if persistent:
            raise NotImplementedError(
                "Persistent REPLs are currently not supported for environment: VercelREPL"
            )
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        self.timeout = timeout
        self.timeout_ms = int(timeout * 1000)
        self.lm_handler_address = lm_handler_address

        self.sandbox = None
        self.broker_process = None
        self.broker_url: str | None = None
        self.poller_thread: threading.Thread | None = None
        self.poller_stop = threading.Event()
        self.pending_llm_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)

        if setup_code:
            self.execute_code(setup_code)

    def _create_sandbox(self):
        return Sandbox.create(
            runtime="python3.13",
            timeout=self.timeout_ms,
            ports=[self.BROKER_PORT],
        )

    def _run_sandbox_command(
        self, command: str, args: list[str] | None = None, detached: bool = False
    ):
        args = args or []

        run_command = getattr(self.sandbox, "run_command", None)
        if callable(run_command):
            return run_command(command, args, detached=detached)

        run_command = getattr(self.sandbox, "runCommand", None)
        if callable(run_command):
            try:
                return run_command(command, args, detached=detached)
            except TypeError:
                payload = {"cmd": command, "args": args, "detached": detached}
                return run_command(payload)

        raise AttributeError("Sandbox does not expose a supported command runner")

    def _get_broker_url(self) -> str:
        domain_method = getattr(self.sandbox, "domain", None)
        if callable(domain_method):
            domain = domain_method(self.BROKER_PORT)
        else:
            domain_method = getattr(self.sandbox, "get_url", None)
            if not callable(domain_method):
                raise AttributeError("Sandbox does not expose a supported domain resolver")
            domain = domain_method(self.BROKER_PORT)

        if hasattr(domain, "url"):
            value = domain.url
            domain = value() if callable(value) else value

        if not isinstance(domain, str):
            raise TypeError("Sandbox domain resolver returned a non-string URL")

        if domain.startswith("http://") or domain.startswith("https://"):
            return domain.rstrip("/")
        return f"https://{domain}".rstrip("/")

    def _write_remote_file(self, path: str, contents: str) -> None:
        for method_name in ("write_files", "writeFiles"):
            method = getattr(self.sandbox, method_name, None)
            if not callable(method):
                continue
            for payload in ({path: contents}, [{"path": path, "content": contents}]):
                try:
                    method(payload)
                    return
                except TypeError:
                    continue

        for method_name in ("write_file", "writeFile"):
            method = getattr(self.sandbox, method_name, None)
            if not callable(method):
                continue
            method(path, contents)
            return

        writer_script = (
            "import base64, pathlib, sys; "
            "path = pathlib.Path(sys.argv[1]); "
            "path.parent.mkdir(parents=True, exist_ok=True); "
            "path.write_text(base64.b64decode(sys.argv[2]).decode('utf-8'))"
        )
        payload = base64.b64encode(contents.encode()).decode()
        self._run_sandbox_command("python", ["-c", writer_script, path, payload])

    def _read_command_output(self, command_result: Any, stream_name: str) -> str:
        value = getattr(command_result, stream_name, None)
        if callable(value):
            value = value()
        elif hasattr(value, "read"):
            value = value.read()

        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def _wait_for_broker(self):
        deadline = time.perf_counter() + self.BROKER_STARTUP_TIMEOUT
        last_error: Exception | None = None

        while time.perf_counter() < deadline:
            try:
                response = requests.get(f"{self.broker_url}/health", timeout=5)
                if response.ok:
                    return
            except requests.RequestException as exc:
                last_error = exc

            time.sleep(0.25)

        raise RuntimeError("Vercel broker did not become healthy in time") from last_error

    def setup(self):
        """Create the sandbox, start the broker, and begin polling if needed."""
        self.sandbox = self._create_sandbox()
        self._write_remote_file(self.BROKER_SCRIPT_PATH, _BROKER_SCRIPT)
        self.broker_process = self._run_sandbox_command(
            "python", [self.BROKER_SCRIPT_PATH], detached=True
        )
        self.broker_url = self._get_broker_url()
        self._wait_for_broker()

        if self.lm_handler_address:
            self.poller_stop.clear()
            self.poller_thread = threading.Thread(target=self._poll_broker, daemon=True)
            self.poller_thread.start()

    def _poll_broker(self):
        """Poll the broker for pending LLM requests and respond to them."""
        while not self.poller_stop.is_set():
            try:
                response = requests.get(f"{self.broker_url}/pending", timeout=5)
                pending = response.json().get("pending", [])

                for item in pending:
                    request_id = item["id"]
                    req_data = item["request"]
                    broker_response = self._handle_llm_request(req_data)
                    requests.post(
                        f"{self.broker_url}/respond",
                        json={"id": request_id, "response": broker_response},
                        timeout=10,
                    )
            except requests.exceptions.RequestException:
                pass
            except Exception:
                pass

            time.sleep(0.1)

    def _handle_llm_request(self, req_data: dict[str, Any]) -> dict[str, Any]:
        """Handle a brokered LLM request from the sandbox."""
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
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                    continue

                with self._calls_lock:
                    self.pending_llm_calls.append(response.chat_completion)
                results.append(response.chat_completion.response)

            return {"responses": results}

        return {"error": "Unknown request type"}

    def load_context(self, context_payload: dict | list | str):
        """Load context into the sandbox environment."""
        if isinstance(context_payload, str):
            escaped = context_payload.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
            context_code = f'context = """{escaped}"""'
        else:
            context_json = json.dumps(context_payload)
            escaped_json = context_json.replace("\\", "\\\\").replace("'", "\\'")
            context_code = f"import json; context = json.loads('{escaped_json}')"

        self.execute_code(context_code)

    def execute_code(self, code: str) -> REPLResult:
        """Execute code inside the Vercel sandbox and return a REPLResult."""
        start_time = time.perf_counter()

        with self._calls_lock:
            self.pending_llm_calls.clear()

        script = _build_exec_script(code, self.BROKER_PORT, self.depth)
        self._write_remote_file(self.EXEC_SCRIPT_PATH, script)
        process = self._run_sandbox_command("python", [self.EXEC_SCRIPT_PATH])

        stdout = self._read_command_output(process, "stdout")
        stderr = self._read_command_output(process, "stderr")

        with self._calls_lock:
            pending_calls = self.pending_llm_calls.copy()
            self.pending_llm_calls.clear()

        execution_time = time.perf_counter() - start_time

        try:
            lines = stdout.strip().split("\n")
            result_json = lines[-1] if lines else "{}"
            result = json.loads(result_json)

            return REPLResult(
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", "") + stderr,
                locals=result.get("locals", {}),
                execution_time=execution_time,
                rlm_calls=pending_calls,
            )
        except json.JSONDecodeError:
            return REPLResult(
                stdout=stdout,
                stderr=stderr or "Failed to parse execution result",
                locals={},
                execution_time=execution_time,
                rlm_calls=pending_calls,
            )

    def cleanup(self):
        """Stop the poller thread and terminate the sandbox."""
        poller_thread = getattr(self, "poller_thread", None)
        if poller_thread is not None:
            self.poller_stop.set()
            poller_thread.join(timeout=2)
            self.poller_thread = None

        sandbox = getattr(self, "sandbox", None)
        if sandbox is not None:
            stop_method = getattr(sandbox, "stop", None)
            if callable(stop_method):
                try:
                    stop_method()
                except Exception:
                    pass
            else:
                terminate_method = getattr(sandbox, "terminate", None)
                if callable(terminate_method):
                    try:
                        terminate_method()
                    except Exception:
                        pass
            self.sandbox = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
