"""
Prime Intellect REPL environment that runs Python code in Prime Sandboxes.

Uses the Prime SDK (https://docs.primeintellect.ai/sandboxes/sdk) for sandbox management.
Follows the same HTTP broker pattern as ModalREPL for LLM communication.
"""

import asyncio
import base64
import json
import textwrap
import threading
import time
from typing import Any

import requests

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import IsolatedEnv

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

# Request queue: {request_id: {"request": {...}, "response": None, "event": Event}}
pending_requests = {}
lock = threading.Lock()

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/enqueue", methods=["POST"])
def enqueue():
    """Called by sandbox code to submit an LLM request and wait for response."""
    data = request.json
    request_id = str(uuid.uuid4())
    event = threading.Event()

    with lock:
        pending_requests[request_id] = {
            "request": data,
            "response": None,
            "event": event,
        }

    # Wait for response (with timeout)
    event.wait(timeout=300)

    with lock:
        entry = pending_requests.pop(request_id, None)

    if entry and entry["response"] is not None:
        return jsonify(entry["response"])
    else:
        return jsonify({"error": "Request timed out"}), 504

@app.route("/pending")
def get_pending():
    """Called by PrimeREPL to get pending requests."""
    with lock:
        pending = [
            {"id": rid, "request": entry["request"]}
            for rid, entry in pending_requests.items()
            if entry["response"] is None
        ]
    return jsonify({"pending": pending})

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
            return jsonify({"status": "ok"})

    return jsonify({"error": "Request not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, threaded=True)
'''
)


# =============================================================================
# Execution Script (runs inside the sandbox for each code block)
# =============================================================================


def _build_exec_script(code: str, broker_port: int = 8080) -> str:
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
    try:
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


class PrimeREPL(IsolatedEnv):
    """
    Prime Intellect REPL environment that runs Python code in Prime Sandboxes.

    Uses Prime's port exposure for LLM communication:
    - Sandbox runs a broker server exposed via sandboxes.expose()
    - PrimeREPL polls the broker for pending LLM requests
    - PrimeREPL forwards requests to the LM handler and posts responses back

    Requires the Prime CLI/SDK to be installed:
        pip install prime
        # or for lightweight SDK only:
        pip install prime-sandboxes

    And authenticated:
        prime login
        # or set PRIME_API_KEY environment variable
    """

    BROKER_PORT = 8888
    DEFAULT_IMAGE = "python:3.11-slim"

    def __init__(
        self,
        name: str = "rlm-sandbox",
        docker_image: str | None = None,
        timeout_minutes: int = 60,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        network_access: bool = True,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        self.name = name
        self.docker_image = docker_image or self.DEFAULT_IMAGE
        self.timeout_minutes = timeout_minutes
        self.lm_handler_address = lm_handler_address
        self.network_access = network_access

        self.sandbox_id: str | None = None
        self.broker_url: str | None = None
        self.broker_exposure_id: str | None = None
        self.poller_thread: threading.Thread | None = None
        self.poller_stop = threading.Event()
        self.pending_llm_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        # Event loop for async operations
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None

        try:
            self.setup()

            if context_payload is not None:
                self.load_context(context_payload)

            if setup_code:
                self.execute_code(setup_code)
        except Exception:
            self.cleanup()
            raise

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop running in a background thread."""
        if self._loop is None or not self._loop.is_running():
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
            self._loop_thread.start()
        return self._loop

    def _run_async(self, coro):
        """Run an async coroutine from sync code."""
        loop = self._get_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=600)  # 10 minute timeout

    async def _async_setup(self):
        """Async setup: create sandbox, start broker, expose port."""
        # Import Prime SDK
        try:
            from prime_sandboxes import AsyncSandboxClient, CreateSandboxRequest
        except ImportError:
            from prime_cli.api.sandbox import AsyncSandboxClient, CreateSandboxRequest

        async with AsyncSandboxClient() as sandboxes:
            # Create the sandbox
            request = CreateSandboxRequest(
                name=self.name,
                docker_image=self.docker_image,
                timeout_minutes=self.timeout_minutes,
                network_access=self.network_access,
            )
            sandbox = await sandboxes.create(request)
            self.sandbox_id = sandbox.id

            # Wait for sandbox to be ready
            await sandboxes.wait_for_creation(self.sandbox_id)

            # Install dependencies for the broker
            await sandboxes.execute_command(
                self.sandbox_id,
                "pip install flask requests dill numpy pandas scipy sympy pyyaml tqdm",
                timeout=300,
            )

            # Write the broker script to the sandbox
            await sandboxes.execute_command(
                self.sandbox_id,
                f"cat > /tmp/broker.py << 'BROKER_EOF'\n{_BROKER_SCRIPT}\nBROKER_EOF",
                timeout=30,
            )

            # Start the broker as a background job
            await sandboxes.execute_command(
                self.sandbox_id,
                "nohup python /tmp/broker.py > /tmp/broker.log 2>&1 &",
                timeout=10,
            )

            # Wait for broker to start
            await asyncio.sleep(2)

            # Expose the broker port
            exposed = await sandboxes.expose(
                self.sandbox_id, port=self.BROKER_PORT, name="rlm-broker"
            )
            self.broker_url = exposed.url
            self.broker_exposure_id = exposed.exposure_id

    def setup(self):
        """Create the Prime sandbox, broker, and start polling."""
        self._run_async(self._async_setup())

        # Start polling thread if we have an LM handler
        if self.lm_handler_address and self.broker_url:
            self.poller_stop.clear()
            self.poller_thread = threading.Thread(target=self._poll_broker, daemon=True)
            self.poller_thread.start()

    def _poll_broker(self):
        """Poll the broker for pending LLM requests and handle them."""
        while not self.poller_stop.is_set():
            try:
                # Get pending requests
                resp = requests.get(
                    f"{self.broker_url}/pending",
                    timeout=5,
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
            request = LMRequest(prompt=prompt, model=model)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return {"error": response.error}

            # Track the call
            with self._calls_lock:
                self.pending_llm_calls.append(response.chat_completion)

            return {"response": response.chat_completion.response}

        elif req_type == "batched":
            prompts = req_data.get("prompts", [])
            responses = send_lm_request_batched(self.lm_handler_address, prompts, model=model)

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

    async def _async_execute_code(self, code: str) -> tuple[str, str]:
        """Async code execution in the sandbox."""
        try:
            from prime_sandboxes import AsyncSandboxClient
        except ImportError:
            from prime_cli.api.sandbox import AsyncSandboxClient

        script = _build_exec_script(code, self.BROKER_PORT)

        # Write script to file and execute (avoids shell escaping issues)
        script_b64 = base64.b64encode(script.encode()).decode()

        async with AsyncSandboxClient() as sandboxes:
            # Write the script
            await sandboxes.execute_command(
                self.sandbox_id,
                f"echo '{script_b64}' | base64 -d > /tmp/exec_script.py",
                timeout=30,
            )

            # Execute the script
            result = await sandboxes.execute_command(
                self.sandbox_id,
                "python /tmp/exec_script.py",
                timeout=300,
            )

            return result.stdout, result.stderr

    def execute_code(self, code: str) -> REPLResult:
        """Execute code in the Prime sandbox and return result."""
        start_time = time.perf_counter()

        # Clear pending LLM calls
        with self._calls_lock:
            self.pending_llm_calls.clear()

        # Execute the code
        stdout, stderr = self._run_async(self._async_execute_code(code))

        # Collect LLM calls made during this execution
        with self._calls_lock:
            pending_calls = self.pending_llm_calls.copy()
            self.pending_llm_calls.clear()

        execution_time = time.perf_counter() - start_time

        # Parse the JSON result
        try:
            lines = stdout.strip().split("\n")
            result_json = lines[-1] if lines else "{}"
            result = json.loads(result_json)

            return REPLResult(
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", "") + (stderr or ""),
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

    async def _async_cleanup(self):
        """Async cleanup: unexpose port and delete sandbox."""
        try:
            from prime_sandboxes import AsyncSandboxClient
        except ImportError:
            from prime_cli.api.sandbox import AsyncSandboxClient

        async with AsyncSandboxClient() as sandboxes:
            # Unexpose the broker port
            if self.sandbox_id and self.broker_exposure_id:
                try:
                    await sandboxes.unexpose(self.sandbox_id, self.broker_exposure_id)
                except Exception:
                    pass

            # Delete the sandbox
            if self.sandbox_id:
                try:
                    await sandboxes.delete(self.sandbox_id)
                except Exception:
                    pass

    def cleanup(self):
        """Terminate the sandbox and stop polling."""
        # Stop the poller thread
        if self.poller_thread is not None:
            self.poller_stop.set()
            self.poller_thread.join(timeout=2)
            self.poller_thread = None

        # Clean up sandbox
        if self.sandbox_id is not None:
            try:
                self._run_async(self._async_cleanup())
            except Exception:
                pass
            self.sandbox_id = None

        # Stop the event loop
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread is not None:
                self._loop_thread.join(timeout=2)
            self._loop = None
            self._loop_thread = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
