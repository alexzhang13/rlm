"""
Kubernetes REPL environment that runs Python code in a Kubernetes pod.

Each environment creates one pod and runs every code block with an exec into it,
the same way DockerREPL uses ``docker exec``. Code in the pod can call:

    - llm_query / llm_query_batched : single LM completions (no recursion)
    - rlm_query  / rlm_query_batched : recursive RLM sub-calls (spawns a child
                                       RLM on the host when max_depth > 1)
    - SHOW_VARS                      : list REPL variables
    - custom tools                  : user-supplied functions/data
    - answer                        : answer["ready"] = True signals completion

LM requests come back to the host as JSON lines over the same exec stream, so the
pod needs no network route to the host. Any cluster in your kubeconfig works
(kind, minikube, or a remote cluster), as does running the RLM inside a cluster.

Setup:
    pip install 'rlms[kubernetes]'
    kind create cluster
"""

import base64
import json
import textwrap
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from kubernetes.stream.ws_client import ERROR_CHANNEL, STDERR_CHANNEL, STDOUT_CHANNEL, WSClient

from rlm.core.comms_utils import LMRequest, LMResponse, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import IsolatedEnv, validate_custom_tools
from rlm.environments.docker_repl import _build_custom_tools_code

DEFAULT_RESOURCES = {
    "requests": {"cpu": "250m", "memory": "512Mi"},
    "limits": {"cpu": "1", "memory": "2Gi"},
}

# Reads the base64-encoded exec script from the first line of stdin and runs it.
_BOOTSTRAP = "import base64, sys; exec(base64.b64decode(sys.stdin.readline()))"

# The API server drops websocket messages over 32 MiB, so stdin is written in chunks.
_STDIN_CHUNK_SIZE = 1 << 20


def _build_exec_script(code: str, custom_tools: dict[str, Any] | None = None) -> str:
    """Build the per-cell execution script that runs inside the pod."""
    code_b64 = base64.b64encode(code.encode()).decode()
    custom_tools_code = _build_custom_tools_code(custom_tools)

    return textwrap.dedent(
        f'''
import sys, io, json, base64, traceback, os, threading
try:
    import dill
except ImportError:
    import pickle as dill

STATE = "/workspace/state.dill"

# stdin/stdout of the exec stream carry LM requests and the result. Keep private
# copies and repoint fds 0 and 1 so executed code and its subprocesses can't
# touch them (anything written to fd 1 shows up in stderr).
_proto_in = os.fdopen(os.dup(0), "r")
_proto_out = os.fdopen(os.dup(1), "w")
os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
os.dup2(2, 1)
_proto_lock = threading.Lock()

def _post(path, payload):
    with _proto_lock:
        _proto_out.write(json.dumps({{"path": path, "body": payload}}) + "\\n")
        _proto_out.flush()
        return json.loads(_proto_in.readline())

def llm_query(prompt, model=None):
    try:
        d = _post("/llm_query", {{"prompt": prompt, "model": model}})
        return d.get("response") or f"Error: {{d.get('error')}}"
    except Exception as e:
        return f"Error: {{e}}"

def llm_query_batched(prompts, model=None):
    try:
        d = _post("/llm_query_batched", {{"prompts": prompts, "model": model}})
        return d.get("responses") or [f"Error: {{d.get('error')}}"] * len(prompts)
    except Exception as e:
        return [f"Error: {{e}}"] * len(prompts)

def rlm_query(prompt, model=None):
    try:
        d = _post("/rlm_query", {{"prompt": prompt, "model": model}})
        return d.get("response") or f"Error: {{d.get('error')}}"
    except Exception as e:
        return f"Error: {{e}}"

def rlm_query_batched(prompts, model=None):
    try:
        d = _post("/rlm_query_batched", {{"prompts": prompts, "model": model}})
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
    traceback.print_exc(file=stderr_buf)
finally:
    sys.stdout, sys.stderr = old_stdout, old_stderr

# Restore the context alias if overwritten by executed code
if "context_0" in _locals:
    _locals["context"] = _locals["context_0"]

save_state(_locals)
_ans = _locals.get("answer") if isinstance(_locals.get("answer"), dict) else None
_final = None
if _ans is not None and _ans.get("ready"):
    _final = str(_ans.get("content", ""))
_proto_out.write(json.dumps({{
    "stdout": stdout_buf.getvalue(),
    "stderr": stderr_buf.getvalue(),
    "locals": {{k: repr(v) for k, v in _locals.items() if not k.startswith("_")}},
    "final_answer": _final,
}}) + "\\n")
_proto_out.flush()
'''
    )


def _write_line(ws: WSClient, line: str):
    """Write one line to the exec stream's stdin."""
    data = line + "\n"
    for i in range(0, len(data), _STDIN_CHUNK_SIZE):
        ws.write_stdin(data[i : i + _STDIN_CHUNK_SIZE])


