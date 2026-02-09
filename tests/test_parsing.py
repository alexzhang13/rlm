"""Tests for parsing utilities."""

from unittest.mock import Mock

from rlm.core.types import CodeBlock, REPLResult, RLMIteration
from rlm.environments.local_repl import LocalREPL
from rlm.utils.parsing import (
    convert_context_for_repl,
    find_code_blocks,
    find_final_answer,
    format_execution_result,
    format_iteration,
)


class TestFindCodeBlocks:
    """Tests for find_code_blocks function."""

    def test_single_code_block(self):
        text = """Here's some code:
```repl
x = 1 + 2
print(x)
```
Done."""
        blocks = find_code_blocks(text)
        assert len(blocks) == 1
        assert "x = 1 + 2" in blocks[0]
        assert "print(x)" in blocks[0]

    def test_multiple_code_blocks(self):
        text = """First block:
```repl
a = 1
```
Second block:
```repl
b = 2
```
End."""
        blocks = find_code_blocks(text)
        assert len(blocks) == 2
        assert "a = 1" in blocks[0]
        assert "b = 2" in blocks[1]

    def test_no_code_blocks(self):
        text = "Just plain text without any code blocks."
        blocks = find_code_blocks(text)
        assert blocks == []

    def test_non_repl_code_blocks_ignored(self):
        text = """Python block:
```python
x = 1
```
REPL block:
```repl
y = 2
```
"""
        blocks = find_code_blocks(text)
        assert len(blocks) == 1
        assert "y = 2" in blocks[0]

    def test_multiline_code_block(self):
        text = """```repl
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
print(result)
```"""
        blocks = find_code_blocks(text)
        assert len(blocks) == 1
        assert "def factorial(n):" in blocks[0]
        assert "return n * factorial(n - 1)" in blocks[0]


