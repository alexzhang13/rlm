"""Unit tests for RLM._subcall() method.

Tests for the parameter propagation to child RLM instances:
1. max_timeout (remaining time) is passed to child
2. max_tokens is passed to child
3. max_errors is passed to child
4. model= parameter overrides child's backend model
"""

import time
from unittest.mock import Mock, patch

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.core.types import ModelUsageSummary, UsageSummary


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


class TestSubcallTimeoutPropagation:
    """Tests for max_timeout propagation to child RLM."""

    def test_child_receives_remaining_timeout(self):
        """When parent has max_timeout=60 and 10s have elapsed, child should get max_timeout approx 50."""
        captured_child_params = {}

        # Create a fake child RLM class to capture initialization params
        original_rlm_class = rlm_module.RLM

        class CapturingRLM(original_rlm_class):
            def __init__(self, *args, **kwargs):
                # Capture the kwargs before calling parent
                captured_child_params.update(kwargs)
                super().__init__(*args, **kwargs)

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"])
            mock_get_client.return_value = mock_lm

            # Create parent RLM with max_timeout
            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                max_depth=3,  # Need depth > 1 to allow child spawning
                max_timeout=60.0,
            )

            # Simulate that 10 seconds have elapsed since completion started
            parent._completion_start_time = time.perf_counter() - 10.0

            # Patch RLM class to capture child creation
            with patch.object(rlm_module, "RLM", CapturingRLM):
                # Call _subcall which should spawn a child RLM
                parent._subcall("test prompt")

            # Verify child received remaining timeout (approximately 50 seconds)
            assert "max_timeout" in captured_child_params
            remaining = captured_child_params["max_timeout"]
            # Allow some tolerance for test execution time
            assert 45.0 < remaining < 55.0, f"Expected ~50s remaining, got {remaining}"

            parent.close()

    def test_child_receives_none_timeout_when_parent_has_none(self):
        """When parent has no max_timeout, child should also have None."""
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
                max_timeout=None,  # No timeout
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("max_timeout") is None

            parent.close()

    def test_subcall_returns_error_when_timeout_exhausted(self):
        """When timeout is already exhausted, _subcall should return error message."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"])
            mock_get_client.return_value = mock_lm

            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                max_depth=3,
                max_timeout=10.0,
            )

            # Simulate that more time has elapsed than the timeout
            parent._completion_start_time = time.perf_counter() - 15.0

            result = parent._subcall("test prompt")

            assert "Error: Timeout exhausted" in result.response

            parent.close()


class TestSubcallTokensPropagation:
    """Tests for max_tokens propagation to child RLM."""

    def test_child_receives_max_tokens(self):
        """Child RLM should get same max_tokens as parent."""
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
                max_tokens=50000,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("max_tokens") == 50000

            parent.close()

    def test_child_receives_none_tokens_when_parent_has_none(self):
        """When parent has no max_tokens, child should also have None."""
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
                max_tokens=None,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("max_tokens") is None

            parent.close()


class TestSubcallErrorsPropagation:
    """Tests for max_errors propagation to child RLM."""

    def test_child_receives_max_errors(self):
        """Child RLM should get same max_errors as parent."""
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
                max_errors=5,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("max_errors") == 5

            parent.close()

    def test_child_receives_none_errors_when_parent_has_none(self):
        """When parent has no max_errors, child should also have None."""
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
                max_errors=None,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt")

            assert captured_child_params.get("max_errors") is None

            parent.close()


class TestSubcallModelOverride:
    """Tests for model= parameter override in _subcall."""

    def test_model_override_sets_child_backend_kwargs(self):
        """When llm_query(prompt, model='test-model') is called, child's backend_kwargs should have model_name='test-model'."""
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
                backend_kwargs={"model_name": "parent-model", "api_key": "test-key"},
                max_depth=3,
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                # Call _subcall with model override
                parent._subcall("test prompt", model="override-model")

            # Verify child received overridden model in backend_kwargs
            child_backend_kwargs = captured_child_params.get("backend_kwargs", {})
            assert child_backend_kwargs.get("model_name") == "override-model"
            # Original kwargs should be preserved
            assert child_backend_kwargs.get("api_key") == "test-key"

            parent.close()

    def test_model_override_does_not_mutate_parent_kwargs(self):
        """Model override should not mutate parent's backend_kwargs."""
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
            )

            original_model = parent.backend_kwargs["model_name"]

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt", model="override-model")

            # Parent's backend_kwargs should be unchanged
            assert parent.backend_kwargs["model_name"] == original_model

            parent.close()

    def test_no_model_override_uses_parent_kwargs(self):
        """When no model override is provided, child uses parent's backend_kwargs."""
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
            )

            with patch.object(rlm_module, "RLM", CapturingRLM):
                # Call _subcall without model override
                parent._subcall("test prompt")

            # Child should use parent's backend_kwargs
            child_backend_kwargs = captured_child_params.get("backend_kwargs", {})
            assert child_backend_kwargs.get("model_name") == "parent-model"

            parent.close()


