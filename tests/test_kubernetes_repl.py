"""Tests for KubernetesREPL.

Every test runs code in a real pod, with a mock LM and mock subcall_fn (no API
cost). Requires the `kubernetes` extra and a reachable cluster, e.g. one created
with `kind create cluster`; skipped otherwise.
"""

import threading
import time
from unittest.mock import patch

import pytest

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import RLMChatCompletion, UsageSummary
from tests.mock_lm import MockLM


def _cluster_available() -> bool:
    try:
        from kubernetes import client, config

        configuration = client.Configuration()
        config.load_config(client_configuration=configuration)
        client.VersionApi(client.ApiClient(configuration)).get_code(_request_timeout=10)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _cluster_available(), reason="Kubernetes cluster not available")


def _completion(response: str) -> RLMChatCompletion:
    return RLMChatCompletion(
        root_model="child",
        prompt="p",
        response=response,
        usage_summary=UsageSummary(model_usage_summaries={}),
        execution_time=0.0,
    )


@pytest.fixture
def handler():
    h = LMHandler(client=MockLM(response_fn=lambda prompt: f"echo:{prompt}"))
    h.start()
    yield h
    h.stop()


@pytest.fixture
def make_repl(handler):
    from rlm.environments.kubernetes_repl import KubernetesREPL

    repls = []

    def make(with_handler=True, **kwargs):
        repl = KubernetesREPL(
            lm_handler_address=handler.address if with_handler else None, **kwargs
        )
        repls.append(repl)
        return repl

    yield make
    for repl in repls:
        repl.cleanup()


class TestExecution:
    def test_variables_and_functions_persist_between_blocks(self, make_repl):
        repl = make_repl()
        repl.execute_code("def double(x):\n    return 2 * x\nbase = 21")
        r = repl.execute_code("print(double(base))")
        assert r.stdout.strip() == "42", (r.stdout, r.stderr)
        assert r.locals["base"] == "21"

    def test_string_and_dict_context(self, make_repl):
        r = make_repl(context_payload="héllo").execute_code("print(context, context_0)")
        assert r.stdout.strip() == "héllo héllo", (r.stdout, r.stderr)
        r = make_repl(context_payload={"a": [1, 2]}).execute_code("print(context['a'][1])")
        assert r.stdout.strip() == "2", (r.stdout, r.stderr)

    def test_exception_goes_to_stderr(self, make_repl):
        r = make_repl().execute_code("1 / 0")
        assert "ZeroDivisionError" in r.stderr
        assert r.stdout == ""

    def test_stdin_and_subprocess_output_do_not_break_protocol(self, make_repl):
        repl = make_repl()
        r = repl.execute_code("input()")
        assert "EOFError" in r.stderr
        r = repl.execute_code(
            "import subprocess\nsubprocess.run(['echo', 'from-subprocess'])\nprint(llm_query('hi'))"
        )
        assert r.stdout.strip() == "echo:hi", (r.stdout, r.stderr)
        assert "from-subprocess" in r.stderr

    def test_large_context(self, make_repl):
        repl = make_repl(context_payload="x" * 20_000_000)
        r = repl.execute_code("print(len(context))")
        assert r.stdout.strip() == "20000000", r.stderr


class TestLLMQuery:
    def test_llm_query_and_tracking(self, make_repl):
        repl = make_repl()
        r = repl.execute_code("print(llm_query('hi'))")
        assert r.stdout.strip() == "echo:hi", (r.stdout, r.stderr)
        assert len(r.rlm_calls) == 1
        r = repl.execute_code("x = 5")
        assert len(r.rlm_calls) == 0

    def test_llm_query_batched_order_and_tracking(self, make_repl):
        r = make_repl().execute_code("print(llm_query_batched(['a', 'b', 'c']))")
        assert r.stdout.strip() == "['echo:a', 'echo:b', 'echo:c']", (r.stdout, r.stderr)
        assert len(r.rlm_calls) == 3

    def test_llm_query_from_threads(self, make_repl):
        code = (
            "import threading\n"
            "res = {}\n"
            "def w(i):\n"
            "    res[i] = llm_query(f'q{i}')\n"
            "ts = [threading.Thread(target=w, args=(i,)) for i in range(5)]\n"
            "[t.start() for t in ts]\n"
            "[t.join() for t in ts]\n"
            "print(sorted(res.items()))"
        )
        r = make_repl().execute_code(code)
        expected = [(i, f"echo:q{i}") for i in range(5)]
        assert r.stdout.strip() == str(expected), (r.stdout, r.stderr)
        assert len(r.rlm_calls) == 5

    def test_llm_query_without_handler_returns_error(self, make_repl):
        r = make_repl(with_handler=False).execute_code("print(llm_query('hi'))")
        assert r.stdout.startswith("Error: No LM handler configured")
        assert len(r.rlm_calls) == 0


