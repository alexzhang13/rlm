# Beta Message Enhancement Features

Message enhancement features are parameters that add advanced capabilities to `client.beta.messages.create()`. Multiple features can be combined in a single request.

## Extended Thinking

Enable Claude to show detailed reasoning process with configurable token budget.

### API

```python { .api }
class ThinkingConfigParam(TypedDict):
    """
    Extended thinking configuration.

    Fields:
        type: "enabled" or "disabled"
        budget_tokens: Maximum tokens for thinking (optional)
    """
    type: Literal["enabled", "disabled"]
    budget_tokens: NotRequired[int]

class ThinkingBlock(BaseModel):
    """
    Thinking content block in response.

    Attributes:
        type: Always "thinking"
        thinking: The reasoning content
    """
    type: Literal["thinking"]
    thinking: str

class RedactedThinkingBlock(BaseModel):
    """
    Redacted thinking block (when thinking disabled mid-conversation).

    Attributes:
        type: Always "redacted_thinking"
    """
    type: Literal["redacted_thinking"]
```

### Example

```python
from anthropic import Anthropic

client = Anthropic()

message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    thinking={
        "type": "enabled",
        "budget_tokens": 2000,
    },
    messages=[
        {
            "role": "user",
            "content": "Solve this complex math problem: ..."
        }
    ]
)

# Check for thinking blocks
for block in message.content:
    if block.type == "thinking":
        print("Claude's reasoning:")
        print(block.thinking)
    elif block.type == "text":
        print("\nFinal answer:")
        print(block.text)
```

### Notes

- Token budgets are approximate and may be exceeded slightly
- Thinking blocks appear before text blocks in the response
- Disabling thinking mid-conversation results in redacted blocks
- Works with all model versions that support beta features

## Structured Outputs

Enable type-safe, validated responses by specifying a Pydantic model schema. Claude will generate output that conforms to your schema and the SDK will automatically parse and validate it.

### API

```python { .api }
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

ResponseFormatT = TypeVar('ResponseFormatT', bound=BaseModel)

class ParsedBetaMessage(BetaMessage, Generic[ResponseFormatT]):
    """
    Beta message response with parsed structured output.

    Attributes:
        content: List of content blocks including ParsedBetaTextBlock
        parsed_output: Convenience property to access the parsed Pydantic model
    """
    content: list[ParsedBetaContentBlock[ResponseFormatT]]

    @property
    def parsed_output(self) -> Optional[ResponseFormatT]:
        """Extract the first parsed output from text content blocks."""
        ...

class ParsedBetaTextBlock(BetaTextBlock, Generic[ResponseFormatT]):
    """
    Text content block with parsed structured output.

    Attributes:
        type: Always "text"
        text: Raw JSON text
        parsed_output: Validated Pydantic model instance
    """
    type: Literal["text"]
    text: str
    parsed_output: Optional[ResponseFormatT]

def transform_schema(
    json_schema: type[BaseModel] | dict[str, Any],
) -> dict[str, Any]:
    """
    Transform a Pydantic model or JSON schema for API compatibility.

    Handles:
    - Format conversion for supported types
    - Property transformations
    - Unsupported property documentation

    Args:
        json_schema: Pydantic BaseModel class or dict schema

    Returns:
        Transformed schema dict compatible with API
    """
    ...
```

### Basic Example

```python
import pydantic
from anthropic import Anthropic

# Define your output schema
class Order(pydantic.BaseModel):
    product_name: str
    price: float
    quantity: int

client = Anthropic()

prompt = """
Extract the product name, price, and quantity from this customer message:
"Hi, I'd like to order 2 packs of Green Tea for 5.50 dollars each."
"""

# Use parse() method with output_format parameter
parsed_message = client.beta.messages.parse(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1024,
    output_format=Order,
)

# Access parsed output directly
order = parsed_message.parsed_output
print(f"Product: {order.product_name}")
print(f"Price: ${order.price}")
print(f"Quantity: {order.quantity}")
# Output:
# Product: Green Tea
# Price: $5.5
# Quantity: 2
```

