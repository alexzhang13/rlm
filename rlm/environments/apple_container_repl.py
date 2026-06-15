import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from http.server import HTTPServer

from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv
from rlm.environments.docker_repl import LLMProxyHandler, _build_exec_script

REQUIRED_PYTHON_PACKAGES = ("dill", "requests")
DEPENDENCY_CHECK_CODE = """
import importlib.util
import sys

missing = [name for name in sys.argv[1:] if importlib.util.find_spec(name) is None]
print(",".join(missing))
raise SystemExit(1 if missing else 0)
""".strip()


class AppleContainerRuntime:
    """Thin wrapper around Apple's `container` CLI."""

    def __init__(self, container_cli: str = "container", timeout: float = 300.0):
        self.container_cli = container_cli
        self.timeout = timeout
        self._resolved_cli: str | None = None

    def _command(self) -> str:
        if self._resolved_cli is not None:
            return self._resolved_cli

        has_path_separator = os.path.sep in self.container_cli or (
            os.path.altsep is not None and os.path.altsep in self.container_cli
        )
        if has_path_separator:
            if os.access(self.container_cli, os.X_OK):
                self._resolved_cli = self.container_cli
                return self.container_cli
            raise RuntimeError(f"Apple container CLI is not executable: {self.container_cli}")

        command = shutil.which(self.container_cli)
        if command is None:
            raise RuntimeError(
                f"Apple container CLI not found: {self.container_cli}. "
                "Install Apple's `container` tool or pass container_cli=..."
            )
        self._resolved_cli = command
        return command

    def run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self._command(), *args],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

    def start(
        self,
        image: str,
        name: str,
        host_workspace: str,
        container_workspace: str,
        cpus: int | None = None,
        memory: str | None = None,
        platform: str | None = None,
        extra_run_args: list[str] | None = None,
    ) -> str:
        args = [
            "run",
            "-d",
            "--rm",
            "--name",
            name,
            "-v",
            f"{host_workspace}:{container_workspace}",
            "-w",
            container_workspace,
        ]
        if cpus is not None:
            args.extend(["--cpus", str(cpus)])
        if memory is not None:
            args.extend(["--memory", memory])
        if platform is not None:
            args.extend(["--platform", platform])
        args.extend(extra_run_args or [])
        args.extend([image, "tail", "-f", "/dev/null"])

        result = self.run(args)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start Apple container: {result.stderr}")
        return result.stdout.strip() or name

    def exec(
        self,
        container_id: str,
        *command: str,
        workdir: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        args = ["exec"]
        if workdir is not None:
            args.extend(["-w", workdir])
        args.extend([container_id, *command])
        return self.run(args)

    def stop(self, container_id: str) -> None:
        self.run(["stop", container_id])


class AppleContainerREPL(NonIsolatedEnv):
    """
    Run Python REPL cells in Apple's `container` CLI.

    The environment mirrors DockerREPL's protocol: generated code runs in an
    isolated Python image, while `llm_query` and `llm_query_batched` call back to
    the host RLM process through a small HTTP proxy.
    """

    def __init__(
        self,
        image: str = "python:3.11-slim",
        container_cli: str = "container",
        container_workspace: str = "/workspace",
        host_proxy_name: str | None = None,
        proxy_bind_host: str = "127.0.0.1",
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        cpus: int | None = None,
        memory: str | None = None,
        platform: str | None = None,
        extra_run_args: list[str] | None = None,
        install_dependencies: bool = True,
        runtime: AppleContainerRuntime | None = None,
        **kwargs,
    ):
        if persistent:
            raise NotImplementedError(
                "Persistent REPLs are currently not supported for AppleContainerREPL"
            )
        super().__init__(persistent=persistent, depth=depth, **kwargs)
        self.image = image
        self.container_workspace = container_workspace
        self.host_proxy_name = host_proxy_name or os.environ.get(
            "RLM_APPLE_CONTAINER_PROXY_HOST",
            "host.container.internal",
        )
        self.proxy_bind_host = proxy_bind_host
        self.lm_handler_address = lm_handler_address
        self.cpus = cpus
        self.memory = memory
        self.platform = platform
        self.extra_run_args = extra_run_args or []
        self.install_dependencies = install_dependencies
        self.runtime = runtime or AppleContainerRuntime(container_cli=container_cli)
        self.container_id: str | None = None
        self.container_name = f"rlm-apple-{uuid.uuid4().hex[:12]}"
        self.proxy_server: HTTPServer | None = None
        self.proxy_thread: threading.Thread | None = None
        self.proxy_port = 0
        self.pending_calls: list[RLMChatCompletion] = []
        self._calls_lock = threading.Lock()
        base_dir = os.environ.get(
            "RLM_APPLE_CONTAINER_WORKSPACE_DIR",
            os.path.join(os.getcwd(), ".rlm_workspace"),
        )
        os.makedirs(base_dir, exist_ok=True)
        self.temp_dir = tempfile.mkdtemp(prefix="apple_container_repl_", dir=base_dir)

        try:
            self.setup()
            if context_payload is not None:
                self.load_context(context_payload)
            if setup_code:
                self.execute_code(setup_code)
        except Exception:
            try:
                self.cleanup()
            except Exception:
                pass
            raise

    def setup(self):
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
        self.proxy_server = HTTPServer((self.proxy_bind_host, 0), handler)
        self.proxy_port = self.proxy_server.server_address[1]
        self.proxy_thread = threading.Thread(target=self.proxy_server.serve_forever, daemon=True)
        self.proxy_thread.start()

        self.container_id = self.runtime.start(
            image=self.image,
            name=self.container_name,
            host_workspace=self.temp_dir,
            container_workspace=self.container_workspace,
            cpus=self.cpus,
            memory=self.memory,
            platform=self.platform,
            extra_run_args=self.extra_run_args,
        )
        if self.install_dependencies:
            self._ensure_dependencies()

    def _ensure_dependencies(self):
        if self.container_id is None:
            raise RuntimeError("Apple container is not running.")

        probe = self.runtime.exec(
            self.container_id,
            "python",
            "-c",
            DEPENDENCY_CHECK_CODE,
            *REQUIRED_PYTHON_PACKAGES,
            workdir=self.container_workspace,
        )
        if probe.returncode == 0:
            return

        missing = [pkg for pkg in probe.stdout.strip().split(",") if pkg]
        packages = missing or list(REQUIRED_PYTHON_PACKAGES)
        result = self.runtime.exec(
            self.container_id,
            "python",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-q",
            *packages,
            workdir=self.container_workspace,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to install Apple container REPL deps: {result.stderr}")

    def load_context(self, context_payload: dict | list | str):
        if isinstance(context_payload, str):
            context_path = os.path.join(self.temp_dir, "context.txt")
            with open(context_path, "w", encoding="utf-8") as f:
                f.write(context_payload)
            self.execute_code(
                f"with open('{self.container_workspace}/context.txt') as f:\n    context = f.read()"
            )
            return

        context_path = os.path.join(self.temp_dir, "context.json")
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(context_payload, f)
        self.execute_code(
            "import json\n"
            f"with open('{self.container_workspace}/context.json') as f:\n"
            "    context = json.load(f)"
        )

    def execute_code(self, code: str) -> REPLResult:
        start = time.perf_counter()
        with self._calls_lock:
            self.pending_calls.clear()

        if self.container_id is None:
            raise RuntimeError("Apple container is not running.")

        script = _build_exec_script(
            code,
            self.proxy_port,
            self.depth,
            proxy_host=self.host_proxy_name,
        )
        result = self.runtime.exec(
            self.container_id,
            "python",
            "-c",
            script,
            workdir=self.container_workspace,
        )

        with self._calls_lock:
            calls = self.pending_calls.copy()
            self.pending_calls.clear()

        try:
            lines = result.stdout.strip().splitlines()
            data = json.loads(lines[-1]) if lines else {}
        except json.JSONDecodeError:
            stderr = result.stderr or "Parse error"
            if result.returncode != 0 and not result.stderr:
                stderr = f"Container command failed with exit code {result.returncode}"
            return REPLResult(
                stdout=result.stdout,
                stderr=stderr,
                locals={},
                execution_time=time.perf_counter() - start,
                rlm_calls=calls,
            )

        return REPLResult(
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", "") + result.stderr,
            locals=data.get("locals", {}),
            execution_time=time.perf_counter() - start,
            rlm_calls=calls,
            final_answer=data.get("final_answer"),
        )

    def cleanup(self):
        stop_error = None
        if getattr(self, "container_id", None):
            try:
                self.runtime.stop(self.container_id)
            except Exception as exc:
                stop_error = exc
            finally:
                self.container_id = None
        if getattr(self, "proxy_server", None):
            self.proxy_server.shutdown()
            self.proxy_server.server_close()
            self.proxy_server = None
        if getattr(self, "proxy_thread", None):
            self.proxy_thread.join(timeout=1)
            self.proxy_thread = None
        if getattr(self, "temp_dir", None):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
        if stop_error is not None:
            raise RuntimeError("Failed to stop Apple container") from stop_error

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
        return False

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
