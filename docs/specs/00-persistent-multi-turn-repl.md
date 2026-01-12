# Spec: Persistent Multi-Turn REPL Sessions

## Summary
Status: Implemented.

Add optional persistent REPL state across multi-turn sessions while retaining prompt-level conversation history. Each session prompt payload is stored as a versioned `session_context_n` in the REPL; the latest prompt is `session_context_{n-1}`. Completion calls use a single `completion_context` variable.

## Goals
- Preserve `RLMSession` behavior and prompt-level history.
- Enable optional REPL persistence across `completion()` calls.
- Keep the persistence protocol environment-agnostic.

## Non-Goals
- Do not change default behavior of `RLM` or `RLMSession`.
- Do not add persistence to isolated environments unless explicitly implemented.
- Do not introduce new core dependencies.

## Terminology
- **Prompt-level history**: `message_history` passed to the root model.
- **Session context**: input payload for `RLMSession.chat()` stored in the REPL as `session_context_0`, `session_context_1`, ...
- **Completion context**: input payload for `RLM.completion()` stored as `completion_context`.
- **Session history**: list of per-call message histories stored as `session_history`.

## API Changes
### RLM
- Add optional `persistent` boolean parameter to `RLM.__init__`.
- When `persistent=True`, reuse a single environment across `completion()` calls.
- Provide a `close()` method to release persistent resources.

### Environment Protocol
Add a `SupportsPersistence` protocol in `rlm/environments/base_env.py` with:
- `update_handler_address(address: tuple[str, int]) -> None`
- `add_context(context_payload: dict | list | str, context_index: int | None = None) -> int`
- `get_context_count() -> int`
- `add_history(message_history: list[dict[str, Any]], history_index: int | None = None) -> int`
- `get_history_count() -> int`
- `set_completion_context(context_payload: dict | list | str) -> None`

## Behavior
### Session Flow (Default)
- Default behavior: each `completion()` call spawns a fresh environment.

### Session Flow (Persistent)
- On first `completion()` call, create the environment and store it for reuse.
- For each new `completion()` call:
  - Update the LM handler address via `update_handler_address()`.
  - Add the prompt payload via `add_context()` for session calls.
  - Set the prompt payload via `set_completion_context()` for completion calls.
  - Run the normal RLM loop.

### Prompt-Level History
- `RLMSession` maintains `message_history` for multi-turn prompts.
- The root model sees conversation history via the prompt message history.

### REPL-Level Context
- Each session prompt payload is stored as `session_context_0`, `session_context_1`, ...
- The latest prompt is `session_context_{n-1}`; `context_history` mirrors all session contexts (overwritten each call).
- Each prompt history is stored as an entry in `session_history`.
- Each completion prompt payload is stored as `completion_context` (overwritten each call).

### Prompt Annotation
- `RLMSession.chat()` prompts always identify the current prompt as `session_context_{n-1}` and treat earlier contexts as historical.
- `RLM.completion()` prompts do not include context/history count notes; they only mention `completion_context`.

## Observed Gains
- Direct access to prior session contexts and histories in the REPL without losing the initial prompt payload.

## Error Handling
- If `persistent=True` and the environment does not implement `SupportsPersistence`, raise `ValueError` during initialization.
- If persistence is enabled but the stored environment does not satisfy the protocol at runtime, raise `RuntimeError`.
- Missing LM handler address during `llm_query()` returns an error string.

## Non-Persistent Behavior
- Each `completion()` call creates a fresh environment.

## Implementation Notes
- Keep a non-isolated environment as the reference implementation.
- Do not remove `RLMSession`; persistence is an additive feature.
- Ensure cleanup via `RLM.close()` and `__exit__` to avoid leaked temp dirs.
- Avoid new dependencies; use standard library only.

## Rollout Plan
1. Implement `SupportsPersistence` protocol with session context/history tracking.
2. Add support in a non-isolated REPL implementation.
3. Wire `persistent=True` into `RLM`.
4. Update docs.

## Minimal Implementation Plan (Slice-Friendly)
- Step 1: Add `SupportsPersistence` protocol + session context/history tracking.
  Files: `rlm/environments/base_env.py`.
  Purpose: environment capability without core wiring.
- Step 2: Add non-isolated REPL support for contexts/histories.
  Files: `rlm/environments/local_repl.py`.
  Purpose: reference implementation for persistent sessions.
- Step 3: Wire `persistent` into `RLM` spawning; keep `RLMSession` intact.
  Files: `rlm/core/rlm.py`.
  Purpose: minimal core integration, easy to rebase.
