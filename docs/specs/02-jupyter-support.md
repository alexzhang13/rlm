# Spec: Jupyter Support

## Summary
Status: Implemented.

Provide a `jupyter` REPL environment that executes RLM-generated code directly in a Jupyter kernel with captured stdout/stderr and optional namespace sync.

## Goals
- Execute code in the notebook kernel with minimal friction.
- Capture stdout/stderr safely.
- Support `llm_query`, `llm_query_batched`, and `FINAL_VAR` helpers.
- Support persistent session/completion context variables per the multi-turn REPL spec.
- Optional bidirectional sync of variables with the user namespace.

## Non-Goals
- Sandboxed execution (this is non-isolated).
- UI-level features (widgets, live tracing).

## Usage
```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5"},
    environment="jupyter",
    environment="jupyter",
    environment_kwargs={
        "sync_to_user_ns": True,
        "sync_from_user_ns": True,
        "sync_vars": ["model", "df"],  # Optional allowlist
    },
)
)
```

## Environment API
- Environment type: `jupyter`
- Class: `JupyterREPL` in `rlm/environments/jupyter_repl.py`
- Base class: `NonIsolatedEnv`

## Behavior
1. Initialize globals/locals with safe builtins.
2. Load `session_context_0` when running in session mode, or `completion_context` for completion calls.
3. Provide helper functions:
   - `llm_query(prompt, model=None)`
   - `llm_query_batched(prompts, model=None)`
   - `FINAL_VAR(name)`
4. Execute code via `exec(...)` in the current kernel.
5. Capture stdout/stderr using `IPython.utils.capture.capture_output`.
6. Optionally sync locals into `ip.user_ns` when `sync_to_user_ns=True`.
7. Optionally sync user variables into REPL globals when `sync_from_user_ns=True` (optionally filtered by `sync_vars`).

## Persistence Support
`JupyterREPL` implements the `SupportsPersistence` protocol described in the multi-turn REPL spec:
- Session prompts are stored as `session_context_0`, `session_context_1`, ...
- `context_history` mirrors session contexts (overwritten each call).
- Per-call histories are stored in `session_history`.
- Completion calls overwrite `completion_context`.

## Configuration
- `workdir`: optional working directory.
- `allow_builtin_imports`: if false, remove `__import__` from builtins.
- `sync_to_user_ns`: push locals into the user namespace.
- `sync_from_user_ns`: pull user variables into the REPL globals.
- `sync_vars`: optional list of variable names to sync from user namespace.
- `setup_code`: optional code to run on setup.

## Registration
- Registered in `rlm/environments/__init__.py` under `"jupyter"`.
- Listed in README as a supported environment.

## Files
- `rlm/environments/jupyter_repl.py`
- `rlm/environments/__init__.py`
- `README.md`
