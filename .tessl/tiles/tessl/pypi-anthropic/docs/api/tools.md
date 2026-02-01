# Tool Use API Reference

Define and use tools (function calling) with automatic schema generation from Python functions.

## Tool Decorators

```python { .api }
def beta_tool(func: Callable) -> BetaFunctionTool:
    """
    Decorator to create a synchronous tool from Python function.

    Automatically generates JSON schema from function signature, type hints,
    and docstring. Supports standard Python types, Optional, Union, List, Dict.

    Parameters:
        func: Python function to convert to tool. Must have type hints and docstring.

    Returns:
        BetaFunctionTool: Wrapper with auto-generated schema and callable interface

    Example:
        @beta_tool
        def get_weather(location: str, unit: str = "fahrenheit") -> dict:
            '''Get weather for location.

            Args:
                location: City and state
                unit: Temperature unit
            '''
            return {"temp": 72, "condition": "sunny"}
    """
    ...

def beta_async_tool(func: Callable) -> BetaAsyncFunctionTool:
    """
    Decorator to create an asynchronous tool from Python async function.

    Automatically generates JSON schema from function signature, type hints,
    and docstring. Use for tools that perform async I/O operations.

    Parameters:
        func: Python async function to convert to tool. Must have type hints and docstring.

    Returns:
        BetaAsyncFunctionTool: Wrapper with auto-generated schema and async callable interface

    Example:
        @beta_async_tool
        async def fetch_url(url: str) -> str:
            '''Fetch content from URL.

            Args:
                url: URL to fetch
            '''
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.text
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
    **kwargs
) -> Iterator[BetaMessage]:
    """
    Run message with automatic tool execution and conversation management.

    Automatically handles the agentic loop: sends message to Claude, executes any
    tool calls, sends results back, and continues until Claude responds without
    tool use (stop_reason == "end_turn").

    Parameters:
        model: Model identifier (required)
        messages: Initial conversation messages (required)
        max_tokens: Maximum tokens per Claude response (required)
        tools: List of available tools - ToolParam dicts or BetaFunctionTool/BetaAsyncFunctionTool
            decorated functions
        tool_choice: Control tool selection behavior - "auto" (default), "any", "none",
            or specific tool name
        **kwargs: Additional parameters passed to messages.create() (system, temperature, etc.)

    Yields:
        BetaMessage: Message after each turn in the conversation loop. Final message
            will have stop_reason "end_turn" when conversation completes.

    Raises:
        Same exceptions as messages.create()
        ToolExecutionError: If tool execution fails and error handling doesn't catch it

    Example:
        for message in client.beta.messages.tool_runner(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            tools=[get_weather, search_db],
            messages=[{"role": "user", "content": "What's the weather?"}]
        ):
            if message.stop_reason == "end_turn":
                print(message.content[0].text)
    """
    ...

async def tool_runner(
    self,
    *,
    model: str,
    messages: list[MessageParam],
    max_tokens: int,
    tools: list[ToolParam | BetaAsyncFunctionTool],
    tool_choice: ToolChoice = NOT_GIVEN,
    **kwargs
) -> AsyncIterator[BetaMessage]:
    """
    Async version of tool_runner.

    Same parameters and behavior as synchronous tool_runner(), but executes
    asynchronously and supports async tools (BetaAsyncFunctionTool).

    Yields:
        BetaMessage: Message after each turn in the conversation loop
    """
    ...
```

## Tool Types

### ToolParam

```python { .api }
class ToolParam(TypedDict):
    """
    Manual tool definition without decorator.

    Fields:
        name: Tool name (alphanumeric + underscores only). Used by Claude to identify tool.
        description: Clear description of what the tool does. Claude uses this to decide
            when to use the tool.
        input_schema: JSON Schema (draft 2020-12) defining tool parameters. Use standard
            JSON Schema types: object, string, number, boolean, array, etc.
        cache_control: Optional prompt caching. Use {"type": "ephemeral"} to cache tool
            definition across requests.
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    cache_control: NotRequired[CacheControlEphemeral]
```

### ToolChoice

