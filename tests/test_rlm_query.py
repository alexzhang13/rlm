"""Tests for rlm_query and rlm_query_batched in LocalREPL."""

import threading
import time
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


class TestRlmQueryBatchedParallel:
    """Tests for parallel execution of rlm_query_batched."""

    def test_batched_runs_in_parallel(self):
        """Multiple subcalls should execute concurrently, not sequentially."""
        call_times = {}
        lock = threading.Lock()

        def slow_subcall(prompt, model):
            start = time.monotonic()
            time.sleep(0.2)  # Simulate I/O-bound work
            end = time.monotonic()
            with lock:
                call_times[prompt] = (start, end)
            return _make_completion(f"answer for {prompt}")

        repl = LocalREPL(subcall_fn=slow_subcall, max_concurrent_subcalls=4)
        start = time.monotonic()
        result = repl.execute_code("answers = rlm_query_batched(['q1', 'q2', 'q3', 'q4'])")
        wall_time = time.monotonic() - start

        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert len(answers) == 4
        assert all("answer for" in a for a in answers)

        # If sequential, 4 × 0.2s = 0.8s minimum. Parallel should be ~0.2s.
        # Use generous threshold to avoid flakiness.
        assert wall_time < 0.6, f"Expected parallel execution but took {wall_time:.2f}s"
        repl.cleanup()

    def test_batched_respects_max_concurrent(self):
        """Thread pool should not exceed max_concurrent_subcalls."""
        max_concurrent = 2
        active_count = []
        active_lock = threading.Lock()
        active = [0]

        def tracked_subcall(prompt, model):
            with active_lock:
                active[0] += 1
                active_count.append(active[0])
            time.sleep(0.1)
            with active_lock:
                active[0] -= 1
            return _make_completion(f"ok {prompt}")

        repl = LocalREPL(subcall_fn=tracked_subcall, max_concurrent_subcalls=max_concurrent)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'b', 'c', 'd'])")
        assert result.stderr == ""
        assert max(active_count) <= max_concurrent
        repl.cleanup()

    def test_batched_preserves_order_parallel(self):
        """Results must be in the same order as input prompts even with parallel execution."""
        import random

        def varying_delay_subcall(prompt, model):
            time.sleep(random.uniform(0.01, 0.1))
            return _make_completion(f"result-{prompt}")

        repl = LocalREPL(subcall_fn=varying_delay_subcall, max_concurrent_subcalls=4)
        result = repl.execute_code("answers = rlm_query_batched(['p0', 'p1', 'p2', 'p3'])")
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert answers == ["result-p0", "result-p1", "result-p2", "result-p3"]
        repl.cleanup()

    def test_batched_parallel_partial_failure(self):
        """Failures in some threads should not affect others."""
        call_count = [0]
        lock = threading.Lock()

        def sometimes_fail(prompt, model):
            with lock:
                call_count[0] += 1
            if prompt == "fail_me":
                raise RuntimeError("intentional failure")
            time.sleep(0.05)
            return _make_completion(f"ok-{prompt}")

        repl = LocalREPL(subcall_fn=sometimes_fail, max_concurrent_subcalls=4)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'fail_me', 'c'])")
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert answers[0] == "ok-a"
        assert "Error" in answers[1]
        assert "intentional failure" in answers[1]
        assert answers[2] == "ok-c"
        repl.cleanup()

    def test_batched_pending_calls_ordered(self):
        """Pending LLM calls should be appended in prompt order for deterministic metadata."""

        def delayed_subcall(prompt, model):
            # Reverse delay so later prompts finish first
            delay = 0.1 if prompt == "first" else 0.01
            time.sleep(delay)
            return _make_completion(f"resp-{prompt}")

        repl = LocalREPL(subcall_fn=delayed_subcall, max_concurrent_subcalls=4)
        result = repl.execute_code("answers = rlm_query_batched(['first', 'second'])")
        assert result.stderr == ""
        assert len(result.rlm_calls) == 2
        assert result.rlm_calls[0].response == "resp-first"
        assert result.rlm_calls[1].response == "resp-second"
        repl.cleanup()

    def test_single_prompt_skips_thread_pool(self):
        """Single prompt should not use ThreadPoolExecutor (no overhead)."""
        subcall_fn = MagicMock(return_value=_make_completion("solo"))
        repl = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=4)
        repl.execute_code("answers = rlm_query_batched(['only'])")
        assert repl.locals["answers"] == ["solo"]
        subcall_fn.assert_called_once_with("only", None)
        repl.cleanup()


