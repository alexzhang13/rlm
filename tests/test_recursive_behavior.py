"""Tests for recursive turn decay and nested RLM spawning."""

from collections import deque
from typing import Any
from unittest.mock import patch

import rlm.clients.recursive as recursive_module
import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary


class FakeLM(BaseLM):
    """Deterministic LM stub with queued responses."""

    def __init__(self, model_name: str, responses: list[str]) -> None:
        super().__init__(model_name=model_name)
        self.responses = deque(responses)
        self.call_count = 0
        self.prompts: list[str | dict[str, Any]] = []
        self.last_usage = ModelUsageSummary(
            total_calls=0, total_input_tokens=0, total_output_tokens=0
        )

    def completion(self, prompt: str | dict[str, Any]) -> str:
        if not self.responses:
            raise AssertionError(f"No responses left for model '{self.model_name}'")
        self.call_count += 1
        self.prompts.append(prompt)
        response = self.responses.popleft()
        self.last_usage = ModelUsageSummary(
            total_calls=1, total_input_tokens=0, total_output_tokens=0
        )
        return response

    async def acompletion(self, prompt: str | dict[str, Any]) -> str:
        return self.completion(prompt)

    def get_usage_summary(self) -> UsageSummary:
        return UsageSummary(
            model_usage_summaries={
                self.model_name: ModelUsageSummary(
                    total_calls=self.call_count,
                    total_input_tokens=0,
                    total_output_tokens=0,
                )
            }
        )

    def get_last_usage(self) -> ModelUsageSummary:
        return self.last_usage


def test_recursive_turn_decay_spawns_sub_rlms():
    root_responses = [
        "Root turn 1\n```repl\nsub_1 = llm_query('depth1 turn 1')\n```",
        "Root turn 2\n```repl\nsub_2 = llm_query('depth1 turn 2')\n```\nFINAL(root done)",
    ]
    depth1_responses = [
        "Depth1 turn 1\n```repl\nleaf_1 = llm_query('depth2 turn 1')\n```\nFINAL(depth1 done 1)",
        "Depth1 turn 2\n```repl\nleaf_2 = llm_query('depth2 turn 2')\n```\nFINAL(depth1 done 2)",
    ]
    depth2_responses = [
        "FINAL(depth2 done 1)",
        "FINAL(depth2 done 2)",
    ]

    clients = {
        "root": FakeLM("root", root_responses),
        "depth1": FakeLM("depth1", depth1_responses),
        "depth2": FakeLM("depth2", depth2_responses),
    }

    def get_fake_client(backend: str, backend_kwargs: dict[str, Any]) -> BaseLM:
        if backend not in clients:
            raise AssertionError(f"Unexpected backend '{backend}'")
        return clients[backend]

    with (
        patch.object(rlm_module, "get_client", side_effect=get_fake_client),
        patch.object(recursive_module, "get_client", side_effect=get_fake_client),
    ):
        rlm = RLM(
            backend="root",
            backend_kwargs={},
            environment="local",
            recursive_max_depth=3,
            max_iterations=2,
            other_backends=["depth1", "depth2"],
            other_backend_kwargs=[{}, {}],
        )
        result = rlm.completion("root context")

    assert result.response == "root done"
    assert clients["root"].call_count == 2
    assert clients["depth1"].call_count == 2
    assert clients["depth2"].call_count == 2
