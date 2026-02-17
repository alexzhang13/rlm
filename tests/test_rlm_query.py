"""Tests for rlm_query and rlm_query_batched in LocalREPL."""

from unittest.mock import MagicMock

from rlm.core.types import RLMChatCompletion, UsageSummary
from rlm.environments.local_repl import LocalREPL


def _make_completion(response: str) -> RLMChatCompletion:
    """Create a minimal RLMChatCompletion for testing."""
    return RLMChatCompletion(
        root_model="test-model",
        prompt="test",
        response=response,
        usage_summary=UsageSummary(model_usage_summaries={}),
        execution_time=0.1,
    )


class TestRlmQueryWithSubcallFn:
    """Tests for rlm_query when subcall_fn is provided (depth > 1)."""

    def test_rlm_query_uses_subcall_fn(self):
        """rlm_query should use subcall_fn when available."""
        subcall_fn = MagicMock(return_value=_make_completion("child response"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        result = repl.execute_code("response = rlm_query('hello')")
        assert result.stderr == ""
        assert repl.locals["response"] == "child response"
        subcall_fn.assert_called_once_with("hello", None)
        repl.cleanup()

    def test_rlm_query_with_model_override(self):
        """rlm_query should pass model to subcall_fn."""
        subcall_fn = MagicMock(return_value=_make_completion("override response"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("response = rlm_query('hello', model='gpt-4')")
        assert repl.locals["response"] == "override response"
        subcall_fn.assert_called_once_with("hello", "gpt-4")
        repl.cleanup()

    def test_rlm_query_tracks_pending_calls(self):
        """rlm_query should append completion to _pending_llm_calls."""
        completion = _make_completion("tracked")
        subcall_fn = MagicMock(return_value=completion)
        repl = LocalREPL(subcall_fn=subcall_fn)
        result = repl.execute_code("rlm_query('test')")
        assert len(result.rlm_calls) == 1
        assert result.rlm_calls[0].response == "tracked"
        repl.cleanup()

    def test_rlm_query_error_handling(self):
        """rlm_query should return error string if subcall_fn raises."""
        subcall_fn = MagicMock(side_effect=RuntimeError("subcall failed"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        result = repl.execute_code("response = rlm_query('hello')")
        assert result.stderr == ""
        assert "Error" in repl.locals["response"]
        assert "subcall failed" in repl.locals["response"]
        repl.cleanup()


class TestRlmQueryWithoutSubcallFn:
    """Tests for rlm_query when no subcall_fn (depth == 1 or max_depth reached)."""

    def test_rlm_query_falls_back_to_llm_query(self):
        """Without subcall_fn, rlm_query should fall back to llm_query (which returns error without handler)."""
        repl = LocalREPL()
        repl.execute_code("response = rlm_query('test')")
        assert "Error" in repl.locals["response"]
        repl.cleanup()


class TestRlmQueryBatchedWithSubcallFn:
    """Tests for rlm_query_batched when subcall_fn is provided."""

    def test_batched_calls_subcall_fn_per_prompt(self):
        """rlm_query_batched should call subcall_fn once per prompt."""
        completions = [
            _make_completion("answer 1"),
            _make_completion("answer 2"),
            _make_completion("answer 3"),
        ]
        subcall_fn = MagicMock(side_effect=completions)
        repl = LocalREPL(subcall_fn=subcall_fn)
        result = repl.execute_code(
            "answers = rlm_query_batched(['q1', 'q2', 'q3'])\nprint(len(answers))"
        )
        assert result.stderr == ""
        assert "3" in result.stdout
        assert repl.locals["answers"] == ["answer 1", "answer 2", "answer 3"]
        assert subcall_fn.call_count == 3
        repl.cleanup()

    def test_batched_tracks_all_pending_calls(self):
        """rlm_query_batched should track all completions in rlm_calls."""
        completions = [_make_completion(f"resp {i}") for i in range(3)]
        subcall_fn = MagicMock(side_effect=completions)
        repl = LocalREPL(subcall_fn=subcall_fn)
        result = repl.execute_code("rlm_query_batched(['a', 'b', 'c'])")
        assert len(result.rlm_calls) == 3
        assert [c.response for c in result.rlm_calls] == ["resp 0", "resp 1", "resp 2"]
        repl.cleanup()

    def test_batched_with_model_override(self):
        """rlm_query_batched should pass model to each subcall_fn call."""
        subcall_fn = MagicMock(return_value=_make_completion("ok"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("rlm_query_batched(['q1', 'q2'], model='custom-model')")
        assert subcall_fn.call_count == 2
        for call in subcall_fn.call_args_list:
            assert call[0][1] == "custom-model"
        repl.cleanup()

    def test_batched_partial_failure(self):
        """If one subcall_fn call fails, others should still succeed."""
        subcall_fn = MagicMock(
            side_effect=[
                _make_completion("ok 1"),
                RuntimeError("boom"),
                _make_completion("ok 3"),
            ]
        )
        repl = LocalREPL(subcall_fn=subcall_fn)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'b', 'c'])")
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert answers[0] == "ok 1"
        assert "Error" in answers[1]
        assert "boom" in answers[1]
        assert answers[2] == "ok 3"
        repl.cleanup()

    def test_batched_empty_prompts(self):
        """rlm_query_batched with empty list should return empty list."""
        subcall_fn = MagicMock()
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("answers = rlm_query_batched([])")
        assert repl.locals["answers"] == []
        subcall_fn.assert_not_called()
        repl.cleanup()

    def test_batched_single_prompt(self):
        """rlm_query_batched with single prompt should work."""
        subcall_fn = MagicMock(return_value=_make_completion("single"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("answers = rlm_query_batched(['only one'])")
        assert repl.locals["answers"] == ["single"]
        subcall_fn.assert_called_once_with("only one", None)
        repl.cleanup()


class TestRlmQueryBatchedWithoutSubcallFn:
    """Tests for rlm_query_batched when no subcall_fn."""

    def test_batched_falls_back_to_llm_query_batched(self):
        """Without subcall_fn, should fall back to llm_query_batched (error without handler)."""
        repl = LocalREPL()
        repl.execute_code("answers = rlm_query_batched(['q1', 'q2'])")
        answers = repl.locals["answers"]
        assert len(answers) == 2
        assert all("Error" in a for a in answers)
        repl.cleanup()


class TestLlmQueryDoesNotUseSubcallFn:
    """Verify that llm_query never uses subcall_fn even when one is present."""

    def test_llm_query_ignores_subcall_fn(self):
        """llm_query should always do a plain LM call, never use subcall_fn."""
        subcall_fn = MagicMock(return_value=_make_completion("should not see this"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("response = llm_query('test')")
        # Without a handler, llm_query returns an error — importantly, subcall_fn is NOT called
        assert "Error" in repl.locals["response"]
        subcall_fn.assert_not_called()
        repl.cleanup()

    def test_llm_query_batched_ignores_subcall_fn(self):
        """llm_query_batched should never use subcall_fn."""
        subcall_fn = MagicMock(return_value=_make_completion("nope"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("answers = llm_query_batched(['q1', 'q2'])")
        assert all("Error" in a for a in repl.locals["answers"])
        subcall_fn.assert_not_called()
        repl.cleanup()


class TestRlmQueryScaffoldRestoration:
    """Test that rlm_query and rlm_query_batched are restored after overwrite."""

    def test_rlm_query_restored_after_overwrite(self):
        """If model overwrites rlm_query, the next execution should have the real one."""
        subcall_fn = MagicMock(return_value=_make_completion("real"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("rlm_query = lambda x: 'hijacked'")
        # After restoration, rlm_query should work normally
        repl.execute_code("response = rlm_query('test')")
        assert repl.locals["response"] == "real"
        subcall_fn.assert_called_once()
        repl.cleanup()

    def test_rlm_query_batched_restored_after_overwrite(self):
        """If model overwrites rlm_query_batched, the next execution should have the real one."""
        subcall_fn = MagicMock(return_value=_make_completion("real"))
        repl = LocalREPL(subcall_fn=subcall_fn)
        repl.execute_code("rlm_query_batched = 'garbage'")
        repl.execute_code("answers = rlm_query_batched(['q1'])")
        assert repl.locals["answers"] == ["real"]
        repl.cleanup()
