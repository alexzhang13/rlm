# RLM Tools API Documentation

**For integration with rlm-service**

## Overview

The RLM library now supports OpenAI function calling (tools) in REPL sub-LLM queries. This enables LLM agents to access external data sources, pre-computed statistics, and APIs through a clean tool-calling interface.

## API Surface Changes

### 1. `llm_query()` - New Parameters

**Location**: Available in REPL environment namespace

**Signature**:
```python
def llm_query(
    prompt: str | list[dict[str, Any]],
    model: str | None = None,
    response_format: dict | None = None,
    tools: list[dict] | None = None,           # NEW
    tool_handler: Callable[[str, dict], str] | None = None  # NEW
) -> str
```

**New Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tools` | `list[dict] \| None` | No | OpenAI tool definitions (function calling schema) |
| `tool_handler` | `Callable[[str, dict], str] \| None` | If `tools` provided | Function that executes tool calls |

**Tool Handler Signature**:
```python
def tool_handler(tool_name: str, arguments: dict) -> str:
    """
    Args:
        tool_name: The name of the tool being called
        arguments: Dict of arguments passed by the model

    Returns:
        String result to send back to the model
    """
```

**Behavior**:
- If `tools=None` (default): Works exactly as before (backward compatible)
- If `tools` provided without `tool_handler`: Raises `ValueError`
- If both provided: Runs automatic tool-calling loop until model returns final content

**Example**:
```python
result = llm_query(
    "What's the average rating for question 3?",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_stats",
            "description": "Get statistics",
            "parameters": {
                "type": "object",
                "properties": {"q_id": {"type": "integer"}},
                "required": ["q_id"]
            }
        }
    }],
    tool_handler=lambda name, args: json.dumps({"avg": 4.2})
)
```

### 2. `llm_query_batched()` - New Parameters

**Location**: Available in REPL environment namespace

**Signature**:
```python
def llm_query_batched(
    prompts: list[str | list[dict[str, Any]]],
    model: str | None = None,
    response_formats: list[dict | None] | None = None,
    tools: list[dict] | None = None,                    # NEW
    tool_handler: Callable[[str, dict], str] | None = None  # NEW
) -> list[str]
```

**New Parameters**: Same as `llm_query()`

**Behavior**:
- Each prompt gets its own independent tool-calling loop
- Tools and handler are shared across all prompts
- Returns list of final responses (same order as input prompts)

**Example**:
```python
results = llm_query_batched(
    ["Analyze Q1", "Analyze Q2", "Analyze Q3"],
    tools=TOOLS,
    tool_handler=handler
)
```

## Socket Protocol Changes

### LMRequest Message

**New fields** in JSON payload:

```json
{
  "prompt": "...",
  "model": "gpt-4",
  "depth": 1,
  "response_format": null,
  "tools": [                          // NEW (optional)
    {
      "type": "function",
      "function": {
        "name": "get_stats",
        "description": "...",
        "parameters": { ... }
      }
    }
  ],
  "tool_choice": "auto"              // NEW (optional)
}
```

**Fields**:
- `tools` (optional): Array of OpenAI tool definitions
- `tool_choice` (optional): `"auto"`, `"none"`, or specific tool object

### LMResponse Message

**No changes** - still returns string in `response` field

However, during tool-calling loop, the response may contain JSON-serialized tool_calls:

```json
{
  "chat_completion": {
    "response": "{\"tool_calls\": [...], \"content\": null}",  // Intermediate
    "model": "gpt-4",
    ...
  }
}
```

This is handled internally by the environment layer. **Clients of rlm-service see only the final string response**.

## Tool-Calling Loop

The environment layer (`LocalREPL`) handles the complete loop:

```
1. Send messages + tools to model
   ↓
2. Model responds with tool_calls
   ↓
3. Execute tool_handler() for each call
   ↓
4. Append tool results to conversation
   ↓
5. Repeat until model returns content
   ↓
6. Return final content (str)
```

**Maximum iterations**: 10 (prevents infinite loops)

## Error Handling

### Validation Errors

**Error**: `ValueError: tool_handler is required when tools are provided`
- **Cause**: `tools` specified but no `tool_handler`
- **Fix**: Provide both parameters

### Tool Execution Errors

If `tool_handler` raises an exception:
```python
def tool_handler(name, args):
    raise RuntimeError("Database connection failed")
```

**Behavior**: Error message is returned to the model as tool result
```
"Error executing get_stats: Database connection failed"
```

The model can then respond to the error or retry.

### Infinite Loop Protection

**Error**: `__LLM_ERROR__|tool_loop_error|0|Maximum tool iterations (10) exceeded`
- **Cause**: Model keeps requesting tools without returning final content
- **Behavior**: Loop terminates, error returned

## Integration Example for rlm-service

### Server-Side Setup

```python
from rlm import RLM

# Pre-computed stats (expensive query, cached)
STATS_CACHE = {
    "q1": {"total": 500, "avg": 4.2, "distribution": {...}},
    "q2": {"total": 500, "avg": 3.8, "distribution": {...}},
}

