# Tool Usage Guide

Comprehensive guide to using tools (function calling) with Claude for building agentic workflows.

## Tool Basics

Tools let Claude call functions you define, enabling it to take actions and retrieve information.

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
```

### Using Tool Decorators

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
    # Implementation
    return {"temperature": 72, "condition": "sunny", "unit": unit}

message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in NYC?"}]
)
```

## Tool Execution Flow

### Manual Execution

```python
# 1. Send initial request
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}]
)

# 2. Extract tool use
tool_use = next(block for block in message.content if block.type == "tool_use")

# 3. Execute function
result = get_weather(location=tool_use.input["location"])

# 4. Send result back
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
                "content": str(result)
            }]
        }
    ]
)
```

### Automatic Execution with Tool Runner

```python
@beta_tool
def get_weather(location: str) -> dict:
    """Get weather for location."""
    return {"temp": 72, "condition": "sunny"}

@beta_tool
def get_time(timezone: str = "UTC") -> str:
    """Get current time in timezone."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M")

for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather, get_time],
    messages=[{"role": "user", "content": "What's the weather and time in SF?"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

## Tool Choice Control

### Auto (Default)

Let Claude decide whether to use tools:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "auto"},
    messages=[...]
)
```

### Force Any Tool

Require Claude to use at least one tool:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "any"},
    messages=[...]
)
```

### Force Specific Tool

Require Claude to use a specific tool:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "tool", "name": "get_weather"},
    messages=[...]
)
```

### Disable All Tools

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "none"},
    messages=[...]
)
```

### Disable Parallel Tool Use

Force sequential tool calls:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={
        "type": "auto",
        "disable_parallel_tool_use": True
    },
    messages=[...]
)
```

## Advanced Patterns

### Stateful Tools

```python
class Calculator:
    def __init__(self):
        self.memory = 0

    @beta_tool
    def calculate(self, expression: str) -> float:
        """Evaluate mathematical expression."""
        result = eval(expression)
        self.memory = result
        return result

    @beta_tool
    def recall(self) -> float:
        """Recall last calculation result."""
        return self.memory

calc = Calculator()

for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[calc.calculate, calc.recall],
    messages=[{"role": "user", "content": "Calculate 5*8, then add 10"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

### Error Handling in Tools

```python
@beta_tool
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# In tool result
try:
    result = divide(10, 0)
    tool_result = str(result)
    is_error = False
except Exception as e:
    tool_result = str(e)
    is_error = True

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    messages=[
        ...,
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": tool_result,
                "is_error": is_error
            }]
        }
    ]
)
```

### Async Tools

```python
from anthropic import beta_async_tool

@beta_async_tool
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Use with async tool runner
async for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[fetch_data],
    messages=[...]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

## Best Practices

### 1. Clear Tool Descriptions

```python
@beta_tool
def search_database(
    query: str,
    limit: int = 10,
    category: str | None = None
) -> list[dict]:
    """
    Search database for items matching query.

    Args:
        query: Search keywords or phrase
        limit: Maximum results to return (1-100)
        category: Optional category filter (e.g., "electronics", "books")

    Returns:
        List of matching items with id, name, price
    """
    ...
```

### 2. Validate Tool Inputs

```python
@beta_tool
def set_temperature(degrees: float, unit: str = "celsius") -> dict:
    """Set thermostat temperature."""
    if unit not in ["celsius", "fahrenheit"]:
        raise ValueError(f"Invalid unit: {unit}")
    if degrees < -50 or degrees > 50:
        raise ValueError(f"Temperature out of range: {degrees}")
    # Set temperature
    return {"status": "success", "temperature": degrees, "unit": unit}
```

### 3. Return Structured Data

```python
@beta_tool
def get_user_info(user_id: str) -> dict:
    """Get user information."""
    return {
        "id": user_id,
        "name": "Alice Smith",
        "email": "alice@example.com",
        "created_at": "2024-01-15"
    }
```

## See Also

- [Tool Use API](../api/tools.md) - Complete API reference
- [Beta Features](../beta/index.md) - Tool runner and advanced features
- [Messages API](../api/messages.md) - Message creation