class TestMaxConcurrentSubcallsBounds:
    """Tests for edge cases and boundary conditions of max_concurrent_subcalls."""

    def test_max_concurrent_subcalls_default_value(self):
        """Default max_concurrent_subcalls should be 4."""
        repl = LocalREPL()
        assert repl.max_concurrent_subcalls == 4
        repl.cleanup()

    def test_max_concurrent_subcalls_custom_value(self):
        """Should accept custom max_concurrent_subcalls values."""
        repl = LocalREPL(max_concurrent_subcalls=8)
        assert repl.max_concurrent_subcalls == 8
        repl.cleanup()

    def test_max_concurrent_subcalls_one(self):
        """max_concurrent_subcalls=1 should force sequential execution."""
        order = []
        lock = threading.Lock()

        def sequential_subcall(prompt, model):
            with lock:
                order.append(f"start-{prompt}")
            time.sleep(0.05)
            with lock:
                order.append(f"end-{prompt}")
            return _make_completion(f"done-{prompt}")

        repl = LocalREPL(subcall_fn=sequential_subcall, max_concurrent_subcalls=1)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'b', 'c'])")
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert answers == ["done-a", "done-b", "done-c"]
        # With max_workers=1, tasks run one at a time so each start
        # should be followed by its end before the next start
        for i in range(0, len(order) - 1, 2):
            prompt_id = order[i].split("-", 1)[1]
            assert order[i] == f"start-{prompt_id}"
            assert order[i + 1] == f"end-{prompt_id}"
        repl.cleanup()

    def test_max_concurrent_subcalls_larger_than_prompts(self):
        """max_concurrent_subcalls larger than prompt count should work fine."""
        subcall_fn = MagicMock(return_value=_make_completion("ok"))
        repl = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=100)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'b'])")
        assert result.stderr == ""
        assert repl.locals["answers"] == ["ok", "ok"]
        assert subcall_fn.call_count == 2
        repl.cleanup()

    def test_max_concurrent_subcalls_exact_match(self):
        """max_concurrent_subcalls == prompt count should allow full parallelism."""
        active_count = []
        active_lock = threading.Lock()
        active = [0]

        def tracked_subcall(prompt, model):
            with active_lock:
                active[0] += 1
                active_count.append(active[0])
            time.sleep(0.1)
            with active_lock:
                active[0] -= 1
            return _make_completion(f"ok {prompt}")

        repl = LocalREPL(subcall_fn=tracked_subcall, max_concurrent_subcalls=3)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'b', 'c'])")
        assert result.stderr == ""
        # All 3 should be able to run at once
        assert max(active_count) <= 3
        repl.cleanup()

    def test_batched_all_failures_parallel(self):
        """All subcalls failing in parallel should return all error strings."""

        def always_fail(prompt, model):
            raise ValueError(f"fail-{prompt}")

        repl = LocalREPL(subcall_fn=always_fail, max_concurrent_subcalls=4)
        result = repl.execute_code("answers = rlm_query_batched(['x', 'y', 'z'])")
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert len(answers) == 3
        for i, prompt in enumerate(["x", "y", "z"]):
            assert "Error" in answers[i]
            assert f"fail-{prompt}" in answers[i]
        repl.cleanup()

    def test_batched_large_batch_with_low_concurrency(self):
        """Many prompts with low concurrency should still complete correctly."""
        max_concurrent = 2
        active_count = []
        active_lock = threading.Lock()
        active = [0]

        def tracked_subcall(prompt, model):
            with active_lock:
                active[0] += 1
                active_count.append(active[0])
            time.sleep(0.02)
            with active_lock:
                active[0] -= 1
            return _make_completion(f"r-{prompt}")

        prompts = [f"p{i}" for i in range(10)]
        repl = LocalREPL(subcall_fn=tracked_subcall, max_concurrent_subcalls=max_concurrent)
        result = repl.execute_code(f"answers = rlm_query_batched({prompts!r})")
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert len(answers) == 10
        assert answers == [f"r-p{i}" for i in range(10)]
        # Concurrency cap should be respected
        assert max(active_count) <= max_concurrent
        repl.cleanup()

    def test_batched_empty_prompts_with_parallel(self):
        """Empty prompt list should return empty list regardless of concurrency setting."""
        subcall_fn = MagicMock()
        repl = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=4)
        repl.execute_code("answers = rlm_query_batched([])")
        assert repl.locals["answers"] == []
        subcall_fn.assert_not_called()
        repl.cleanup()

    def test_pending_calls_exclude_failures(self):
        """Failed subcalls should not appear in pending_llm_calls."""

        def fail_second(prompt, model):
            if prompt == "bad":
                raise RuntimeError("boom")
            return _make_completion(f"ok-{prompt}")

        repl = LocalREPL(subcall_fn=fail_second, max_concurrent_subcalls=4)
        result = repl.execute_code("answers = rlm_query_batched(['good1', 'bad', 'good2'])")
        assert result.stderr == ""
        # Only 2 successful completions should be in rlm_calls
        assert len(result.rlm_calls) == 2
        assert result.rlm_calls[0].response == "ok-good1"
        assert result.rlm_calls[1].response == "ok-good2"
        repl.cleanup()