class TestSubcallModelOverrideAtLeafDepth:
    """Tests for model override at max_depth (leaf LM completion)."""

    def test_model_override_at_leaf_depth_uses_overridden_model(self):
        """When at max_depth, the leaf LM completion should use the overridden model."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["leaf response"])
            mock_get_client.return_value = mock_lm

            # Parent at depth 1, max_depth 2 means next depth (2) will be at max_depth
            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                depth=1,
                max_depth=2,
            )

            # Call _subcall with model override - should trigger leaf LM completion
            result = parent._subcall("test prompt", model="leaf-override-model")

            # Verify get_client was called with overridden model in backend_kwargs
            # The call should be: get_client("openai", {"model_name": "leaf-override-model"})
            call_args = mock_get_client.call_args_list
            # Find the call that has the overridden model
            found_override_call = False
            for call in call_args:
                args, kwargs = call
                if len(args) >= 2:
                    backend_kwargs = args[1]
                    if (
                        isinstance(backend_kwargs, dict)
                        and backend_kwargs.get("model_name") == "leaf-override-model"
                    ):
                        found_override_call = True
                        break

            assert found_override_call, (
                f"Expected get_client to be called with model_name='leaf-override-model', got calls: {call_args}"
            )
            assert result.response == "leaf response"

            parent.close()

    def test_leaf_depth_without_model_override_uses_parent_model(self):
        """When at max_depth without model override, uses parent's model."""
        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(["FINAL(answer)"] * 2 + ["leaf response"])
            mock_get_client.return_value = mock_lm

            # Parent at depth 1, max_depth 2 means next depth (2) will be at max_depth
            parent = RLM(
                backend="openai",
                backend_kwargs={"model_name": "parent-model"},
                depth=1,
                max_depth=2,
            )

            # Call _subcall without model override
            parent._subcall("test prompt")

            # Verify get_client was called with parent's model
            # The last call should use the parent's backend_kwargs
            call_args = mock_get_client.call_args_list
            # Check the most recent call (for leaf completion)
            last_call = call_args[-1]
            args, _ = last_call
            if len(args) >= 2:
                backend_kwargs = args[1]
                assert backend_kwargs.get("model_name") == "parent-model"

            parent.close()


class TestSubcallCombinedParameters:
    """Tests for combined parameter propagation."""

    def test_all_parameters_propagate_together(self):
        """All parameters (timeout, tokens, errors, model) should propagate correctly together."""
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
                backend_kwargs={"model_name": "parent-model", "api_key": "test-key"},
                max_depth=3,
                max_timeout=120.0,
                max_tokens=100000,
                max_errors=10,
            )

            # Simulate 30 seconds elapsed
            parent._completion_start_time = time.perf_counter() - 30.0

            with patch.object(rlm_module, "RLM", CapturingRLM):
                parent._subcall("test prompt", model="override-model")

            # Verify all parameters
            assert captured_child_params.get("max_tokens") == 100000
            assert captured_child_params.get("max_errors") == 10

            # Remaining timeout should be around 90 seconds
            remaining_timeout = captured_child_params.get("max_timeout")
            assert 85.0 < remaining_timeout < 95.0

            # Model should be overridden
            child_backend_kwargs = captured_child_params.get("backend_kwargs", {})
            assert child_backend_kwargs.get("model_name") == "override-model"
            assert child_backend_kwargs.get("api_key") == "test-key"

            parent.close()
