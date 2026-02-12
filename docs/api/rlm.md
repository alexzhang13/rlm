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
    backend_kwargs={"model_name": "gpt-5"},
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
    custom_system_prompt: str | None = None,
    other_backends: list[str] | None = None,
    other_backend_kwargs: list[dict] | None = None,
    logger: RLMLogger | None = None,
    verbose: bool = False,
)
```

### Parameters

#### `backend`
{: .no_toc }

**Type:** `Literal["openai", "anthropic", "azure_anthropic", "azure_openai", "portkey", "openrouter", "vllm", "litellm", "gemini", "vercel"]`
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
| `azure_anthropic` | `model_name` | `api_key`, `resource`, `base_url` |
| `azure_openai` | `model_name` | `api_key`, `azure_endpoint`, `azure_deployment`, `api_version` |
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

**Type:** `Literal["local", "modal", "docker"]`  
**Default:** `"local"`

The execution environment for running generated code.

| Environment | Description |
|:------------|:------------|
| `local` | Same-process execution with sandboxed builtins |
| `docker` | Containerized execution in Docker |
| `modal` | Cloud sandbox via Modal |

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

Maximum recursion depth for nested RLM calls. Currently only depth 1 is fully supported.

When `depth >= max_depth`, the RLM falls back to a regular LM completion.

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
rlm = RLM(
    ...,
    max_iterations=50,
)
```

---

#### `custom_system_prompt`
{: .no_toc }

**Type:** `str | None`  
**Default:** `None`

Override the default RLM system prompt. The default prompt instructs the LM on:
- How to use the `context` variable
- How to call `llm_query()` and `llm_query_batched()`
- How to signal completion with `FINAL()`

```python
custom_prompt = """You are a data analysis expert.
Use the REPL to analyze the context variable.
When done, output FINAL(your answer)."""

rlm = RLM(
    ...,
    custom_system_prompt=custom_prompt,
)
```

---

#### `other_backends` / `other_backend_kwargs`
{: .no_toc }

**Type:** `list[str] | None` / `list[dict] | None`  
**Default:** `None`

Register additional LM backends available for sub-calls via `llm_query()`.

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    other_backends=["anthropic", "openai"],
    other_backend_kwargs=[
        {"model_name": "claude-sonnet-4-20250514"},
        {"model_name": "gpt-4o-mini"},
    ],
)

# Inside REPL, code can call:
# llm_query(prompt)  # Uses default (gpt-4o)
# llm_query(prompt, model="claude-sonnet-4-20250514")  # Uses Claude
# llm_query(prompt, model="gpt-4o-mini")  # Uses GPT-4o-mini
```

---

#### `logger`
{: .no_toc }

**Type:** `RLMLogger | None`  
**Default:** `None`

Logger for saving iteration trajectories to disk.

```python
from rlm.logger import RLMLogger

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

Optional short prompt shown to the root LM. Useful for Q&A tasks where the question should be visible throughout.

```python
# The context is the document, but the LM sees the question
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
    root_model: str           # Model name used
    prompt: str | dict        # Original input
    response: str             # Final answer
    usage_summary: UsageSummary  # Token usage
    execution_time: float     # Total seconds
```

#### Example

```python
result = rlm.completion(
    "Calculate the factorial of 100 and return the number of digits."
)

print(result.response)          # "158"
print(result.execution_time)    # 12.34
print(result.usage_summary.to_dict())
# {'model_usage_summaries': {'gpt-4o': {'total_calls': 5, ...}}}
```

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

## Error Handling

RLM follows a "fail fast" philosophy:

```python
# Missing required argument
rlm = RLM(
    backend="vllm",
    backend_kwargs={"model_name": "llama"},
)
# Raises: AssertionError: base_url is required for vLLM

# Unknown backend
rlm = RLM(backend="unknown")
# Raises: ValueError: Unknown backend: unknown
```

If the RLM exhausts `max_iterations` without finding a `FINAL()` answer, it prompts the LM one more time to provide a final answer based on the conversation history.

---

## Thread Safety

Each `completion()` call:
1. Spawns its own `LMHandler` socket server
2. Creates a fresh environment instance
3. Cleans up both when done

This makes `completion()` calls independent, but the `RLM` instance itself should not be shared across threads without external synchronization.

---

## Example: Full Configuration

```python
import os
from rlm import RLM
from rlm.logger import RLMLogger

logger = RLMLogger(log_dir="./logs", file_name="analysis")

rlm = RLM(
    # Primary model
    backend="anthropic",
    backend_kwargs={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model_name": "claude-sonnet-4-20250514",
    },
    
    # Execution environment
    environment="docker",
    environment_kwargs={
        "image": "python:3.11-slim",
    },
    
    # Additional models for sub-calls
    other_backends=["openai"],
    other_backend_kwargs=[{
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-4o-mini",
    }],
    
    # Behavior
    max_iterations=40,
    max_depth=1,
    
    # Debugging
    logger=logger,
    verbose=True,
)

result = rlm.completion(
    prompt=massive_document,
    root_prompt="Summarize the key findings"
)
```

