# Assistants API

Build AI assistants with advanced capabilities including code interpretation, file search, and function calling. Assistants maintain conversation state and can access tools to help users accomplish tasks.

## Capabilities

### Create Assistant

Create an AI assistant with specific instructions and tools.

```python { .api }
def create(
    self,
    *,
    model: str,
    description: str | Omit = omit,
    instructions: str | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    name: str | Omit = omit,
    reasoning_effort: str | Omit = omit,
    response_format: dict | Omit = omit,
    temperature: float | Omit = omit,
    tool_resources: dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    top_p: float | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Assistant:
    """
    Create an AI assistant.

    Args:
        model: Model ID to use (e.g., "gpt-4", "gpt-3.5-turbo").

        description: Description of the assistant (max 512 chars).

        instructions: System instructions that guide assistant behavior (max 256k chars).

        metadata: Key-value pairs for storing additional info (max 16).
            Keys max 64 chars, values max 512 chars.

        name: Name of the assistant (max 256 chars).

        reasoning_effort: Constrains effort on reasoning for reasoning models.
            Currently supported values are "none", "minimal", "low", "medium", and "high".
            Reducing reasoning effort can result in faster responses and fewer tokens used.
            - gpt-5.1 defaults to "none" (no reasoning). Supports: none, low, medium, high.
            - Models before gpt-5.1 default to "medium" and do not support "none".
            - gpt-5-pro defaults to (and only supports) "high" reasoning effort.

        response_format: Output format specification.
            - {"type": "text"}: Plain text (default)
            - {"type": "json_object"}: Valid JSON
            - {"type": "json_schema", "json_schema": {...}}: Structured output

        temperature: Sampling temperature between 0 and 2. Default 1.

        tool_resources: Resources for tools. Options:
            - {"code_interpreter": {"file_ids": [...]}}
            - {"file_search": {"vector_store_ids": [...]}}

        tools: List of enabled tools (maximum of 128 tools per assistant). Options:
            - {"type": "code_interpreter"}: Python code execution
            - {"type": "file_search"}: Search uploaded files
            - {"type": "function", "function": {...}}: Custom functions

        top_p: Nucleus sampling parameter between 0 and 1. Default 1.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Assistant: Created assistant.

    Raises:
        BadRequestError: Invalid parameters
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic assistant
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a helpful math tutor. Explain concepts clearly.",
    model="gpt-4"
)

print(f"Assistant ID: {assistant.id}")

# With code interpreter
assistant = client.beta.assistants.create(
    name="Data Analyst",
    instructions="Analyze data and create visualizations.",
    model="gpt-4",
    tools=[{"type": "code_interpreter"}]
)

# With file search
assistant = client.beta.assistants.create(
    name="Documentation Helper",
    instructions="Help users find information in documentation.",
    model="gpt-4",
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": ["vs_abc123"]
        }
    }
)

# With function calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

assistant = client.beta.assistants.create(
    name="Weather Assistant",
    instructions="Help users check weather.",
    model="gpt-4",
    tools=tools
)

# With structured output
assistant = client.beta.assistants.create(
    name="Structured Assistant",
    instructions="Generate structured responses.",
    model="gpt-4",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"}
                },
                "required": ["answer"],
                "additionalProperties": False
            }
        }
    }
)

# With metadata
assistant = client.beta.assistants.create(
    name="Customer Support",
    instructions="Assist customers with inquiries.",
    model="gpt-4",
    metadata={
        "department": "support",
        "version": "1.0"
    }
)

# With reasoning effort (for reasoning models)
assistant = client.beta.assistants.create(
    name="Reasoning Assistant",
    instructions="Solve complex problems with reasoning.",
    model="gpt-5.1",
    reasoning_effort="high"
)
```

### Retrieve Assistant

Get assistant details.

```python { .api }
def retrieve(
    self,
    assistant_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Assistant:
    """
    Retrieve assistant details.

    Args:
        assistant_id: The ID of the assistant.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Assistant: Assistant details.

    Raises:
        NotFoundError: Assistant not found
    """
```

Usage example:

```python
assistant = client.beta.assistants.retrieve("asst_abc123")

print(f"Name: {assistant.name}")
print(f"Model: {assistant.model}")
print(f"Tools: {assistant.tools}")
```

### Update Assistant

Modify assistant properties.

```python { .api }
def update(
    self,
    assistant_id: str,
    *,
    description: str | Omit = omit,
    instructions: str | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    model: str | Omit = omit,
    name: str | Omit = omit,
    reasoning_effort: str | Omit = omit,
    response_format: dict | Omit = omit,
    temperature: float | Omit = omit,
    tool_resources: dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    top_p: float | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Assistant:
    """
    Update assistant properties.

    Args: Same as create method, but all optional.

    Returns:
        Assistant: Updated assistant.
    """
```

