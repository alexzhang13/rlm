# Tool Integration Tasks

Practical patterns for function calling and agentic workflows. For complete reference, see **[Tools API](../api/tools.md)** and **[Tool Usage Guide](../guides/tool-usage.md)**.

## Quick Start with Tool Decorator

```python
from anthropic import Anthropic, beta_tool

client = Anthropic()

# Define tool with decorator
@beta_tool
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """
    Get weather for a location.

    Args:
        location: City and state, e.g. "San Francisco, CA"
        unit: Temperature unit - "celsius" or "fahrenheit"
    """
    # Your implementation here
    return {
        "location": location,
        "temperature": 72,
        "unit": unit,
        "condition": "sunny"
    }

# Auto-execute tools with tool_runner
for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in NYC?"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

**That's it!** The `tool_runner` automatically:
- Sends the request to Claude
- Detects when Claude wants to use a tool
- Executes the tool function
- Sends results back to Claude
- Continues until Claude responds with text

## Manual Tool Handling

For more control over the execution flow:

```python
# 1. Define tool manually
tools = [{
    "name": "get_weather",
    "description": "Get weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City and state"}
        },
        "required": ["location"]
    }
}]

# 2. Send initial request
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in SF?"}]
)

# 3. Check if Claude wants to use a tool
if message.stop_reason == "tool_use":
    # Extract tool use
    tool_use = next(block for block in message.content if block.type == "tool_use")
    print(f"Claude wants to use: {tool_use.name}")
    print(f"With params: {tool_use.input}")

    # 4. Execute the tool
    result = get_weather(location=tool_use.input["location"])

    # 5. Send result back to Claude
    final_message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather in SF?"},
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

    print(final_message.content[0].text)
```

## Multiple Tools

Claude can choose from multiple tools:

```python
@beta_tool
def get_weather(location: str) -> dict:
    """Get current weather for a location"""
    return {"temp": 72, "condition": "sunny"}

@beta_tool
def search_database(query: str, limit: int = 10) -> list:
    """Search database for items matching query"""
    return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

