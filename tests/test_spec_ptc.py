"""Real spec-ptc integration tests; no external model API calls."""

import threading
import time
from collections import Counter
from contextlib import contextmanager
from unittest.mock import patch

import pytest

pytest.importorskip("spec_ptc")

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary
from rlm.logger import RLMLogger


class ScriptedLM(BaseLM):
    supports_streaming = True

    def __init__(self, model_name, workload):
        super().__init__(model_name=model_name)
        self.workload = workload
        self.calls = 0

    def completion(self, prompt, model=None):
        self.calls += 1
        if self.model_name == "root" and isinstance(prompt, list):
            return self.workload.script(prompt, self.calls)
        with self.workload.lock:
            self.workload.requests.append((prompt, model or self.model_name))
        self.workload.started.set()
        time.sleep(self.workload.latency)
        if prompt == "fail":
            raise RuntimeError("failed tool")
        return f"result:{prompt}"

    async def acompletion(self, prompt, model=None):
        return self.completion(prompt, model)

    def stream_completion(self, prompt, model=None):
        response = self.completion(prompt, model)
        for line in response.splitlines(keepends=True):
            yield line
            if self.workload.await_early and "_query" in line:
                assert self.workload.started.wait(2), "tool did not start during generation"
            time.sleep(self.workload.token_delay)
        self.workload.generation_finished.set()

    def get_usage_summary(self):
        return UsageSummary(
            {
                self.model_name: ModelUsageSummary(
                    self.calls, self.calls * 11, self.calls * 7, self.calls * 0.001
                )
            }
        )

    def get_last_usage(self):
        return ModelUsageSummary(1, 11, 7, 0.001)


class Workload:
    def __init__(self, script, latency=0.01, token_delay=0.01, await_early=False):
        self.script = script if callable(script) else lambda prompt, call: script
        self.latency = latency
        self.token_delay = token_delay
        self.await_early = await_early
        self.lock = threading.Lock()
        self.started = threading.Event()
        self.generation_finished = threading.Event()
        self.requests = []
        self.clients = []
        self.environments = []
        self.metrics = []
        self.original_get_environment = rlm_module.get_environment

    def client(self, backend, kwargs):
        client = ScriptedLM(kwargs["model_name"], self)
        self.clients.append(client)
        return client

    def environment(self, name, kwargs):
        environment = self.original_get_environment(name, kwargs)
        self.environments.append(environment)
        return environment

    def run(self, spec=True, max_depth=1, context="context", **kwargs):
        with (
            patch.object(rlm_module, "get_client", side_effect=self.client),
            patch.object(rlm_module, "get_environment", side_effect=self.environment),
            RLM(
                backend_kwargs={"model_name": "root"},
                other_backends=["openai"],
                other_backend_kwargs=[{"model_name": "leaf"}],
                experimental_spec_ptc=spec,
                stream=True,
                max_depth=max_depth,
                max_iterations=2,
                environment_kwargs={"speculation_observer": self.metrics.append} if spec else {},
                **kwargs,
            ) as rlm,
        ):
            return rlm.completion(context, root_prompt="solve")


def code(body):
    return "```repl\n" + body + "\n```\n"


def test_starts_during_stream_and_claims_once_with_tracking():
    workload = Workload(
        code("x = llm_query('one')\nanswer['content'] = x\nanswer['ready'] = True"),
        await_early=True,
    )
    result = workload.run()
    assert result.response == "result:one"
    assert workload.requests == [("one", "leaf")]
    assert workload.metrics[0]["claim_hit"] == 1
    assert result.usage_summary.model_usage_summaries["leaf"].total_calls == 1
    assert all(env.spec_session is None for env in workload.environments)


@pytest.mark.parametrize(
    "call",
    [
        "llm_query('one')",
        "llm_query(prompt='one', model='leaf')",
        "rlm_query('one', context='data')",
        "llm_query_batched(['one', 'two'], model='leaf')",
        "llm_query_batched(prompts=['one', 'two'])",
        "rlm_query_batched(queries=[('one', 'data'), ('two', 'data')])",
    ],
)
def test_plain_and_recursive_helpers_match_non_speculative_results(call):
    script = code(f"x = {call}\nanswer['content'] = str(x)\nanswer['ready'] = True")
    baseline = Workload(script)
    speculative = Workload(script)
    assert speculative.run().response == baseline.run().response
    assert Counter(speculative.requests) == Counter(baseline.requests)


