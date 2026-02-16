"""
Tests for custom tools support in REPL environments.

These tests verify that all REPL implementations correctly handle custom tools:
- Callable tools are available as functions
- Non-callable tools are available as variables
- Reserved names cannot be overridden

Run with: uv run pytest tests/repl/test_custom_tools.py -v
"""

import pytest

from rlm.environments import (
    RESERVED_TOOL_NAMES,
    SupportsCustomTools,
    extract_tool_value,
    format_tools_for_prompt,
    parse_custom_tools,
    parse_tool_entry,
    validate_custom_tools,
)
from rlm.environments.local_repl import LocalREPL

# =============================================================================
# Test Fixtures
# =============================================================================


def sample_tool_function(x: int) -> int:
    """A simple test function."""
    return x * 2


def another_tool_function(a: str, b: str) -> str:
    """Another test function."""
    return f"{a}-{b}"


@pytest.fixture
def custom_tools():
    """Standard set of custom tools for testing."""
    return {
        "double": sample_tool_function,
        "concat": another_tool_function,
        "CONFIG": {"key": "value", "number": 42},
        "CONSTANT": "hello world",
    }


# =============================================================================
# Base Validation Tests (no environment needed)
# =============================================================================


class TestValidateCustomTools:
    """Tests for the validate_custom_tools function."""

    def test_none_is_valid(self):
        """None custom_tools should pass validation."""
        validate_custom_tools(None)  # Should not raise

    def test_empty_dict_is_valid(self):
        """Empty dict should pass validation."""
        validate_custom_tools({})  # Should not raise

    def test_valid_tools_pass(self, custom_tools):
        """Valid custom tools should pass validation."""
        validate_custom_tools(custom_tools)  # Should not raise

    @pytest.mark.parametrize("reserved_name", list(RESERVED_TOOL_NAMES))
    def test_reserved_names_rejected(self, reserved_name):
        """Each reserved name should be rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_custom_tools({reserved_name: lambda: None})
        assert reserved_name in str(exc_info.value)
        assert "reserved" in str(exc_info.value).lower()

    def test_multiple_reserved_names_all_reported(self):
        """When multiple reserved names are used, all should be reported."""
        tools = {"llm_query": 1, "FINAL_VAR": 2, "valid_name": 3}
        with pytest.raises(ValueError) as exc_info:
            validate_custom_tools(tools)
        error_msg = str(exc_info.value)
        assert "llm_query" in error_msg
        assert "FINAL_VAR" in error_msg

    def test_reserved_names_constant_is_frozen(self):
        """RESERVED_TOOL_NAMES should be immutable."""
        assert isinstance(RESERVED_TOOL_NAMES, frozenset)
        with pytest.raises(AttributeError):
            RESERVED_TOOL_NAMES.add("new_name")


# =============================================================================
# REPL Environment Tests
# =============================================================================


class TestLocalREPLCustomTools:
    """Tests for custom tools in LocalREPL."""

    def test_supports_custom_tools_protocol(self):
        """LocalREPL should implement SupportsCustomTools protocol."""
        repl = LocalREPL(custom_tools={"test": lambda: 1})
        assert isinstance(repl, SupportsCustomTools)
        repl.cleanup()

    def test_callable_tool_available(self, custom_tools):
        """Callable tools should be available as functions."""
        repl = LocalREPL(custom_tools=custom_tools)

        result = repl.execute_code("result = double(21)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == 42

        repl.cleanup()

    def test_callable_tool_with_args(self, custom_tools):
        """Callable tools should work with multiple arguments."""
        repl = LocalREPL(custom_tools=custom_tools)

        result = repl.execute_code('result = concat("hello", "world")')
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == "hello-world"

        repl.cleanup()

    def test_non_callable_dict_available(self, custom_tools):
        """Non-callable dict tools should be available as variables."""
        repl = LocalREPL(custom_tools=custom_tools)

        result = repl.execute_code('result = CONFIG["key"]')
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == "value"

        repl.cleanup()

    def test_non_callable_string_available(self, custom_tools):
        """Non-callable string tools should be available as variables."""
        repl = LocalREPL(custom_tools=custom_tools)

        result = repl.execute_code("result = CONSTANT.upper()")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == "HELLO WORLD"

        repl.cleanup()

    def test_tools_persist_across_executions(self, custom_tools):
        """Custom tools should remain available across multiple executions."""
        repl = LocalREPL(custom_tools=custom_tools)

        repl.execute_code("x = double(5)")
        result = repl.execute_code("y = double(x)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("y") == 20

        repl.cleanup()

    def test_reserved_name_raises_on_init(self):
        """Using a reserved name should raise ValueError during initialization."""
        with pytest.raises(ValueError) as exc_info:
            LocalREPL(custom_tools={"llm_query": lambda: None})
        assert "llm_query" in str(exc_info.value)

    def test_empty_custom_tools(self):
        """Empty custom_tools dict should work fine."""
        repl = LocalREPL(custom_tools={})

        result = repl.execute_code("x = 1 + 1")
        assert result.stderr == ""
        assert repl.locals.get("x") == 2

        repl.cleanup()

    def test_none_custom_tools(self):
        """None custom_tools should work fine (default behavior)."""
        repl = LocalREPL(custom_tools=None)

        result = repl.execute_code("x = 1 + 1")
        assert result.stderr == ""
        assert repl.locals.get("x") == 2

        repl.cleanup()

    def test_builtin_functions_still_work(self, custom_tools):
        """Built-in REPL functions should still work with custom tools."""
        repl = LocalREPL(custom_tools=custom_tools)

        # FINAL_VAR should still work
        repl.execute_code("answer = double(21)")
        result = repl.execute_code('print(FINAL_VAR("answer"))')
        assert "42" in result.stdout

        # SHOW_VARS should still work
        result = repl.execute_code("print(SHOW_VARS())")
        assert "answer" in result.stdout

        repl.cleanup()


class TestCustomToolsWithContext:
    """Tests for custom tools interacting with context."""

    def test_tools_can_access_context(self):
        """Custom tools should be able to work with context data."""

        def process_context(ctx):
            return f"Processed: {ctx['name']}"

        repl = LocalREPL(
            custom_tools={"process_context": process_context},
            context_payload={"name": "test_data"},
        )

        result = repl.execute_code("result = process_context(context)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == "Processed: test_data"

        repl.cleanup()

    def test_tools_with_string_context(self):
        """Custom tools should work with string context."""

        def count_words(text):
            return len(text.split())

        repl = LocalREPL(
            custom_tools={"count_words": count_words},
            context_payload="hello world from test",
        )

        result = repl.execute_code("result = count_words(context)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == 4

        repl.cleanup()


class TestCustomToolsEdgeCases:
    """Edge case tests for custom tools."""

    def test_tool_that_raises_exception(self):
        """Tools that raise exceptions should propagate errors properly."""

        def failing_tool():
            raise ValueError("Tool failed!")

        repl = LocalREPL(custom_tools={"failing_tool": failing_tool})

        result = repl.execute_code("result = failing_tool()")
        assert "ValueError" in result.stderr
        assert "Tool failed!" in result.stderr

        repl.cleanup()

    def test_tool_with_closure(self):
        """Tools with closures should work correctly."""
        multiplier = 10

        def multiply(x):
            return x * multiplier

        repl = LocalREPL(custom_tools={"multiply": multiply})

        result = repl.execute_code("result = multiply(5)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == 50

        repl.cleanup()

    def test_tool_returning_none(self):
        """Tools returning None should work correctly."""

        def returns_none():
            return None

        repl = LocalREPL(custom_tools={"returns_none": returns_none})

        result = repl.execute_code("result = returns_none()")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") is None

        repl.cleanup()

    def test_lambda_tool(self):
        """Lambda functions should work as tools."""
        repl = LocalREPL(custom_tools={"square": lambda x: x**2})

        result = repl.execute_code("result = square(7)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == 49

        repl.cleanup()

    def test_class_instance_as_tool(self):
        """Class instances with __call__ should work as tools."""

        class Adder:
            def __init__(self, n):
                self.n = n

            def __call__(self, x):
                return x + self.n

        repl = LocalREPL(custom_tools={"add_five": Adder(5)})

        result = repl.execute_code("result = add_five(10)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == 15

        repl.cleanup()

    def test_tool_name_shadowing_import(self):
        """Custom tools shouldn't prevent importing modules with same name."""
        repl = LocalREPL(custom_tools={"json": "not the real json"})

        # The custom tool should be a string variable
        result = repl.execute_code("result = json")
        assert repl.locals.get("result") == "not the real json"

        # But we should still be able to import the real json module
        result = repl.execute_code(
            "import json as json_module; result2 = json_module.dumps({'a': 1})"
        )
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result2") == '{"a": 1}'

        repl.cleanup()