```python { .api }
ToolChoice = Union[
    ToolChoiceAuto,      # Let Claude decide whether to use tools (default)
    ToolChoiceAny,       # Force Claude to use at least one tool
    ToolChoiceNone,      # Disable all tool use for this request
    ToolChoiceTool,      # Force Claude to use specific tool by name
]

class ToolChoiceAuto(TypedDict):
    """
    Let Claude decide whether to use tools based on conversation context.

    Fields:
        type: Always "auto"
        disable_parallel_tool_use: Set to True to force sequential tool calls.
            Default is False (parallel calls allowed).
    """
    type: Literal["auto"]
    disable_parallel_tool_use: NotRequired[bool]

class ToolChoiceAny(TypedDict):
    """
    Force Claude to use at least one tool (any tool from available tools).

    Useful when you want to ensure Claude performs an action rather than just
    responding with text.

    Fields:
        type: Always "any"
        disable_parallel_tool_use: Set to True to force sequential tool calls
    """
    type: Literal["any"]
    disable_parallel_tool_use: NotRequired[bool]

class ToolChoiceNone(TypedDict):
    """
    Disable all tool use for this request.

    Claude will respond with text only, even if tools are provided. Useful for
    forcing text responses in multi-turn conversations.

    Fields:
        type: Always "none"
    """
    type: Literal["none"]

class ToolChoiceTool(TypedDict):
    """
    Force Claude to use a specific tool by name.

    Claude will always use this tool in its first response. Useful for
    deterministic workflows.

    Fields:
        type: Always "tool"
        name: Exact name of tool to use (must match tool in tools list)
        disable_parallel_tool_use: Set to True to force only this tool call
    """
    type: Literal["tool"]
    name: str
    disable_parallel_tool_use: NotRequired[bool]
```

### Tool Function Classes

```python { .api }
class BetaFunctionTool:
    """
    Synchronous function tool wrapper created by @beta_tool decorator.

    Attributes:
        name: Tool name derived from function name
        description: Tool description from function docstring
        input_schema: Auto-generated JSON Schema from function signature
        func: Underlying Python function
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable

    def __call__(self, **kwargs) -> Any:
        """Execute tool with parameters."""
        ...

    def to_param(self) -> ToolParam:
        """Convert to ToolParam dict for API calls."""
        ...

class BetaAsyncFunctionTool:
    """
    Asynchronous function tool wrapper created by @beta_async_tool decorator.

    Attributes:
        name: Tool name derived from function name
        description: Tool description from function docstring
        input_schema: Auto-generated JSON Schema from function signature
        func: Underlying Python async function
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable

    async def __call__(self, **kwargs) -> Any:
        """Execute async tool with parameters."""
        ...

    def to_param(self) -> ToolParam:
        """Convert to ToolParam dict for API calls."""
        ...
```

## Quick Examples

### Manual Tool Definition

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[{
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City and state"}
            },
            "required": ["location"]
        }
    }],
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
)

for block in message.content:
    if block.type == "tool_use":
        print(f"Tool: {block.name}, Input: {block.input}")
```

### Using Tool Decorator

```python
from anthropic import beta_tool

@beta_tool
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """
    Get weather for a location.

    Args:
        location: City and state, e.g. San Francisco, CA
        unit: Temperature unit (celsius or fahrenheit)
    """
    return {"location": location, "temperature": 72, "unit": unit, "condition": "sunny"}

message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in NYC?"}]
)
```

### Tool Runner with Auto-Execution

```python
@beta_tool
def get_weather(location: str) -> dict:
    """Get weather for location."""
    return {"temp": 72, "condition": "sunny"}

@beta_tool
def search_database(query: str) -> list:
    """Search database."""
    return [{"id": 1, "name": "Result 1"}]

for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather, search_database],
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

### Handle Tool Call Manually

```python
# First request - Claude requests tool use
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}]
)

# Extract and execute tool call
tool_use = next(block for block in message.content if block.type == "tool_use")
weather_data = get_weather(location=tool_use.input["location"])

# Send result back
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"},
        {"role": "assistant", "content": message.content},
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(weather_data)
            }]
        }
    ]
)
```

### Force Tool Use

```python
# Force any tool
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "any"},
    messages=[{"role": "user", "content": "Hello"}]
)

# Force specific tool
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "tool", "name": "get_weather"},
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Disable Parallel Tool Use

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={
        "type": "auto",
        "disable_parallel_tool_use": True
    },
    messages=[{"role": "user", "content": "Get weather for NYC and LA"}]
)
```

## See Also

- [Messages API](./messages.md) - Core message creation
- [Tool Usage Guide](../guides/tool-usage.md) - Advanced tool patterns
- [Type System](../reference/types.md) - Complete type definitions
