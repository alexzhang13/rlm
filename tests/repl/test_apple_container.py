import json
import subprocess

import pytest

from rlm.environments import get_environment
from rlm.environments.apple_container_repl import AppleContainerREPL, AppleContainerRuntime


class RecordingRuntime(AppleContainerRuntime):
    def __init__(self):
        super().__init__()
        self.calls = []

    def run(self, args):
        self.calls.append(args)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="cid\n", stderr="")


class FakeRuntime:
    def __init__(self, dependencies_present=False):
        self.dependencies_present = dependencies_present
        self.started = False
        self.stopped = False
        self.exec_calls = []

    def start(self, **kwargs):
        self.start_kwargs = kwargs
        self.started = True
        return "fake-container"

    def exec(self, container_id, *command, workdir=None):
        self.exec_calls.append((container_id, command, workdir))
        if len(command) > 2 and command[:2] == ("python", "-c") and "importlib.util" in command[2]:
            return subprocess.CompletedProcess(
                command,
                returncode=0 if self.dependencies_present else 1,
                stdout="" if self.dependencies_present else "dill,requests\n",
                stderr="",
            )
        if command[:6] == (
            "python",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-q",
        ):
            return subprocess.CompletedProcess(command, returncode=0, stdout="", stderr="")
        payload = {
            "stdout": "ran\n",
            "stderr": "",
            "locals": {"answer": "{'content': 'ok', 'ready': True}"},
            "final_answer": "ok",
        }
        return subprocess.CompletedProcess(
            command,
            returncode=0,
            stdout=json.dumps(payload) + "\n",
            stderr="",
        )

    def stop(self, container_id):
        self.stopped = True
        self.stopped_container_id = container_id


def test_apple_container_runtime_builds_container_cli_commands(tmp_path):
    runtime = RecordingRuntime()
    container_id = runtime.start(
        image="python:3.11-slim",
        name="rlm-test",
        host_workspace=str(tmp_path),
        container_workspace="/workspace",
        cpus=2,
        memory="1G",
        platform="linux/arm64",
        extra_run_args=["--dns", "1.1.1.1"],
    )
    runtime.exec(container_id, "python", "-c", "print(1)", workdir="/workspace")
    runtime.stop(container_id)

    assert container_id == "cid"
    assert runtime.calls[0] == [
        "run",
        "-d",
        "--rm",
        "--name",
        "rlm-test",
        "-v",
        f"{tmp_path}:/workspace",
        "-w",
        "/workspace",
        "--cpus",
        "2",
        "--memory",
        "1G",
        "--platform",
        "linux/arm64",
        "--dns",
        "1.1.1.1",
        "python:3.11-slim",
        "tail",
        "-f",
        "/dev/null",
    ]
    assert runtime.calls[1] == ["exec", "-w", "/workspace", "cid", "python", "-c", "print(1)"]
    assert runtime.calls[2] == ["stop", "cid"]


def test_apple_container_runtime_fails_loudly_without_cli(monkeypatch):
    monkeypatch.setattr("rlm.environments.apple_container_repl.shutil.which", lambda _: None)
    runtime = AppleContainerRuntime(container_cli="missing-container")

    with pytest.raises(RuntimeError, match="Apple container CLI not found"):
        runtime.run(["--version"])


def test_apple_container_repl_routes_and_parses_results():
    runtime = FakeRuntime()
    repl = AppleContainerREPL(runtime=runtime)
    try:
        result = repl.execute_code("answer['content'] = 'ok'\nanswer['ready'] = True")
    finally:
        repl.cleanup()

    assert runtime.started is True
    assert runtime.stopped is True
    assert runtime.stopped_container_id == "fake-container"
    assert result.stdout == "ran\n"
    assert result.stderr == ""
    assert result.final_answer == "ok"
    assert runtime.exec_calls[0][1][0:2] == ("python", "-c")
    assert runtime.exec_calls[0][2] == "/workspace"
    assert runtime.exec_calls[1][1] == (
        "python",
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "-q",
        "dill",
        "requests",
    )
    assert runtime.exec_calls[1][2] == "/workspace"
    assert runtime.exec_calls[2][1][0:2] == ("python", "-c")
    assert runtime.exec_calls[2][2] == "/workspace"
    assert "host.container.internal" in runtime.exec_calls[2][1][2]


def test_apple_container_repl_skips_install_when_dependencies_exist():
    runtime = FakeRuntime(dependencies_present=True)
    repl = AppleContainerREPL(runtime=runtime)
    try:
        commands = [call[1] for call in runtime.exec_calls]
    finally:
        repl.cleanup()

    assert len(commands) == 1
    assert commands[0][0:2] == ("python", "-c")
    assert "importlib.util" in commands[0][2]
    assert commands[0][3:] == ("dill", "requests")


def test_apple_container_repl_uses_proxy_host_override(monkeypatch):
    monkeypatch.setenv("RLM_APPLE_CONTAINER_PROXY_HOST", "proxy.example.internal")
    runtime = FakeRuntime()
    repl = AppleContainerREPL(runtime=runtime, install_dependencies=False)
    try:
        repl.execute_code("answer['content'] = 'ok'")
    finally:
        repl.cleanup()

    assert "proxy.example.internal" in runtime.exec_calls[0][1][2]
    assert runtime.exec_calls[0][2] == "/workspace"


def test_get_environment_routes_apple():
    runtime = FakeRuntime()
    repl = get_environment(
        "apple",
        {"runtime": runtime, "install_dependencies": False},
    )
    try:
        assert isinstance(repl, AppleContainerREPL)
        assert runtime.started is True
    finally:
        repl.cleanup()