# =============================================================================
# Tool Description Tests
# =============================================================================


class TestParseToolEntry:
    """Tests for parse_tool_entry function."""

    def test_plain_callable(self):
        """Plain callable should have no description."""

        def func(x):
            return x * 2

        info = parse_tool_entry("my_func", func)

        assert info.name == "my_func"
        assert info.value is func
        assert info.description is None
        assert info.is_callable is True

    def test_plain_value(self):
        """Plain value should have no description."""
        info = parse_tool_entry("config", ["a", "b", "c"])

        assert info.name == "config"
        assert info.value == ["a", "b", "c"]
        assert info.description is None
        assert info.is_callable is False

    def test_dict_with_description(self):
        """Dict with 'tool' and 'description' keys should extract both."""

        def func(x):
            return x * 2

        info = parse_tool_entry("my_func", {"tool": func, "description": "Doubles the input"})

        assert info.name == "my_func"
        assert info.value is func
        assert info.description == "Doubles the input"
        assert info.is_callable is True

    def test_dict_value_with_description(self):
        """Non-callable with description."""
        info = parse_tool_entry(
            "config", {"tool": {"key": "value"}, "description": "Configuration settings"}
        )

        assert info.name == "config"
        assert info.value == {"key": "value"}
        assert info.description == "Configuration settings"
        assert info.is_callable is False

    def test_dict_with_tool_but_no_description(self):
        """Dict with 'tool' key but no description."""

        def func(x):
            return x

        info = parse_tool_entry("my_func", {"tool": func})

        assert info.name == "my_func"
        assert info.value is func
        assert info.description is None

    def test_plain_dict_without_tool_key(self):
        """Plain dict without 'tool' key should be treated as data value."""
        info = parse_tool_entry("config", {"key": "value", "other": 123})

        assert info.name == "config"
        assert info.value == {"key": "value", "other": 123}
        assert info.description is None
        assert info.is_callable is False