def test_repeated_calls_are_distinct_samples():
    workload = Workload(
        code(
            "a = llm_query('one')\nb = llm_query('one')\n"
            "answer['content'] = a + b\nanswer['ready'] = True"
        )
    )
    assert workload.run().response == "result:oneresult:one"
    assert len(workload.requests) == 2


def test_dependent_queries():
    workload = Workload(
        code(
            "a = llm_query('one')\nb = llm_query(a)\nanswer['content'] = b\nanswer['ready'] = True"
        )
    )
    assert workload.run().response == "result:result:one"
    assert workload.requests == [("one", "leaf"), ("result:one", "leaf")]


def test_multiple_blocks_share_claims_and_track_calls_in_each_cell():
    workload = Workload(
        code("a = llm_query('one')")
        + code("b = llm_query('two')\nanswer['content'] = a + b\nanswer['ready'] = True")
    )
    result = workload.run(logger=RLMLogger())
    assert result.response == "result:oneresult:two"
    assert len(workload.requests) == 2
    assert workload.metrics[0]["claim_hit"] == 2

    blocks = result.metadata["iterations"][0]["code_blocks"]
    assert [[call["response"] for call in block["result"]["rlm_calls"]] for block in blocks] == [
        ["result:one"],
        ["result:two"],
    ]


def test_custom_tool_is_not_executed_by_shadow():
    observed = []
    workload = Workload(
        code("touch()\nx = llm_query('one')\nanswer['content'] = x\nanswer['ready'] = True")
    )
    result = workload.run(custom_tools={"touch": lambda: observed.append("called")})
    assert result.response == "result:one"
    assert observed == ["called"]


def test_shadow_cannot_submit_final_answer_or_mutate_context():
    workload = Workload(
        code(
            "context.append('real')\nx = llm_query(str(context))\n"
            "answer['content'] = str(context)\nanswer['ready'] = True"
        )
    )
    assert workload.run(context=[]).response == "['real']"
    assert workload.requests == [("['real']", "leaf")]


def test_tool_errors_match_baseline():
    script = code("answer['content'] = llm_query('fail')\nanswer['ready'] = True")
    assert Workload(script).run().response == Workload(script).run(spec=False).response


def test_recursive_child_speculates_with_same_depth_limit():
    def script(prompt, call):
        if "child-task" in prompt[1]["content"]:
            return code("answer['content'] = llm_query('child-leaf')\nanswer['ready'] = True")
        return code(
            "x = rlm_query('child-task', context={'data': 1})\n"
            "answer['content'] = x\nanswer['ready'] = True"
        )

    workload = Workload(script)
    result = workload.run(max_depth=2)
    assert result.response == "result:child-leaf"
    assert sorted(env.depth for env in workload.environments) == [1, 2]
    assert len(workload.requests) == 1
    assert result.usage_summary.model_usage_summaries["root"].total_calls == 3
    assert result.usage_summary.model_usage_summaries["leaf"].total_calls == 0
    assert sum(metric["claim_hit"] for metric in workload.metrics) == 2


def test_unclaimed_work_is_drained_counted_and_not_put_in_real_call_tracking():
    def script(prompt, call):
        if call == 1:
            return "```repl\nx = llm_query('unclaimed')\n"  # incomplete block is never executed
        return code("answer['content'] = 'done'\nanswer['ready'] = True")

    workload = Workload(script, await_early=True)
    result = workload.run()
    assert result.response == "done"
    assert workload.requests == [("unclaimed", "leaf")]
    assert workload.metrics[0]["evict"] == 1
    assert workload.metrics[0]["claim_hit"] == 0
    assert result.usage_summary.total_cost == pytest.approx(0.003)
    assert workload.environments[0]._pending_llm_calls == []


