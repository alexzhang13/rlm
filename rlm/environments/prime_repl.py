"""
Prime Intellect REPL environment that runs Python code in Prime Sandboxes.

Uses the Prime SDK (https://docs.primeintellect.ai/sandboxes/sdk) for sandbox management.
Follows the same HTTP broker pattern as ModalREPL for LLM communication.
"""

import base64
import json
import textwrap
import threading
import time
from typing import Any

import requests
from dotenv import load_dotenv
from prime_sandboxes import (
    APIClient,
    BackgroundJob,
    CreateSandboxRequest,
    SandboxClient,
)

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import IsolatedEnv
from rlm.environments.constants import APT_PACKAGES, PIP_PACKAGES

load_dotenv()

# =============================================================================
# Broker Server Script (runs inside sandbox, handles LLM request queue)
# =============================================================================

_BROKER_SCRIPT = textwrap.dedent(
    '''
import json
import threading
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

# Request queue: {{request_id: {{"request": {{...}}, "response": None, "event": Event}}}}
pending_requests = {{}}
lock = threading.Lock()

@app.route("/health")
def health():
    return jsonify({{"status": "ok"}})

@app.route("/enqueue", methods=["POST"])
def enqueue():
    """Called by sandbox code to submit an LLM request and wait for response."""
    data = request.json
    request_id = str(uuid.uuid4())
    event = threading.Event()

    with lock:
        pending_requests[request_id] = {{
            "request": data,
            "response": None,
            "event": event,
        }}

    # Wait for response (with timeout)
    event.wait(timeout=300)

    with lock:
        entry = pending_requests.pop(request_id, None)

    if entry and entry["response"] is not None:
        return jsonify(entry["response"])
    else:
        return jsonify({{"error": "Request timed out"}}), 504

@app.route("/pending")
def get_pending():
    """Called by PrimeREPL to get pending requests."""
    with lock:
        pending = [
            {{"id": rid, "request": entry["request"]}}
            for rid, entry in pending_requests.items()
            if entry["response"] is None
        ]
    return jsonify({{"pending": pending}})

@app.route("/respond", methods=["POST"])
def respond():
    """Called by PrimeREPL to submit a response."""
    data = request.json
    request_id = data.get("id")
    response = data.get("response")

    with lock:
        if request_id in pending_requests:
            pending_requests[request_id]["response"] = response
            pending_requests[request_id]["event"].set()
            return jsonify({{"status": "ok"}})

    return jsonify({{"error": "Request not found"}}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port={broker_port}, threaded=True)
'''
)


# =============================================================================
# Execution Script (runs inside the sandbox for each code block)
# =============================================================================


