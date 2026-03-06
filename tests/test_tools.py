"""Tests for tool_prompts and tool_code functionality."""

import pytest

from rlm.environments.local_repl import LocalREPL
from rlm.utils.prompts import RLM_SYSTEM_PROMPT, append_prompt_sections


class TestAppendPromptSections:
    """Tests for append_prompt_sections helper."""

    def test_none_returns_base(self):
        assert append_prompt_sections("base", None) == "base"

    def test_empty_list_returns_base(self):
        assert append_prompt_sections("base", []) == "base"

    def test_list_of_empty_strings_returns_base(self):
        assert append_prompt_sections("base", ["", "  ", ""]) == "base"

    def test_single_section(self):
        result = append_prompt_sections("base", ["extra info"])
        assert result == "base\n\nextra info\n"

    def test_multiple_sections(self):
        result = append_prompt_sections("base", ["section1", "section2"])
        assert result == "base\n\nsection1\n\nsection2\n"

    def test_strips_whitespace_from_sections(self):
        result = append_prompt_sections("base", ["  padded  "])
        assert result == "base\n\npadded\n"

    def test_filters_out_empty_among_valid(self):
        result = append_prompt_sections("base", ["valid", "", "also valid"])
        assert result == "base\n\nvalid\n\nalso valid\n"

    def test_preserves_base_prompt_content(self):
        result = append_prompt_sections(RLM_SYSTEM_PROMPT, ["tool hint"])
        assert result.startswith(RLM_SYSTEM_PROMPT.rstrip())
        assert result.endswith("tool hint\n")


class TestToolCodeValidation:
    """Tests for tool_code syntax validation in RLM.__init__."""

    def test_invalid_tool_code_raises_value_error(self):
        from rlm.core.rlm import RLM

        with pytest.raises(ValueError, match="tool_code contains invalid Python syntax"):
            RLM(
                backend="openai",
                backend_kwargs={"model_name": "gpt-4"},
                tool_code="def broken(",
            )

    def test_none_tool_code_is_accepted(self):
        from rlm.core.rlm import RLM

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            tool_code=None,
        )
        assert rlm.tool_code is None

    def test_valid_tool_code_is_accepted(self):
        from rlm.core.rlm import RLM

        code = "def add(a, b):\n    return a + b\n"
        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            tool_code=code,
        )
        assert rlm.tool_code == code


class TestToolPromptsNormalization:
    """Tests for tool_prompts accepting str | list[str] | None."""

    def test_string_tool_prompts(self):
        from rlm.core.rlm import RLM

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            tool_prompts="You can call add(a, b).",
        )
        assert "You can call add(a, b)." in rlm.system_prompt

    def test_list_tool_prompts(self):
        from rlm.core.rlm import RLM

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            tool_prompts=["hint1", "hint2"],
        )
        assert "hint1" in rlm.system_prompt
        assert "hint2" in rlm.system_prompt

    def test_none_tool_prompts_uses_default(self):
        from rlm.core.rlm import RLM

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            tool_prompts=None,
        )
        assert rlm.system_prompt == RLM_SYSTEM_PROMPT


class TestToolCodeMerge:
    """Tests for tool_code merging with setup_code in environment kwargs."""

    def test_tool_code_only(self):
        """tool_code becomes setup_code when no existing setup_code."""
        from rlm.core.rlm import RLM

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            tool_code="x = 1",
        )
        # We can't easily test the merge without calling completion, so
        # verify the attribute is stored and will be used.
        assert rlm.tool_code == "x = 1"

    def test_both_setup_and_tool_code_order(self):
        """setup_code should run before tool_code when both are provided."""
        from rlm.core.rlm import RLM

        rlm = RLM(
            backend="openai",
            backend_kwargs={"model_name": "gpt-4"},
            environment_kwargs={"setup_code": "first = 1"},
            tool_code="second = 2",
        )
        # Simulate the merge logic that happens in _spawn_completion_context
        env_kwargs = rlm.environment_kwargs.copy()
        if rlm.tool_code and rlm.tool_code.strip():
            existing = env_kwargs.get("setup_code")
            if existing and existing.strip():
                env_kwargs["setup_code"] = existing.rstrip() + "\n\n" + rlm.tool_code.lstrip()
            else:
                env_kwargs["setup_code"] = rlm.tool_code

        merged = env_kwargs["setup_code"]
        first_pos = merged.index("first = 1")
        second_pos = merged.index("second = 2")
        assert first_pos < second_pos, "setup_code should come before tool_code"


class TestToolCodeInREPL:
    """End-to-end test: tool function defined via setup_code is callable."""

    def test_tool_function_callable_in_repl(self):
        setup = "def add(a, b):\n    return a + b\n"
        repl = LocalREPL(setup_code=setup)
        result = repl.execute_code("result = add(2, 3)\nprint(result)")
        assert result.stderr == ""
        assert "5" in result.stdout
        assert repl.locals["result"] == 5
        repl.cleanup()

    def test_setup_code_then_tool_code_both_available(self):
        combined = "base_val = 10\n\ndef multiply(a, b):\n    return a * b\n"
        repl = LocalREPL(setup_code=combined)
        result = repl.execute_code("result = multiply(base_val, 3)\nprint(result)")
        assert result.stderr == ""
        assert "30" in result.stdout
        repl.cleanup()