def test_recursive_batch_keeps_pairs_and_order():
    def script(prompt, call):
        metadata = prompt[1]["content"]
        if "child-A" in metadata or "child-B" in metadata:
            return code("answer['content'] = str(context)\nanswer['ready'] = True")
        return code(
            "x = rlm_query_batched([('child-A', {'x': 1}), ('child-B', ['two'])])\n"
            "answer['content'] = str(x)\nanswer['ready'] = True"
        )

    workload = Workload(script)
    result = workload.run(max_depth=2)
    assert result.response == """["{'x': 1}", "['two']"]"""
    assert sorted(env.depth for env in workload.environments) == [1, 2, 2]
    assert result.usage_summary.model_usage_summaries["root"].total_calls == 3


def test_recursive_calls_with_custom_tools_do_not_start_early():
    observed = []
    starts = []

    def script(prompt, call):
        if "child-task" in prompt[1]["content"]:
            return code("touch()\nanswer['content'] = 'child'\nanswer['ready'] = True")
        return code("answer['content'] = rlm_query('child-task', '')\nanswer['ready'] = True")

    workload = Workload(script)
    result = workload.run(
        max_depth=2,
        custom_tools={"touch": lambda: observed.append("once")},
        on_subcall_start=lambda *_: starts.append(workload.generation_finished.is_set()),
    )
    assert result.response == "child"
    assert observed == ["once"]
    assert starts == [True]


def test_stream_failure_drains_workers_and_closes_session():
    class BrokenStream(ScriptedLM):
        def stream_completion(self, prompt, model=None):
            yield "```repl\nx = llm_query('started')\n"
            assert self.workload.started.wait(2)
            raise RuntimeError("stream interrupted")

    workload = Workload("")

    def client(backend, kwargs):
        cls = BrokenStream if kwargs["model_name"] == "root" else ScriptedLM
        return cls(kwargs["model_name"], workload)

    with patch.object(workload, "client", side_effect=client):
        with pytest.raises(RuntimeError, match="stream interrupted"):
            workload.run()
    assert workload.requests == [("started", "leaf")]
    assert workload.environments[0].spec_session is None
    assert workload.environments[0].claim_hooks == {}


def test_parallel_recursive_children_keep_stdout_and_relative_files_isolated():
    from pathlib import Path

    original_cwd = Path.cwd()

    def script(prompt, call):
        if "child-" in prompt[1]["content"]:
            return code(
                "print('start', context)\n"
                "with open('marker.txt', 'w') as f:\n    f.write(context)\n"
                "llm_query(context)\n"
                "with open('marker.txt') as f:\n    value = f.read()\n"
                "print('end', context)\nanswer['content'] = value\nanswer['ready'] = True"
            )
        return code(
            "print('parent-start')\n"
            "x = rlm_query_batched([('child-A', 'A'), ('child-B', 'B')])\n"
            "print('parent-end')\nanswer['content'] = str(x)\nanswer['ready'] = True"
        )

    workload = Workload(script, latency=0.04)
    outputs = []
    create_environment = workload.environment

    def capture(name, kwargs):
        env = create_environment(name, kwargs)
        execute = env.execute_code

        def execute_and_record(source):
            result = execute(source)
            outputs.append((env.depth, result.stdout, result.stderr))
            return result

        env.execute_code = execute_and_record
        return env

    with patch.object(workload, "environment", side_effect=capture):
        result = workload.run(max_depth=2)
    assert result.response == "['A', 'B']"
    assert (1, "parent-start\nparent-end\n", "") in outputs
    assert (2, "start A\nend A\n", "") in outputs
    assert (2, "start B\nend B\n", "") in outputs
    assert Path.cwd() == original_cwd


