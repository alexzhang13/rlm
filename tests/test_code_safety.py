"""Tests for the code_safety static analysis module."""

import pytest

from rlm.utils.code_safety import (
    DANGEROUS_ATTRIBUTES,
    DANGEROUS_CALLS,
    DANGEROUS_MODULES,
    SafetyCheckResult,
    check_code_safety,
)


class TestSafetyCheckResultBasics:
    """Tests for SafetyCheckResult dataclass."""

    def test_safe_result_is_truthy(self):
        result = SafetyCheckResult(is_safe=True, reason="")
        assert result
        assert bool(result) is True

    def test_unsafe_result_is_falsy(self):
        result = SafetyCheckResult(is_safe=False, reason="Dangerous import")
        assert not result
        assert bool(result) is False


class TestSafeCode:
    """Tests that legitimate code is allowed."""

    def test_simple_math(self):
        code = "x = 1 + 2 * 3"
        result = check_code_safety(code)
        assert result.is_safe

    def test_function_definition(self):
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        result = check_code_safety(code)
        assert result.is_safe

    def test_list_comprehension(self):
        code = "squares = [x**2 for x in range(10)]"
        result = check_code_safety(code)
        assert result.is_safe

    def test_safe_imports(self):
        code = """
import math
import json
import re
import collections
"""
        result = check_code_safety(code)
        assert result.is_safe

    def test_class_definition(self):
        code = """
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
"""
        result = check_code_safety(code)
        assert result.is_safe

    def test_safe_builtins(self):
        code = """
result = len([1, 2, 3])
result = sum([1, 2, 3])
result = sorted([3, 1, 2])
result = max([1, 2, 3])
"""
        result = check_code_safety(code)
        assert result.is_safe

    def test_syntax_error_passes_through(self):
        code = "def broken("
        result = check_code_safety(code)
        # Syntax errors are allowed through to be handled by exec()
        assert result.is_safe


class TestDangerousImports:
    """Tests that dangerous imports are blocked."""

    def test_import_os(self):
        code = "import os"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "os" in result.reason

    def test_import_subprocess(self):
        code = "import subprocess"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "subprocess" in result.reason

    def test_from_os_import(self):
        code = "from os import system"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "os" in result.reason

    def test_from_subprocess_import(self):
        code = "from subprocess import run"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "subprocess" in result.reason

    def test_import_socket(self):
        code = "import socket"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "socket" in result.reason

    def test_import_requests(self):
        code = "import requests"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "requests" in result.reason

    def test_import_ctypes(self):
        code = "import ctypes"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "ctypes" in result.reason

    def test_import_pickle(self):
        code = "import pickle"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "pickle" in result.reason

    def test_import_shutil(self):
        code = "import shutil"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "shutil" in result.reason

    def test_import_sys(self):
        code = "import sys"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "sys" in result.reason

    def test_submodule_import(self):
        code = "import os.path"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "os" in result.reason

    def test_from_submodule_import(self):
        code = "from urllib.request import urlopen"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "urllib" in result.reason

    @pytest.mark.parametrize("module", list(DANGEROUS_MODULES)[:20])
    def test_all_dangerous_modules_blocked(self, module):
        code = f"import {module}"
        result = check_code_safety(code)
        assert not result.is_safe


class TestDangerousCalls:
    """Tests that dangerous function calls are blocked."""

    def test_eval_call(self):
        code = "eval('1 + 1')"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "eval" in result.reason

    def test_exec_call(self):
        code = "exec('x = 1')"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "exec" in result.reason

    def test_compile_call(self):
        code = "compile('x = 1', '<string>', 'exec')"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "compile" in result.reason

    def test_dunder_import_call(self):
        code = "__import__('os')"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__import__" in result.reason

    def test_breakpoint_call(self):
        code = "breakpoint()"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "breakpoint" in result.reason

    def test_exit_call(self):
        code = "exit()"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "exit" in result.reason

    @pytest.mark.parametrize("call", DANGEROUS_CALLS)
    def test_all_dangerous_calls_blocked(self, call):
        code = f"{call}()"
        result = check_code_safety(code)
        assert not result.is_safe


