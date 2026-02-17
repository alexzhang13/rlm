"""Tests verifying depth=1 functionality is preserved and depth>1 metadata propagation works.

1. depth=1: completion loop, limit checks, logger metadata all work as before
2. depth>1: child RLM gets its own logger, metadata flows back through RLMChatCompletion
"""

from unittest.mock import Mock, patch

import pytest

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.core.types import ModelUsageSummary, UsageSummary
from rlm.logger import RLMLogger
from rlm.utils.exceptions import (
    BudgetExceededError,
    ErrorThresholdExceededError,
    TimeoutExceededError,
    TokenLimitExceededError,
)


def create_mock_lm(responses: list[str], model_name: str = "mock-model") -> Mock:
    """Create a mock LM that returns responses in order."""
    mock = Mock()
    mock.model_name = model_name
    mock.completion.side_effect = list(responses)
    mock.get_usage_summary.return_value = UsageSummary(
        model_usage_summaries={
            model_name: ModelUsageSummary(
                total_calls=1, total_input_tokens=100, total_output_tokens=50
            )
        }
    )
    mock.get_last_usage.return_value = mock.get_usage_summary.return_value
    return mock


# ========================================================================
# depth=1 tests: verify existing behavior is preserved
# ========================================================================


class TestDepth1CompletionLoop:
    """Verify depth=1 completion loop works identically to before refactoring."""

    def test_basic_completion_with_final_answer(self):
        """depth=1 RLM should complete normally with FINAL() answer."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(42)"])
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=1,
            )
            result = rlm.completion("What is the answer?")
            assert result.response == "42"
            assert result.root_model == "test-model"

    def test_multi_iteration_before_final(self):
        """depth=1 should iterate multiple times before finding FINAL()."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(
                [
                    "Let me think...\n```repl\nx = 1 + 1\nprint(x)\n```",
                    "Now I know.\n```repl\ny = x * 2\nprint(y)\n```",
                    "FINAL(4)",
                ]
            )
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=1,
            )
            result = rlm.completion("Compute 2*2")
            assert result.response == "4"

    def test_no_subcall_fn_at_depth_1(self):
        """depth=1 (max_depth=1) should NOT pass subcall_fn to environment."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(done)"])
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=1,
            )

            # Patch get_environment to capture kwargs without running full loop
            with patch.object(rlm_module, "get_environment") as mock_get_env:
                # Make get_environment raise to short-circuit after capturing args
                mock_get_env.side_effect = lambda env_type, kwargs: (_ for _ in ()).throw(
                    RuntimeError("captured")
                )
                try:
                    rlm.completion("test")
                except RuntimeError:
                    pass

                call_args = mock_get_env.call_args
                env_kwargs = call_args[0][1]
                assert "subcall_fn" not in env_kwargs

    def test_subcall_fn_passed_at_depth_gt_1(self):
        """max_depth>1 SHOULD pass subcall_fn to environment."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(done)"])
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=2,
            )

            with patch.object(rlm_module, "get_environment") as mock_get_env:
                mock_get_env.side_effect = lambda env_type, kwargs: (_ for _ in ()).throw(
                    RuntimeError("captured")
                )
                try:
                    rlm.completion("test")
                except RuntimeError:
                    pass

                call_args = mock_get_env.call_args
                env_kwargs = call_args[0][1]
                assert "subcall_fn" in env_kwargs
                assert env_kwargs["subcall_fn"] is not None