### Streaming Example

```python
# Stream with structured outputs
with client.beta.messages.stream(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1024,
    output_format=Order,
) as stream:
    for event in stream:
        if event.type == "text":
            # Get partial parsed output as it streams
            partial = event.parsed_snapshot()
            print(f"Partial: {partial}")

# Get final parsed result
final_message = stream.get_final_message()
order = final_message.parsed_output
```

### Complex Schema Example

```python
from typing import Literal
import pydantic

class Address(pydantic.BaseModel):
    street: str
    city: str
    postal_code: str
    country: str

class Customer(pydantic.BaseModel):
    name: str
    email: str
    phone: str | None = None
    address: Address

class OrderItem(pydantic.BaseModel):
    product_id: str
    product_name: str
    quantity: int
    price: float

class CompleteOrder(pydantic.BaseModel):
    order_id: str
    customer: Customer
    items: list[OrderItem]
    total_amount: float
    status: Literal["pending", "confirmed", "shipped", "delivered"]
    notes: str | None = None

# Use with complex nested schema
parsed_message = client.beta.messages.parse(
    model="claude-sonnet-4-5-20250929",
    messages=[{
        "role": "user",
        "content": "Extract order details from: [long email or document]"
    }],
    max_tokens=2048,
    output_format=CompleteOrder,
)

order = parsed_message.parsed_output
print(f"Order ID: {order.order_id}")
print(f"Customer: {order.customer.name}")
print(f"Items: {len(order.items)}")
for item in order.items:
    print(f"  - {item.product_name}: ${item.price} x {item.quantity}")
print(f"Total: ${order.total_amount}")
```

### Using transform_schema()

```python
from anthropic import transform_schema

# Transform a Pydantic model
class MyModel(pydantic.BaseModel):
    name: str
    age: int = pydantic.Field(ge=0, le=150, description="Age in years")

# Get transformed schema
schema = transform_schema(MyModel)
print(schema)
# Transforms Pydantic schema to API-compatible format
# Unsupported constraints (ge, le) are moved to description

# Or transform a dict schema directly
schema = transform_schema({
    "type": "integer",
    "minimum": 1,
    "maximum": 10,
    "description": "A number"
})
# Returns: {'type': 'integer', 'description': 'A number\n\n{minimum: 1, maximum: 10}'}
```

### Async Example

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    parsed_message = await client.beta.messages.parse(
        model="claude-sonnet-4-5-20250929",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        output_format=Order,
    )

    order = parsed_message.parsed_output
    print(f"Extracted: {order}")

asyncio.run(main())
```

### Async Streaming Example

```python
async def main():
    client = AsyncAnthropic()

    async with client.beta.messages.stream(
        model="claude-sonnet-4-5-20250929",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        output_format=Order,
    ) as stream:
        async for event in stream:
            if event.type == "text":
                partial = event.parsed_snapshot()
                print(f"Partial: {partial}")

    final_message = await stream.get_final_message()
    order = final_message.parsed_output

asyncio.run(main())
```

### Notes

- Requires models that support structured outputs (e.g., claude-sonnet-4-5-20250929)
- Uses Pydantic for schema definition and validation
- The `parse()` method is a convenience wrapper around `create()` that handles schema transformation
- Automatically validates output against your schema
- Raises `pydantic.ValidationError` if output doesn't match schema
- In streaming mode, `parsed_snapshot()` provides incremental parsing
- The feature automatically adds `"structured-outputs-2025-11-13"` beta header
- Supported formats: date-time, time, date, duration, email, hostname, uri, ipv4, ipv6, uuid
- Unsupported Pydantic constraints (ge, le, gt, lt, etc.) are documented in schema description

## Context Management

Automatically manage conversation context by clearing thinking blocks or tool uses when limits are approached.

### API

```python { .api }
class BetaContextManagementConfigParam(TypedDict, total=False):
    edits: list[Union[BetaClearToolUses20250919EditParam, BetaClearThinking20251015EditParam]]