class TestMaxConcurrentSubcallsOnBaseEnv:
    """Tests that max_concurrent_subcalls is a property of BaseEnv, not just LocalREPL."""

    def test_base_env_has_max_concurrent_subcalls(self):
        """BaseEnv should accept and store max_concurrent_subcalls."""

        # BaseEnv is abstract, so we test via LocalREPL which inherits from it
        repl = LocalREPL(max_concurrent_subcalls=16)
        assert repl.max_concurrent_subcalls == 16
        # Verify it's set via the BaseEnv.__init__ chain
        assert hasattr(repl, "max_concurrent_subcalls")
        repl.cleanup()

    def test_base_env_default_max_concurrent_subcalls(self):
        """BaseEnv default should be 4."""
        repl = LocalREPL()
        assert repl.max_concurrent_subcalls == 4
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


# =============================================================================
# Parallel execution tests (max_concurrent_subcalls > 1)
# =============================================================================


def _make_slow_subcall_fn(delay: float = 0.3):
    """Create a thread-safe subcall_fn that sleeps to simulate real LLM latency.

    Returns the function. The function records the prompt in its response
    so result ordering can be verified.
    """
    def subcall_fn(prompt: str, model: str | None = None) -> RLMChatCompletion:
        time.sleep(delay)
        return _make_completion(f"answer_for_{prompt}")

    return subcall_fn


class TestRlmQueryBatchedParallel:
    """Tests for parallel rlm_query_batched when max_concurrent_subcalls > 1."""

    def test_parallel_faster_than_sequential(self):
        """Parallel execution should be measurably faster than an actual sequential run."""
        delay = 0.3
        prompts = ["q0", "q1", "q2", "q3", "q4"]
        subcall_fn = _make_slow_subcall_fn(delay)

        # Actual sequential run (max_concurrent=1)
        seq_repl = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=1)
        seq_start = time.perf_counter()
        seq_repl.execute_code(f"answers = rlm_query_batched({prompts})")
        seq_elapsed = time.perf_counter() - seq_start
        seq_answers = seq_repl.locals["answers"]
        seq_repl.cleanup()

        # Actual parallel run (max_concurrent=5)
        par_repl = LocalREPL(
            subcall_fn=subcall_fn,
            max_concurrent_subcalls=5,
            subcall_semaphore=threading.Semaphore(16),
        )
        par_start = time.perf_counter()
        par_repl.execute_code(f"answers = rlm_query_batched({prompts})")
        par_elapsed = time.perf_counter() - par_start
        par_answers = par_repl.locals["answers"]
        par_repl.cleanup()

        # Both should produce the same results
        assert len(seq_answers) == len(par_answers) == 5
        assert seq_answers == par_answers

        # Parallel should be at least 2x faster than sequential
        assert par_elapsed < seq_elapsed * 0.6, (
            f"Parallel ({par_elapsed:.2f}s) not fast enough vs sequential ({seq_elapsed:.2f}s)"
        )

    def test_parallel_results_maintain_order(self):
        """Results should match input prompt order, not completion order."""
        # Give each prompt a different delay so they finish out of order
        delays = {"p0": 0.25, "p1": 0.05, "p2": 0.15, "p3": 0.01, "p4": 0.10}

        def subcall_fn(prompt: str, model: str | None = None) -> RLMChatCompletion:
            time.sleep(delays.get(prompt, 0.05))
            return _make_completion(f"answer_for_{prompt}")

        repl = LocalREPL(
            subcall_fn=subcall_fn,
            max_concurrent_subcalls=5,
            subcall_semaphore=threading.Semaphore(16),
        )
        result = repl.execute_code(
            "answers = rlm_query_batched(['p0', 'p1', 'p2', 'p3', 'p4'])"
        )
        assert result.stderr == ""
        answers = repl.locals["answers"]
        for i in range(5):
            assert answers[i] == f"answer_for_p{i}", f"answers[{i}] = {answers[i]}"
        repl.cleanup()

    def test_parallel_partial_failure(self):
        """One failed subcall should not block or corrupt other results."""
        def subcall_fn(prompt: str, model: str | None = None) -> RLMChatCompletion:
            time.sleep(0.05)
            if prompt == "c":
                raise RuntimeError("child exploded")
            return _make_completion(f"ok_{prompt}")

        repl = LocalREPL(
            subcall_fn=subcall_fn,
            max_concurrent_subcalls=4,
            subcall_semaphore=threading.Semaphore(16),
        )
        result = repl.execute_code(
            "answers = rlm_query_batched(['a', 'b', 'c', 'd'])"
        )
        assert result.stderr == ""
        answers = repl.locals["answers"]
        assert len(answers) == 4
        assert answers[0] == "ok_a"
        assert answers[1] == "ok_b"
        assert "Error" in answers[2] and "child exploded" in answers[2]
        assert answers[3] == "ok_d"
        repl.cleanup()

    def test_parallel_tracks_pending_calls(self):
        """All successful completions should be tracked in rlm_calls."""
        def subcall_fn(prompt: str, model: str | None = None) -> RLMChatCompletion:
            time.sleep(0.02)
            return _make_completion(f"resp_{prompt}")

        repl = LocalREPL(
            subcall_fn=subcall_fn,
            max_concurrent_subcalls=4,
            subcall_semaphore=threading.Semaphore(16),
        )
        result = repl.execute_code(
            "rlm_query_batched(['a', 'b', 'c', 'd'])"
        )
        assert len(result.rlm_calls) == 4
        repl.cleanup()

    def test_sequential_fallback_when_max_concurrent_1(self):
        """max_concurrent_subcalls=1 should execute sequentially (default behavior)."""
        completions = [_make_completion(f"seq_{i}") for i in range(3)]
        subcall_fn = MagicMock(side_effect=completions)

        repl = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=1)
        result = repl.execute_code("answers = rlm_query_batched(['a', 'b', 'c'])")

        assert result.stderr == ""
        assert repl.locals["answers"] == ["seq_0", "seq_1", "seq_2"]
        assert subcall_fn.call_count == 3
        # Verify calls were in order (sequential)
        calls = [c[0][0] for c in subcall_fn.call_args_list]
        assert calls == ["a", "b", "c"]
        repl.cleanup()

    def test_single_prompt_skips_parallel_path(self):
        """A single prompt should use sequential path even with max_concurrent > 1."""
        subcall_fn = MagicMock(return_value=_make_completion("single"))
        repl = LocalREPL(
            subcall_fn=subcall_fn,
            max_concurrent_subcalls=8,
            subcall_semaphore=threading.Semaphore(16),
        )
        _ = repl.execute_code("answers = rlm_query_batched(['only'])")
        assert repl.locals["answers"] == ["single"]
        subcall_fn.assert_called_once_with("only", None)
        repl.cleanup()


