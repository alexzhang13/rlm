"""
Cloudflare Workers Sandbox REPL environment.

Uses Cloudflare's Sandbox SDK to run Python code in isolated containers.
Unlike Modal, Cloudflare Sandboxes are accessed via HTTP API rather than a Python SDK.
"""

import base64
import json
import os
import textwrap
import threading
import time
from typing import Any

import requests

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import IsolatedEnv


# =============================================================================
# Execution Script (runs inside the Cloudflare sandbox)
# =============================================================================


def _build_exec_script(code: str, broker_url: str | None = None) -> str:
    """
    Build a script that executes code with state persistence.
    If broker_url is provided, LLM queries go through the broker.
    """
    code_b64 = base64.b64encode(code.encode()).decode()
    broker_url_str = f'"{broker_url}"' if broker_url else "None"

    return textwrap.dedent(
        f'''
import sys
import io
import json
import base64
import traceback
import os

try:
    import dill
except ImportError:
    try:
        import pickle as dill
    except ImportError:
        dill = None

# =============================================================================
# LLM Query Functions (via external broker if configured)
# =============================================================================

BROKER_URL = {broker_url_str}

def llm_query(prompt, model=None):
    """Query the LM via the broker (if configured)."""
    if BROKER_URL is None:
        return "Error: LLM broker not configured"
    try:
        import requests
        response = requests.post(
            f"{{BROKER_URL}}/enqueue",
            json={{"type": "single", "prompt": prompt, "model": model}},
            timeout=300,
        )
        data = response.json()
        if data.get("error"):
            return f"Error: {{data['error']}}"
        return data.get("response", "Error: No response")
    except Exception as e:
        return f"Error: LM query failed - {{e}}"


def llm_query_batched(prompts, model=None):
    """Query the LM with multiple prompts."""
    if BROKER_URL is None:
        return ["Error: LLM broker not configured"] * len(prompts)
    try:
        import requests
        response = requests.post(
            f"{{BROKER_URL}}/enqueue",
            json={{"type": "batched", "prompts": prompts, "model": model}},
            timeout=300,
        )
        data = response.json()
        if data.get("error"):
            return [f"Error: {{data['error']}}"] * len(prompts)
        return data.get("responses", ["Error: No response"] * len(prompts))
    except Exception as e:
        return [f"Error: LM query failed - {{e}}"] * len(prompts)


# =============================================================================
# State Management
# =============================================================================

STATE_FILE = "/tmp/rlm_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {{}}

def save_state(state):
    clean_state = {{}}
    for k, v in state.items():
        if k.startswith("_"):
            continue
        try:
            json.dumps(v)  # Test if JSON serializable
            clean_state[k] = v
        except:
            try:
                clean_state[k] = repr(v)
            except:
                pass
    with open(STATE_FILE, "w") as f:
        json.dump(clean_state, f)

def serialize_locals(state):
    result = {{}}
    for k, v in state.items():
        if k.startswith("_"):
            continue
        try:
            result[k] = repr(v)
        except:
            result[k] = f"<{{type(v).__name__}}>"
    return result

# =============================================================================
# Execution
# =============================================================================

_locals = load_state()

def FINAL_VAR(variable_name):
    variable_name = variable_name.strip().strip("\\"\\'")
    if variable_name in _locals:
        return str(_locals[variable_name])
    return f"Error: Variable '{{variable_name}}' not found"

_globals = {{
    "__builtins__": __builtins__,
    "__name__": "__main__",
    "llm_query": llm_query,
    "llm_query_batched": llm_query_batched,
    "FINAL_VAR": FINAL_VAR,
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
except Exception as e:
    traceback.print_exc(file=stderr_buf)
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

save_state(_locals)

result = {{
    "stdout": stdout_buf.getvalue(),
    "stderr": stderr_buf.getvalue(),
    "locals": serialize_locals(_locals),
}}
print(json.dumps(result))
'''
    )