def _build_exec_script(code: str, broker_port: int = 8888, depth: int = 1) -> str:
    """
    Build a script that executes code with state persistence.
    LLM queries go through the local broker server.
    """
    code_b64 = base64.b64encode(code.encode()).decode()

    return textwrap.dedent(
        f'''
import sys
import io
import json
import base64
import traceback
import os
import requests

try:
    import dill
except ImportError:
    import pickle as dill

# =============================================================================
# LLM Query Functions (via local broker)
# =============================================================================

BROKER_URL = "http://127.0.0.1:{broker_port}"

def llm_query(prompt, model=None):
    """Query the LM via the broker."""
    try:
        response = requests.post(
            f"{{BROKER_URL}}/enqueue",
            json={{"type": "single", "prompt": prompt, "model": model, "depth": {depth}}},
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
    try:
        response = requests.post(
            f"{{BROKER_URL}}/enqueue",
            json={{"type": "batched", "prompts": prompts, "model": model, "depth": {depth}}},
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

STATE_FILE = "/tmp/rlm_state.dill"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "rb") as f:
                return dill.load(f)
        except:
            pass
    return {{}}

def save_state(state):
    clean_state = {{}}
    for k, v in state.items():
        if k.startswith("_"):
            continue
        try:
            dill.dumps(v)
            clean_state[k] = v
        except:
            pass
    with open(STATE_FILE, "wb") as f:
        dill.dump(clean_state, f)

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
    available = [k for k in _locals.keys() if not k.startswith("_")]
    if available:
        return f"Error: Variable '{{variable_name}}' not found. Available variables: {{available}}. You must create and assign a variable BEFORE calling FINAL_VAR on it."
    return f"Error: Variable '{{variable_name}}' not found. No variables have been created yet. You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."

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


class PrimeREPL(IsolatedEnv):
    """
    Prime Intellect REPL environment that runs Python code in Prime Sandboxes.

    Uses Prime's port exposure for LLM communication:
    - Sandbox runs a broker server exposed via sandboxes.expose()
    - PrimeREPL polls the broker for pending LLM requests
    - PrimeREPL forwards requests to the LM handler and posts responses back
    """

    BROKER_PORT = 8888

    def __init__(
        self,
        name: str = "rlm-sandbox",
        docker_image: str = "python:3.11-slim",
        timeout_minutes: int = 60,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        network_access: bool = True,
        persistent: bool = False,
        depth: int = 1,
        **kwargs: Any,
    ):
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        if persistent:
            raise NotImplementedError(
                "Persistent REPLs are currently not supported for environment: PrimeREPL"
            )

        self.name = name
        self.docker_image = docker_image
        self.timeout_minutes = timeout_minutes
        self.lm_handler_address = lm_handler_address
        self.network_access = network_access

        # Client and sandbox state
        self.client: SandboxClient | None = None
        self.sandbox_id: str | None = None
        self.broker_job: BackgroundJob | None = None
        self.broker_url: str | None = None
        self.broker_exposure_id: str | None = None

        # Polling thread for LLM requests
        self.poller_thread: threading.Thread | None = None
        self.poller_stop = threading.Event()
        self.pending_llm_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)

        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Create the Prime sandbox, broker, and start polling."""
        # Create the client
        self.client = SandboxClient(APIClient())

        # Create the sandbox
        request = CreateSandboxRequest(
            name=self.name,
            docker_image=self.docker_image,
            timeout_minutes=self.timeout_minutes,
            network_access=self.network_access,
        )
        sandbox = self.client.create(request)
        self.sandbox_id = sandbox.id

        # Wait for sandbox to be ready
        self.client.wait_for_creation(self.sandbox_id, max_attempts=self.timeout_minutes * 60)

        # Install apt dependencies
        apt_cmd = "apt-get update && apt-get install -y " + " ".join(APT_PACKAGES)
        self.client.execute_command(self.sandbox_id, apt_cmd)

        # Install pip dependencies
        pip_cmd = "pip install " + " ".join(f'"{pkg}"' for pkg in PIP_PACKAGES)
        self.client.execute_command(self.sandbox_id, pip_cmd)

        # Write the broker script to the sandbox.
        # Unlike Modal's sandbox.exec() which accepts separate args, Prime's
        # start_background_job() takes a shell command string. We write to a file
        # to avoid shell escaping issues with quotes/special chars in the script.
        broker_script = _BROKER_SCRIPT.format(broker_port=self.BROKER_PORT)
        broker_script_b64 = base64.b64encode(broker_script.encode()).decode()
        self.client.execute_command(
            self.sandbox_id,
            f"echo '{broker_script_b64}' | base64 -d > /tmp/broker.py",
        )

        # Start the broker as a background job
        self.broker_job = self.client.start_background_job(
            self.sandbox_id,
            "python /tmp/broker.py",
        )

        # Wait for broker to be ready with health check
        self._wait_for_broker()

        # Expose the broker port
        exposed = self.client.expose(self.sandbox_id, port=self.BROKER_PORT, name="rlm-broker")
        self.broker_url = exposed.url
        self.broker_exposure_id = exposed.exposure_id

        # Start polling thread if we have an LM handler
        if self.lm_handler_address and self.broker_url:
            self.poller_stop.clear()
            self.poller_thread = threading.Thread(target=self._poll_broker, daemon=True)
            self.poller_thread.start()

    def _wait_for_broker(self, max_attempts: int = 30):
        """Wait for the broker to be ready by checking health endpoint."""
        # Use Python to check health (curl may not be installed in slim images)
        health_check_cmd = (
            f'python -c "import requests; '
            f"r = requests.get('http://127.0.0.1:{self.BROKER_PORT}/health', timeout=2); "
            f'print(r.text)"'
        )

        for _ in range(max_attempts):
            time.sleep(1)
            try:
                result = self.client.execute_command(
                    self.sandbox_id,
                    health_check_cmd,
                )
                if "ok" in result.stdout.lower():
                    return
            except Exception:
                pass

        # Get broker logs for debugging by reading log files directly
        error_info = "Broker failed to start."
        if self.broker_job:
            try:
                stdout_result = self.client.execute_command(
                    self.sandbox_id,
                    f"cat {self.broker_job.stdout_log_file} 2>/dev/null || echo 'No stdout log'",
                )
                stderr_result = self.client.execute_command(
                    self.sandbox_id,
                    f"cat {self.broker_job.stderr_log_file} 2>/dev/null || echo 'No stderr log'",
                )
                error_info += f"\nstdout: {stdout_result.stdout}\nstderr: {stderr_result.stdout}"
            except Exception as e:
                error_info += f"\nFailed to read logs: {e}"
        raise RuntimeError(error_info)

    def _poll_broker(self):
        """Poll the broker for pending LLM requests and handle them."""
        while not self.poller_stop.is_set():
            try:
                # Get pending requests
                resp = requests.get(
                    f"{self.broker_url}/pending",
                    timeout=10,
                )
                pending = resp.json().get("pending", [])

                for item in pending:
                    request_id = item["id"]
                    req_data = item["request"]

                    # Handle the request
                    response = self._handle_llm_request(req_data)

                    # Send response back
                    requests.post(
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
            request = LMRequest(prompt=prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return {"error": response.error}

            # Track the call
            with self._calls_lock:
                self.pending_llm_calls.append(response.chat_completion)

            return {"response": response.chat_completion.response}

        elif req_type == "batched":
            prompts = req_data.get("prompts", [])
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
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
        """Execute code in the Prime sandbox and return result."""
        start_time = time.perf_counter()

        # Clear pending LLM calls
        with self._calls_lock:
            self.pending_llm_calls.clear()

        # Build and write the script
        script = _build_exec_script(code, self.BROKER_PORT, self.depth)
        script_b64 = base64.b64encode(script.encode()).decode()
        self.client.execute_command(
            self.sandbox_id,
            f"echo '{script_b64}' | base64 -d > /tmp/exec_script.py",
        )

        # Execute the script
        result = self.client.execute_command(
            self.sandbox_id, "python /tmp/exec_script.py", timeout=60 * 10
        )
        stdout = result.stdout
        stderr = result.stderr

        # Collect LLM calls made during this execution
        with self._calls_lock:
            pending_calls = self.pending_llm_calls.copy()
            self.pending_llm_calls.clear()

        execution_time = time.perf_counter() - start_time

        # Parse the JSON result
        try:
            lines = stdout.strip().split("\n")
            result_json = lines[-1] if lines else "{}"
            parsed = json.loads(result_json)

            return REPLResult(
                stdout=parsed.get("stdout", ""),
                stderr=parsed.get("stderr", "") + stderr,
                locals=parsed.get("locals", {}),
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
        """Terminate the sandbox and stop polling."""
        # Stop the poller thread
        if self.poller_thread is not None:
            self.poller_stop.set()
            self.poller_thread.join(timeout=2)
            self.poller_thread = None

        # Cleanup sandbox resources
        if self.client is None or self.sandbox_id is None:
            return

        # Unexpose the broker port
        if self.broker_exposure_id:
            try:
                self.client.unexpose(self.sandbox_id, self.broker_exposure_id)
            except Exception:
                pass

        # Delete the sandbox
        try:
            self.client.delete(self.sandbox_id)
        except Exception:
            pass

        self.sandbox_id = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