@pytest.mark.parametrize("depth", [1, 2, 3])
@pytest.mark.parametrize("batched", [False, True])
def test_full_recursive_tree_and_usage(depth, batched):
    width = 2 if batched else 1
    query = (
        "x = rlm_query_batched([('recurse', {'level': context['level'] + 1}) for _ in range(2)])\n"
        if batched
        else "x = rlm_query('recurse', {'level': context['level'] + 1})\n"
    )
    workload = Workload(code(query + "answer['content'] = str(x)\nanswer['ready'] = True"))
    result = workload.run(max_depth=depth, context={"level": 0})
    assert "Error:" not in result.response
    assert len(workload.environments) == sum(width**level for level in range(depth))
    assert len(workload.requests) == width**depth
    assert max(env.depth for env in workload.environments) == depth
    actual_calls = sum(client.calls for client in workload.clients)
    reported_calls = sum(
        usage.total_calls for usage in result.usage_summary.model_usage_summaries.values()
    )
    assert reported_calls == actual_calls
    assert result.usage_summary.total_cost == pytest.approx(actual_calls * 0.001)


def test_persistent_completions_do_not_reuse_stale_results_or_usage():
    script = code(
        "counter += 1\nx = llm_query('same')\n"
        "answer['content'] = str(counter) + x\nanswer['ready'] = True"
    )
    workload = Workload(script)
    with (
        patch.object(rlm_module, "get_client", side_effect=workload.client),
        patch.object(rlm_module, "get_environment", side_effect=workload.environment),
        RLM(
            backend_kwargs={"model_name": "root"},
            other_backends=["openai"],
            other_backend_kwargs=[{"model_name": "leaf"}],
            experimental_spec_ptc=True,
            persistent=True,
            environment_kwargs={"setup_code": "counter = 0"},
        ) as rlm,
    ):
        first = rlm.completion("first", root_prompt="solve")
        second = rlm.completion("second", root_prompt="solve again")
    assert first.response == "1result:same"
    assert second.response == "2result:same"
    assert len(workload.requests) == 2
    assert first.usage_summary.model_usage_summaries["leaf"].total_calls == 1
    assert second.usage_summary.model_usage_summaries["leaf"].total_calls == 1


def test_dispatch_limit_falls_through_to_real_execution_without_duplicate_calls():
    workload = Workload(
        code(
            "x = llm_query_batched(['one', 'two', 'three'])\n"
            "answer['content'] = str(x)\nanswer['ready'] = True"
        )
    )
    create_environment = workload.environment

    def limited(name, kwargs):
        return create_environment(name, {**kwargs, "spec_max_dispatches_per_turn": 1})

    with patch.object(workload, "environment", side_effect=limited):
        result = workload.run()
    assert result.response == "['result:one', 'result:two', 'result:three']"
    assert Counter(workload.requests) == Counter((name, "leaf") for name in ["one", "two", "three"])
    assert workload.metrics[0]["dispatch"] == 1


def test_wasted_calls_are_included_in_budget_check():
    from rlm.utils.exceptions import BudgetExceededError

    workload = Workload("```repl\nx = llm_query('waste')\n", await_early=True)
    with pytest.raises(BudgetExceededError) as caught:
        workload.run(max_budget=0.0015)
    assert caught.value.spent == pytest.approx(0.002)
    assert all(env.spec_session is None for env in workload.environments)


def test_non_streaming_client_rejected_before_environment_creation():
    from tests.mock_lm import MockLM

    with (
        patch.object(rlm_module, "get_client", return_value=MockLM()),
        patch.object(rlm_module, "get_environment") as create_environment,
        RLM(experimental_spec_ptc=True) as rlm,
    ):
        with pytest.raises(ValueError, match="streaming-capable"):
            rlm.completion("context")
    create_environment.assert_not_called()


def test_missing_optional_package_has_actionable_error():
    with patch("rlm.environments.speculative_repl.find_spec", return_value=None):
        with pytest.raises(ImportError, match=r"rlms\[spec-ptc\]"):
            RLM(experimental_spec_ptc=True)


def test_unsupported_environment_is_rejected():
    with pytest.raises(ValueError, match="environment='local'"):
        RLM(environment="docker", experimental_spec_ptc=True)


