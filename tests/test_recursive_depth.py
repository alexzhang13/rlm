"""Exercise complete recursive trees through real REPLs with deterministic LMs."""

import copy
import itertools
import json
import shutil
import subprocess
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

import rlm.core.rlm as rlm_module
from rlm import RLM
from tests.mock_lm import MockLM


@pytest.mark.parametrize("batched", [False, True], ids=["single", "batched"])
@pytest.mark.parametrize(
    ("environment", "environment_kwargs", "max_depth"),
    [pytest.param("local", {}, depth, id=f"local-depth-{depth}") for depth in range(1, 5)]
    + [
        pytest.param("ipython", {"kernel_mode": "in_process"}, 3, id="ipython-in-process"),
        pytest.param("ipython", {"kernel_mode": "subprocess"}, 3, id="ipython-subprocess"),
        pytest.param("docker", {}, 3, id="docker"),
    ],
)
def test_recursive_tree_stops_at_depth_limit(environment, environment_kwargs, max_depth, batched):
    if environment == "ipython":
        pytest.importorskip("IPython")
        if environment_kwargs["kernel_mode"] == "subprocess":
            pytest.importorskip("jupyter_client")
            pytest.importorskip("ipykernel")
    if environment == "docker":
        if shutil.which("docker") is None:
            pytest.skip("Docker not available")
        if subprocess.run(["docker", "info"], capture_output=True, timeout=15).returncode:
            pytest.skip("Docker not available")

    width = 2 if batched else 1
    instruction = "Return leaf paths."
    payload = {"level": 0, "path": "root", "token": "offloaded-recursive-payload"}
    environments = []
    model_messages = []
    leaf_inputs = []
    starts = []
    finishes = []
    lock = threading.Lock()
    original_get_environment = rlm_module.get_environment

    def create_environment(kind, kwargs):
        env = original_get_environment(kind, kwargs)
        with lock:
            environments.append((env, copy.deepcopy(kwargs["context_payload"])))
        return env

    def respond(prompt):
        if isinstance(prompt, str):
            task, raw_context = prompt.split("\n\nContext:\n", 1)
            with lock:
                leaf_inputs.append((task, json.loads(raw_context)))
            return json.loads(raw_context)["path"]
        with lock:
            model_messages.append(copy.deepcopy(prompt))
        queries = (
            "queries = [(" + repr(instruction) + ", {"
            "'level': context['level'] + 1, "
            "'path': context['path'] + '/' + str(i), "
            "'token': context['token']}) for i in range(" + str(width) + ")]\n"
        )
        delegate = (
            "responses = rlm_query_batched(queries=queries)\n"
            if batched
            else "responses = [rlm_query(*queries[0])]\n"
        )
        return (
            "```repl\n"
            + queries
            + delegate
            + "answer['content'] = '|'.join(responses)\nanswer['ready'] = True\n```"
        )

    def create_client(backend, kwargs):
        return MockLM(model_name=kwargs["model_name"], response_fn=respond)

    with (
        patch.object(rlm_module, "get_client", side_effect=create_client),
        patch.object(rlm_module, "get_environment", side_effect=create_environment),
        RLM(
            backend_kwargs={"model_name": "mock"},
            environment=environment,
            environment_kwargs=environment_kwargs,
            max_depth=max_depth,
            max_iterations=1,
            max_concurrent_subcalls=2,
            orchestrator=False,
            on_subcall_start=lambda depth, *_: starts.append(depth),
            on_subcall_complete=lambda depth, *_: finishes.append(depth),
        ) as root,
    ):
        result = root.completion(payload, root_prompt=instruction)

    expected_paths = [
        "root/" + "/".join(map(str, path))
        for path in itertools.product(range(width), repeat=max_depth)
    ]
    assert result.response.split("|") == expected_paths
    assert sorted(context["path"] for _, context in leaf_inputs) == sorted(expected_paths)
    assert all(task == instruction for task, _ in leaf_inputs)
    assert all(context["level"] == max_depth for _, context in leaf_inputs)
    assert all(context["token"] == payload["token"] for _, context in leaf_inputs)
    assert len(environments) == sum(width**level for level in range(max_depth))
    assert len(model_messages) == len(environments)
    assert all(env.depth == context["level"] + 1 for env, context in environments)
    assert max(env.depth for env, _ in environments) == max_depth
    assert all(not Path(env.temp_dir).exists() for env, _ in environments)
    assert all(instruction in history[1]["content"] for history in model_messages)
    assert all(payload["token"] not in json.dumps(history) for history in model_messages)
    assert all(history[0] == model_messages[0][0] for history in model_messages)
    expected_child_depths = [level for level in range(1, max_depth) for _ in range(width**level)]
    assert sorted(starts) == expected_child_depths
    assert sorted(finishes) == expected_child_depths
    assert payload == {"level": 0, "path": "root", "token": "offloaded-recursive-payload"}
