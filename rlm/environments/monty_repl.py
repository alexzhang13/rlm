"""
Monty REPL environment that runs Python code in the Monty sandbox.

Requires: pydantic-monty
"""

from __future__ import annotations

import ast
import copy
import time
from typing import Any, Literal

import pydantic_monty

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv

RESERVED_NAMES = {
    "__rlm_state",
    "__rlm_capture_locals",
    "__rlm_state_out",
    "llm_query",
    "llm_query_batched",
    "FINAL_VAR",
    "SHOW_VARS",
    "print",
}


class AssignedNameCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.scope_depth = 0

    def add_target(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self.names.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self.add_target(item)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.scope_depth == 0:
            for target in node.targets:
                self.add_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.scope_depth == 0:
            self.add_target(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if self.scope_depth == 0:
            self.add_target(node.target)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if self.scope_depth == 0:
            self.add_target(node.target)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        if self.scope_depth == 0:
            self.add_target(node.target)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        if self.scope_depth == 0:
            for item in node.items:
                if item.optional_vars is not None:
                    self.add_target(item.optional_vars)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        if self.scope_depth == 0:
            for item in node.items:
                if item.optional_vars is not None:
                    self.add_target(item.optional_vars)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if self.scope_depth == 0 and node.name:
            self.names.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        if self.scope_depth == 0:
            for alias in node.names:
                self.names.add(alias.asname or alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self.scope_depth == 0:
            for alias in node.names:
                self.names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.scope_depth == 0:
            self.names.add(node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if self.scope_depth == 0:
            self.names.add(node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.scope_depth == 0:
            self.names.add(node.name)
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        if self.scope_depth == 0:
            self.add_target(node.target)
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        if self.scope_depth == 0:
            for case in node.cases:
                self.collect_match_pattern(case.pattern)
        self.generic_visit(node)

    def collect_match_pattern(self, pattern: ast.pattern) -> None:
        if isinstance(pattern, ast.MatchAs):
            if pattern.name:
                self.names.add(pattern.name)
            if pattern.pattern is not None:
                self.collect_match_pattern(pattern.pattern)
        elif isinstance(pattern, ast.MatchStar):
            if pattern.name:
                self.names.add(pattern.name)
        elif isinstance(pattern, ast.MatchMapping):
            if pattern.rest:
                self.names.add(pattern.rest)
            for subpattern in pattern.patterns:
                self.collect_match_pattern(subpattern)
        elif isinstance(pattern, ast.MatchSequence):
            for subpattern in pattern.patterns:
                self.collect_match_pattern(subpattern)
        elif isinstance(pattern, ast.MatchClass):
            for subpattern in pattern.patterns:
                self.collect_match_pattern(subpattern)
            for subpattern in pattern.kwd_patterns:
                self.collect_match_pattern(subpattern)
        elif isinstance(pattern, ast.MatchOr):
            for subpattern in pattern.patterns:
                self.collect_match_pattern(subpattern)


class MontyREPL(NonIsolatedEnv):
    """
    Monty REPL environment that runs Python code in a sandboxed interpreter.

    Monty runs in-process but is sandboxed, so this is treated as a non-isolated
    environment.
    """

    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        resource_limits: pydantic_monty.ResourceLimits | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        self.lm_handler_address = lm_handler_address
        self.resource_limits = resource_limits
        self.locals: dict[str, Any] = {}
        self.pending_llm_calls: list[RLMChatCompletion] = []
        self.stdout_parts: list[str] = []
        self.stderr_parts: list[str] = []
        self._context_count = 0
        self._history_count = 0

        self.setup()

        if context_payload is not None:
            self.load_context(context_payload)

        if setup_code:
            self.execute_code(setup_code)

    def setup(self) -> None:
        """Setup the environment."""
        self.locals = {}
        self.pending_llm_calls = []
        self.stdout_parts = []
        self.stderr_parts = []
        self._context_count = 0
        self._history_count = 0

    def load_context(self, context_payload: dict | list | str) -> None:
        """Load context into the environment as context_0 (and 'context' alias)."""
        self.add_context(context_payload, 0)

    def execute_code(self, code: str) -> REPLResult:
        """Execute code in the Monty sandbox and return result."""
        start_time = time.perf_counter()
        self.stdout_parts = []
        self.stderr_parts = []
        self.pending_llm_calls = []

        wrapper_script = self.build_wrapper_script(code)
        external_functions = {
            "__rlm_capture_locals": self.capture_locals,
            "llm_query": self.llm_query,
            "llm_query_batched": self.llm_query_batched,
        }

        try:
            runner = pydantic_monty.Monty(
                wrapper_script,
                inputs=["__rlm_state"],
                external_functions=list(external_functions.keys()),
            )
            result = runner.run(
                inputs={"__rlm_state": self.locals},
                external_functions=external_functions,
                limits=self.resource_limits,
                print_callback=self.handle_print_callback,
            )
            if result is not None:
                self.stdout_parts.append(str(result))

            return REPLResult(
                stdout="".join(self.stdout_parts),
                stderr="".join(self.stderr_parts),
                locals=self.locals.copy(),
                execution_time=time.perf_counter() - start_time,
                rlm_calls=self.pending_llm_calls.copy(),
            )
        except Exception as exc:
            stderr = "".join(self.stderr_parts)
            if stderr:
                stderr = f"{stderr.rstrip()}\n{type(exc).__name__}: {exc}"
            else:
                stderr = f"{type(exc).__name__}: {exc}"
            return REPLResult(
                stdout="".join(self.stdout_parts),
                stderr=stderr,
                locals=self.locals.copy(),
                execution_time=time.perf_counter() - start_time,
                rlm_calls=self.pending_llm_calls.copy(),
            )

    def build_wrapper_script(self, user_code: str) -> str:
        """Build a wrapper script that restores state, captures output, and persists locals."""
        lines: list[str] = []
        assigned_names = self.collect_assigned_names(user_code)
        persisted_names = {
            name
            for name in set(self.locals) | assigned_names
            if name.isidentifier() and not name.startswith("_") and name not in RESERVED_NAMES
        }
        for name in sorted(persisted_names):
            lines.append(f"if {name!r} in __rlm_state:")
            lines.append(f"    {name} = __rlm_state[{name!r}]")

        lines.append("def FINAL_VAR(variable_name):")
        lines.append('    variable_name = variable_name.strip().strip("\\"\'")')
        for name in sorted(persisted_names):
            lines.append(f"    if variable_name == {name!r}:")
            lines.append("        try:")
            lines.append(f"            return str({name})")
            lines.append("        except NameError:")
            lines.append("            pass")
        lines.append("    available = []")
        for name in sorted(persisted_names):
            lines.append("    try:")
            lines.append(f"        {name}")
            lines.append(f"        available.append({name!r})")
            lines.append("    except NameError:")
            lines.append("        pass")
        lines.append("    if available:")
        lines.append(
            "        return f\"Error: Variable '{variable_name}' not found. "
            "Available variables: {available}. "
            'You must create and assign a variable BEFORE calling FINAL_VAR on it."'
        )
        lines.append(
            "    return f\"Error: Variable '{variable_name}' not found. "
            "No variables have been created yet. "
            'You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."'
        )

        lines.append("def SHOW_VARS():")
        lines.append("    available = {}")
        for name in sorted(persisted_names):
            lines.append("    try:")
            lines.append(f"        available[{name!r}] = type({name}).__name__")
            lines.append("    except NameError:")
            lines.append("        pass")
        lines.append("    if not available:")
        lines.append(
            '        return "No variables created yet. Use ```repl``` blocks to create variables."'
        )
        lines.append('    return f"Available variables: {available}"')

        lines.append(user_code)

        lines.append("__rlm_state_out = {}")
        for name in sorted(persisted_names):
            lines.append("try:")
            lines.append(f"    __rlm_state_out[{name!r}] = {name}")
            lines.append("except NameError:")
            lines.append("    pass")
        lines.append("__rlm_capture_locals(__rlm_state_out)")

        return "\n".join(lines)

    def handle_print_callback(self, stream: Literal["stdout", "stderr"], text: str) -> None:
        """Collect printed output from Monty."""
        if stream == "stdout":
            self.stdout_parts.append(text)
        elif stream == "stderr":
            self.stderr_parts.append(text)

    def capture_locals(self, vars_dict: dict[str, Any]) -> None:
        """Capture locals after execution."""
        self.locals = vars_dict.copy()

    @staticmethod
    def collect_assigned_names(code: str) -> set[str]:
        """Collect names assigned at module scope in the provided code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return set()

        collector = AssignedNameCollector()
        collector.visit(tree)
        return collector.names

    def update_handler_address(self, address: tuple[str, int]) -> None:
        """Update the LM handler address for a new completion call."""
        self.lm_handler_address = address

    def add_context(
        self, context_payload: dict | list | str, context_index: int | None = None
    ) -> int:
        """Add a context with versioned variable name."""
        if context_index is None:
            context_index = self._context_count

        var_name = f"context_{context_index}"
        self.locals[var_name] = context_payload
        if context_index == 0:
            self.locals["context"] = context_payload

        self._context_count = max(self._context_count, context_index + 1)
        return context_index

    def get_context_count(self) -> int:
        """Return the number of contexts loaded."""
        return self._context_count

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        """Store a conversation's message history as a versioned variable."""
        if history_index is None:
            history_index = self._history_count

        var_name = f"history_{history_index}"
        self.locals[var_name] = copy.deepcopy(message_history)
        if history_index == 0:
            self.locals["history"] = self.locals[var_name]

        self._history_count = max(self._history_count, history_index + 1)
        return history_index

    def get_history_count(self) -> int:
        """Return the number of conversation histories stored."""
        return self._history_count

    def llm_query(self, prompt: str, model: str | None = None) -> str:
        """Query the LM via socket connection to the handler."""
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            request = LMRequest(prompt=prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            self.pending_llm_calls.append(response.chat_completion)
            return response.chat_completion.response
        except Exception as exc:
            return f"Error: LM query failed - {exc}"

    def llm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Query the LM with multiple prompts concurrently."""
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)

        try:
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
            )
            results: list[str] = []
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                else:
                    self.pending_llm_calls.append(response.chat_completion)
                    results.append(response.chat_completion.response)

            return results
        except Exception as exc:
            return [f"Error: LM query failed - {exc}"] * len(prompts)

    def cleanup(self) -> None:
        """Clean up environment state."""
        self.locals.clear()
        self.pending_llm_calls.clear()
        self.stdout_parts.clear()
        self.stderr_parts.clear()
        self._context_count = 0
        self._history_count = 0

    def __enter__(self) -> MontyREPL:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.cleanup()
        return False

    def __del__(self) -> None:
        self.cleanup()