# Tool definitions
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_stats",
        "description": "Get pre-computed statistics for a question",
        "parameters": {
            "type": "object",
            "properties": {
                "question_id": {"type": "string"}
            },
            "required": ["question_id"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

# Tool handler (access to server-side data)
def stats_handler(tool_name, arguments):
    if tool_name == "get_stats":
        q_id = arguments["question_id"]
        return json.dumps(STATS_CACHE.get(q_id, {}))
    return json.dumps({"error": "Unknown tool"})

# Setup code with tools
SETUP_CODE = f"""
import json

TOOLS = {TOOLS}

def tool_handler(name, args):
    # This gets injected by RLM - calls back to server
    # In practice, this would be the stats_handler above
    pass

# Available in REPL:
# - llm_query(prompt, tools=TOOLS, tool_handler=tool_handler)
# - llm_query_batched(prompts, tools=TOOLS, tool_handler=tool_handler)
"""

rlm = RLM(backend="openai", setup_code=SETUP_CODE)
```

### Client Request

```python
# Client sends task
response = rlm.completion(
    "Analyze responses to questions 1-3 and provide detailed insights"
)

# RLM generates REPL code that uses tools:
"""
results = []
for q in ["q1", "q2", "q3"]:
    stats = json.loads(tool_handler("get_stats", {"question_id": q}))

    # Qualitative analysis with sub-LLM
    insight = llm_query(
        f"Given these stats: {stats}, provide key insights",
        model="gpt-4o-mini"
    )

    results.append({"question": q, "stats": stats, "insight": insight})

FINAL_VAR("results")
"""
```

## Async & Observability

### 1. `RLM.acompletion()`

**Location**: `rlm.core.rlm.RLM`

**Signature**:
```python
async def acompletion(
    self,
    prompt: str | dict[str, Any],
    root_prompt: str | None = None,
    on_iteration: Callable[[RLMIteration, int], Coroutine] | None = None
) -> RLMChatCompletion
```

**New Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `on_iteration` | `Callable \| None` | No | Async callback triggered after each reasoning turn. Receives `(iteration, index)`. |

**Usage with Inngest**:
```python
async def on_step(iteration, index):
    await ctx.step.run(f"Reasoning Step {index}", lambda: iteration.to_dict())

result = await rlm.acompletion(prompt, on_iteration=on_step)
```

### 2. `on_request` Callback

**Location**: `RLM.__init__`

**Signature**:
```python
def __init__(..., on_request: Callable[[LMRequest, LMResponse], None] | None = None)
```

**Description**:
A synchronous callback triggered every time the REPL environment makes a call back to the LM (sub-queries).

**Usage**:
```python
def log_event(req, res):
    inngest_client.send_sync(inngest.Event(name="rlm/sub-query", data=res.to_dict()))

rlm = RLM(..., on_request=log_event)
```

## Backward Compatibility

✅ **All existing code works unchanged**

- `llm_query(prompt)` - works as before
- `llm_query(prompt, model="gpt-4")` - works as before
- `llm_query(prompt, response_format={...})` - works as before

New parameters are **optional** and default to `None`.

## Performance Considerations

### Efficiency Gains

**Tools avoid LLM calls for deterministic work:**

```python
# BAD: Using LLM for simple computation
count = llm_query(f"Count how many responses = 'A': {data}")

# GOOD: Use tool (instant, free)
count = tool_handler("count_responses", {"choice": "A"})
```

**Mixed approach is most efficient:**

```python
# Quantitative: Tools (pre-computed)
stats = get_stats_tool(q_id=3)

# Qualitative: Batched sub-LLM (cheap model)
themes = llm_query_batched(
    sample_responses,
    model="gpt-4o-mini",
    tools=None  # No tools needed here
)
```

### Tool-Calling Overhead

- Simple path (no tools): **No overhead** (optimized backward-compatible code)
- With tools: Adds message history management + tool execution time
- Batched with tools: Each prompt gets independent loop (may be slower than simple batch)

## Testing

Comprehensive test suite included:

```bash
pytest tests/test_tools.py -v  # 14 tests, all passing
```

**Test coverage**:
- ✅ Single and multiple tool call rounds
- ✅ Tool handler exceptions
- ✅ Infinite loop protection
- ✅ Backward compatibility (20 existing tests pass)
- ✅ Batched queries with tools
- ✅ Multiple tools in single response

## Migration Guide

### If you're NOT using tools

**No changes required**. Your code works as-is.

### If you want to add tools

**Step 1**: Define tool schemas (OpenAI format)
```python
TOOLS = [{"type": "function", "function": {...}}]
```

**Step 2**: Implement tool handler
```python
def handler(tool_name: str, args: dict) -> str:
    # Execute tool, return result as string
    return json.dumps(result)
```

**Step 3**: Pass to llm_query
```python
result = llm_query(prompt, tools=TOOLS, tool_handler=handler)
```

## Limitations

1. **Tool handler must be synchronous** (no async)
2. **Tools are shared in batched queries** (same tools/handler for all prompts)
3. **Maximum 10 tool-calling iterations** per query
4. **Tool handler must return string** (serialize complex objects as JSON)

## Support

For issues or questions:
- GitHub Issues: [Delta-Labs-AG/rlm/issues](https://github.com/Delta-Labs-AG/rlm/issues)
- See also: [TOOLS_IMPLEMENTATION_SUMMARY.md](./TOOLS_IMPLEMENTATION_SUMMARY.md)

## Version

This API is available in `v0.1.0-delta.2` and later.
