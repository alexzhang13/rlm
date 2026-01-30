"""Tests for core types."""

from rlm.core.types import (
    CodeBlock,
    ModelUsageSummary,
    QueryMetadata,
    REPLResult,
    RLMIteration,
    RLMMetadata,
    UsageSummary,
    _serialize_value,
)


class TestSerializeValue:
    """Tests for _serialize_value helper."""

    def test_primitives(self):
        assert _serialize_value(None) is None
        assert _serialize_value(True) is True
        assert _serialize_value(42) == 42
        assert _serialize_value(3.14) == 3.14
        assert _serialize_value("hello") == "hello"

    def test_list(self):
        result = _serialize_value([1, 2, "three"])
        assert result == [1, 2, "three"]

    def test_dict(self):
        result = _serialize_value({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_callable(self):
        def my_func():
            pass

        result = _serialize_value(my_func)
        assert "function" in result.lower()
        assert "my_func" in result


class TestModelUsageSummary:
    """Tests for ModelUsageSummary."""

    def test_to_dict(self):
        summary = ModelUsageSummary(
            total_calls=10, total_input_tokens=1000, total_output_tokens=500
        )
        d = summary.to_dict()
        assert d["total_calls"] == 10
        assert d["total_input_tokens"] == 1000
        assert d["total_output_tokens"] == 500

    def test_from_dict(self):
        data = {
            "total_calls": 5,
            "total_input_tokens": 200,
            "total_output_tokens": 100,
        }
        summary = ModelUsageSummary.from_dict(data)
        assert summary.total_calls == 5
        assert summary.total_input_tokens == 200
        assert summary.total_output_tokens == 100


class TestUsageSummary:
    """Tests for UsageSummary."""

    def test_to_dict(self):
        model_summary = ModelUsageSummary(
            total_calls=1, total_input_tokens=10, total_output_tokens=5
        )
        summary = UsageSummary(model_usage_summaries={"gpt-4": model_summary})
        d = summary.to_dict()
        assert "gpt-4" in d["model_usage_summaries"]

    def test_from_dict(self):
        data = {
            "model_usage_summaries": {
                "gpt-4": {
                    "total_calls": 2,
                    "total_input_tokens": 50,
                    "total_output_tokens": 25,
                }
            }
        }
        summary = UsageSummary.from_dict(data)
        assert "gpt-4" in summary.model_usage_summaries
        assert summary.model_usage_summaries["gpt-4"].total_calls == 2


class TestREPLResult:
    """Tests for REPLResult."""

    def test_basic_creation(self):
        result = REPLResult(stdout="output", stderr="", locals={"x": 1})
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.locals == {"x": 1}

    def test_to_dict(self):
        result = REPLResult(stdout="hello", stderr="", locals={"num": 42}, execution_time=0.5)
        d = result.to_dict()
        assert d["stdout"] == "hello"
        assert d["locals"]["num"] == 42
        assert d["execution_time"] == 0.5

    def test_str_representation(self):
        result = REPLResult(stdout="test", stderr="", locals={})
        s = str(result)
        assert "REPLResult" in s
        assert "stdout=test" in s


class TestCodeBlock:
    """Tests for CodeBlock."""

    def test_to_dict(self):
        result = REPLResult(stdout="3", stderr="", locals={"x": 3})
        block = CodeBlock(code="x = 1 + 2", result=result)
        d = block.to_dict()
        assert d["code"] == "x = 1 + 2"
        assert d["result"]["stdout"] == "3"


class TestRLMIteration:
    """Tests for RLMIteration."""

    def test_basic_creation(self):
        iteration = RLMIteration(prompt="test prompt", response="test response", code_blocks=[])
        assert iteration.prompt == "test prompt"
        assert iteration.final_answer is None

    def test_with_final_answer(self):
        iteration = RLMIteration(
            prompt="test",
            response="FINAL(42)",
            code_blocks=[],
            final_answer=("FINAL", "42"),
        )
        assert iteration.final_answer == ("FINAL", "42")

    def test_to_dict(self):
        result = REPLResult(stdout="", stderr="", locals={})
        block = CodeBlock(code="pass", result=result)
        iteration = RLMIteration(
            prompt="p",
            response="r",
            code_blocks=[block],
            iteration_time=1.5,
        )
        d = iteration.to_dict()
        assert d["prompt"] == "p"
        assert d["response"] == "r"
        assert len(d["code_blocks"]) == 1
        assert d["iteration_time"] == 1.5


class TestQueryMetadata:
    """Tests for QueryMetadata."""

    def test_string_prompt(self):
        meta = QueryMetadata("Hello, world!")
        assert meta.context_type == "str"
        assert meta.context_total_length == 13
        assert meta.context_lengths == [13]


class TestRLMMetadata:
    """Tests for RLMMetadata."""

    def test_to_dict(self):
        meta = RLMMetadata(
            root_model="gpt-4",
            recursive_max_depth=2,
            max_iterations=10,
            backend="openai",
            backend_kwargs={"api_key": "secret"},
            environment_type="local",
            environment_kwargs={},
        )
        d = meta.to_dict()
        assert d["root_model"] == "gpt-4"
        assert d["recursive_max_depth"] == 2
        assert d["backend"] == "openai"