class KubernetesREPL(IsolatedEnv):
    """
    Kubernetes REPL - runs Python in a dedicated pod with LLM and recursive RLM support.

    Requires: a cluster reachable through your kubeconfig (or in-cluster config) and
    a Python 3.11+ image (default: python:3.11-slim).

    The pod runs as a non-root user with all capabilities dropped, no service account
    token and CPU/memory limits, so it is admitted under the "restricted" Pod Security
    Standard. cleanup() deletes it, and Kubernetes stops it after ``timeout`` seconds
    if cleanup never runs.
    """

    def __init__(
        self,
        image: str = "python:3.11-slim",
        namespace: str = "default",
        resources: dict[str, dict[str, str]] | None = None,
        timeout: int = 600,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        subcall_fn: Callable[[str, str | None], RLMChatCompletion] | None = None,
        custom_tools: dict[str, Any] | None = None,
        **kwargs,
    ):
        """
        Args:
            image: Container image with Python 3.11+.
            namespace: Namespace to create the pod in.
            resources: Container resources (requests/limits), defaults to DEFAULT_RESOURCES.
            timeout: Pod lifetime in seconds (activeDeadlineSeconds), also the startup timeout.
            lm_handler_address: (host, port) tuple for the LM Handler server.
            context_payload: Initial context to load into the environment.
            setup_code: Optional code to run during setup.
            persistent: Whether to persist state across completion() calls (not yet supported).
            depth: Depth level for LLM request routing (used by LMHandler).
            subcall_fn: Callback for rlm_query. Without it, rlm_query falls back to llm_query.
            custom_tools: Python code strings or JSON-serializable values to inject.
            **kwargs: Additional arguments passed to base class.
        """
        if persistent:
            raise NotImplementedError(
                "Persistent REPLs are currently not supported for environment: KubernetesREPL"
            )
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        self.image = image
        self.namespace = namespace
        self.resources = resources or DEFAULT_RESOURCES
        self.timeout = timeout
        self.lm_handler_address = lm_handler_address
        self.subcall_fn = subcall_fn
        self.custom_tools = custom_tools or {}
        validate_custom_tools(self.custom_tools)

        self.pod_name: str | None = None
        self.pending_calls: list[RLMChatCompletion] = []

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Create the pod, wait for it to run, and install dill into it."""
        configuration = client.Configuration()
        config.load_config(client_configuration=configuration)
        self.api = client.CoreV1Api(client.ApiClient(configuration))

        pod = self.api.create_namespaced_pod(
            self.namespace,
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "generateName": "rlm-repl-",
                    "labels": {"app.kubernetes.io/managed-by": "rlm"},
                },
                "spec": {
                    "restartPolicy": "Never",
                    "activeDeadlineSeconds": self.timeout,
                    "automountServiceAccountToken": False,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 1000,
                        "runAsGroup": 1000,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": "repl",
                            "image": self.image,
                            "command": ["sleep", "infinity"],
                            "workingDir": "/workspace",
                            "env": [
                                {"name": "HOME", "value": "/workspace"},
                                {"name": "PIP_DISABLE_PIP_VERSION_CHECK", "value": "1"},
                            ],
                            "resources": self.resources,
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "capabilities": {"drop": ["ALL"]},
                            },
                            "volumeMounts": [{"name": "workspace", "mountPath": "/workspace"}],
                        }
                    ],
                    "volumes": [{"name": "workspace", "emptyDir": {}}],
                },
            },
        )
        self.pod_name = pod.metadata.name

        try:
            self._wait_until_running()
        except Exception:
            self.cleanup()
            raise

        # dill lets functions and classes survive between code blocks. If it can't be
        # installed (e.g. no egress to PyPI), the exec script falls back to pickle.
        stream(
            self.api.connect_get_namespaced_pod_exec,
            self.pod_name,
            self.namespace,
            command=["python3", "-m", "pip", "install", "-q", "--user", "--retries", "0", "dill"],
            stdout=True,
            stderr=True,
            stdin=False,
            tty=False,
        )

    def _wait_until_running(self):
        deadline = time.monotonic() + self.timeout
        while True:
            status = self.api.read_namespaced_pod(self.pod_name, self.namespace).status
            if status.phase == "Running":
                return
            for container in status.container_statuses or []:
                waiting = container.state.waiting
                if waiting and waiting.reason not in ("ContainerCreating", "PodInitializing"):
                    raise RuntimeError(
                        f"Pod {self.pod_name} failed to start: {waiting.reason}: {waiting.message}"
                    )
            if status.phase != "Pending":
                raise RuntimeError(f"Pod {self.pod_name} failed to start: {status.reason}")
            if time.monotonic() > deadline:
                conditions = [c.message for c in status.conditions or [] if c.message]
                raise TimeoutError(
                    f"Pod {self.pod_name} not running after {self.timeout}s: {conditions}"
                )
            time.sleep(0.5)

    def _exec(self, script: str) -> tuple[dict | None, str]:
        """Run a script in the pod, serving its LM requests over the exec stream.

        Returns the script's result message (None if it exited without one) and
        whatever the process wrote to stderr.
        """
        ws = stream(
            self.api.connect_get_namespaced_pod_exec,
            self.pod_name,
            self.namespace,
            command=["python3", "-c", _BOOTSTRAP],
            stdin=True,
            stdout=True,
            stderr=True,
            tty=False,
            _preload_content=False,
        )
        result = None
        stdout: list[bytes] = []
        stderr: list[bytes] = []
        status = b""
        try:
            _write_line(ws, base64.b64encode(script.encode()).decode())
            # Read frames off the socket directly: WSClient's channel buffers grow
            # by string concatenation, which is quadratic for large outputs.
            while frame := ws.sock.recv():
                channel, data = frame[0], frame[1:]
                if channel == STDERR_CHANNEL:
                    stderr.append(data)
                elif channel == ERROR_CHANNEL:
                    status = data
                elif channel == STDOUT_CHANNEL:
                    stdout.append(data)
                    if b"\n" not in data:
                        continue
                    line, _, rest = b"".join(stdout).partition(b"\n")
                    stdout = [rest]
                    message = json.loads(line)
                    if "path" not in message:
                        result = message
                        continue
                    response = self._handle_request(message["path"], message["body"])
                    _write_line(ws, json.dumps(response))
        finally:
            ws.close()

        errors = b"".join(stderr).decode(errors="replace")
        if result is None and status:
            # e.g. "command terminated with non-zero exit code: ... exit code 137" (OOMKilled)
            errors += json.loads(status).get("message", "")
        return result, errors

    def _handle_request(self, path: str, body: dict) -> dict:
        """Answer an llm_query / rlm_query request with DockerREPL's proxy semantics."""
        batched = path.endswith("_batched")
        prompts = body["prompts"] if batched else [body["prompt"]]
        model = body.get("model")

        if path.startswith("/rlm_query") and self.subcall_fn is not None:
            responses = self._rlm_query_batched(prompts, model)
        elif self.lm_handler_address is None:
            return {"error": "No LM handler configured"}
        elif batched:
            responses = [
                self._track(r)
                for r in send_lm_request_batched(
                    self.lm_handler_address, prompts, model=model, depth=self.depth
                )
            ]
        else:
            request = LMRequest(prompt=prompts[0], model=model, depth=self.depth)
            responses = [self._track(send_lm_request(self.lm_handler_address, request))]

        return {"responses": responses} if batched else {"response": responses[0]}

    def _track(self, response: LMResponse) -> str:
        if not response.success:
            return f"Error: {response.error}"
        self.pending_calls.append(response.chat_completion)
        return response.chat_completion.response

    def _rlm_query_batched(self, prompts: list[str], model: str | None) -> list[str]:
        """Run child RLMs, at most max_concurrent_subcalls at a time, in prompt order."""

        def run(prompt: str) -> tuple[RLMChatCompletion | None, str]:
            try:
                completion = self.subcall_fn(prompt, model)
                return completion, completion.response
            except Exception as e:
                return None, f"Error: RLM query failed - {e}"

        max_workers = max(1, min(self.max_concurrent_subcalls, len(prompts)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(run, prompts))
        self.pending_calls.extend(completion for completion, _ in results if completion)
        return [response for _, response in results]

    def load_context(self, context_payload: dict | list | str):
        """Load context as ``context_0`` (with ``context`` aliased to it)."""
        payload_b64 = base64.b64encode(json.dumps(context_payload).encode()).decode()
        self.execute_code(
            f"import base64, json\ncontext_0 = json.loads(base64.b64decode({payload_b64!r}))\n"
            "context = context_0"
        )

    def execute_code(self, code: str) -> REPLResult:
        start = time.perf_counter()
        self.pending_calls = []

        result, stderr = self._exec(_build_exec_script(code, self.custom_tools))

        if result is None:
            return REPLResult(
                stdout="",
                stderr=stderr or "Execution ended without a result",
                locals={},
                execution_time=time.perf_counter() - start,
                rlm_calls=self.pending_calls,
            )
        return REPLResult(
            stdout=result["stdout"],
            stderr=result["stderr"] + stderr,
            locals=result["locals"],
            execution_time=time.perf_counter() - start,
            rlm_calls=self.pending_calls,
            final_answer=result["final_answer"],
        )

    def cleanup(self):
        """Delete the pod. Idempotent."""
        if getattr(self, "pod_name", None) is None:
            return
        try:
            self.api.delete_namespaced_pod(self.pod_name, self.namespace, grace_period_seconds=0)
        except ApiException as e:
            if e.status != 404:
                raise
        self.pod_name = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()