class BetaClearThinking20251015EditParam(TypedDict, total=False):
    type: Literal["clear_thinking_20251015"]
    keep: Union[int, Literal["all"]]  # Number of recent turns to keep thinking blocks

class BetaClearToolUses20250919EditParam(TypedDict, total=False):
    type: Literal["clear_tool_uses_20250919"]
    trigger: Union[BetaInputTokensTriggerParam, BetaToolUsesTriggerParam]
    keep: BetaToolUsesKeepParam
    clear_at_least: Optional[BetaInputTokensClearAtLeastParam]
    clear_tool_inputs: Union[bool, list[str], None]
    exclude_tools: Optional[list[str]]
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    thinking={"type": "enabled"},
    context_management={
        "edits": [
            {"type": "clear_thinking_20251015", "keep": 3},  # Keep last 3 turns
            {
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": 100000},
                "keep": {"type": "turns", "value": 5},
                "clear_tool_inputs": True,
            }
        ]
    },
    messages=conversation_history,
)
```

## Container Support

Enable container-based file operations for beta features.

### API

```python { .api }
class BetaContainerParams(TypedDict, total=False):
    # Container configuration parameters (check API docs for details)
    pass

class BetaContainerUploadBlock(BaseModel):
    type: Literal["container_upload"]
    # Upload result information
```

## Search Tools

Enable document search capabilities with BM25 or regex patterns.

### API

```python { .api }
class BetaToolSearchToolBM2520251119Param(TypedDict, total=False):
    """BM25 search tool for document retrieval."""
    type: Literal["search_tool_bm25_20251119"]
    name: str

class BetaToolSearchToolRegex20251119Param(TypedDict, total=False):
    """Regex pattern search tool."""
    type: Literal["search_tool_regex_20251119"]
    name: str
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=[
        {"type": "search_tool_bm25_20251119", "name": "document_search"},
    ],
    messages=[{"role": "user", "content": "Search for relevant passages about AI"}]
)
```

## Citations

Enable source attribution for responses when working with documents.

### API

```python { .api }
class CitationsConfigParam(TypedDict):
    """
    Citations configuration.

    Fields:
        type: "enabled" or "disabled"
    """
    type: Literal["enabled", "disabled"]

class TextCitation(BaseModel):
    """
    Citation in text content.

    Attributes:
        type: Always "text_citation"
        text: Cited text
        cited_text: Original source text
        location: Location in source
    """
    type: Literal["text_citation"]
    text: str
    cited_text: str
    location: CitationCharLocation | CitationContentBlockLocation | CitationPageLocation
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    citations={"type": "enabled"},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Summarize this document with citations.",
                },
            ],
        }
    ]
)

# Extract citations
for block in message.content:
    if hasattr(block, 'citations'):
        for citation in block.citations:
            print(f"Citation: {citation.cited_text}")
            print(f"Location: {citation.location}")
```

### Notes

- Works best with document inputs (PDFs, text files)
- Citations reference specific locations in source documents
- Multiple citations can appear in a single response
- Location types: character position, content block, or page number

## Web Search

Enable real-time web information retrieval.

### API

```python { .api }
class WebSearchConfigParam(TypedDict):
    """
    Web search configuration.

    Fields:
        type: "enabled" or "disabled"
    """
    type: Literal["enabled", "disabled"]

class WebSearchResultBlock(BaseModel):
    """
    Web search result in response.

    Attributes:
        type: Always "web_search_result"
        url: Result URL
        title: Page title
        snippet: Text snippet
    """
    type: Literal["web_search_result"]
    url: str
    title: str
    snippet: str
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    web_search={"type": "enabled"},
    messages=[
        {
            "role": "user",
            "content": "What are the latest AI developments in 2025?"
        }
    ]
)

