---
layout: default
title: RLM Class
parent: API Reference
nav_order: 1
---

# RLM Class Reference
{: .no_toc }

Complete API documentation for the core RLM class.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The `RLM` class is the main entry point for Recursive Language Model completions. It wraps an LM client and execution environment to enable iterative, code-augmented reasoning.

```python
from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-5-nano"},
)
```

---

## Constructor

```python
RLM(
    backend: str = "openai",
    backend_kwargs: dict | None = None,
    environment: str = "local",
    environment_kwargs: dict | None = None,
    depth: int = 0,
    max_depth: int = 1,
    max_iterations: int = 30,
    max_budget: float | None = None,
    max_timeout: float | None = None,
    max_tokens: int | None = None,
    max_errors: int | None = None,
    custom_system_prompt: str | None = None,
    other_backends: list[str] | None = None,
    other_backend_kwargs: list[dict] | None = None,
    logger: RLMLogger | None = None,
    verbose: bool = False,
    persistent: bool = False,
    custom_tools: dict[str, Any] | None = None,
    custom_sub_tools: dict[str, Any] | None = None,
    compaction: bool = False,
    compaction_threshold_pct: float = 0.85,
    on_subcall_start: Callable | None = None,
    on_subcall_complete: Callable | None = None,
    on_iteration_start: Callable | None = None,
    on_iteration_complete: Callable | None = None,
)
```

### Parameters

#### `backend`
{: .no_toc }

**Type:** `Literal["openai", "portkey", "openrouter", "vllm", "litellm", "anthropic"]`
**Default:** `"openai"`

The LM provider backend to use for the root model.

```python
# OpenAI
rlm = RLM(backend="openai", ...)

# Anthropic
rlm = RLM(backend="anthropic", ...)

# Local vLLM server
rlm = RLM(backend="vllm", ...)
```

---

#### `backend_kwargs`
{: .no_toc }

**Type:** `dict[str, Any] | None`
**Default:** `None`

Configuration passed to the LM client. Required fields vary by backend:

| Backend | Required | Optional |
|:--------|:---------|:---------|
| `openai` | `model_name` | `api_key`, `base_url` |
| `anthropic` | `model_name` | `api_key` |
| `portkey` | `model_name`, `api_key` | `base_url` |
| `openrouter` | `model_name` | `api_key` |
| `vllm` | `model_name`, `base_url` | — |
| `litellm` | `model_name` | varies by provider |

```python
backend_kwargs = {
    "api_key": "sk-...",
    "model_name": "gpt-4o",
    "base_url": "https://api.openai.com/v1",  # Optional
}
```

---

#### `environment`
{: .no_toc }

**Type:** `Literal["local", "docker", "modal", "prime", "daytona", "e2b"]`
**Default:** `"local"`

The execution environment for running generated code.

| Environment | Description |
|:------------|:------------|
| `local` | Same-process execution with sandboxed builtins (default) |
| `docker` | Containerized execution in Docker |
| `modal` | Cloud sandbox via Modal |
| `prime` | Cloud sandbox via Prime Intellect |
| `daytona` | Cloud sandbox via Daytona |
| `e2b` | Cloud sandbox via E2B |

---

#### `environment_kwargs`
{: .no_toc }

**Type:** `dict[str, Any] | None`
**Default:** `None`

Configuration for the execution environment:

**Local:**
```python
environment_kwargs = {
    "setup_code": "import numpy as np",  # Run before each completion
}
```

**Docker:**
```python
environment_kwargs = {
    "image": "python:3.11-slim",  # Docker image
}
```

**Modal:**
```python
environment_kwargs = {
    "app_name": "my-rlm-app",  # Modal app name
    "timeout": 600,            # Sandbox timeout in seconds
    "image": modal.Image...,   # Custom Modal image (optional)
}
```

---

#### `max_depth`
{: .no_toc }

**Type:** `int`
**Default:** `1`

Maximum recursion depth for nested RLM calls. When `max_depth > 1`, the REPL provides `rlm_query()` and `rlm_query_batched()` functions that spawn child RLMs with their own REPL environments.

When `depth >= max_depth`, `rlm_query()` falls back to a plain `llm_query()` call (no REPL, no iteration).