def test_claim_identity_preserves_context_dict_order():
    from spec_ptc.contracts.tools import spec_key

    from rlm.environments.speculative_repl import SpeculativeLocalREPL

    with SpeculativeLocalREPL() as env:
        with env.speculation_turn():
            tool = env.spec_session.reg.get("rlm_query")
            first = spec_key(tool, ("list keys", {"a": 1, "b": 2}), {})
            second = spec_key(tool, ("list keys", {"b": 2, "a": 1}), {})
            assert first != second
            assert first == spec_key(
                tool, (), {"instruction": "list keys", "context": {"a": 1, "b": 2}, "model": None}
            )


@pytest.mark.parametrize(
    "option", ["spec_max_inflight", "spec_max_inflight_chars", "spec_max_dispatches_per_turn"]
)
def test_invalid_limits_stop_the_started_handler(option):
    # Import smoke tests reload modules; patch the exact class used by RLM.
    LMHandler = rlm_module.LMHandler

    stopped = []
    original_stop = LMHandler.stop

    def stop(handler):
        original_stop(handler)
        stopped.append(handler)

    workload = Workload("")
    create_environment = workload.environment

    def invalid(name, kwargs):
        return create_environment(name, {**kwargs, option: 0})

    with (
        patch.object(workload, "environment", side_effect=invalid),
        patch.object(LMHandler, "stop", stop),
        pytest.raises(ValueError, match="must be positive"),
    ):
        workload.run()
    assert len(stopped) == 1
    assert stopped[0]._thread is None


def test_plain_speculation_concurrency_is_independent_of_recursive_limit():
    from rlm.environments.speculative_repl import SpeculativeLocalREPL

    with SpeculativeLocalREPL(max_concurrent_subcalls=2) as env:
        with env.speculation_turn():
            assert env.spec_session.launcher.budget.max_inflight == 16
            assert env.max_concurrent_subcalls == 2


def test_failed_recursive_child_still_counts_its_executed_model_work():
    def script(prompt, call):
        if "child-task" in prompt[1]["content"]:
            return code("1 / 0")
        return code("answer['content'] = rlm_query('child-task', '')\nanswer['ready'] = True")

    workload = Workload(script)
    result = workload.run(max_depth=2, max_errors=1)
    assert "Error:" in result.response
    actual_calls = sum(client.calls for client in workload.clients)
    reported_calls = sum(
        summary.total_calls for summary in result.usage_summary.model_usage_summaries.values()
    )
    assert reported_calls == actual_calls == 2
    assert result.usage_summary.total_cost == pytest.approx(0.002)


def test_evicted_work_waiting_for_character_budget_never_starts_api_call():
    release = threading.Event()
    evictions = 0

    def script(prompt, call):
        if call == 1:
            return "```repl\nx = llm_query_batched(['one', 'two', 'three'])\n"
        return code("answer['content'] = 'done'\nanswer['ready'] = True")

    workload = Workload(script, await_early=True)

    class GatedClient(ScriptedLM):
        def completion(self, prompt, model=None):
            self.calls += 1
            with self.workload.lock:
                self.workload.requests.append((prompt, self.model_name))
            self.workload.started.set()
            assert release.wait(5), "turn did not evict the queued calls"
            return f"result:{prompt}"

    create_client = workload.client

    def client(backend, kwargs):
        if kwargs["model_name"] == "root":
            return create_client(backend, kwargs)
        value = GatedClient(kwargs["model_name"], workload)
        workload.clients.append(value)
        return value

    def observe(event):
        nonlocal evictions
        if event.kind == "evict":
            evictions += 1
            if evictions == 3:
                release.set()

    create_environment = workload.environment

    def limited(name, kwargs):
        env = create_environment(name, {**kwargs, "spec_max_inflight_chars": 1})
        original_turn = env.speculation_turn

        @contextmanager
        def monitored_turn():
            with original_turn() as turn:
                env.spec_session.bus.subscribe(observe)
                yield turn

        env.speculation_turn = monitored_turn
        return env

    with (
        patch.object(workload, "environment", side_effect=limited),
        patch.object(workload, "client", side_effect=client),
    ):
        result = workload.run()
    assert result.response == "done"
    assert len(workload.requests) == 1
    assert result.usage_summary.model_usage_summaries["leaf"].total_calls == 1
    assert workload.metrics[0]["dispatch"] == 3
    assert workload.metrics[0]["evict"] == 3