# Check for web search results
for block in message.content:
    if block.type == "web_search_result":
        print(f"Found: {block.title}")
        print(f"URL: {block.url}")
        print(f"Snippet: {block.snippet}")
```

### Notes

- Requires internet connectivity
- Adds latency to requests (typically 1-3 seconds)
- Results are current at time of request
- May not be available in all regions

## Code Execution

Enable Python code execution in secure sandbox environment.

### API

```python { .api }
class CodeExecutionConfigParam(TypedDict):
    """
    Code execution configuration.

    Fields:
        type: "enabled" or "disabled"
    """
    type: Literal["enabled", "disabled"]
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    code_execution={"type": "enabled"},
    messages=[
        {
            "role": "user",
            "content": "Calculate the first 10 Fibonacci numbers."
        }
    ]
)
```

### Notes

- Runs in isolated sandbox with limited packages
- Security restrictions prevent file system access
- Network access is disabled
- Execution timeout applies (typically 30 seconds)
- Available packages: NumPy, Pandas, Matplotlib, etc. (check docs)

## Computer Use

Enable computer interaction capabilities including screenshots, mouse, and keyboard control.

### API

```python { .api }
class ComputerUseConfigParam(TypedDict):
    """
    Computer use configuration.

    Fields:
        type: "enabled" or "disabled"
        display_width_px: Display width in pixels
        display_height_px: Display height in pixels
        display_number: Display number (optional)
    """
    type: Literal["enabled", "disabled"]
    display_width_px: NotRequired[int]
    display_height_px: NotRequired[int]
    display_number: NotRequired[int]
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    computer_use={
        "type": "enabled",
        "display_width_px": 1920,
        "display_height_px": 1080,
    },
    messages=[
        {
            "role": "user",
            "content": "Open a web browser and search for Python tutorials."
        }
    ]
)
```

### Notes

- Requires display configuration
- Security restrictions apply
- Not available in all regions
- Use with caution - can interact with GUI
- Suitable for automation and testing scenarios

## Bash Commands

Enable bash command execution.

### API

```python { .api }
class BashConfigParam(TypedDict):
    """
    Bash configuration.

    Fields:
        type: "enabled" or "disabled"
    """
    type: Literal["enabled", "disabled"]

class ToolBash20250124(TypedDict):
    """
    Bash tool definition.

    Fields:
        type: Always "bash_20250124"
        name: Tool name
    """
    type: Literal["bash_20250124"]
    name: str
```

### Notes

- Executes shell commands in sandboxed environment
- Security restrictions apply
- Limited access to system resources
- Use with caution in production

## Text Editor

Enable text file editing capabilities.

### API

```python { .api }
class TextEditorConfigParam(TypedDict):
    """
    Text editor configuration.

    Fields:
        type: "enabled" or "disabled"
    """
    type: Literal["enabled", "disabled"]

class ToolTextEditor20250124(TypedDict):
    """
    Text editor tool (latest version).

    Fields:
        type: Always "text_editor_20250124"
        name: Tool name
    """
    type: Literal["text_editor_20250124"]
    name: str
```

### Notes

- Supports text file creation and editing
- Works in sandboxed environment
- File operations are temporary unless persisted
- Suitable for code generation and modification

## MCP Integration

Enable Model Context Protocol tool integration for custom external tools.

### API

```python { .api }
class BetaRequestMCPServerURLDefinitionParam(TypedDict, total=False):
    """MCP server URL definition."""
    url: Required[str]
    """URL of the MCP server"""

class BetaMCPToolsetParam(TypedDict, total=False):
    """MCP toolset configuration."""
    servers: list[BetaRequestMCPServerURLDefinitionParam]
    """List of MCP server definitions"""

class BetaMCPToolConfigParam(TypedDict, total=False):
    """MCP tool configuration."""
    # Tool-specific configuration

class BetaMCPToolUseBlock(BaseModel):
    """MCP tool use in response."""
    type: Literal["mcp_tool_use"]
    # MCP tool execution information