class TestFindFinalAnswer:
    """Tests for find_final_answer function."""

    def test_final_answer(self):
        text = "The answer is:\nFINAL(42)"
        result = find_final_answer(text)
        assert result == "42"

    def test_final_var_answer(self):
        text = "Check the variable:\nFINAL_VAR(result)"
        # Create a mock environment that returns the variable value
        mock_env = Mock()
        mock_env.execute_code.return_value = REPLResult(stdout="42", stderr="", locals={})
        result = find_final_answer(text, environment=mock_env)
        assert result == "42"
        # Verify execute_code was called with the correct code
        mock_env.execute_code.assert_called_once()
        call_args = mock_env.execute_code.call_args[0][0]
        assert "FINAL_VAR('result')" in call_args or 'FINAL_VAR("result")' in call_args

    def test_final_var_without_environment(self):
        text = "Check the variable:\nFINAL_VAR(result)"
        # Without environment, FINAL_VAR should return None
        result = find_final_answer(text)
        assert result is None

    def test_no_final_answer(self):
        text = "Still working on the problem..."
        result = find_final_answer(text)
        assert result is None

    def test_final_with_multiline_content(self):
        text = """FINAL(This is a
multiline answer)"""
        result = find_final_answer(text)
        assert result is not None
        assert "multiline" in result
        assert "This is a" in result

    def test_final_must_be_at_start_of_line(self):
        # FINAL not at start of line should not match
        text = "The result is FINAL(42)"
        result = find_final_answer(text)
        assert result is None

    def test_final_with_whitespace(self):
        text = "   FINAL(answer with spaces)"
        result = find_final_answer(text)
        assert result == "answer with spaces"

    def test_final_with_nested_parentheses_greedy_matching(self):
        """Test that greedy matching captures content with nested parentheses correctly.
        Greedy matching (.*) matches to the last closing parenthesis, correctly handling
        nested parentheses in FINAL() content. Non-greedy (.*?) would incorrectly stop
        at the first closing parenthesis, breaking functions, tuples, and nested structures.
        """
        # Function call with nested parentheses
        text = "FINAL(func(arg1, arg2))"
        result = find_final_answer(text)
        assert result == "func(arg1, arg2)"

        # List and tuple with multiple closing parentheses
        text = "FINAL([1, 2, 3], (4, 5))"
        result = find_final_answer(text)
        assert result == "[1, 2, 3], (4, 5)"

        # Complex nested dictionary
        text = "FINAL({'key': 'value', 'nested': {'a': 1, 'b': 2}})"
        result = find_final_answer(text)
        assert "'key': 'value'" in result
        assert "'nested':" in result

        # Multiple function calls with nested parentheses
        text = "FINAL(calculate(10, 20) + process(data))"
        result = find_final_answer(text)
        assert result == "calculate(10, 20) + process(data)"

    def test_final_and_final_var_parsing(self):
        """Test that both FINAL and FINAL_VAR patterns are parsed correctly."""
        # Test FINAL with various content types
        test_cases_final = [
            ("FINAL(42)", "42"),
            ("FINAL('hello world')", "'hello world'"),
            ('FINAL("test")', '"test"'),
            ("FINAL(123.45)", "123.45"),
            ("FINAL([1, 2, 3])", "[1, 2, 3]"),
        ]

        for text, expected in test_cases_final:
            result = find_final_answer(text)
            assert result == expected, f"Failed for text: {text}"

        # Test FINAL_VAR with environment
        mock_env = Mock()
        mock_env.execute_code.return_value = REPLResult(
            stdout="computed_result", stderr="", locals={}
        )

        test_cases_final_var = [
            ("FINAL_VAR(result)", "result"),
            ("FINAL_VAR('my_var')", "my_var"),
            ('FINAL_VAR("another_var")', "another_var"),
            ("FINAL_VAR(answer)", "answer"),
        ]

        for text, var_name in test_cases_final_var:
            result = find_final_answer(text, environment=mock_env)
            assert result == "computed_result", f"Failed for text: {text}"
            # Verify the variable name was extracted correctly
            call_args = mock_env.execute_code.call_args[0][0]
            assert (
                var_name in call_args
                or f"'{var_name}'" in call_args
                or f'"{var_name}"' in call_args
            )

    def test_final_var_takes_precedence_over_final(self):
        """Test that FINAL_VAR is checked first and takes precedence over FINAL."""
        mock_env = Mock()
        mock_env.execute_code.return_value = REPLResult(stdout="var_value", stderr="", locals={})

        # If both appear, FINAL_VAR should be found first (checked first in the function)
        text = "FINAL_VAR(result)\nFINAL(direct_answer)"
        result = find_final_answer(text, environment=mock_env)
        assert result == "var_value"  # FINAL_VAR should be returned

        # Without environment, FINAL_VAR pattern is found but returns None (no fallback to FINAL)
        # This is expected behavior - FINAL_VAR takes precedence when found
        result = find_final_answer(text)
        assert result is None  # FINAL_VAR found but no environment, so returns None

        # Test that FINAL alone works when FINAL_VAR is not present
        text_final_only = "FINAL(direct_answer)"
        result = find_final_answer(text_final_only)
        assert result == "direct_answer"

    def test_final_var_retrieves_actual_variables_from_environment(self):
        """Test that FINAL_VAR actually retrieves variables from a real code environment."""
        # Create a real LocalREPL environment
        env = LocalREPL()

        try:
            # Execute code to create variables with different types
            env.execute_code("x = 42")
            env.execute_code("result = 'hello world'")
            env.execute_code("answer = [1, 2, 3, 4, 5]")
            env.execute_code("computed = 10 * 5 + 2")
            env.execute_code("nested = {'key': 'value', 'num': 123}")

            # Test retrieving integer variable
            text = "FINAL_VAR(x)"
            result = find_final_answer(text, environment=env)
            assert result == "42", f"Expected '42', got '{result}'"

            # Test retrieving string variable
            text = "FINAL_VAR(result)"
            result = find_final_answer(text, environment=env)
            assert result == "hello world", f"Expected 'hello world', got '{result}'"

            # Test retrieving list variable
            text = "FINAL_VAR(answer)"
            result = find_final_answer(text, environment=env)
            assert result == "[1, 2, 3, 4, 5]", f"Expected '[1, 2, 3, 4, 5]', got '{result}'"

            # Test retrieving computed variable
            text = "FINAL_VAR(computed)"
            result = find_final_answer(text, environment=env)
            assert result == "52", f"Expected '52', got '{result}'"

            # Test retrieving dictionary variable
            text = "FINAL_VAR(nested)"
            result = find_final_answer(text, environment=env)
            assert "'key': 'value'" in result or '"key": "value"' in result
            assert "'num': 123" in result or '"num": 123' in result

            # Test that variable updates are reflected
            env.execute_code("x = 100")
            text = "FINAL_VAR(x)"
            result = find_final_answer(text, environment=env)
            assert result == "100", f"Expected '100', got '{result}'"

            # Test that non-existent variable returns error message
            text = "FINAL_VAR(nonexistent)"
            result = find_final_answer(text, environment=env)
            assert "Error" in result or "not found" in result.lower()
        finally:
            env.cleanup()