```python
# Enable one level of recursive sub-calls
rlm = RLM(..., max_depth=2)
```

---

#### `max_iterations`
{: .no_toc }

**Type:** `int`
**Default:** `30`

Maximum number of REPL iterations before forcing a final answer.

Each iteration consists of:
1. LM generates response (potentially with code blocks)
2. Code blocks are executed
3. Results are appended to conversation history

```python
# For complex tasks, allow more iterations
rlm = RLM(..., max_iterations=50)
```

---

#### `max_budget`
{: .no_toc }

**Type:** `float | None`
**Default:** `None`

Maximum total USD cost for a completion. If exceeded, raises `BudgetExceededError`. Requires a backend that reports cost.

---

#### `max_timeout`
{: .no_toc }

**Type:** `float | None`
**Default:** `None`

Maximum wall-clock seconds for a completion. If exceeded, raises `TimeoutExceededError`. The partial answer (if any) is available on the exception.

---

#### `max_tokens`
{: .no_toc }

**Type:** `int | None`
**Default:** `None`

Maximum total tokens (input + output) for a completion. If exceeded, raises `TokenLimitExceededError`.

---

#### `max_errors`
{: .no_toc }

**Type:** `int | None`
**Default:** `None`

Maximum consecutive REPL errors before aborting. The error counter resets on a successful execution. If exceeded, raises `ErrorThresholdExceededError`.

---

#### `custom_system_prompt`
{: .no_toc }

**Type:** `str | None`
**Default:** `None`

Override the default RLM system prompt. The default prompt instructs the LM on:
- How to use the `context` variable
- How to call `llm_query()` / `llm_query_batched()` for plain LM calls
- How to call `rlm_query()` / `rlm_query_batched()` for recursive sub-calls
- How to signal completion with `FINAL()` or `FINAL_VAR()`

```python
custom_prompt = """You are a data analysis expert.
Use the REPL to analyze the context variable.
When done, output FINAL(your answer)."""

rlm = RLM(..., custom_system_prompt=custom_prompt)
```

---

#### `other_backends` / `other_backend_kwargs`
{: .no_toc }

**Type:** `list[str] | None` / `list[dict] | None`
**Default:** `None`

Register additional LM backends. The first `other_backend` is used as the default for depth-routed sub-calls (e.g. `llm_query()` calls from code at depth > 0 are routed to the other backend). Additional backends are registered by model name and can be selected explicitly.

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    other_backends=["anthropic"],
    other_backend_kwargs=[
        {"model_name": "claude-sonnet-4-20250514"},
    ],
)

# Inside REPL, code can call:
# llm_query(prompt)  # Routed to other_backend (Claude) at depth > 0
# llm_query(prompt, model="gpt-4o")  # Explicit model override
```

---

#### `logger`
{: .no_toc }

**Type:** `RLMLogger | None`
**Default:** `None`

Logger for capturing trajectory metadata. When provided, the returned `RLMChatCompletion.metadata` field contains the full trajectory (iterations, code blocks, sub-calls).

```python
from rlm.logger import RLMLogger

# In-memory only (trajectory on result.metadata)
logger = RLMLogger()

# Also save to disk (JSONL for the visualizer)
logger = RLMLogger(log_dir="./logs")

rlm = RLM(..., logger=logger)
```

---

#### `verbose`
{: .no_toc }

**Type:** `bool`
**Default:** `False`

Enable rich console output showing:
- Metadata at startup
- Each iteration's response
- Code execution results
- Final answer and statistics

---

#### `persistent`
{: .no_toc }

**Type:** `bool`
**Default:** `False`

When enabled, reuses the same environment across multiple `completion()` calls. This enables multi-turn conversations where each call adds a new context and the model retains all previous variables and state.

Contexts are versioned (`context_0`, `context_1`, ...) with `context` always aliasing `context_0`. Conversation histories from previous calls are available as `history_0`, `history_1`, etc.

Supports the context manager protocol for automatic cleanup:

```python
with RLM(..., persistent=True) as rlm:
    result1 = rlm.completion("First context")
    result2 = rlm.completion("Second context")  # Can access context_0 and context_1