class BetaMCPToolResultBlock(BaseModel):
    """MCP tool result in response."""
    type: Literal["mcp_tool_result"]
    # MCP tool result data
```

### Example

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    mcp_servers=[
        {"url": "http://localhost:8080/mcp"},
    ],
    messages=[
        {"role": "user", "content": "Use the MCP tools to fetch data"}
    ]
)

# Check for MCP tool uses
for block in message.content:
    if block.type == "mcp_tool_use":
        print(f"MCP tool used: {block}")
    elif block.type == "mcp_tool_result":
        print(f"MCP result: {block}")
```

### Notes

- Integrates external tools via Model Context Protocol
- Requires running MCP server(s)
- Enables custom tool integration beyond built-in tools
- Supports multiple MCP servers simultaneously
- Advanced feature for specialized use cases

## Memory Tools

Enable persistent memory across conversations.

### API

```python { .api }
class MemoryConfigParam(TypedDict):
    """
    Memory configuration.

    Fields:
        type: "enabled" or "disabled"
    """
    type: Literal["enabled", "disabled"]

class BetaAbstractMemoryTool:
    """
    Abstract base class for memory tools.

    Subclass to implement custom memory backends.
    """
    def store(self, key: str, value: Any) -> None:
        """Store value in memory."""
        ...

    def retrieve(self, key: str) -> Any:
        """Retrieve value from memory."""
        ...

    def delete(self, key: str) -> None:
        """Delete value from memory."""
        ...
```

### Example - Custom Memory Implementation

```python
# Example custom memory tool implementation
class DatabaseMemoryTool(BetaAbstractMemoryTool):
    def __init__(self, db_connection):
        self.db = db_connection

    def store(self, key: str, value: Any) -> None:
        """Store value in database."""
        self.db.execute("INSERT INTO memory (key, value) VALUES (?, ?)", (key, value))

    def retrieve(self, key: str) -> Any:
        """Retrieve value from database."""
        result = self.db.execute("SELECT value FROM memory WHERE key = ?", (key,)).fetchone()
        return result[0] if result else None

    def delete(self, key: str) -> None:
        """Delete value from database."""
        self.db.execute("DELETE FROM memory WHERE key = ?", (key,))

# Use with beta messages
db_memory = DatabaseMemoryTool(db_conn)

message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    memory={"type": "enabled"},
    messages=[
        {"role": "user", "content": "Remember that my favorite color is blue."}
    ]
)
```

### Notes

- Enables persistent context across conversations
- Requires custom memory backend implementation
- Useful for multi-turn conversations with state
- Memory persists beyond single request

## Combined Features Example

Use multiple beta features together for maximum capability:

```python
# Use multiple beta features in one request
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    thinking={"type": "enabled", "budget_tokens": 2000},
    web_search={"type": "enabled"},
    code_execution={"type": "enabled"},
    citations={"type": "enabled"},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}
                },
                {
                    "type": "text",
                    "text": "Analyze this research paper, search for recent related work, and write Python code to replicate key results. Include citations."
                }
            ]
        }
    ]
)

# Process response with all beta features
for block in message.content:
    if block.type == "thinking":
        print(f"Reasoning: {block.thinking}")
    elif block.type == "text":
        print(f"Analysis: {block.text}")
        if hasattr(block, 'citations'):
            print("Citations:")
            for citation in block.citations:
                print(f"  - {citation.cited_text}")
    elif block.type == "web_search_result":
        print(f"Related work: {block.title} ({block.url})")
```

## Streaming with Beta Features

Stream responses while using beta features:

```python
with client.beta.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    thinking={"type": "enabled"},
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"[Thinking: {event.delta.thinking}]")
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)
    print()

# Get final message
message = stream.get_final_message()
print(f"\nTokens used: {message.usage.output_tokens}")
```

## Async Beta Messages

