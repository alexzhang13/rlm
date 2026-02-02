---
layout: default
title: Getting Started
nav_order: 2
---

# Getting Started
{: .no_toc }

A complete guide to installing and configuring RLM for your projects.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Installation

### Prerequisites

- Python 3.11 or higher
- An API key from a supported LLM provider (OpenAI, Anthropic, etc.)

### Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv init && uv venv --python 3.12
source .venv/bin/activate

# Install RLM in editable mode
uv pip install -e .
```

### Optional: Modal Support

For cloud-based sandboxed execution:

```bash
# Install Modal extra
uv pip install -e ".[modal]"

# Authenticate Modal
modal setup
```

### Optional: Docker Support

For containerized execution, ensure Docker is installed and running:

```bash
# Verify Docker is available
docker --version
```

---

## Your First RLM Call

### Step 1: Set Up API Keys

Create a `.env` file in your project root:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PORTKEY_API_KEY=...
```

### Step 2: Basic Usage

```python
import os
from dotenv import load_dotenv
from rlm import RLM

load_dotenv()

# Create RLM instance
rlm = RLM(
    backend="openai",
    backend_kwargs={
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-4o",
    },
)

# Make a completion call
result = rlm.completion("Calculate the 50th Fibonacci number using Python.")
print(result.response)
```

### Step 3: Enable Verbose Output

See what the RLM is doing step by step:

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-4o",
    },
    verbose=True,  # Enable rich console output
)
```

This will display:
- Each iteration's LM response
- Code blocks being executed
- Stdout/stderr from execution
- Final answer when reached

---

## Understanding the RLM Class

### Constructor Arguments

| Argument | Type | Default | Description |
|:---------|:-----|:--------|:------------|
| `backend` | `str` | `"openai"` | LM provider backend |
| `backend_kwargs` | `dict` | `None` | Backend-specific configuration |
| `environment` | `str` | `"local"` | Execution environment type |
| `environment_kwargs` | `dict` | `None` | Environment configuration |
| `max_depth` | `int` | `1` | Maximum recursion depth |
| `max_iterations` | `int` | `30` | Max REPL iterations per call |
| `max_budget` | `float` | `None` | Max total USD cost (if provider reports cost) |
| `max_timeout` | `float` | `None` | Max wall-clock seconds per completion |
| `max_tokens` | `int` | `None` | Max total tokens (input + output) per completion |
| `max_errors` | `int` | `None` | Max consecutive REPL errors before abort |
| `custom_system_prompt` | `str` | `None` | Override default system prompt |
| `other_backends` | `list` | `None` | Additional backends for sub-calls |
| `other_backend_kwargs` | `list` | `None` | Configs for additional backends |
| `logger` | `RLMLogger` | `None` | Logger for trajectory tracking |
| `verbose` | `bool` | `False` | Enable console output |

### The `completion()` Method

```python
result = rlm.completion(
    prompt="Your input text or context",
    root_prompt="Optional: A short prompt visible to the root LM"
)
```

**Parameters:**
- `prompt`: The main context/input (string or dict). This becomes the `context` variable in the REPL.
- `root_prompt`: Optional hint shown to the root LM (useful for Q&A tasks).

**Returns:** `RLMChatCompletion` with:
- `response`: The final answer string
- `usage_summary`: Token usage statistics
- `execution_time`: Total time in seconds
- `root_model`: Model name used
- `prompt`: Original input

### Depth>1 Recursion

Depth>1 recursive subcalls are supported. When code inside the REPL calls `llm_query()` and `max_depth` allows it, RLM spawns a child RLM with its own REPL. When `depth >= max_depth`, it falls back to a plain LM completion.

### Limits and Exceptions

RLM raises explicit exceptions when limits are exceeded:
- `BudgetExceededError`
- `TimeoutExceededError`
- `TokenLimitExceededError`
- `ErrorThresholdExceededError`

---

## Choosing an Environment

RLM supports three execution environments:

### Local (Default)

Code runs in the same Python process with sandboxed builtins.

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    environment="local",
)
```

**Pros:** Fast, no setup required  
**Cons:** Less isolation from host process

### Docker

Code runs in a Docker container with full isolation.

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    environment="docker",
    environment_kwargs={
        "image": "python:3.11-slim",  # Custom image
    },
)
```

**Pros:** Containerized isolation, reproducible  
**Cons:** Requires Docker, slower startup

### Modal

Code runs in Modal's cloud sandboxes for full isolation.

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    environment="modal",
    environment_kwargs={
        "app_name": "my-rlm-app",
        "timeout": 600,
    },
)
```

**Pros:** Cloud-native, scalable, fully isolated  
**Cons:** Requires Modal account, network latency

---

## Choosing a Backend

### OpenAI

```python
rlm = RLM(
    backend="openai",
    backend_kwargs={
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model_name": "gpt-4o",
        # Optional: custom base URL
        # "base_url": "https://api.openai.com/v1",
    },
)
```

### Anthropic

```python
rlm = RLM(
    backend="anthropic",
    backend_kwargs={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model_name": "claude-sonnet-4-20250514",
    },
)
```

### Portkey (Router)

```python
rlm = RLM(
    backend="portkey",
    backend_kwargs={
        "api_key": os.getenv("PORTKEY_API_KEY"),
        "model_name": "@openai/gpt-5-nano",  # Portkey model format
    },
)
```

### OpenRouter

```python
rlm = RLM(
    backend="openrouter",
    backend_kwargs={
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model_name": "openai/gpt-4o",
    },
)
```

### vLLM (Local)

```python
rlm = RLM(
    backend="vllm",
    backend_kwargs={
        "base_url": "http://localhost:8000/v1",  # Required
        "model_name": "meta-llama/Llama-3-70b",
    },
)
```

---

## Logging and Debugging

### Enable Logging

```python
from rlm import RLM
from rlm.logger import RLMLogger

# Create logger
logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="openai",
    backend_kwargs={"model_name": "gpt-4o"},
    logger=logger,
    verbose=True,
)

result = rlm.completion("...")
# Logs saved to ./logs/rlm_TIMESTAMP_UUID.jsonl
```

### Log File Format

Logs are JSON-lines files with:

```json
{"type": "metadata", "root_model": "gpt-4o", "max_iterations": 30, ...}
{"type": "iteration", "iteration": 1, "response": "...", "code_blocks": [...]}
{"type": "iteration", "iteration": 2, "response": "...", "final_answer": "..."}
```

### Visualizer

Use the included visualizer to explore trajectories:

```bash
cd visualizer/
npm install
npm run dev  # Opens at localhost:3001
```

Upload `.jsonl` log files to visualize:
- Iteration timeline
- Code execution results
- Sub-LM call traces
- Token usage

---

## Next Steps

- [API Reference](api/rlm.md) - Complete RLM class documentation
- [Environments](environments/) - Deep dive into each environment
- [Backends](backends.md) - Detailed backend configuration