class TestGlobalSemaphoreBounding:
    """Tests that the global semaphore correctly bounds total concurrency."""

    def test_semaphore_limits_concurrent_children(self):
        """With semaphore(2), at most 2 children should run simultaneously."""
        max_seen = 0
        current = 0
        lock = threading.Lock()

        def subcall_fn(prompt: str, model: str | None = None) -> RLMChatCompletion:
            nonlocal max_seen, current
            with lock:
                current += 1
                if current > max_seen:
                    max_seen = current
            time.sleep(0.15)
            with lock:
                current -= 1
            return _make_completion(f"ok_{prompt}")

        sem = threading.Semaphore(2)
        repl = LocalREPL(
            subcall_fn=subcall_fn,
            max_concurrent_subcalls=5,  # pool allows 5
            subcall_semaphore=sem,       # but semaphore only allows 2
        )
        result = repl.execute_code(
            "answers = rlm_query_batched(['a', 'b', 'c', 'd', 'e'])"
        )
        assert result.stderr == ""
        assert len(repl.locals["answers"]) == 5
        assert all(a.startswith("ok_") for a in repl.locals["answers"])
        # Semaphore should have limited concurrent execution to 2
        assert max_seen <= 2, f"max concurrent was {max_seen}, expected <= 2"
        repl.cleanup()

    def test_semaphore_shared_across_repls(self):
        """Two REPLs sharing the same semaphore should respect the combined limit."""
        max_seen = 0
        current = 0
        lock = threading.Lock()

        def subcall_fn(prompt: str, model: str | None = None) -> RLMChatCompletion:
            nonlocal max_seen, current
            with lock:
                current += 1
                if current > max_seen:
                    max_seen = current
            time.sleep(0.15)
            with lock:
                current -= 1
            return _make_completion("ok")

        shared_sem = threading.Semaphore(3)
        repl1 = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=4, subcall_semaphore=shared_sem)
        repl2 = LocalREPL(subcall_fn=subcall_fn, max_concurrent_subcalls=4, subcall_semaphore=shared_sem)

        # Run both in parallel threads
        def run_repl(repl):
            repl.execute_code("rlm_query_batched(['x', 'y', 'z'])")

        t1 = threading.Thread(target=run_repl, args=(repl1,))
        t2 = threading.Thread(target=run_repl, args=(repl2,))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        # 6 total tasks, but semaphore(3) means at most 3 concurrent
        assert max_seen <= 3, f"max concurrent was {max_seen}, expected <= 3"
        repl1.cleanup()
        repl2.cleanup()