class CloudflareREPL(IsolatedEnv):
    """
    Cloudflare Workers Sandbox REPL environment.

    Runs Python code in Cloudflare's container-based Sandbox SDK.
    Requires a running Cloudflare Worker with Sandbox SDK configured.

    Configuration:
    - worker_url: URL of the Cloudflare Worker (or set RLM_CF_WORKER_URL env var)
    - auth_token: Bearer token for the Worker (or set RLM_CF_AUTH_TOKEN env var)
    - sandbox_id: Optional sandbox ID for session persistence (auto-generated if not provided)

    Environment variables:
    - RLM_CF_WORKER_URL: Default worker URL if not passed to constructor
    - RLM_CF_AUTH_TOKEN: Default auth token if not passed to constructor

    The Worker should expose these endpoints:
    - POST /sandbox/exec - Execute a command in the sandbox
    - POST /sandbox/write - Write a file to the sandbox
    - GET /sandbox/read - Read a file from the sandbox
    """

    def __init__(
        self,
        worker_url: str | None = None,
        auth_token: str | None = None,
        sandbox_id: str | None = None,
        timeout: int = 300,
        lm_handler_address: tuple[str, int] | None = None,
        broker_url: str | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Support env vars for worker URL and auth token
        self.worker_url = (worker_url or os.environ.get("RLM_CF_WORKER_URL", "")).rstrip("/")
        if not self.worker_url:
            raise ValueError(
                "worker_url must be provided or RLM_CF_WORKER_URL environment variable must be set"
            )
        self.auth_token = auth_token if auth_token is not None else os.environ.get("RLM_CF_AUTH_TOKEN", "")
        self.sandbox_id = sandbox_id or f"rlm-{int(time.time())}"
        self.timeout = timeout
        self.lm_handler_address = lm_handler_address
        self.broker_url = broker_url

        # LLM call tracking
        self.pending_llm_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        # Polling thread for LLM requests (if broker is configured)
        self.poller_thread: threading.Thread | None = None
        self.poller_stop = threading.Event()

        # Session for HTTP requests
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        })

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)

        if setup_code:
            self.execute_code(setup_code)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Cloudflare Worker."""
        url = f"{self.worker_url}{endpoint}"
        timeout = timeout or self.timeout

        try:
            if method.upper() == "GET":
                resp = self._session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                resp = self._session.post(url, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False}

    def setup(self):
        """Initialize the Cloudflare sandbox connection."""
        # Verify connection by running a simple command
        result = self._exec_command("python3 --version")
        if "error" in result and not result.get("stdout"):
            raise RuntimeError(
                f"Failed to connect to Cloudflare Worker: {result.get('error')}"
            )

        # Start LLM polling if broker is configured
        if self.broker_url and self.lm_handler_address:
            self.poller_stop.clear()
            self.poller_thread = threading.Thread(target=self._poll_broker, daemon=True)
            self.poller_thread.start()

    def _exec_command(self, cmd: str) -> dict[str, Any]:
        """Execute a shell command in the sandbox."""
        return self._request(
            "POST",
            "/sandbox/exec",
            json_data={
                "sandbox_id": self.sandbox_id,
                "command": cmd,
            },
        )

    def _write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write a file to the sandbox."""
        return self._request(
            "POST",
            "/sandbox/write",
            json_data={
                "sandbox_id": self.sandbox_id,
                "path": path,
                "content": content,
            },
        )

    def _read_file(self, path: str) -> dict[str, Any]:
        """Read a file from the sandbox."""
        return self._request(
            "GET",
            f"/sandbox/read?sandbox_id={self.sandbox_id}&path={path}",
        )

    def _poll_broker(self):
        """Poll the broker for pending LLM requests and handle them."""
        while not self.poller_stop.is_set():
            try:
                resp = self._session.get(
                    f"{self.broker_url}/pending",
                    timeout=5,
                )
                pending = resp.json().get("pending", [])

                for item in pending:
                    request_id = item["id"]
                    req_data = item["request"]

                    response = self._handle_llm_request(req_data)

                    self._session.post(
                        f"{self.broker_url}/respond",
                        json={"id": request_id, "response": response},
                        timeout=10,
                    )

            except requests.exceptions.RequestException:
                pass
            except Exception:
                pass

            time.sleep(0.1)

    def _handle_llm_request(self, req_data: dict) -> dict:
        """Handle an LLM request from the sandbox."""
        req_type = req_data.get("type")
        model = req_data.get("model")

        if req_type == "single":
            prompt = req_data.get("prompt")
            request = LMRequest(prompt=prompt, model=model)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return {"error": response.error}

            with self._calls_lock:
                self.pending_llm_calls.append(response.chat_completion)

            return {"response": response.chat_completion.response}

        elif req_type == "batched":
            prompts = req_data.get("prompts", [])
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model
            )

            results = []
            for resp in responses:
                if not resp.success:
                    results.append(f"Error: {resp.error}")
                else:
                    with self._calls_lock:
                        self.pending_llm_calls.append(resp.chat_completion)
                    results.append(resp.chat_completion.response)

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
        """Execute Python code in the Cloudflare sandbox and return result."""
        start_time = time.perf_counter()

        # Clear pending LLM calls
        with self._calls_lock:
            self.pending_llm_calls.clear()

        # Build the execution script
        script = _build_exec_script(code, self.broker_url)

        # Write script to temp file and execute
        script_path = "/tmp/rlm_exec.py"
        write_result = self._write_file(script_path, script)
        if "error" in write_result and not write_result.get("success", True):
            return REPLResult(
                stdout="",
                stderr=f"Failed to write script: {write_result.get('error')}",
                locals={},
                execution_time=time.perf_counter() - start_time,
                rlm_calls=[],
            )

        # Execute the script
        exec_result = self._exec_command(f"python3 {script_path}")

        # Collect LLM calls made during this execution
        with self._calls_lock:
            pending_calls = self.pending_llm_calls.copy()
            self.pending_llm_calls.clear()

        execution_time = time.perf_counter() - start_time

        stdout = exec_result.get("stdout", "")
        stderr = exec_result.get("stderr", "")

        # Parse the JSON result from stdout
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
        """Stop polling and clean up resources."""
        if self.poller_thread is not None:
            self.poller_stop.set()
            self.poller_thread.join(timeout=2)
            self.poller_thread = None

        self._session.close()

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
