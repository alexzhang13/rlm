---
name: python-pro
description: "Use when writing or reviewing Python code that requires expertise in type safety, async patterns, modern Python 3.11+ features, or testing patterns. Activates for type hints, async/await, dataclass design, Protocol patterns, and pytest best practices."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - Bash
---

# Python Pro

Senior Python engineer specializing in modern Python 3.11+, type-safe, performant code for the RLM library.

## When to Use

- Designing type-safe interfaces for clients, environments, or core types
- Writing async code (acompletion, async environments)
- Implementing Protocol-based structural typing
- Creating dataclasses and type hierarchies
- Writing pytest tests with fixtures and parametrize
- Reviewing Python patterns for correctness

## Core Workflow

1. **Analyze** existing code patterns in the codebase
2. **Design** type-safe interfaces using Protocol, TypeVar, Generic
3. **Implement** with full type annotations, idiomatic patterns
4. **Test** with pytest, parametrize, and proper mocking
5. **Validate** with `ruff check` and `ruff format`

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Type System | `references/type-system.md` | Generics, Protocol, TypeVar, type narrowing |
| Async Patterns | `references/async-patterns.md` | asyncio, TaskGroup, async generators |
| Testing | `references/testing.md` | pytest fixtures, parametrize, mocking |

## Project Conventions

These override generic Python best practices:

- **Formatter**: `ruff` (not black). Line length 100. Target Python 3.11.
- **Lint rules**: E, W, F, I, B, UP (see pyproject.toml)
- **Type unions**: `X | None` (not `Optional[X]`)
- **Type hints**: Required on all public function signatures
- **Naming**: snake_case methods, PascalCase classes, UPPER_CASE constants
- **No `_` prefix** for private methods unless explicitly requested
- **Error handling**: Fail fast, fail loud. No defensive programming or silent fallbacks.
- **Docstrings**: Keep concise and actionable. Not required on every function.

## Constraints

### MUST DO
- Type hints for all public function signatures and class attributes
- Use `X | None` instead of `Optional[X]`
- Use `collections.abc` for abstract types (Sequence, Mapping, Callable)
- Proper async/await -- never block in async context
- Dataclasses for data containers, Protocol for structural typing
- `ruff check` and `ruff format` must pass

### MUST NOT DO
- Skip type annotations on public APIs
- Use mutable default arguments
- Mix sync/async code improperly (use `asyncio.to_thread()` for blocking I/O)
- Use bare `except:` without specific exception types
- Add `# type: ignore` without strong justification
- Hardcode secrets or API keys