class TestDangerousAttributes:
    """Tests that dangerous attribute access is blocked."""

    def test_class_access(self):
        code = "x.__class__"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__class__" in result.reason

    def test_globals_access(self):
        code = "func.__globals__"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__globals__" in result.reason

    def test_code_access(self):
        code = "func.__code__"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__code__" in result.reason

    def test_subclasses_access(self):
        code = "object.__subclasses__()"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__subclasses__" in result.reason

    def test_bases_access(self):
        code = "cls.__bases__"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__bases__" in result.reason

    def test_mro_access(self):
        code = "cls.__mro__"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__mro__" in result.reason

    def test_builtins_access(self):
        code = "x.__builtins__"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__builtins__" in result.reason

    def test_getattr_with_dangerous_attr(self):
        code = "getattr(obj, '__globals__')"
        result = check_code_safety(code)
        assert not result.is_safe
        assert "__globals__" in result.reason

    def test_getattr_with_safe_attr(self):
        code = "getattr(obj, 'name')"
        result = check_code_safety(code)
        assert result.is_safe

    @pytest.mark.parametrize("attr", list(DANGEROUS_ATTRIBUTES)[:10])
    def test_dangerous_attributes_blocked(self, attr):
        code = f"x.{attr}"
        result = check_code_safety(code)
        assert not result.is_safe


class TestComplexPatterns:
    """Tests for complex code patterns."""

    def test_multiple_violations(self):
        code = """
import os
import subprocess
eval('code')
"""
        result = check_code_safety(code)
        assert not result.is_safe
        # Should report multiple violations
        assert "os" in result.reason
        assert "subprocess" in result.reason
        assert "eval" in result.reason

    def test_dangerous_code_in_function(self):
        code = """
def attack():
    import os
    return os.system('rm -rf /')
"""
        result = check_code_safety(code)
        assert not result.is_safe
        assert "os" in result.reason

    def test_dangerous_code_in_class(self):
        code = """
class Attacker:
    def run(self):
        exec('import os')
"""
        result = check_code_safety(code)
        assert not result.is_safe
        assert "exec" in result.reason

    def test_nested_dangerous_access(self):
        code = "obj.__class__.__bases__[0].__subclasses__()"
        result = check_code_safety(code)
        assert not result.is_safe
        # Should catch at least one dangerous attribute
        assert any(attr in result.reason for attr in ["__class__", "__bases__", "__subclasses__"])


class TestEdgeCases:
    """Tests for edge cases and potential bypasses."""

    def test_empty_code(self):
        result = check_code_safety("")
        assert result.is_safe

    def test_whitespace_only(self):
        result = check_code_safety("   \n\t  \n")
        assert result.is_safe

    def test_comments_only(self):
        code = "# This is a comment\n# Another comment"
        result = check_code_safety(code)
        assert result.is_safe

    def test_docstring_with_dangerous_text(self):
        code = '''
def safe_func():
    """This docstring mentions import os but is safe."""
    return 42
'''
        result = check_code_safety(code)
        assert result.is_safe

    def test_string_with_dangerous_text(self):
        code = "x = \"import os; os.system('rm -rf /')\""
        result = check_code_safety(code)
        # String literals are safe - we only care about actual imports/calls
        assert result.is_safe


class TestIntegrationWithLocalREPL:
    """Integration tests with LocalREPL."""

    def test_repl_blocks_dangerous_import(self):
        from rlm.environments.local_repl import LocalREPL

        repl = LocalREPL()
        result = repl.execute_code("import os")
        assert "Security" in result.stderr
        assert "os" in result.stderr
        repl.cleanup()

    def test_repl_blocks_exec(self):
        from rlm.environments.local_repl import LocalREPL

        repl = LocalREPL()
        result = repl.execute_code("exec('x = 1')")
        assert "Security" in result.stderr
        assert "exec" in result.stderr
        repl.cleanup()

    def test_repl_allows_safe_code(self):
        from rlm.environments.local_repl import LocalREPL

        repl = LocalREPL()
        result = repl.execute_code("x = 1 + 2")
        assert result.stderr == ""
        assert repl.locals["x"] == 3
        repl.cleanup()

    def test_repl_blocks_attribute_escape(self):
        from rlm.environments.local_repl import LocalREPL

        repl = LocalREPL()
        result = repl.execute_code("x = ().__class__.__bases__[0]")
        assert "Security" in result.stderr
        repl.cleanup()