class TestExtractToolValue:
    """Tests for extract_tool_value function."""

    def test_plain_value(self):
        """Plain value should be returned as-is."""
        assert extract_tool_value(42) == 42
        assert extract_tool_value("hello") == "hello"

    def test_plain_callable(self):
        """Plain callable should be returned as-is."""

        def func(x):
            return x

        assert extract_tool_value(func) is func

    def test_dict_with_tool_key(self):
        """Dict with 'tool' key should return just the tool value."""

        def func(x):
            return x

        assert extract_tool_value({"tool": func, "description": "desc"}) is func
        assert extract_tool_value({"tool": {"key": "val"}, "description": "config"}) == {
            "key": "val"
        }

    def test_plain_dict_without_tool_key(self):
        """Dict without 'tool' key should return whole dict."""
        assert extract_tool_value({"key": "val"}) == {"key": "val"}
        assert extract_tool_value({"a": 1, "b": 2}) == {"a": 1, "b": 2}


class TestParseCustomTools:
    """Tests for parse_custom_tools function."""

    def test_none_returns_empty_list(self):
        """None should return empty list."""
        assert parse_custom_tools(None) == []

    def test_empty_dict_returns_empty_list(self):
        """Empty dict should return empty list."""
        assert parse_custom_tools({}) == []

    def test_mixed_tools(self):
        """Mix of plain and described tools."""

        def func1(x):
            return x

        def func2(x):
            return x * 2

        tools = {
            "plain_func": func1,
            "described_func": {"tool": func2, "description": "Doubles input"},
            "plain_data": [1, 2, 3],
            "described_data": {"tool": [1, 2, 3], "description": "A list of numbers"},
        }

        infos = parse_custom_tools(tools)
        assert len(infos) == 4

        # Find each by name
        by_name = {info.name: info for info in infos}

        assert by_name["plain_func"].description is None
        assert by_name["described_func"].description == "Doubles input"
        assert by_name["plain_data"].description is None
        assert by_name["described_data"].description == "A list of numbers"