Use beta features with async client:

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    message = await client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        thinking={"type": "enabled"},
        messages=[
            {"role": "user", "content": "Explain machine learning"}
        ]
    )

    for block in message.content:
        if block.type == "thinking":
            print(f"Thinking: {block.thinking}")
        elif block.type == "text":
            print(f"Answer: {block.text}")

asyncio.run(main())
```

## Async Streaming with Beta Features

Combine async streaming with beta features:

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    async with client.beta.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        thinking={"type": "enabled"},
        web_search={"type": "enabled"},
        messages=[
            {"role": "user", "content": "What are the latest quantum computing breakthroughs?"}
        ]
    ) as stream:
        async for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    print(f"[Thinking: {event.delta.thinking}]")
                elif event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)
        print()

asyncio.run(main())
```

## Tool Runner with Beta Tools

Use tool runner with beta features:

```python
from anthropic import beta_tool

@beta_tool
def search_database(query: str) -> list:
    """Search database for query."""
    return [{"id": 1, "title": "Result"}]

for message in client.beta.messages.tool_runner(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    tools=[search_database],
    messages=[{"role": "user", "content": "Search for Python tutorials"}]
):
    if message.stop_reason == "end_turn":
        print(message.content[0].text)
```

## Best Practices

### 1. Choose Appropriate Features

Only enable features you need:
```python
# Don't do this (unnecessary features)
message = client.beta.messages.create(
    thinking={"type": "enabled"},
    web_search={"type": "enabled"},
    code_execution={"type": "enabled"},
    messages=[{"role": "user", "content": "What is 2+2?"}]  # Simple question
)

# Do this (appropriate features)
message = client.beta.messages.create(
    messages=[{"role": "user", "content": "What is 2+2?"}]  # No features needed
)
```

### 2. Set Reasonable Token Budgets

For thinking, set budgets appropriate to task complexity:
```python
# Simple task
thinking={"type": "enabled", "budget_tokens": 500}

# Complex reasoning
thinking={"type": "enabled", "budget_tokens": 2000}
```

### 3. Handle Feature-Specific Content

Check for feature-specific content blocks:
```python
for block in message.content:
    if block.type == "thinking":
        # Handle reasoning
        ...
    elif block.type == "web_search_result":
        # Handle search result
        ...
    elif block.type == "text":
        # Handle text
        ...
```

### 4. Test Features Individually

Test each feature separately before combining:
```python
# Test thinking alone
message1 = client.beta.messages.create(
    thinking={"type": "enabled"},
    messages=[...]
)

# Test web search alone
message2 = client.beta.messages.create(
    web_search={"type": "enabled"},
    messages=[...]
)

# Combine after testing
message3 = client.beta.messages.create(
    thinking={"type": "enabled"},
    web_search={"type": "enabled"},
    messages=[...]
)
```

### 5. Monitor Costs

Beta features may have additional costs:
```python
# Track usage
print(f"Input tokens: {message.usage.input_tokens}")
print(f"Output tokens: {message.usage.output_tokens}")
if message.usage.cache_creation_input_tokens:
    print(f"Cache creation: {message.usage.cache_creation_input_tokens}")
```

## Limitations and Considerations

### Token Usage
- Extended thinking increases token usage
- Web search adds overhead
- Budget accordingly for production use

### Latency
- Web search adds 1-3 seconds
- Code execution adds execution time
- Computer use may have delays

### Availability
- Not all features available in all regions
- Some features require specific models
- Check documentation for current availability

### Security
- Code execution is sandboxed
- Computer use has security restrictions
- Bash commands are limited
- Use appropriate caution in production

### Stability
- Beta features may change
- Breaking changes possible
- Monitor for deprecations
- Test after SDK updates

## See Also

- [Beta Overview](./index.md) - Overview of all beta features
- [Beta Batches](./batches.md) - Use beta features in batches
- [Messages API](../api/messages.md) - Core message creation
- [Streaming API](../api/streaming.md) - Streaming responses
