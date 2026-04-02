import importlib
import json
import sys
import types
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary


class FakeCommandResult:
    def __init__(self, stdout: str = "", stderr: str = ""):
        self._stdout = stdout
        self._stderr = stderr

    def stdout(self):
        return self._stdout

    def stderr(self):
        return self._stderr


def _make_chat_completion(response: str = "mock response") -> RLMChatCompletion:
    usage = UsageSummary(
        model_usage_summaries={
            "mock-model": ModelUsageSummary(
                total_calls=1, total_input_tokens=1, total_output_tokens=1
            )
        }
    )
    return RLMChatCompletion(
        root_model="mock-model",
        prompt="prompt",
        response=response,
        usage_summary=usage,
        execution_time=0.01,
    )


@pytest.fixture
def vercel_repl_module(monkeypatch):
    fake_vercel = types.ModuleType("vercel")
    fake_sandbox_module = types.ModuleType("vercel.sandbox")

    class DummySandbox:
        @classmethod
        def create(cls, *args, **kwargs):
            raise AssertionError("Patch Sandbox.create in the test before use")

    fake_sandbox_module.Sandbox = DummySandbox
    fake_vercel.sandbox = fake_sandbox_module

    monkeypatch.setitem(sys.modules, "vercel", fake_vercel)
    monkeypatch.setitem(sys.modules, "vercel.sandbox", fake_sandbox_module)
    sys.modules.pop("rlm.environments.vercel_repl", None)

    module = importlib.import_module("rlm.environments.vercel_repl")
    yield module

    sys.modules.pop("rlm.environments.vercel_repl", None)


def _build_env(vercel_repl_module, monkeypatch, requests_get=None):
    sandbox = Mock()
    sandbox.write_files = Mock()
    sandbox.run_command = Mock(return_value=FakeCommandResult())
    sandbox.domain = Mock(return_value="https://broker.example.test")
    sandbox.stop = Mock()

    create_mock = Mock(return_value=sandbox)
    monkeypatch.setattr(vercel_repl_module.Sandbox, "create", create_mock)

    if requests_get is None:
        healthy_response = Mock()
        healthy_response.ok = True
        healthy_response.json.return_value = {"status": "ok"}
        requests_get = Mock(return_value=healthy_response)

    monkeypatch.setattr(vercel_repl_module.requests, "get", requests_get)

    env = vercel_repl_module.VercelREPL()
    return env, sandbox, create_mock, requests_get


def test_persistent_mode_is_rejected(vercel_repl_module):
    with pytest.raises(NotImplementedError, match="Persistent REPLs are currently not supported"):
        vercel_repl_module.VercelREPL(persistent=True)


def test_get_environment_dispatches_to_vercel_repl(vercel_repl_module, monkeypatch):
    from rlm.environments import get_environment

    sandbox = Mock()
    sandbox.write_files = Mock()
    sandbox.run_command = Mock(return_value=FakeCommandResult())
    sandbox.domain = Mock(return_value="https://broker.example.test")
    sandbox.stop = Mock()

    create_mock = Mock(return_value=sandbox)
    monkeypatch.setattr(vercel_repl_module.Sandbox, "create", create_mock)

    healthy_response = Mock()
    healthy_response.ok = True
    monkeypatch.setattr(vercel_repl_module.requests, "get", Mock(return_value=healthy_response))

    env = get_environment("vercel", {})

    assert isinstance(env, vercel_repl_module.VercelREPL)
    env.cleanup()


def test_setup_creates_python_sandbox(vercel_repl_module, monkeypatch):
    env, sandbox, create_mock, _ = _build_env(vercel_repl_module, monkeypatch)

    create_mock.assert_called_once_with(
        runtime="python3.13",
        timeout=600000,
        ports=[vercel_repl_module.VercelREPL.BROKER_PORT],
    )
    sandbox.write_files.assert_called_once_with(
        {vercel_repl_module.VercelREPL.BROKER_SCRIPT_PATH: vercel_repl_module._BROKER_SCRIPT}
    )
    sandbox.run_command.assert_called_once_with(
        "python",
        [vercel_repl_module.VercelREPL.BROKER_SCRIPT_PATH],
        detached=True,
    )
    assert env.broker_url == "https://broker.example.test"
    env.cleanup()


def test_health_wait_retries_until_ready(vercel_repl_module, monkeypatch):
    not_ready = vercel_repl_module.requests.exceptions.ConnectionError("not ready")
    healthy_response = Mock()
    healthy_response.ok = True
    healthy_response.json.return_value = {"status": "ok"}
    requests_get = Mock(side_effect=[not_ready, healthy_response])

    env, _, _, requests_get = _build_env(vercel_repl_module, monkeypatch, requests_get=requests_get)

    assert requests_get.call_count == 2
    env.cleanup()


