"""Tests for MontyREPL environment."""

import pytest

pytest.importorskip("pydantic_monty")

from rlm.environments.monty_repl import MontyREPL


class TestMontyREPLBasic:
    """Basic functionality tests for MontyREPL."""

    def test_basic_execution_and_print(self):
        repl = MontyREPL()
        result = repl.execute_code("x = 2 + 3\nprint(x)")
        assert "5" in result.stdout

    def test_state_retention_across_blocks(self):
        repl = MontyREPL()
        repl.execute_code("x = 2 + 3\nprint(x)")
        result = repl.execute_code("y = x * 2\nprint(y)")
        assert "10" in result.stdout
        assert "x" in result.locals
        assert "y" in result.locals

    def test_final_var(self):
        repl = MontyREPL()
        repl.execute_code("x = 10")
        result = repl.execute_code("print(FINAL_VAR('x'))")
        assert "10" in result.stdout
