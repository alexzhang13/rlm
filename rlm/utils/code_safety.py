"""
Static analysis module for detecting dangerous code patterns before execution.

This module provides AST-based analysis to catch dangerous imports, function calls,
and attribute access patterns that could be used to escape the sandbox.
"""

import ast
from dataclasses import dataclass

# =============================================================================
# Blocklists - Dangerous patterns to detect
# =============================================================================

DANGEROUS_MODULES = frozenset(
    {
        # System access
        "os",
        "sys",
        "subprocess",
        "shutil",
        "pathlib",
        # Code execution
        "importlib",
        "runpy",
        "code",
        "codeop",
        # Network
        "socket",
        "requests",
        "urllib",
        "http",
        "ftplib",
        "smtplib",
        "telnetlib",
        "ssl",
        # Process/threading abuse
        "multiprocessing",
        "concurrent",
        # Low-level
        "ctypes",
        "cffi",
        "mmap",
        # Serialization (can execute code)
        "pickle",
        "shelve",
        "marshal",
        # Debugging (can inspect internals)
        "inspect",
        "gc",
        "traceback",
        # Signal handling
        "signal",
        # Platform/resource access
        "platform",
        "resource",
        "pty",
        "tty",
        "termios",
        "fcntl",
        # Other dangerous modules
        "builtins",
        "_thread",
        "asyncio",
        "atexit",
        "tempfile",
        "glob",
        "fnmatch",
        "linecache",
        "tokenize",
        "dis",
        "compileall",
        "py_compile",
        "zipimport",
        "pkgutil",
        "modulefinder",
        "pdb",
        "bdb",
        "profile",
        "cProfile",
        "trace",
        "webbrowser",
    }
)

DANGEROUS_ATTRIBUTES = frozenset(
    {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__globals__",
        "__code__",
        "__builtins__",
        "__dict__",
        "__getattribute__",
        "__reduce__",
        "__reduce_ex__",
        "__setstate__",
        "__getstate__",
        "func_globals",
        "f_globals",
        "f_locals",
        "f_builtins",
        "gi_frame",
        "gi_code",
        "co_code",
    }
)

DANGEROUS_CALLS = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "breakpoint",
        "exit",
        "quit",
    }
)


# =============================================================================
# Safety Check Result
# =============================================================================


@dataclass(frozen=True)
class SafetyCheckResult:
    """Result of a code safety check."""

    is_safe: bool
    reason: str

    def __bool__(self) -> bool:
        return self.is_safe


# =============================================================================
# AST Visitor for Dangerous Patterns
# =============================================================================


class DangerousPatternVisitor(ast.NodeVisitor):
    """AST visitor that detects dangerous code patterns."""

    def __init__(self):
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Check for dangerous imports: import os, import subprocess"""
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            if module_name in DANGEROUS_MODULES:
                self.violations.append(f"Dangerous import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for dangerous from imports: from os import system"""
        if node.module:
            module_name = node.module.split(".")[0]
            if module_name in DANGEROUS_MODULES:
                self.violations.append(f"Dangerous import: 'from {node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check for dangerous function calls."""
        func_name = self._get_call_name(node.func)

        if func_name in DANGEROUS_CALLS:
            self.violations.append(f"Dangerous call: '{func_name}()'")

        # Check for getattr used to access dangerous attributes
        if func_name == "getattr" and len(node.args) >= 2:
            attr_arg = node.args[1]
            if isinstance(attr_arg, ast.Constant) and isinstance(attr_arg.value, str):
                if attr_arg.value in DANGEROUS_ATTRIBUTES:
                    self.violations.append(f"Dangerous getattr access: '{attr_arg.value}'")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check for dangerous attribute access patterns."""
        if node.attr in DANGEROUS_ATTRIBUTES:
            self.violations.append(f"Dangerous attribute access: '{node.attr}'")
        self.generic_visit(node)

    def _get_call_name(self, node: ast.expr) -> str:
        """Extract the name of a called function."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""


# =============================================================================
# Public API
# =============================================================================


def check_code_safety(code: str) -> SafetyCheckResult:
    """
    Check if code is safe to execute using static analysis.

    Parses the code into an AST and walks the tree looking for dangerous
    patterns including:
    - Imports of dangerous modules (os, subprocess, socket, etc.)
    - Dangerous function calls (eval, exec, compile, __import__)
    - Dangerous attribute access (__class__, __globals__, etc.)

    Args:
        code: Python source code to analyze.

    Returns:
        SafetyCheckResult with is_safe=True if code passes checks,
        or is_safe=False with reason describing the violation.

    Note:
        Static analysis cannot catch all attacks (e.g., obfuscated strings,
        dynamic imports). This is one layer in a defense-in-depth strategy.
    """
    # Parse the code into an AST
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Let syntax errors pass through to be handled by exec()
        return SafetyCheckResult(is_safe=True, reason="")

    # Visit all nodes looking for dangerous patterns
    visitor = DangerousPatternVisitor()
    visitor.visit(tree)

    if visitor.violations:
        return SafetyCheckResult(is_safe=False, reason="; ".join(visitor.violations))

    return SafetyCheckResult(is_safe=True, reason="")