def test_load_context_string_uses_exec_code(vercel_repl_module, monkeypatch):
    env, _, _, _ = _build_env(vercel_repl_module, monkeypatch)
    env.execute_code = Mock()

    env.load_context('hello """vercel"""')

    context_code = env.execute_code.call_args[0][0]
    assert 'context = """' in context_code
    assert '\\"\\"\\"' in context_code
    env.cleanup()


def test_load_context_structured_payload_uses_json(vercel_repl_module, monkeypatch):
    env, _, _, _ = _build_env(vercel_repl_module, monkeypatch)
    env.execute_code = Mock()

    env.load_context({"x": [1, 2], "message": "hello"})

    context_code = env.execute_code.call_args[0][0]
    assert "json.loads" in context_code
    assert '"message": "hello"' in context_code
    env.cleanup()


def test_handle_single_lm_request_tracks_calls(vercel_repl_module, monkeypatch):
    env, _, _, _ = _build_env(vercel_repl_module, monkeypatch)
    chat_completion = _make_chat_completion("single response")
    response = SimpleNamespace(success=True, error=None, chat_completion=chat_completion)
    send_mock = Mock(return_value=response)
    monkeypatch.setattr(vercel_repl_module, "send_lm_request", send_mock)

    result = env._handle_llm_request({"type": "single", "prompt": "hi", "model": "test-model"})

    assert result == {"response": "single response"}
    assert env.pending_llm_calls == [chat_completion]
    send_mock.assert_called_once()
    env.cleanup()


def test_handle_batched_lm_request_tracks_calls(vercel_repl_module, monkeypatch):
    env, _, _, _ = _build_env(vercel_repl_module, monkeypatch)
    first = SimpleNamespace(
        success=True, error=None, chat_completion=_make_chat_completion("first")
    )
    second = SimpleNamespace(
        success=True,
        error=None,
        chat_completion=_make_chat_completion("second"),
    )
    send_mock = Mock(return_value=[first, second])
    monkeypatch.setattr(vercel_repl_module, "send_lm_request_batched", send_mock)

    result = env._handle_llm_request(
        {"type": "batched", "prompts": ["a", "b"], "model": "test-model"}
    )

    assert result == {"responses": ["first", "second"]}
    assert [call.response for call in env.pending_llm_calls] == ["first", "second"]
    send_mock.assert_called_once()
    env.cleanup()


def test_execute_code_returns_repl_result_and_calls(vercel_repl_module, monkeypatch):
    env, _, _, _ = _build_env(vercel_repl_module, monkeypatch)
    env._write_remote_file = Mock()
    nested_call = _make_chat_completion("nested")
    payload = json.dumps({"stdout": "hello\n", "stderr": "", "locals": {"value": "42"}})

    def fake_run(command, args, detached=False):
        env.pending_llm_calls.append(nested_call)
        return FakeCommandResult(stdout=payload)

    env._run_sandbox_command = Mock(side_effect=fake_run)

    result = env.execute_code("print('hello')")

    assert result.stdout == "hello\n"
    assert result.stderr == ""
    assert result.locals == {"value": "42"}
    assert result.rlm_calls == [nested_call]
    env.cleanup()


def test_execute_code_falls_back_to_raw_output(vercel_repl_module, monkeypatch):
    env, _, _, _ = _build_env(vercel_repl_module, monkeypatch)
    env._write_remote_file = Mock()
    env._run_sandbox_command = Mock(
        return_value=FakeCommandResult(stdout="not-json", stderr="boom")
    )

    result = env.execute_code("print('hello')")

    assert result.stdout == "not-json"
    assert result.stderr == "boom"
    assert result.locals == {}
    env.cleanup()


def test_cleanup_stops_thread_and_sandbox(vercel_repl_module, monkeypatch):
    env, sandbox, _, _ = _build_env(vercel_repl_module, monkeypatch)
    fake_thread = Mock()
    env.poller_thread = fake_thread

    env.cleanup()

    assert env.poller_stop.is_set()
    fake_thread.join.assert_called_once_with(timeout=2)
    sandbox.stop.assert_called_once()


def test_exec_script_exposes_rlm_query_helpers(vercel_repl_module):
    script = vercel_repl_module._build_exec_script("print('ok')")

    assert "def rlm_query(prompt, model=None):" in script
    assert "def rlm_query_batched(prompts, model=None):" in script


def test_exec_script_handles_http_error_json(vercel_repl_module):
    script = vercel_repl_module._build_exec_script("print('ok')")

    assert "import urllib.error" in script
    assert "except urllib.error.HTTPError as exc:" in script