class TestDepth1LimitChecks:
    """Verify limit checks work correctly in the refactored helpers."""

    def test_timeout_check_raises(self):
        """_check_timeout should raise TimeoutExceededError when exceeded."""
        import time

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_timeout=10.0,
        )
        # Simulate start time 15 seconds ago
        fake_start = time.perf_counter() - 15.0

        with pytest.raises(TimeoutExceededError) as exc_info:
            rlm._check_timeout(0, fake_start)
        assert exc_info.value.elapsed > 10.0
        assert exc_info.value.timeout == 10.0

    def test_timeout_check_no_raise_within_limit(self):
        """_check_timeout should not raise when within limit."""
        import time

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_timeout=100.0,
        )
        fake_start = time.perf_counter() - 1.0
        # Should not raise
        rlm._check_timeout(0, fake_start)

    def test_timeout_check_noop_when_none(self):
        """_check_timeout should be a no-op when max_timeout is None."""
        import time

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_timeout=None,
        )
        # Even with a very old start time, should not raise
        rlm._check_timeout(0, time.perf_counter() - 99999)

    def test_error_threshold_check(self):
        """_check_iteration_limits should raise on consecutive errors."""
        from rlm.core.types import CodeBlock, REPLResult, RLMIteration

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_errors=2,
        )

        mock_handler = Mock()
        mock_handler.get_usage_summary.return_value = UsageSummary(
            model_usage_summaries={
                "test": ModelUsageSummary(
                    total_calls=1, total_input_tokens=10, total_output_tokens=10
                )
            }
        )

        error_result = REPLResult(stdout="", stderr="SyntaxError: bad", locals={}, rlm_calls=[])
        error_iteration = RLMIteration(
            prompt="test", response="code", code_blocks=[CodeBlock(code="bad", result=error_result)]
        )

        # First error
        rlm._check_iteration_limits(error_iteration, 0, mock_handler)
        assert rlm._consecutive_errors == 1

        # Second error should raise
        with pytest.raises(ErrorThresholdExceededError) as exc_info:
            rlm._check_iteration_limits(error_iteration, 1, mock_handler)
        assert exc_info.value.error_count == 2
        assert exc_info.value.threshold == 2

    def test_error_count_resets_on_success(self):
        """Consecutive error count should reset on a successful iteration."""
        from rlm.core.types import CodeBlock, REPLResult, RLMIteration

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_errors=3,
        )

        mock_handler = Mock()
        mock_handler.get_usage_summary.return_value = UsageSummary(
            model_usage_summaries={
                "test": ModelUsageSummary(
                    total_calls=1, total_input_tokens=10, total_output_tokens=10
                )
            }
        )

        error_result = REPLResult(stdout="", stderr="Error!", locals={}, rlm_calls=[])
        error_iter = RLMIteration(
            prompt="test", response="code", code_blocks=[CodeBlock(code="bad", result=error_result)]
        )

        ok_result = REPLResult(stdout="ok", stderr="", locals={}, rlm_calls=[])
        ok_iter = RLMIteration(
            prompt="test", response="code", code_blocks=[CodeBlock(code="good", result=ok_result)]
        )

        # Two errors
        rlm._check_iteration_limits(error_iter, 0, mock_handler)
        rlm._check_iteration_limits(error_iter, 1, mock_handler)
        assert rlm._consecutive_errors == 2

        # Success resets
        rlm._check_iteration_limits(ok_iter, 2, mock_handler)
        assert rlm._consecutive_errors == 0

    def test_budget_check_raises(self):
        """_check_iteration_limits should raise BudgetExceededError when budget exceeded."""
        from rlm.core.types import RLMIteration

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_budget=0.01,
        )

        mock_handler = Mock()
        mock_handler.get_usage_summary.return_value = UsageSummary(
            model_usage_summaries={
                "test": ModelUsageSummary(
                    total_calls=10,
                    total_input_tokens=10000,
                    total_output_tokens=10000,
                    total_cost=0.05,
                )
            }
        )

        iteration = RLMIteration(prompt="test", response="code", code_blocks=[])

        with pytest.raises(BudgetExceededError) as exc_info:
            rlm._check_iteration_limits(iteration, 0, mock_handler)
        assert exc_info.value.spent > 0.01
        assert exc_info.value.budget == 0.01

    def test_token_limit_check_raises(self):
        """_check_iteration_limits should raise TokenLimitExceededError when tokens exceeded."""
        from rlm.core.types import RLMIteration

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            max_tokens=100,
        )

        mock_handler = Mock()
        mock_handler.get_usage_summary.return_value = UsageSummary(
            model_usage_summaries={
                "test": ModelUsageSummary(
                    total_calls=1,
                    total_input_tokens=80,
                    total_output_tokens=80,
                )
            }
        )

        iteration = RLMIteration(prompt="test", response="code", code_blocks=[])

        with pytest.raises(TokenLimitExceededError) as exc_info:
            rlm._check_iteration_limits(iteration, 0, mock_handler)
        assert exc_info.value.tokens_used == 160
        assert exc_info.value.token_limit == 100