```

---

#### `custom_tools`
{: .no_toc }

**Type:** `dict[str, Any] | None`
**Default:** `None`

Custom functions and data available in the REPL environment. Callable values are added to globals (callable by the model), non-callable values are added to locals (accessible as variables).

Two formats are supported:

```python
custom_tools = {
    # Plain value
    "fetch_data": my_fetch_function,
    "API_KEY": "sk-...",

    # With description (shown in system prompt)
    "calculator": {
        "tool": calc_function,
        "description": "Performs arithmetic calculations",
    },
}
```

Reserved names (`llm_query`, `rlm_query`, `context`, `history`, `FINAL_VAR`, `SHOW_VARS`, and their batched variants) cannot be used as tool names.

---

#### `custom_sub_tools`
{: .no_toc }

**Type:** `dict[str, Any] | None`
**Default:** `None`

Separate set of custom tools for child RLMs spawned via `rlm_query()`. If `None`, children inherit the parent's `custom_tools`. Pass an empty dict `{}` to disable custom tools for children.

---

#### `compaction`
{: .no_toc }

**Type:** `bool`
**Default:** `False`

When enabled, automatically summarizes the conversation history when token usage exceeds `compaction_threshold_pct` of the model's context window. The full history (including summaries) is available in the REPL as the `history` variable.

---

#### `compaction_threshold_pct`
{: .no_toc }

**Type:** `float`
**Default:** `0.85`

Fraction of the model's context window that triggers compaction. Only used when `compaction=True`.

---

#### Event Callbacks
{: .no_toc }

Optional callbacks for monitoring execution progress:

| Callback | Signature | Triggered when |
|:---------|:----------|:---------------|
| `on_iteration_start` | `(depth: int, iteration_num: int)` | An iteration begins |
| `on_iteration_complete` | `(depth: int, iteration_num: int, duration: float)` | An iteration completes |
| `on_subcall_start` | `(depth: int, model: str, prompt_preview: str)` | A child RLM is spawned |
| `on_subcall_complete` | `(depth: int, model: str, duration: float, error: str \| None)` | A child RLM finishes |

---

## Methods

### `completion()`

Main entry point for RLM completions.

```python
def completion(
    self,
    prompt: str | dict[str, Any],
    root_prompt: str | None = None,
) -> RLMChatCompletion
```

#### Parameters

**`prompt`**
{: .no_toc }

The context/input to process. Becomes the `context` variable in the REPL.

```python
# String input
result = rlm.completion("Analyze this text...")

# Structured input (serialized to JSON)
result = rlm.completion({
    "documents": [...],
    "query": "Find relevant sections",
})

# List input
result = rlm.completion(["doc1", "doc2", "doc3"])
```

**`root_prompt`**
{: .no_toc }

Optional short prompt shown to the root LM on every iteration. Useful for Q&A tasks where the question should be visible throughout.

```python
# The context is the document, but the LM sees the question each iteration
result = rlm.completion(
    prompt=long_document,
    root_prompt="What is the main theme of this document?"
)
```

#### Returns

`RLMChatCompletion` dataclass:

```python
@dataclass
class RLMChatCompletion:
    root_model: str              # Model name used
    prompt: str | dict           # Original input
    response: str                # Final answer
    usage_summary: UsageSummary  # Token usage
    execution_time: float        # Total seconds
    metadata: dict | None        # Full trajectory when logger is provided
```

#### Example

```python
result = rlm.completion(
    "Calculate the factorial of 100 and return the number of digits."
)

print(result.response)          # "158"
print(result.execution_time)    # 12.34
print(result.metadata)          # Trajectory dict (if logger provided), else None
print(result.usage_summary.to_dict())
# {'model_usage_summaries': {'gpt-4o': {'total_calls': 5, ...}}}
```

### `close()`

Clean up persistent environment resources. Called automatically when using the context manager protocol (`with RLM(...) as rlm:`).

---

## Response Types

### `RLMChatCompletion`

```python
from rlm.core.types import RLMChatCompletion

result: RLMChatCompletion = rlm.completion(...)

result.root_model      # "gpt-4o"
result.prompt          # Original input
result.response        # Final answer string
result.execution_time  # Total time in seconds
result.usage_summary   # UsageSummary object
result.metadata        # Full trajectory dict (if logger provided)
```

### `UsageSummary`

```python
from rlm.core.types import UsageSummary