@beta_tool
def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email"""
    return {"status": "sent", "message_id": "abc123"}

# Claude picks the right tool(s)
for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_weather, search_database, send_email],
    messages=[{"role": "user", "content": "Check the weather in NYC and email it to bob@example.com"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

## Async Tools

For I/O-bound operations:

```python
import httpx
from anthropic import AsyncAnthropic, beta_async_tool

client = AsyncAnthropic()

@beta_async_tool
async def fetch_url(url: str) -> str:
    """Fetch content from a URL"""
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url)
        return response.text

# Use with async tool_runner
async for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[fetch_url],
    messages=[{"role": "user", "content": "Fetch https://example.com and summarize it"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

## Control Tool Selection

### Force Tool Use

Require Claude to use at least one tool:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "any"},  # Force any tool
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Force Specific Tool

Require Claude to use a specific tool:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "tool", "name": "get_weather"},  # Force specific tool
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Disable Tools for a Turn

Temporarily disable tool use:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[...],
    tool_choice={"type": "none"},  # No tools this turn
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
    messages=[{"role": "user", "content": "Do task A and then task B"}]
)
```

## Error Handling in Tools

Report tool execution failures to Claude:

```python
@beta_tool
def divide(a: float, b: float) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# Manual handling with error reporting
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[divide.to_param()],
    messages=[{"role": "user", "content": "What is 10 divided by 0?"}]
)

tool_use = next(block for block in message.content if block.type == "tool_use")

# Execute and catch errors
try:
    result = divide(**tool_use.input)
    tool_result = str(result)
    is_error = False
except Exception as e:
    tool_result = str(e)
    is_error = True

# Send error back to Claude
final_message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[divide.to_param()],
    messages=[
        {"role": "user", "content": "What is 10 divided by 0?"},
        {"role": "assistant", "content": message.content},
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": tool_result,
                "is_error": is_error  # Tell Claude this is an error
            }]
        }
    ]
)

print(final_message.content[0].text)  # Claude handles the error gracefully
```

## Stateful Tools

Tools that maintain state:

```python
class Calculator:
    def __init__(self):
        self.memory = 0

    @beta_tool
    def calculate(self, expression: str) -> float:
        """Evaluate a mathematical expression and store result"""
        result = eval(expression)  # Use safe evaluation in production
        self.memory = result
        return result

    @beta_tool
    def recall(self) -> float:
        """Recall the last calculation result"""
        return self.memory

    @beta_tool
    def clear(self) -> str:
        """Clear calculator memory"""
        self.memory = 0
        return "Memory cleared"

# Use stateful tools
calc = Calculator()

for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[calc.calculate, calc.recall, calc.clear],
    messages=[{"role": "user", "content": "Calculate 5 * 8, then add 10 to that result"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
        print(f"Final memory: {calc.memory}")
```

## Validate Tool Inputs

```python
@beta_tool
def set_temperature(degrees: float, unit: str = "celsius") -> dict:
    """Set thermostat temperature"""
    # Validate unit
    if unit not in ["celsius", "fahrenheit"]:
        raise ValueError(f"Invalid unit: {unit}. Must be 'celsius' or 'fahrenheit'")

    # Validate range
    if degrees < -50 or degrees > 50:
        raise ValueError(f"Temperature {degrees} out of safe range (-50 to 50)")

    # Set temperature
    return {"status": "success", "temperature": degrees, "unit": unit}
```

## Return Structured Data

```python
from typing import TypedDict

class UserInfo(TypedDict):
    id: str
    name: str
    email: str
    created_at: str

@beta_tool
def get_user_info(user_id: str) -> UserInfo:
    """Get user information by ID"""
    # Fetch from database
    return {
        "id": user_id,
        "name": "Alice Smith",
        "email": "alice@example.com",
        "created_at": "2024-01-15"
    }

# Claude can work with structured data
for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[get_user_info],
    messages=[{"role": "user", "content": "Get info for user user_123 and send them a welcome email"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

## Complex Tool Example

Database query tool with validation:

```python
@beta_tool
def query_database(
    table: str,
    filters: dict,
    limit: int = 10,
    sort_by: str | None = None
) -> list[dict]:
    """
    Query database with filters.

    Args:
        table: Table name to query
        filters: Key-value pairs for filtering (e.g., {"status": "active"})
        limit: Maximum number of results (1-100)
        sort_by: Optional field to sort by
    """
    # Validate inputs
    valid_tables = ["users", "orders", "products"]
    if table not in valid_tables:
        raise ValueError(f"Invalid table. Must be one of: {valid_tables}")

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    # Execute query (pseudocode)
    results = db.query(table).filter(**filters).limit(limit)
    if sort_by:
        results = results.sort(sort_by)

    return results.all()
```

## Tool Usage Best Practices

### 1. Clear Descriptions

Write clear docstrings - Claude uses these to decide when to call the tool:

```python
@beta_tool
def search_products(
    query: str,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = True
) -> list[dict]:
    """
    Search product catalog for matching items.

    Use this tool when the user wants to find or browse products.

    Args:
        query: Search keywords or product name
        category: Optional category filter (e.g., "electronics", "books", "clothing")
        min_price: Minimum price in USD
        max_price: Maximum price in USD
        in_stock_only: Only show products currently in stock
    """
    ...
```

### 2. Use Type Hints

Type hints improve schema generation:

```python
from typing import Literal

@beta_tool
def book_appointment(
    date: str,  # Use specific format hints in docstring
    time: str,
    service: Literal["haircut", "coloring", "styling"]
) -> dict:
    """
    Book an appointment.

    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        service: Type of service
    """
    ...
```

### 3. Return Useful Data

Return structured data that Claude can work with:

```python
@beta_tool
def get_order_status(order_id: str) -> dict:
    """Get status of an order"""
    return {
        "order_id": order_id,
        "status": "shipped",
        "tracking_number": "1Z999AA10123456784",
        "estimated_delivery": "2024-01-20",
        "items_count": 3
    }
```

## See Also

- **[Tools API Reference](../api/tools.md)** - Complete API documentation
- **[Tool Usage Guide](../guides/tool-usage.md)** - Advanced patterns and examples
- **[Messages API](../api/messages.md)** - Core message creation