class TestDepth1LoggerMetadata:
    """Verify depth=1 logger metadata is captured correctly."""

    def test_completion_returns_metadata_with_logger(self):
        """When logger is provided, completion result should have metadata."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(42)"])
            mock_get_client.return_value = mock_lm

            logger = RLMLogger()
            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=1,
                logger=logger,
            )
            result = rlm.completion("What is the answer?")

            assert result.metadata is not None
            assert "run_metadata" in result.metadata
            assert "iterations" in result.metadata
            assert len(result.metadata["iterations"]) == 1
            assert result.metadata["run_metadata"]["root_model"] == "test-model"

    def test_completion_returns_no_metadata_without_logger(self):
        """When no logger is provided, metadata should be None."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(42)"])
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=1,
            )
            result = rlm.completion("What is the answer?")
            assert result.metadata is None

    def test_metadata_has_multiple_iterations(self):
        """Logger should capture all iterations."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(
                [
                    "Let me compute.\n```repl\nx = 1\n```",
                    "More work.\n```repl\ny = 2\n```",
                    "FINAL(done)",
                ]
            )
            mock_get_client.return_value = mock_lm

            logger = RLMLogger()
            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=1,
                logger=logger,
            )
            result = rlm.completion("compute")

            assert result.metadata is not None
            assert len(result.metadata["iterations"]) == 3


# ========================================================================
# depth>1 tests: verify subcall metadata propagation
# ========================================================================


class TestSubcallLoggerPropagation:
    """Verify child RLM gets a logger when parent has one, and metadata flows back."""

    def test_child_gets_logger_when_parent_has_logger(self):
        """When parent has a logger, child RLM should also get a logger."""
        captured_child_params = {}

        original_rlm_class = rlm_module.RLM

        class CapturingRLM(original_rlm_class):
            def __init__(self, *args, **kwargs):
                captured_child_params.update(kwargs)
                super().__init__(*args, **kwargs)

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"])
            mock_get_client.return_value = mock_lm

            logger = RLMLogger()
            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                max_depth=3,
                logger=logger,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            # Child should have received a logger
            child_logger = captured_child_params.get("logger")
            assert child_logger is not None
            assert isinstance(child_logger, RLMLogger)
            # But it should be a DIFFERENT instance from parent's logger
            assert child_logger is not logger

            parent.close()

    def test_child_gets_no_logger_when_parent_has_none(self):
        """When parent has no logger, child should also get None."""
        captured_child_params = {}

        original_rlm_class = rlm_module.RLM

        class CapturingRLM(original_rlm_class):
            def __init__(self, *args, **kwargs):
                captured_child_params.update(kwargs)
                super().__init__(*args, **kwargs)

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"])
            mock_get_client.return_value = mock_lm

            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                max_depth=3,
                logger=None,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("logger") is None

            parent.close()

    def test_leaf_subcall_returns_no_metadata(self):
        """At max_depth (leaf), subcall returns plain LM completion with no metadata."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["leaf response"] * 3)
            mock_get_client.return_value = mock_lm

            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                depth=1,
                max_depth=2,  # next_depth=2 >= max_depth=2 → leaf
                logger=RLMLogger(),
            )

            result = parent._subcall("test prompt")

            # Leaf completions don't use RLM, so no metadata
            assert result.metadata is None
            assert result.response == "leaf response"

            parent.close()

    def test_subcall_metadata_has_trajectory(self):
        """When child RLM completes with a logger, the returned RLMChatCompletion should have metadata."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            # Need enough responses: parent init + child init + child completion
            mock_lm = create_mock_lm(["FINAL(child answer)"] * 5, model_name="test-model")
            mock_get_client.return_value = mock_lm

            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                depth=0,
                max_depth=3,  # Allows child at depth=1 to have its own REPL
                logger=RLMLogger(),
            )

            result = parent._subcall("What is 2+2?")

            # Child should have returned metadata with trajectory
            assert result.metadata is not None
            assert "run_metadata" in result.metadata
            assert "iterations" in result.metadata
            assert len(result.metadata["iterations"]) >= 1

            parent.close()


class TestSubcallCustomToolsPropagation:
    """Verify custom_tools propagation to child RLM in _subcall."""

    def test_sub_tools_propagated_to_child(self):
        """Child should receive parent's custom_sub_tools as its custom_tools."""
        captured_child_params = {}

        original_rlm_class = rlm_module.RLM

        class CapturingRLM(original_rlm_class):
            def __init__(self, *args, **kwargs):
                captured_child_params.update(kwargs)
                super().__init__(*args, **kwargs)

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"])
            mock_get_client.return_value = mock_lm

            my_tool = lambda x: x * 2  # noqa: E731
            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=3,
                custom_tools={"double": my_tool},
                custom_sub_tools={"double": my_tool},
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert "double" in captured_child_params.get("custom_tools", {})
            assert "double" in captured_child_params.get("custom_sub_tools", {})

            parent.close()

    def test_empty_sub_tools_propagated(self):
        """When custom_sub_tools is empty dict, child should get empty dict (no tools)."""
        captured_child_params = {}

        original_rlm_class = rlm_module.RLM

        class CapturingRLM(original_rlm_class):
            def __init__(self, *args, **kwargs):
                captured_child_params.update(kwargs)
                super().__init__(*args, **kwargs)

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"])
            mock_get_client.return_value = mock_lm

            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test-model"},
                max_depth=3,
                custom_tools={"tool": lambda: 1},
                custom_sub_tools={},  # Explicitly no tools for children
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("custom_tools") == {}
            assert captured_child_params.get("custom_sub_tools") == {}

            parent.close()
