# Spec: Trace Artifacts (Notebook + Markdown)

## Summary
Status: Implemented.

Provide two trace artifacts for each RLM run:
- A file-based `.trace.ipynb` notebook in `logs/` that mirrors the JSONL trajectory.
- A markdown trace exposed on `RLMChatCompletion.trace_markdown`.

## Goals
- Keep a durable, replayable notebook artifact per run.
- Provide a lightweight, notebook-friendly markdown trace for quick inspection.
- Preserve trace availability outside Jupyter (plain markdown string).

## Non-Goals
- No live rendering or auto-refresh in the notebook UI.
- No in-notebook UI components or extensions.
- No changes to iteration log format.

## Source of Truth
- JSONL trajectory log written by `RLMLogger`.
- Entry types used:
  - `metadata`
  - `run_context` (prompt + root_prompt + session_mode)
  - `iteration`

## Trace Markdown on Result
### API Changes
- `RLMChatCompletion` adds `trace_markdown: str`.
- `RLM` maintains `trace_markdown_history: str` for each `completion()` run.
- `RLMSession` accumulates `trace_markdown_history: str` across chat turns.

### Trace Format
- Run header with prompt/root_prompt as JSON.
- Iterations include model response, code blocks, stdout/stderr, and sub-LM calls.
- Each run is separated by a markdown horizontal rule (`---`).

### Workflow
1. On `RLM.completion()` start, capture the run context (prompt, root_prompt, session_mode, environment kwargs).
2. Accumulate `RLMIteration` objects as the run proceeds.
3. At completion, build a markdown trace for the run and set `trace_markdown_history` for that run.
4. Return `RLMChatCompletion(trace_markdown=trace_markdown_history)`.

## Trace Notebook File
### Notebook Structure
1. Title cell (markdown)
2. Resume cell (code)
3. Optional metadata cell(s)
4. Per-iteration cells:
   - Markdown cell with iteration header + model response
   - Code cell for each ```repl``` block
   - Outputs attached to code cell (stdout/stderr)
   - Optional markdown cell for nested `llm_query` summaries

### Cell Tagging
Use tags for filtering:
- Title: `["rlm", "rlm-title"]`
- Resume: `["rlm", "rlm-resume"]`
- Metadata: `["rlm", "rlm-metadata"]`
- Iteration response: `["rlm", "iteration-N", "role-assistant"]`
- Code cells: `["rlm", "iteration-N", "role-code"]`
- Subcalls: `["rlm", "iteration-N", "role-llm-calls"]`

### Resume Cell Behavior
- When `run_context` is logged, inject:
  - `completion_context` for completion runs, or `session_context_0` for session runs.
  - `root_prompt` rehydrated from JSON.
- Session runs also initialize `context_history` and `session_history` in the resume cell.
- If the prompt is not JSON-serializable, include a comment and fall back to `repr(...)`.
- Replay support:
  - `llm_query` and `llm_query_batched` replay recorded subcalls by prompt match.
  - Raises if a prompt is not found in the replay map.
  - Live `llm_query` calls are not implemented in trace notebooks.

### Failure & Fallback
- If `nbformat` is missing: raise a clear error.
- If JSONL is malformed: skip that entry.
- If multiple runs share a logger: each `run_context` updates the resume cell (or add a run boundary cell in the future).

## Session History Behavior
- When using `RLMSession.chat()`, the context payload passed to the REPL is the current prompt (string or dict).
- Prompt-level history is maintained in the LM message history.
- If `persistent=True`, histories are stored in the REPL after each run as entries in `session_history`.
- Assistant responses are always strings; `FINAL_VAR(...)` values are coerced to string.

## Public API
- `enable_trace_notebook(log_dir, file_name="rlm", notebook_path=None, poll_interval=0.25) -> (RLMLogger, TraceWriterHandle)`
- `start_trace_writer(log_path, notebook_path, poll_interval=0.25)`
- `stop_trace_writer(handle)`

## Files
- `rlm/utils/trace_notebook.py` (implementation)
- `rlm/utils/trace_markdown.py` (trace builder)
- `rlm/core/rlm.py` (trace accumulation + return)
- `rlm/core/types.py` (trace_markdown field)
