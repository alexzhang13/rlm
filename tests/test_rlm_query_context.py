"""Instruction/context separation through child RLMs and environment transports."""

import json
import threading
from functools import partial
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.core.lm_handler import LMHandler
from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary
from rlm.environments.docker_repl import LLMProxyHandler
from rlm.environments.ipython_repl import IPythonREPL
from rlm.environments.local_repl import LocalREPL
from rlm.utils.prompts import format_rlm_query


def completion(response: str) -> RLMChatCompletion:
    return RLMChatCompletion(
        root_model="mock",
        prompt="",
        response=response,
        usage_summary=UsageSummary({}),
        execution_time=0,
    )


def mock_lm(responses: list[str]) -> Mock:
    client = Mock(model_name="mock")
    client.completion.side_effect = responses
    client.acompletion = AsyncMock(side_effect=lambda prompt: client.completion(prompt))
    client.get_usage_summary.return_value = UsageSummary({})
    client.get_last_usage.return_value = ModelUsageSummary(1, 0, 0)
    return client


@pytest.mark.parametrize("orchestrator", [True, False])
@pytest.mark.parametrize("custom_prompt", [None, "Custom shared system prompt."])
def test_child_receives_instruction_and_offloads_context(orchestrator, custom_prompt):
    """Run a real child REPL; only its output introduces the payload to model history."""
    instruction = "Return the token stored in context."
    context = {"token": "distinctive-offloaded-payload"}
    client = mock_lm(
        [
            '```repl\nprint(context["token"])\n```',
            '```repl\nanswer["content"] = context["token"]\nanswer["ready"] = True\n```',
        ]
    )
    with patch.object(rlm_module, "get_client", return_value=client):
        with RLM(
            backend_kwargs={"model_name": "mock"},
            max_depth=3,
            custom_system_prompt=custom_prompt,
            orchestrator=orchestrator,
        ) as parent:
            expected_system = parent._setup_prompt(context, root_prompt=instruction)[0]
            # Copy messages now: completion() appends to its history in place.
            messages = []
            responses = iter(client.completion.side_effect)
            client.completion.side_effect = lambda history: (
                messages.append([dict(message) for message in history]) or next(responses)
            )
            result = parent._subcall(instruction, context)
    assert result.response == context["token"]
    assert messages[0][0] == expected_system
    assert instruction in messages[0][1]["content"]
    assert context["token"] not in json.dumps(messages[0])
    assert context["token"] in json.dumps(messages[1])


@pytest.mark.parametrize("context", ["a document", ["one", "two"], {"n": 2}, "", [], {}])
def test_core_depth_limit_preserves_both_inputs(context):
    client = mock_lm(["leaf answer"])
    with patch.object(rlm_module, "get_client", return_value=client):
        with RLM(backend_kwargs={"model_name": "mock"}, max_depth=1) as parent:
            result = parent._subcall("Summarize", context)
    client.completion.assert_called_once_with(format_rlm_query("Summarize", context))
    assert result.response == "leaf answer"


@pytest.fixture(params=["local", "in_process", "subprocess"])
def environment_factory(request):
    if request.param == "local":
        return LocalREPL
    pytest.importorskip("IPython")
    if request.param == "subprocess":
        pytest.importorskip("jupyter_client")
        pytest.importorskip("ipykernel")
    return partial(IPythonREPL, kernel_mode=request.param)


def test_environment_single_and_batch_forward_context(environment_factory):
    callback = Mock(
        side_effect=lambda instruction, context, model: completion(
            f"{instruction}:{context['value']}:{model}"
        )
    )
    with environment_factory(subcall_fn=callback) as environment:
        result = environment.execute_code(
            "print(rlm_query('single', context={'value': 1}, model='override'))\n"
            "print(rlm_query_batched(queries=[('first', {'value': 2}), ('second', {'value': 3})], model='override'))"
        )
    assert result.stderr == ""
    assert "single:1:override" in result.stdout
    assert "['first:2:override', 'second:3:override']" in result.stdout
    callback.assert_has_calls(
        [
            call("single", {"value": 1}, "override"),
            call("first", {"value": 2}, "override"),
            call("second", {"value": 3}, "override"),
        ],
        any_order=True,
    )
    assert [c.response for c in result.rlm_calls] == [
        "single:1:override",
        "first:2:override",
        "second:3:override",
    ]


def test_environment_fallback_preserves_both_inputs(environment_factory):
    # A real handler exercises subprocess fallback as well as the local path.

    client = mock_lm(["one", "two", "three"])
    with LMHandler(client) as handler:
        with environment_factory(lm_handler_address=handler.address) as environment:
            result = environment.execute_code(
                "print(rlm_query('single', {'value': 1}))\n"
                "print(rlm_query_batched([('first', ['a']), ('second', '')]))"
            )
    assert result.stderr == ""
    assert "one" in result.stdout
    assert "two" in result.stdout and "three" in result.stdout
    client.completion.assert_has_calls(
        [
            call(format_rlm_query("single", {"value": 1})),
            call(format_rlm_query("first", ["a"])),
            call(format_rlm_query("second", "")),
        ],
        any_order=True,
    )


def test_docker_proxy_forwards_context_and_fallback_without_daemon():
    handler = object.__new__(LLMProxyHandler)
    handler.lock = threading.Lock()
    handler.pending_calls = []
    callback = Mock(side_effect=lambda instruction, context, model: completion(str(context)))
    handler.subcall_fn = callback
    single = {"instruction": "task", "context": {"value": 1}, "model": "override"}
    assert handler._handle_rlm_single(single) == {"response": "{'value': 1}"}
    queries = [("first", ["a"]), ("second", "text")]
    assert handler._handle_rlm_batched({"queries": queries, "model": "override"}) == {
        "responses": ["['a']", "text"]
    }
    callback.assert_has_calls(
        [
            call("task", {"value": 1}, "override"),
            call("first", ["a"], "override"),
            call("second", "text", "override"),
        ],
        any_order=True,
    )
    handler.subcall_fn = None
    handler._handle_single = Mock(return_value={"response": "leaf"})
    handler._handle_batched = Mock(return_value={"responses": ["a", "b"]})
    handler._handle_rlm_single(single)
    handler._handle_single.assert_called_once_with(
        {**single, "prompt": format_rlm_query("task", {"value": 1})}
    )
    handler._handle_rlm_batched({"queries": queries, "model": "override"})
    handler._handle_batched.assert_called_once_with(
        {
            "queries": queries,
            "prompts": [format_rlm_query(*q) for q in queries],
            "model": "override",
        }
    )
