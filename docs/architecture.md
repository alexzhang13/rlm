---
layout: default
title: Architecture
nav_order: 3
---

# Architecture
{: .no_toc }

How the RLM runtime, LM handler, code execution, and recursive sub-calls fit together.
{: .fs-6 .fw-300 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

An RLM completion involves three cooperating pieces:

1. **RLM** (`rlm/core/rlm.py`) — the main loop that drives iteration.
2. **LMHandler** (`rlm/core/lm_handler.py`) — a per-completion TCP server that routes LM API calls.
3. **LocalREPL** (`rlm/environments/local_repl.py`) — the Python execution environment where model-generated code runs.

```
┌────────────────────────────────────────────────────────────────┐
│  RLM.completion(prompt)                                        │
│                                                                │
│  1. Spawn LMHandler (TCP server on localhost, auto port)       │
│  2. Create LocalREPL (in-process exec() namespace)             │
│  3. Iterate:                                                   │
│     a. Send message history → LM backend → get response        │
│     b. Extract ```repl``` code blocks from response            │
│     c. Execute code in LocalREPL                               │
│     d. Append stdout/stderr to message history                 │
│     e. Repeat until FINAL_VAR / FINAL or limits exceeded       │
│  4. Tear down handler and environment                          │
└────────────────────────────────────────────────────────────────┘
```

---

## LM Handler

### What it is

The LMHandler is a **multi-threaded TCP socket server** that sits between
the execution environment and the actual LM API backends. Every call to
`RLM.completion()` spins up a fresh handler (unless the environment is
persistent and already has one).

### Why a socket server?

The handler exists so that code running inside the execution environment
can make LM calls back to the host process without directly importing or
calling the LM client. This is essential for isolated environments (Docker,
Modal) that run in separate processes or machines — they communicate with
the handler over TCP. The local environment uses the same protocol for
consistency, even though it runs in-process.

### Lifecycle

```python
# Inside RLM._spawn_completion_context():
client = get_client(backend, backend_kwargs)            # 1. Create LM client
lm_handler = LMHandler(client, other_backend_client=…)  # 2. Wrap in handler
lm_handler.start()                                       # 3. Start TCP server (daemon thread)
# … run completion loop …
lm_handler.stop()                                        # 4. Shut down server
```

- The server binds to `127.0.0.1` with port `0` (OS auto-assigns an available port).
- It runs in a **daemon thread** so it doesn't block process exit.
- Each incoming connection is handled by a new thread (`ThreadingTCPServer`).

### Wire protocol

All messages use a simple framing: **4-byte big-endian length prefix + UTF-8 JSON payload**.

```
┌──────────┬─────────────────────────┐
│ 4 bytes  │  N bytes                │
│ len (BE) │  JSON payload (UTF-8)   │
└──────────┴─────────────────────────┘
```

Implemented in `socket_send()` / `socket_recv()` in `rlm/core/comms_utils.py`.

### Client routing

The handler can hold multiple LM clients and routes requests based on the
`model` and `depth` fields in the request:

```python
def get_client(self, model=None, depth=0):
    if model and model in self.clients:
        return self.clients[model]        # Explicit model override
    if depth == 1 and self.other_backend_client:
        return self.other_backend_client  # Depth-based routing
    return self.default_client            # Fallback
```

This lets you use a different (e.g. cheaper/faster) model for sub-LM calls
by specifying `other_backends` / `other_backend_kwargs` in the RLM constructor.

---

## Code Execution Environment (LocalREPL)

### In-process `exec()` — not a subprocess

LocalREPL executes model-generated code **in the same Python interpreter
process** as the RLM, using Python's built-in `exec()`. There is no
subprocess, no fork, and no IPC for code execution.

```python
# Simplified from LocalREPL.execute_code():
combined = {**self.globals, **self.locals}
exec(code, combined, combined)
```

### What this means in practice

- **Fast**: No process spawn overhead. Code execution is as fast as native Python.
- **Persistent namespace**: Variables created in one code block are visible in the next. The `self.locals` dict accumulates state across iterations.
- **Shared memory**: Helper functions like `llm_query()` and `rlm_query()` are plain Python closures in `self.globals`. When model code calls `llm_query("...")`, it's a direct function call within the same process.
- **Limited sandbox**: Dangerous builtins (`eval`, `exec`, `compile`, `input`) are removed from the namespace. This is a soft sandbox — it prevents accidental misuse but is not a security boundary.

### Namespace layout

```
globals (shared across all executions):
├── __builtins__        → _SAFE_BUILTINS (eval/exec/input removed)
├── llm_query()         → plain LM call via handler
├── llm_query_batched() → batched plain LM calls
├── rlm_query()         → recursive RLM sub-call (or fallback to llm_query)
├── rlm_query_batched() → batched recursive sub-calls
├── FINAL_VAR()         → mark a variable as the final answer
├── SHOW_VARS()         → list user-created variables
└── <custom_tools>      → user-provided callable tools

locals (accumulates user variables):
├── context             → alias for context_0
├── context_0           → first context payload
├── context_1, …        → additional contexts (persistent mode)
├── history             → conversation history (persistent/compaction mode)
└── <user variables>    → anything created by model code
```

### Scaffold restoration

After each `exec()`, LocalREPL restores all reserved names to prevent model
code from corrupting the environment. If the model writes
`llm_query = "oops"` or `context = None`, the next execution will still
have the real functions and data. See `_restore_scaffold()`.

---

## How `llm_query()` and `rlm_query()` Work

These are the two functions available to model-generated code for making LM calls.
They have very different behaviors:

### `llm_query(prompt, model=None)` — Plain LM call

Always makes a single, direct LM completion. No REPL, no iteration — just
prompt in, text out. Fast and lightweight.

```
Model code: answer = llm_query("Summarize this text: ...")
    │
    ▼
LocalREPL._llm_query()
    │  Creates LMRequest(prompt=..., depth=self.depth)
    │  Opens TCP socket to handler
    ▼
LMHandler (TCP server)
    │  get_client(model, depth) → selects backend
    │  client.completion(prompt) → calls LM API
    ▼
Response flows back over socket
    │
    ▼
Returns response string to model code
```

### `rlm_query(prompt, model=None)` — Recursive RLM sub-call

Spawns a **child RLM** that gets its own REPL and can reason iteratively
over the prompt — just like the parent. Use this when the subtask needs
multi-step reasoning, code execution, or its own iterative problem-solving.

Falls back to `llm_query` when recursion is not available (i.e. the current
depth has reached `max_depth`).

```
Model code: answer = rlm_query("Solve this complex problem: ...")
    │
    ▼
LocalREPL._rlm_query()
    │  if self.subcall_fn is not None:    ← set when max_depth > 1
    │      calls self.subcall_fn(prompt, model)
    │  else:
    │      falls back to _llm_query()
    │
    ▼  (when subcall_fn exists)
RLM._subcall(prompt, model)
    │  next_depth = self.depth + 1
    │  if next_depth >= max_depth:
    │      → plain client.completion() (leaf call, no REPL)
    │  else:
    │      → create child RLM(depth=next_depth, ...)
    │      → child.completion(prompt)  ← full RLM with its own handler + REPL
    │
    ▼
Returns RLMChatCompletion to parent
```

### `llm_query_batched` / `rlm_query_batched`

Same semantics as above, but for multiple prompts. `llm_query_batched` sends
all prompts as a single batched request to the handler, which processes them
concurrently with `asyncio.gather`. `rlm_query_batched` calls `subcall_fn`
sequentially for each prompt (each child RLM is a blocking call).

---

## Recursive Sub-Calls (Depth > 1)

### How depth works

```
max_depth=3

RLM (depth=0)
 └─ rlm_query() → child RLM (depth=1)
     └─ rlm_query() → child RLM (depth=2)
         └─ rlm_query() → plain LM call (depth=3 >= max_depth, no REPL)
```

- `depth=0` is the root RLM that the user calls.
- Each child increments depth by 1.
- When `next_depth >= max_depth`, `_subcall()` does a plain `client.completion()` instead of creating a child RLM. This is the leaf case — no REPL, no iteration.
- `llm_query()` always does a plain LM call regardless of depth. Only `rlm_query()` triggers recursion.

### Each child gets its own handler and environment

When a child RLM is created via `_subcall()`, its `completion()` method calls
`_spawn_completion_context()` which creates:

1. **A new `LMHandler`** listening on a **different auto-assigned port**.
2. **A new `LocalREPL`** with its own isolated namespace.

```
Parent RLM (depth=0)
├── LMHandler #1 on port 52301
├── LocalREPL #1 (depth=1)
│   ├── globals: {llm_query, rlm_query, ...}
│   ├── locals: {context: "parent prompt", ...}
│   └── subcall_fn = RLM._subcall  ← enables rlm_query()
│
└── When model code calls rlm_query("subtask"):
    │
    └── Child RLM (depth=1)
        ├── LMHandler #2 on port 52302  ← NEW handler, NEW port
        ├── LocalREPL #2 (depth=2)      ← NEW namespace
        │   ├── locals: {context: "subtask", ...}
        │   └── subcall_fn = child._subcall (or None if at max_depth-1)
        │
        └── Runs its own iteration loop, returns RLMChatCompletion
```

The child's handler and environment are torn down when the child's `completion()` finishes.

### Resource limits propagate

The parent passes **remaining** budget/timeout/tokens to the child, not the
original totals. This prevents a child from consuming all of the parent's resources:

```python
# In _subcall():
remaining_timeout = self.max_timeout - elapsed  # not self.max_timeout
remaining_budget = self.max_budget - spent       # not self.max_budget
child = RLM(..., max_timeout=remaining_timeout, max_budget=remaining_budget)
```

### Metadata flows back

Each child RLM can have its own `RLMLogger`. When the child completes, its
full trajectory metadata (iterations, code blocks, sub-calls) is captured in
the returned `RLMChatCompletion.metadata` dict. The parent's logger records
this as part of the REPL result's `rlm_calls` list, creating a nested
metadata tree.

---

## Putting It All Together

Here's the complete request flow for a depth-2 RLM call:

```
User: rlm.completion("Analyze this data")
 │
 ▼
RLM (depth=0)
 ├─ _spawn_completion_context()
 │   ├─ LMHandler #1 starts on port 52301
 │   └─ LocalREPL #1 created with context="Analyze this data"
 │
 ├─ Iteration 1: LM generates code
 │   │  ```repl
 │   │  answer = rlm_query("What patterns exist in: " + context[:5000])
 │   │  ```
 │   │
 │   └─ LocalREPL.execute_code() runs the code via exec()
 │       │
 │       ├─ rlm_query() → _rlm_query() → subcall_fn()
 │       │   │
 │       │   └─ RLM._subcall("What patterns exist in: ...")
 │       │       │
 │       │       ├─ depth=1 < max_depth=2, so create child RLM
 │       │       │
 │       │       └─ Child RLM (depth=1)
 │       │           ├─ LMHandler #2 on port 52302
 │       │           ├─ LocalREPL #2 with context="What patterns..."
 │       │           │
 │       │           ├─ Child iteration 1: LM generates code
 │       │           │   │  result = llm_query("Extract key metrics: " + context)
 │       │           │   │
 │       │           │   └─ llm_query() → TCP to Handler #2 → LM API → response
 │       │           │
 │       │           ├─ Child iteration 2: LM calls FINAL_VAR(result)
 │       │           │
 │       │           └─ Returns RLMChatCompletion to parent
 │       │
 │       └─ answer = child_completion.response
 │
 ├─ Iteration 2: LM uses answer, calls FINAL_VAR(final)
 │
 ├─ LMHandler #1 stops
 └─ Returns RLMChatCompletion to user
```

### Key takeaways

| Aspect | Detail |
|:-------|:-------|
| Code execution | In-process `exec()` in the same Python interpreter. Not a subprocess. |
| LM calls from code | Go through a local TCP socket server (LMHandler), even for in-process execution. |
| Handler per completion | Each `completion()` call gets its own handler on an auto-assigned port. |
| Child RLMs | Created by `_subcall()`, each with its own handler + LocalREPL. Fully independent. |
| `llm_query` vs `rlm_query` | `llm_query` = always plain LM call. `rlm_query` = recursive child RLM (or fallback). |
| Depth limit | At `max_depth`, `rlm_query` falls back to `llm_query`. No further recursion. |
| Resource isolation | Children get remaining budget/timeout, not the full amount. |
| Namespace isolation | Each LocalREPL has its own `globals`/`locals`. No shared state between parent and child. |