class TestFormatToolsForPrompt:
    """Tests for format_tools_for_prompt function."""

    def test_none_returns_none(self):
        """None tools should return None."""
        assert format_tools_for_prompt(None) is None

    def test_empty_returns_none(self):
        """Empty tools should return None."""
        assert format_tools_for_prompt({}) is None

    def test_callable_with_description(self):
        """Callable with description should show description."""
        tools = {"my_func": {"tool": lambda x: x, "description": "Does something useful"}}
        result = format_tools_for_prompt(tools)

        assert "my_func" in result
        assert "Does something useful" in result

    def test_callable_without_description(self):
        """Callable without description should show generic message."""
        tools = {"my_func": lambda x: x}
        result = format_tools_for_prompt(tools)

        assert "my_func" in result
        assert "custom function" in result.lower()

    def test_value_with_description(self):
        """Value with description should show description."""
        tools = {"config": {"tool": ["a", "b", "c"], "description": "Configuration settings"}}
        result = format_tools_for_prompt(tools)

        assert "config" in result
        assert "Configuration settings" in result

    def test_value_without_description(self):
        """Value without description should show type."""
        tools = {"config": ["a", "b", "c"]}
        result = format_tools_for_prompt(tools)

        assert "config" in result
        assert "list" in result.lower()

    def test_multiple_tools_formatted(self):
        """Multiple tools should all appear in output."""
        tools = {
            "func1": {"tool": lambda x: x, "description": "First function"},
            "func2": lambda x: x,
            "data1": {"tool": [1, 2, 3], "description": "Some data"},
            "data2": "plain string",
        }
        result = format_tools_for_prompt(tools)

        assert "func1" in result
        assert "First function" in result
        assert "func2" in result
        assert "data1" in result
        assert "Some data" in result
        assert "data2" in result


class TestToolsWithDescriptionsInREPL:
    """Tests for tools with descriptions in LocalREPL."""

    def test_callable_with_description_works(self):
        """Callable tool with description should work in REPL."""
        repl = LocalREPL(
            custom_tools={
                "double": {"tool": lambda x: x * 2, "description": "Doubles the input value"},
            }
        )

        result = repl.execute_code("result = double(21)")
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == 42

        repl.cleanup()

    def test_value_with_description_works(self):
        """Value tool with description should work in REPL."""
        repl = LocalREPL(
            custom_tools={
                "CONFIG": {"tool": {"api_key": "test123"}, "description": "API configuration"},
            }
        )

        result = repl.execute_code('result = CONFIG["api_key"]')
        assert result.stderr == "", f"Unexpected error: {result.stderr}"
        assert repl.locals.get("result") == "test123"

        repl.cleanup()

    def test_mixed_tools_with_descriptions(self):
        """Mix of described and undescribed tools should work."""
        repl = LocalREPL(
            custom_tools={
                "described_func": {"tool": lambda x: x + 1, "description": "Adds one"},
                "plain_func": lambda x: x - 1,
                "described_data": {"tool": 100, "description": "A constant"},
                "plain_data": 200,
            }
        )

        repl.execute_code("a = described_func(5)")
        repl.execute_code("b = plain_func(5)")
        repl.execute_code("c = described_data")
        repl.execute_code("d = plain_data")

        assert repl.locals.get("a") == 6
        assert repl.locals.get("b") == 4
        assert repl.locals.get("c") == 100
        assert repl.locals.get("d") == 200

        repl.cleanup()

    def test_described_tools_validate_reserved_names(self):
        """Described tools should still validate against reserved names."""
        with pytest.raises(ValueError) as exc_info:
            LocalREPL(
                custom_tools={
                    "llm_query": {"tool": lambda x: x, "description": "Override attempt"},
                }
            )
        assert "llm_query" in str(exc_info.value)
