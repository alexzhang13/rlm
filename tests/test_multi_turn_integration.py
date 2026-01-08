"""Integration tests for multi-turn persistent REPL sessions.

Tests that multiple LM completion calls in one RLM session:
1. Share the same environment
2. Accumulate contexts (context_0, context_1, ...)
3. Accumulate histories (history_0, history_1, ...)
4. Preserve variables across calls
5. Properly inform the model about available contexts/histories
"""

from unittest.mock import Mock, patch

import pytest

import rlm.core.rlm as rlm_module
from rlm import RLM
from rlm.core.types import ModelUsageSummary, UsageSummary


def create_mock_lm(responses: list[str]) -> Mock:
    """Create a mock LM that returns responses in order."""
    mock = Mock()
    mock.completion.side_effect = list(responses)
    mock.get_usage_summary.return_value = UsageSummary(
        model_usage_summaries={
            "mock": ModelUsageSummary(total_calls=1, total_input_tokens=100, total_output_tokens=50)
        }
    )
    mock.get_last_usage.return_value = mock.get_usage_summary.return_value
    return mock


class TestMultiTurnPersistentEnvironment:
    """Tests for environment persistence across completion calls."""

    def test_environment_reused_in_persistent_mode(self):
        """Verify the same environment instance is reused across completion calls."""
        responses = ["FINAL(answer from call)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("First context")
                first_env = rlm._persistent_env

                mock_lm.completion.side_effect = list(responses)

                rlm.completion("Second context")
                second_env = rlm._persistent_env

                assert first_env is second_env
                assert first_env is not None

    def test_context_accumulation_across_calls(self):
        """Verify contexts accumulate: context_0, context_1, etc."""
        responses = ["FINAL(got it)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("First document")
                mock_lm.completion.side_effect = list(responses)
                rlm.completion("Second document")
                mock_lm.completion.side_effect = list(responses)
                rlm.completion("Third document")

                env = rlm._persistent_env
                assert env.get_context_count() == 3
                assert env.locals["context_0"] == "First document"
                assert env.locals["context_1"] == "Second document"
                assert env.locals["context_2"] == "Third document"
                assert env.locals["context"] == "First document"

    def test_history_accumulation_across_calls(self):
        """Verify message histories accumulate: history_0, history_1, etc."""
        responses = ["FINAL(done)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("Context A")
                mock_lm.completion.side_effect = list(responses)
                rlm.completion("Context B")
                mock_lm.completion.side_effect = list(responses)
                rlm.completion("Context C")

                env = rlm._persistent_env
                assert env.get_history_count() == 3
                assert "history_0" in env.locals
                assert "history_1" in env.locals
                assert "history_2" in env.locals
                assert isinstance(env.locals["history_0"], list)
                assert len(env.locals["history_0"]) > 0
                assert env.locals["history"] == env.locals["history_0"]

    def test_variable_persistence_across_completions(self):
        """Variables computed in one completion should be available in subsequent ones."""
        first_responses = [
            "Let me compute something\n```repl\ncomputed_value = 42 * 2\nprint(computed_value)\n```",
            "FINAL(84)",
        ]
        second_responses = [
            "```repl\nresult = computed_value + 10\nprint(result)\n```",
            "FINAL(94)",
        ]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(first_responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("Compute 42 * 2")
                assert rlm._persistent_env.locals.get("computed_value") == 84

                mock_lm.completion.side_effect = list(second_responses)
                rlm.completion("Add 10 to the previous result")

                assert rlm._persistent_env.locals.get("computed_value") == 84
                assert rlm._persistent_env.locals.get("result") == 94


class TestMultiTurnPromptAwareness:
    """Tests that prompts correctly inform the model about contexts/histories."""

    def test_prompt_includes_context_count(self):
        """Model should be informed about available contexts."""
        responses = ["FINAL(ok)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("First")
                mock_lm.completion.side_effect = list(responses)
                rlm.completion("Second")

                last_prompt = mock_lm.completion.call_args[0][0]
                user_messages = [m for m in last_prompt if m.get("role") == "user"]
                user_content = " ".join(m.get("content", "") for m in user_messages)

                assert "2 contexts" in user_content or "context_0" in user_content

    def test_prompt_includes_history_count(self):
        """Model should be informed about available histories."""
        responses = ["FINAL(ok)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("First task")
                mock_lm.completion.side_effect = list(responses)
                rlm.completion("Second task")

                last_prompt = mock_lm.completion.call_args[0][0]
                user_messages = [m for m in last_prompt if m.get("role") == "user"]
                user_content = " ".join(m.get("content", "") for m in user_messages)

                assert "history" in user_content.lower()


class TestMultiTurnCodeExecution:
    """Tests for code execution in multi-turn sessions."""

    def test_can_access_previous_context_in_code(self):
        """Code should be able to reference earlier contexts."""
        first_responses = ["FINAL(first done)"]
        second_responses = [
            "```repl\nprint(f'First: {context_0}, Second: {context_1}')\n```",
            "FINAL(printed both)",
        ]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(first_responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("Document A")

                mock_lm.completion.side_effect = list(second_responses)
                rlm.completion("Document B")

                env = rlm._persistent_env
                assert env.locals["context_0"] == "Document A"
                assert env.locals["context_1"] == "Document B"

    def test_can_access_history_in_code(self):
        """Code should be able to reference stored histories."""
        first_responses = ["FINAL(first)"]
        second_responses = [
            "```repl\nprint(f'History entries: {len(history)}')\n```",
            "FINAL(accessed history)",
        ]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(first_responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("First query")

                mock_lm.completion.side_effect = list(second_responses)
                rlm.completion("Second query")

                env = rlm._persistent_env
                assert "history" in env.locals
                assert isinstance(env.locals["history"], list)


class TestNonPersistentMode:
    """Tests to ensure non-persistent mode still works correctly."""

    def test_non_persistent_creates_fresh_environment(self):
        """Non-persistent mode should create new environment each call."""
        responses = ["FINAL(done)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=False,
            )

            rlm.completion("First")
            assert rlm._persistent_env is None

            mock_lm.completion.side_effect = list(responses)
            rlm.completion("Second")
            assert rlm._persistent_env is None

    def test_default_is_non_persistent(self):
        """Default behavior should be non-persistent."""
        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
        )
        assert rlm.persistent is False


class TestPersistentModeResourceManagement:
    """Tests for proper resource cleanup in persistent mode."""

    def test_context_manager_cleanup(self):
        """Environment should be cleaned up when exiting context manager."""
        responses = ["FINAL(done)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                rlm.completion("Test")
                assert rlm._persistent_env is not None

            assert rlm._persistent_env is None

    def test_explicit_close(self):
        """Calling close() should clean up persistent environment."""
        responses = ["FINAL(done)"]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(responses)
            mock_get_client.return_value = mock_lm

            rlm = RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            )
            rlm.completion("Test")
            assert rlm._persistent_env is not None

            rlm.close()
            assert rlm._persistent_env is None


class TestPersistentModeValidation:
    """Tests for persistent mode validation."""

    def test_unsupported_environment_raises_error(self):
        """Persistent mode should raise error for unsupported environments."""
        with pytest.raises(ValueError, match="persistent=True is not supported"):
            RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                environment="docker",  # Not supported for persistent
                persistent=True,
            )

    def test_local_environment_supported(self):
        """Local environment should support persistent mode."""
        # Should not raise
        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "test"},
            environment="local",
            persistent=True,
        )
        assert rlm.persistent is True


class TestMultiTurnEndToEnd:
    """End-to-end tests simulating realistic multi-turn usage."""

    def test_three_turn_conversation(self):
        """Simulate a 3-turn conversation with context accumulation."""
        turn1_responses = [
            "Looking at the first document\n```repl\ndoc1_summary = 'Has info about cats'\nprint(doc1_summary)\n```",
            "FINAL(Summarized first doc)",
        ]
        turn2_responses = [
            "Looking at second document and comparing\n```repl\ndoc2_summary = 'Has info about dogs'\nprint(f'Doc1: {doc1_summary}, Doc2: {doc2_summary}')\n```",
            "FINAL(Compared both docs)",
        ]
        turn3_responses = [
            "Final synthesis\n```repl\nfinal = f'Combined: {doc1_summary} and {doc2_summary} from context_2'\nprint(final)\n```",
            "FINAL(synthesized all)",
        ]

        with patch.object(rlm_module, "get_client") as mock_get_client:
            mock_lm = create_mock_lm(turn1_responses)
            mock_get_client.return_value = mock_lm

            with RLM(
                backend="openai",
                backend_kwargs={"model_name": "test"},
                persistent=True,
            ) as rlm:
                result1 = rlm.completion("First document about cats")
                assert "Summarized" in result1.response

                mock_lm.completion.side_effect = list(turn2_responses)
                result2 = rlm.completion("Second document about dogs")
                assert "Compared" in result2.response

                mock_lm.completion.side_effect = list(turn3_responses)
                result3 = rlm.completion("Synthesize everything")
                assert "synthesized" in result3.response

                env = rlm._persistent_env
                assert env.get_context_count() == 3
                assert env.get_history_count() == 3
                assert env.locals.get("doc1_summary") == "Has info about cats"
                assert env.locals.get("doc2_summary") == "Has info about dogs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