Usage example:

```python
# Update instructions
assistant = client.beta.assistants.update(
    "asst_abc123",
    instructions="Updated instructions."
)

# Add tools
assistant = client.beta.assistants.update(
    "asst_abc123",
    tools=[
        {"type": "code_interpreter"},
        {"type": "file_search"}
    ]
)
```

### List Assistants

List all assistants with pagination.

```python { .api }
def list(
    self,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Assistant]:
    """
    List assistants with pagination.

    Args:
        after: Cursor for next page.
        before: Cursor for previous page.
        limit: Number to retrieve (max 100). Default 20.
        order: Sort order. "asc" or "desc". Default "desc".
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncCursorPage[Assistant]: Paginated list of assistants.
    """
```

Usage example:

```python
# List all assistants
assistants = client.beta.assistants.list()

for assistant in assistants:
    print(f"{assistant.name} ({assistant.id})")

# Pagination
page1 = client.beta.assistants.list(limit=10)
page2 = client.beta.assistants.list(limit=10, after=page1.data[-1].id)
```

### Delete Assistant

Delete an assistant.

```python { .api }
def delete(
    self,
    assistant_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> AssistantDeleted:
    """
    Delete an assistant.

    Args:
        assistant_id: The ID of the assistant to delete.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        AssistantDeleted: Deletion confirmation.

    Raises:
        NotFoundError: Assistant not found
    """
```

Usage example:

```python
result = client.beta.assistants.delete("asst_abc123")

print(f"Deleted: {result.deleted}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Assistant(BaseModel):
    """AI Assistant."""
    id: str
    created_at: int
    description: str | None
    instructions: str | None
    metadata: dict[str, str] | None
    model: str
    name: str | None
    object: Literal["assistant"]
    tools: list[dict]
    response_format: dict | None
    temperature: float | None
    tool_resources: dict | None
    top_p: float | None

class AssistantDeleted(BaseModel):
    """Deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["assistant.deleted"]

# Tool types
class CodeInterpreterTool(TypedDict):
    type: Literal["code_interpreter"]

class FileSearchTool(TypedDict):
    type: Literal["file_search"]

class FunctionTool(TypedDict):
    type: Literal["function"]
    function: FunctionDefinition

class FunctionDefinition(TypedDict):
    name: str
    description: NotRequired[str]
    parameters: dict  # JSON Schema
    strict: NotRequired[bool]

# Tool resources
class ToolResources(TypedDict, total=False):
    code_interpreter: CodeInterpreterResources
    file_search: FileSearchResources

class CodeInterpreterResources(TypedDict, total=False):
    file_ids: list[str]

class FileSearchResources(TypedDict, total=False):
    vector_store_ids: list[str]
```

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Create specialized assistants
support_assistant = client.beta.assistants.create(
    name="Customer Support",
    instructions="Friendly and helpful support agent.",
    model="gpt-4",
    tools=[{"type": "file_search"}]
)

code_assistant = client.beta.assistants.create(
    name="Code Helper",
    instructions="Help with coding questions.",
    model="gpt-4",
    tools=[{"type": "code_interpreter"}]
)

# 2. Organize with metadata
assistant = client.beta.assistants.create(
    name="Sales Bot",
    model="gpt-4",
    metadata={
        "team": "sales",
        "region": "us-west",
        "version": "2.0"
    }
)

# 3. Update as needed
assistant = client.beta.assistants.update(
    assistant.id,
    instructions="Updated instructions based on feedback."
)

# 4. Clean up unused assistants
assistants = client.beta.assistants.list()
for assistant in assistants:
    if should_delete(assistant):
        client.beta.assistants.delete(assistant.id)
```

## Complete Example

```python
from openai import OpenAI

client = OpenAI()

# 1. Create assistant
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a helpful math tutor.",
    model="gpt-4",
    tools=[{"type": "code_interpreter"}]
)

# 2. Create thread
thread = client.beta.threads.create()

# 3. Add message
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Can you help me solve x^2 + 5x + 6 = 0?"
)

# 4. Run assistant
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)

# 5. Wait for completion
import time

while run.status not in ["completed", "failed"]:
    time.sleep(1)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

# 6. Get response
messages = client.beta.threads.messages.list(thread_id=thread.id)

for message in messages.data:
    if message.role == "assistant":
        print(message.content[0].text.value)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_assistant():
    client = AsyncOpenAI()

    assistant = await client.beta.assistants.create(
        name="Async Assistant",
        model="gpt-4",
        instructions="I help async."
    )

    return assistant.id

assistant_id = asyncio.run(create_assistant())
```
