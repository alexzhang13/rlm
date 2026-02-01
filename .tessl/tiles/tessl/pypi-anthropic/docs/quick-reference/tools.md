# Tools API - Quick Reference

Compact API signatures for tool use (function calling). For examples, see **[Tools API Reference](../api/tools.md)**.

## Decorators

```python { .api }
def beta_tool(func: Callable) -> BetaFunctionTool:
    """
    Convert sync function to tool with auto-generated schema.
    Function must have type hints and docstring.
    """
    ...

def beta_async_tool(func: Callable) -> BetaAsyncFunctionTool:
    """
    Convert async function to tool with auto-generated schema.
    Function must have type hints and docstring.
    """
    ...
```

## Tool Runner

```python { .api }
def tool_runner(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    tools: list[ToolParam | BetaFunctionTool],
    tool_choice: ToolChoice = NOT_GIVEN,
    **kwargs  # Additional messages.create() parameters
) -> Iterator[BetaMessage]:
    """
    Auto-execute tools in agentic loop.
    Yields message after each turn until stop_reason == "end_turn".
    """
    ...
```

**Async:** `async def tool_runner(...) -> AsyncIterator[BetaMessage]`

## Tool Types

```python { .api }
class ToolParam(TypedDict):
    name: str                              # Tool identifier
    description: str                       # Tool purpose (for Claude)
    input_schema: dict[str, Any]           # JSON Schema (draft 2020-12)
    cache_control: NotRequired[CacheControlEphemeral]

ToolChoice = Union[
    ToolChoiceAuto,      # Let Claude decide (default)
    ToolChoiceAny,       # Force Claude to use any tool
    ToolChoiceNone,      # Disable tools
    ToolChoiceTool,      # Force specific tool
]

class ToolChoiceAuto(TypedDict):
    type: Literal["auto"]
    disable_parallel_tool_use: NotRequired[bool]

class ToolChoiceAny(TypedDict):
    type: Literal["any"]
    disable_parallel_tool_use: NotRequired[bool]

class ToolChoiceTool(TypedDict):
    type: Literal["tool"]
    name: str  # Tool name to force
    disable_parallel_tool_use: NotRequired[bool]
```

## Response Types

```python { .api }
class ToolUseBlock(BaseModel):
    """Tool invocation in assistant response"""
    type: Literal["tool_use"]
    id: str                    # Use in tool_result
    name: str                  # Tool name
    input: dict[str, Any]      # Tool parameters

class ToolResultBlockParam(TypedDict):
    """Tool result in user message"""
    type: Literal["tool_result"]
    tool_use_id: str           # ID from ToolUseBlock
    content: NotRequired[str | list[TextBlockParam | ImageBlockParam]]
    is_error: NotRequired[bool]  # True if tool execution failed
    cache_control: NotRequired[CacheControlEphemeral]
```

## Function Tool Classes

```python { .api }
class BetaFunctionTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable

    def __call__(self, **kwargs) -> Any: ...
    def to_param(self) -> ToolParam: ...

class BetaAsyncFunctionTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable

    async def __call__(self, **kwargs) -> Any: ...
    def to_param(self) -> ToolParam: ...
```

## Common Patterns

```python
# Decorator usage
@beta_tool
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """Get weather for location.

    Args:
        location: City and state
        unit: Temperature unit
    """
    return {"temp": 72, "unit": unit}

# Tool runner (auto-execution)
for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in NYC?"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)

# Manual tool handling
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather.to_param()],
    messages=[...]
)

# Extract tool use
for block in message.content:
    if block.type == "tool_use":
        result = get_weather(**block.input)
        # Send result back in next request
```

## See Also

- **[Complete Tools Documentation](../api/tools.md)** - Full details and examples
- **[Tool Integration Tasks](../common-tasks/tool-integration.md)** - Task-oriented guide
- **[Tool Usage Guide](../guides/tool-usage.md)** - Advanced patterns
