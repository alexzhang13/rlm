"""
Docker REPL environment that runs Python code in a Docker container.

Setup:
    docker build -t rlm-sandbox -f Dockerfile.sandbox .

Or use any Python 3.11+ image with: pip install dill requests
"""

import base64
import json
import os
import subprocess
import tempfile
import textwrap
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv


class LLMProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler for LLM requests from the container."""

    lm_handler_address: tuple[str, int] | None = None
    pending_calls: list[RLMChatCompletion] = []
    lock: threading.Lock = threading.Lock()
    depth: int = 1

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))

        if self.path == "/llm_query":
            result = self._handle_single(body)
        elif self.path == "/llm_query_batched":
            result = self._handle_batched(body)
        else:
            self._respond(404, {"error": "Not found"})
            return

        self._respond(200, result)

    def _respond(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _handle_single(self, body: dict) -> dict:
        if not self.lm_handler_address:
            return {"error": "No LM handler configured"}

        request = LMRequest(prompt=body.get("prompt"), model=body.get("model"), depth=self.depth)
        response = send_lm_request(self.lm_handler_address, request)

        if not response.success:
            return {"error": response.error}

        with self.lock:
            self.pending_calls.append(response.chat_completion)

        return {"response": response.chat_completion.response}

    def _handle_batched(self, body: dict) -> dict:
        if not self.lm_handler_address:
            return {"error": "No LM handler configured"}

        prompts = body.get("prompts", [])
        responses = send_lm_request_batched(
            self.lm_handler_address, prompts, model=body.get("model"), depth=self.depth
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


def _build_exec_script(code: str, proxy_port: int, depth: int = 1) -> str:
    """Build execution script for the container."""
    code_b64 = base64.b64encode(code.encode()).decode()

    return textwrap.dedent(
        f'''
import sys, io, json, base64, traceback, os, requests
try:
    import dill
except ImportError:
    import pickle as dill

PROXY = "http://host.docker.internal:{proxy_port}"
STATE = "/workspace/state.dill"

def llm_query(prompt, model=None):
    try:
        r = requests.post(f"{{PROXY}}/llm_query", json={{"prompt": prompt, "model": model, "depth": {depth}}}, timeout=300)
        d = r.json()
        return d.get("response") or f"Error: {{d.get('error')}}"
    except Exception as e:
        return f"Error: {{e}}"

def llm_query_batched(prompts, model=None):
    try:
        r = requests.post(f"{{PROXY}}/llm_query_batched", json={{"prompts": prompts, "model": model, "depth": {depth}}}, timeout=300)
        d = r.json()
        return d.get("responses") or [f"Error: {{d.get('error')}}"] * len(prompts)
    except Exception as e:
        return [f"Error: {{e}}"] * len(prompts)

def load_state():
    if os.path.exists(STATE):
        try:
            with open(STATE, "rb") as f:
                return dill.load(f)
        except:
            pass
    return {{}}

def save_state(s):
    clean = {{k: v for k, v in s.items() if not k.startswith("_")}}
    for k in list(clean.keys()):
        try:
            dill.dumps(clean[k])
        except:
            del clean[k]
    with open(STATE, "wb") as f:
        dill.dump(clean, f)

_locals = load_state()

def FINAL_VAR(name):
    name = name.strip().strip("\\"\\'")
    if name in _locals:
        return str(_locals[name])
    available = [k for k in _locals.keys() if not k.startswith("_")]
    if available:
        return f"Error: Variable '{{name}}' not found. Available variables: {{available}}. You must create and assign a variable BEFORE calling FINAL_VAR on it."
    return f"Error: Variable '{{name}}' not found. No variables have been created yet. You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."

def SHOW_VARS():
    available = {{k: type(v).__name__ for k, v in _locals.items() if not k.startswith("_")}}
    if not available:
        return "No variables created yet. Use ```repl``` blocks to create variables."
    return f"Available variables: {{available}}"

_globals = {{"__builtins__": __builtins__, "__name__": "__main__", "llm_query": llm_query, "llm_query_batched": llm_query_batched, "FINAL_VAR": FINAL_VAR, "SHOW_VARS": SHOW_VARS}}

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
except:
    traceback.print_exc(file=stderr_buf)
finally:
    sys.stdout, sys.stderr = old_stdout, old_stderr

save_state(_locals)
print(json.dumps({{"stdout": stdout_buf.getvalue(), "stderr": stderr_buf.getvalue(), "locals": {{k: repr(v) for k, v in _locals.items() if not k.startswith("_")}}}}, ensure_ascii=False))
'''
    )


class DockerREPL(NonIsolatedEnv):
    """
    Docker REPL - runs Python in a Docker container with LLM support.

    Requires: Docker with a Python 3.11+ image (default: python:3.11-slim).
    """

    def __init__(
        self,
        image: str = "python:3.11-slim",
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        **kwargs,
    ):
        if persistent:
            raise NotImplementedError(
                "Persistent REPLs are currently not supported for environment: DockerREPL"
            )
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        self.image = image
        self.lm_handler_address = lm_handler_address
        self.container_id: str | None = None
        self.proxy_server: HTTPServer | None = None
        self.proxy_thread: threading.Thread | None = None
        self.proxy_port: int = 0
        base_dir = os.environ.get(
            "RLM_DOCKER_WORKSPACE_DIR", os.path.join(os.getcwd(), ".rlm_workspace")
        )
        os.makedirs(base_dir, exist_ok=True)
        self.temp_dir = tempfile.mkdtemp(prefix="docker_repl_", dir=base_dir)
        self.pending_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()

        self.setup()

        if context_payload:
            self.load_context(context_payload)
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Start the proxy server and Docker container."""
        # Start LLM proxy server
        handler = type(
            "Handler",
            (LLMProxyHandler,),
            {
                "lm_handler_address": self.lm_handler_address,
                "pending_calls": self.pending_calls,
                "lock": self._calls_lock,
                "depth": self.depth,
            },
        )
        self.proxy_server = HTTPServer(("127.0.0.1", 0), handler)
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
            raise RuntimeError(f"Failed to start container: {result.stderr}")

        self.container_id = result.stdout.strip()

        # Install dependencies
        subprocess.run(
            ["docker", "exec", self.container_id, "pip", "install", "-q", "dill", "requests"],
            capture_output=True,
        )

    def load_context(self, context_payload: dict | list | str):
        """Load context by writing to a file in the mounted workspace."""
        if isinstance(context_payload, str):
            context_path = os.path.join(self.temp_dir, "context.txt")
            with open(context_path, "w") as f:
                f.write(context_payload)
            self.execute_code(
                "with open('/workspace/context.txt', 'r') as f:\n    context = f.read()"
            )
        else:
            context_path = os.path.join(self.temp_dir, "context.json")
            with open(context_path, "w") as f:
                json.dump(context_payload, f)
            self.execute_code(
                "import json\nwith open('/workspace/context.json', 'r') as f:\n    context = json.load(f)"
            )

    def execute_code(self, code: str) -> REPLResult:
        start = time.perf_counter()

        with self._calls_lock:
            self.pending_calls.clear()

        script = _build_exec_script(code, self.proxy_port, self.depth)
        result = subprocess.run(
            ["docker", "exec", self.container_id, "python", "-c", script],
            capture_output=True,
            text=True,
        )

        with self._calls_lock:
            calls = self.pending_calls.copy()
            self.pending_calls.clear()

        try:
            lines = result.stdout.strip().split("\n")
            data = json.loads(lines[-1]) if lines else {}
            return REPLResult(
                stdout=data.get("stdout", ""),
                stderr=data.get("stderr", "") + result.stderr,
                locals=data.get("locals", {}),
                execution_time=time.perf_counter() - start,
                rlm_calls=calls,
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
        if hasattr(self, "container_id") and self.container_id:
            subprocess.run(["docker", "stop", self.container_id], capture_output=True)
            self.container_id = None
        if hasattr(self, "proxy_server") and self.proxy_server:
            self.proxy_server.shutdown()
            self.proxy_server = None
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