class TestRLMQuery:
    def test_rlm_query_uses_subcall_fn(self, make_repl):
        seen = {}

        def sub(prompt, model=None):
            seen["model"] = model
            return _completion(f"child:{prompt}")

        r = make_repl(subcall_fn=sub).execute_code("print(rlm_query('task', model='m1'))")
        assert r.stdout.strip() == "child:task", (r.stdout, r.stderr)
        assert seen["model"] == "m1"
        assert len(r.rlm_calls) == 1

    def test_rlm_query_falls_back_to_llm_query(self, make_repl):
        r = make_repl().execute_code("print(rlm_query('task'), rlm_query_batched(['a']))")
        assert r.stdout.strip() == "echo:task ['echo:a']", (r.stdout, r.stderr)
        assert len(r.rlm_calls) == 2

    def test_rlm_query_batched_order_and_partial_failure(self, make_repl):
        def sub(prompt, model=None):
            if prompt == "bad":
                raise ValueError("nope")
            time.sleep({"p0": 0.2, "p1": 0.1}.get(prompt, 0))
            return _completion(f"r:{prompt}")

        r = make_repl(subcall_fn=sub).execute_code(
            "print(rlm_query_batched(['p0', 'bad', 'p1']))\nprint(rlm_query('bad'))"
        )
        lines = r.stdout.strip().split("\n")
        assert lines[0] == "['r:p0', 'Error: RLM query failed - nope', 'r:p1']", r.stderr
        assert lines[1] == "Error: RLM query failed - nope"
        assert [c.response for c in r.rlm_calls] == ["r:p0", "r:p1"]

    def test_rlm_query_batched_respects_max_concurrent(self, make_repl):
        active, peak = [0], [0]
        lock = threading.Lock()

        def sub(prompt, model=None):
            with lock:
                active[0] += 1
                peak[0] = max(peak[0], active[0])
            time.sleep(0.1)
            with lock:
                active[0] -= 1
            return _completion(prompt)

        repl = make_repl(subcall_fn=sub, max_concurrent_subcalls=2)
        r = repl.execute_code("print(len(rlm_query_batched(list('abcdef'))))")
        assert r.stdout.strip() == "6", (r.stdout, r.stderr)
        assert peak[0] == 2


class TestScaffold:
    def test_reserved_names_restored(self, make_repl):
        repl = make_repl(context_payload="ctx")
        repl.execute_code("llm_query = None\ncontext = 'clobbered'")
        r = repl.execute_code("print(llm_query('hi'), context)")
        assert r.stdout.strip() == "echo:hi ctx", (r.stdout, r.stderr)

    def test_answer_ready_surfaces_final_answer(self, make_repl):
        repl = make_repl()
        assert repl.execute_code("answer['content'] = 'draft'").final_answer is None
        r = repl.execute_code("answer['ready'] = True")
        assert r.final_answer == "draft"

    def test_custom_tools(self, make_repl):
        repl = make_repl(custom_tools={"triple": "def triple(x):\n    return 3 * x", "BASE": 7})
        r = repl.execute_code("print(triple(BASE))")
        assert r.stdout.strip() == "21", (r.stdout, r.stderr)


class TestPod:
    def test_pod_is_sandboxed(self, make_repl):
        repl = make_repl(namespace="default", timeout=120)
        spec = repl.api.read_namespaced_pod(repl.pod_name, "default").spec
        container = spec.containers[0]
        assert spec.automount_service_account_token is False
        assert spec.security_context.run_as_non_root is True
        assert spec.active_deadline_seconds == 120
        assert container.security_context.allow_privilege_escalation is False
        assert container.security_context.capabilities.drop == ["ALL"]
        assert container.resources.limits == {"cpu": "1", "memory": "2Gi"}
        r = repl.execute_code("import os\nprint(os.getuid(), os.path.exists('/var/run/secrets'))")
        assert r.stdout.strip() == "1000 False", (r.stdout, r.stderr)

    def test_cleanup_deletes_pod(self, make_repl):
        repl = make_repl()
        name = repl.pod_name
        repl.cleanup()
        repl.cleanup()
        pod = repl.api.list_namespaced_pod("default", field_selector=f"metadata.name={name}")
        assert all(p.metadata.deletion_timestamp for p in pod.items)

    def test_persistent_not_supported(self):
        from rlm.environments.kubernetes_repl import KubernetesREPL

        with pytest.raises(NotImplementedError):
            KubernetesREPL(persistent=True)


def test_rlm_completion_with_recursive_subcall():
    """A root RLM calls rlm_query from its pod, which runs a child RLM in a second pod."""
    lm = MockLM(
        responses=[
            "```repl\nanswer['content'] = rlm_query('child task')\nanswer['ready'] = True\n```",
            "```repl\nanswer['content'] = 'child done'\nanswer['ready'] = True\n```",
        ]
    )
    with patch.object(rlm_module, "get_client", return_value=lm):
        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "mock-model"},
            environment="kubernetes",
            max_depth=2,
            max_iterations=2,
        )
        result = rlm.completion("root task")
    assert result.response == "child done"