usage: UsageSummary = result.usage_summary
usage.to_dict()
# {
#     "model_usage_summaries": {
#         "gpt-4o": {
#             "total_calls": 5,
#             "total_input_tokens": 15000,
#             "total_output_tokens": 2000
#         }
#     }
# }
```

---

## REPL Functions

The following functions are available to model-generated code inside the REPL:

| Function | Description |
|:---------|:------------|
| `llm_query(prompt, model=None)` | Single plain LM completion. Fast, no REPL or iteration. |
| `llm_query_batched(prompts, model=None)` | Multiple plain LM completions concurrently. |
| `rlm_query(prompt, model=None)` | Spawn a child RLM with its own REPL for deeper thinking. Falls back to `llm_query` at max depth. |
| `rlm_query_batched(prompts, model=None)` | Spawn multiple child RLMs. Falls back to `llm_query_batched` at max depth. |
| `FINAL_VAR(variable_name)` | Return a REPL variable as the final answer. |
| `SHOW_VARS()` | List all user-created variables in the REPL. |
| `print(...)` | Print output visible to the model in the next iteration. |

---

## Error Handling

RLM follows a "fail fast" philosophy:

```python
# Missing required argument
rlm = RLM(backend="vllm", backend_kwargs={"model_name": "llama"})
# Raises: AssertionError: base_url is required for vLLM

# Unknown backend
rlm = RLM(backend="unknown")
# Raises: ValueError: Unknown backend: unknown
```

If the RLM exhausts `max_iterations` without finding a `FINAL()` / `FINAL_VAR()` answer, it prompts the LM one more time to provide a final answer based on the conversation history.

RLM raises explicit exceptions when limits are exceeded:

| Exception | Raised when | Key attributes |
|:----------|:------------|:---------------|
| `BudgetExceededError` | `max_budget` exceeded | `spent`, `budget` |
| `TimeoutExceededError` | `max_timeout` exceeded | `elapsed`, `timeout`, `partial_answer` |
| `TokenLimitExceededError` | `max_tokens` exceeded | `tokens_used`, `token_limit`, `partial_answer` |
| `ErrorThresholdExceededError` | `max_errors` consecutive errors | `error_count`, `threshold`, `last_error`, `partial_answer` |
| `CancellationError` | `KeyboardInterrupt` during completion | `partial_answer` |

All exceptions are importable from the top-level package:

```python
from rlm import RLM, TimeoutExceededError, CancellationError

try:
    result = rlm.completion(prompt)
except TimeoutExceededError as e:
    print(f"Timed out after {e.elapsed:.1f}s, partial: {e.partial_answer}")
except CancellationError as e:
    print(f"Cancelled, partial: {e.partial_answer}")
```

---

## Thread Safety

Each `completion()` call:
1. Spawns its own `LMHandler` socket server
2. Creates a fresh environment instance (unless persistent)
3. Cleans up both when done

This makes `completion()` calls independent, but the `RLM` instance itself should not be shared across threads without external synchronization.

---

## Example: Full Configuration

```python
import os
from rlm import RLM
from rlm.logger import RLMLogger

logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    # Primary model
    backend="anthropic",
    backend_kwargs={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model_name": "claude-sonnet-4-20250514",
    },

    # Execution environment
    environment="local",

    # Additional model for sub-calls (routed at depth > 0)
    other_backends=["openai"],
    other_backend_kwargs=[{
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-4o-mini",
    }],

    # Recursion: allow one level of child RLMs via rlm_query()
    max_depth=2,
    max_iterations=40,

    # Limits
    max_timeout=120.0,
    max_budget=1.0,
    max_errors=5,

    # Custom tools available in the REPL
    custom_tools={
        "fetch_data": {"tool": my_fetch_fn, "description": "Fetch data from API"},
    },

    # Compaction for long conversations
    compaction=True,
    compaction_threshold_pct=0.85,

    # Debugging
    logger=logger,
    verbose=True,
)

result = rlm.completion(
    prompt=massive_document,
    root_prompt="Summarize the key findings",
)

print(result.response)
print(result.metadata)  # Full trajectory (iterations, sub-calls, etc.)
```