class TestFormatExecutionResult:
    """Tests for format_execution_result function."""

    def test_stdout_only(self):
        result = REPLResult(stdout="Hello, World!", stderr="", locals={})
        formatted = format_execution_result(result)
        assert "Hello, World!" in formatted

    def test_stderr_only(self):
        result = REPLResult(stdout="", stderr="Error occurred", locals={})
        formatted = format_execution_result(result)
        assert "Error occurred" in formatted

    def test_with_locals(self):
        result = REPLResult(stdout="", stderr="", locals={"x": 42, "name": "test"})
        formatted = format_execution_result(result)
        assert "x" in formatted
        assert "name" in formatted

    def test_excludes_private_vars(self):
        result = REPLResult(stdout="", stderr="", locals={"_private": 1, "public": 2})
        formatted = format_execution_result(result)
        assert "public" in formatted
        # Private vars should be excluded
        assert "_private" not in formatted

    def test_empty_result(self):
        result = REPLResult(stdout="", stderr="", locals={})
        formatted = format_execution_result(result)
        assert formatted == "No output"


class TestFormatIteration:
    """Tests for format_iteration function."""

    def test_iteration_with_code_blocks(self):
        code_result = REPLResult(stdout="3", stderr="", locals={"x": 3})
        iteration = RLMIteration(
            prompt="Calculate 1+2",
            response="Let me calculate that.",
            code_blocks=[CodeBlock(code="x = 1 + 2\nprint(x)", result=code_result)],
        )
        messages = format_iteration(iteration)
        assert len(messages) == 2
        assert messages[0]["role"] == "assistant"
        assert messages[1]["role"] == "user"
        assert "x = 1 + 2" in messages[1]["content"]

    def test_iteration_without_code_blocks(self):
        iteration = RLMIteration(
            prompt="Just thinking",
            response="I'm considering the options.",
            code_blocks=[],
        )
        messages = format_iteration(iteration)
        assert len(messages) == 1
        assert messages[0]["role"] == "assistant"

    def test_truncates_long_results(self):
        long_output = "x" * 30000
        code_result = REPLResult(stdout=long_output, stderr="", locals={})
        iteration = RLMIteration(
            prompt="Test",
            response="Running...",
            code_blocks=[CodeBlock(code="print('x' * 30000)", result=code_result)],
        )
        messages = format_iteration(iteration, max_character_length=100)
        # Result should be truncated
        assert len(messages[1]["content"]) < 30000


class TestConvertContextForRepl:
    """Tests for convert_context_for_repl function."""

    def test_string_context(self):
        context_data, context_str = convert_context_for_repl("Hello world")
        assert context_data is None
        assert context_str == "Hello world"

    def test_dict_context(self):
        context_data, context_str = convert_context_for_repl({"key": "value"})
        assert context_data == {"key": "value"}
        assert context_str is None

    def test_list_of_strings(self):
        context_data, context_str = convert_context_for_repl(["a", "b", "c"])
        assert context_data == ["a", "b", "c"]
        assert context_str is None

    def test_list_of_message_dicts(self):
        messages = [
            {"content": "Hello"},
            {"content": "World"},
        ]
        context_data, context_str = convert_context_for_repl(messages)
        assert context_data == ["Hello", "World"]
        assert context_str is None
