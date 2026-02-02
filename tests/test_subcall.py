"""Tests for depth>1 recursive subcalls."""

from unittest.mock import Mock, patch

import rlm.core.rlm as rlm_module
from rlm.core.types import ModelUsageSummary, RLMChatCompletion, UsageSummary
from rlm.environments.local_repl import LocalREPL


def _dummy_completion_response(response_text: str) -> RLMChatCompletion:
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
        response=response_text,
        usage_summary=usage,
        execution_time=0.0,
    )


class TestSubcall:
    def test_subcall_falls_back_to_lm_at_max_depth(self):
        parent = rlm_module.RLM(max_depth=1)
        mock_client = Mock()
        mock_client.completion.return_value = "leaf"

        with patch.object(rlm_module, "get_client", return_value=mock_client):
            result = parent._subcall("hello")

        assert result == "leaf"
        mock_client.completion.assert_called_once_with("hello")

    def test_subcall_spawns_child_with_incremented_depth(self):
        parent = rlm_module.RLM(max_depth=2)
        captured: dict[str, object] = {}

        class DummyRLM:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            def completion(self, prompt, root_prompt=None):
                _ = prompt
                _ = root_prompt
                return _dummy_completion_response("child")

            def close(self):
                pass

        with patch.object(rlm_module, "RLM", DummyRLM):
            result = parent._subcall("hello")

        assert result == "child"
        assert captured["depth"] == 1
        assert captured["max_depth"] == 2


class TestLocalReplSubcall:
    def test_local_repl_uses_subcall_fn(self):
        def subcall_fn(prompt: str, model: str | None = None) -> str:
            _ = model
            return f"sub:{prompt}"

        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("response = llm_query('hi')")
        assert repl.locals["response"] == "sub:hi"

        repl.execute_code("responses = llm_query_batched(['a', 'b'])")
        assert repl.locals["responses"] == ["sub:a", "sub:b"]
        repl.cleanup()
