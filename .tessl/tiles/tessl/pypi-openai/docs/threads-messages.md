# Threads and Messages

Create conversational threads and manage messages within the Assistants API. Threads maintain conversation state and messages represent user inputs and assistant responses.

## Threads

### Create Thread

Create a new conversation thread.

```python { .api }
def create(
    self,
    *,
    messages: list[dict] | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    tool_resources: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Thread:
    """
    Create a conversation thread.

    Args:
        messages: Initial messages to add to thread.
            [{"role": "user", "content": "Hello"}]

        metadata: Key-value pairs (max 16). Keys max 64 chars, values max 512 chars.

        tool_resources: Resources for tools.
            - {"code_interpreter": {"file_ids": [...]}}
            - {"file_search": {"vector_store_ids": [...]}}

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Thread: Created thread.
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Create empty thread
thread = client.beta.threads.create()
print(f"Thread ID: {thread.id}")

# Create with initial messages
thread = client.beta.threads.create(
    messages=[
        {"role": "user", "content": "Hello!"},
        {"role": "user", "content": "How are you?"}
    ]
)

# With metadata
thread = client.beta.threads.create(
    metadata={
        "user_id": "user-123",
        "session": "abc"
    }
)

# With tool resources
thread = client.beta.threads.create(
    tool_resources={
        "file_search": {
            "vector_store_ids": ["vs_abc123"]
        }
    }
)
```

### Retrieve Thread

Get thread details.

```python { .api }
def retrieve(
    self,
    thread_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Thread:
    """Get thread details."""
```

### Update Thread

Modify thread metadata.

```python { .api }
def update(
    self,
    thread_id: str,
    *,
    metadata: dict[str, str] | Omit = omit,
    tool_resources: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Thread:
    """Update thread properties."""
```

### Delete Thread

Delete a thread.

```python { .api }
def delete(
    self,
    thread_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ThreadDeleted:
    """Delete a thread."""
```

### Create and Run

Create thread and immediately run assistant (convenience method).

```python { .api }
def create_and_run(
    self,
    *,
    assistant_id: str,
    instructions: str | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    model: str | Omit = omit,
    thread: dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    stream: bool | Omit = omit,
    temperature: float | Omit = omit,
    tool_choice: str | dict | Omit = omit,
    top_p: float | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """
    Create thread and run assistant in one call.

    Args:
        assistant_id: The assistant ID.
        instructions: Override assistant instructions.
        metadata: Thread metadata.
        model: Override assistant model.
        thread: Thread configuration including messages.
        tools: Override assistant tools.
        stream: Enable streaming.
        temperature: Sampling temperature.
        tool_choice: Tool choice configuration.
        top_p: Nucleus sampling.

    Returns:
        Run: Created run.
    """
```

Usage example:

```python
# Create thread and run
run = client.beta.threads.create_and_run(
    assistant_id="asst_abc123",
    thread={
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)

print(f"Run ID: {run.id}")
print(f"Thread ID: {run.thread_id}")
```

### Create and Run with Polling

Create a thread, start a run, and automatically poll until the run reaches a terminal state.

```python { .api }
def create_and_run_poll(
    self,
    *,
    assistant_id: str,
    instructions: str | Omit = omit,
    max_completion_tokens: int | Omit = omit,
    max_prompt_tokens: int | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    model: str | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    response_format: dict | Omit = omit,
    temperature: float | Omit = omit,
    thread: dict | Omit = omit,
    tool_choice: str | dict | Omit = omit,
    tool_resources: dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    top_p: float | Omit = omit,
    truncation_strategy: dict | Omit = omit,
    poll_interval_ms: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """
    Create a thread, start a run, and poll for completion.

    Helper method that automatically polls the run until it reaches a terminal state
    (completed, failed, cancelled, expired). More information on Run lifecycles:
    https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps

    Args:
        assistant_id: The assistant ID to run.
        poll_interval_ms: Polling interval in milliseconds (defaults to 1000ms).
        thread: Thread configuration including messages.
        instructions: Override assistant instructions.
        tools: Override assistant tools.
        metadata: Thread metadata.
        (Additional parameters same as create_and_run)

    Returns:
        Run: Completed run in terminal state.
    """
```

Usage example:

```python
# Create and poll automatically
run = client.beta.threads.create_and_run_poll(
    assistant_id="asst_abc123",
    thread={
        "messages": [{"role": "user", "content": "Explain quantum computing"}]
    },
    poll_interval_ms=500  # Poll every 500ms
)

# Run is guaranteed to be in terminal state
print(f"Status: {run.status}")  # completed, failed, cancelled, or expired
```

### Create and Run with Streaming

Create a thread, start a run, and stream the response back in real-time.

```python { .api }
def create_and_run_stream(
    self,
    *,
    assistant_id: str,
    instructions: str | Omit = omit,
    max_completion_tokens: int | Omit = omit,
    max_prompt_tokens: int | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    model: str | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    response_format: dict | Omit = omit,
    temperature: float | Omit = omit,
    thread: dict | Omit = omit,
    tool_choice: str | dict | Omit = omit,
    tool_resources: dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    top_p: float | Omit = omit,
    truncation_strategy: dict | Omit = omit,
    event_handler: AssistantEventHandler | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> AssistantStreamManager[AssistantEventHandler]:
    """
    Create a thread and stream the run back in real-time.

    Args:
        assistant_id: The assistant ID to run.
        event_handler: Optional custom event handler for processing stream events.
        thread: Thread configuration including messages.
        instructions: Override assistant instructions.
        (Additional parameters same as create_and_run)

    Returns:
        AssistantStreamManager: Stream manager for handling assistant events.
    """
```

Usage example:

```python
# Stream with default handler
with client.beta.threads.create_and_run_stream(
    assistant_id="asst_abc123",
    thread={
        "messages": [{"role": "user", "content": "Tell me a story"}]
    }
) as stream:
    for event in stream:
        if event.event == 'thread.message.delta':
            print(event.data.delta.content[0].text.value, end='', flush=True)

# With custom event handler
from openai import AssistantEventHandler

class MyHandler(AssistantEventHandler):
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end='', flush=True)

with client.beta.threads.create_and_run_stream(
    assistant_id="asst_abc123",
    thread={
        "messages": [{"role": "user", "content": "Hello"}]
    },
    event_handler=MyHandler()
) as stream:
    stream.until_done()
```

## Messages

### Create Message

Add a message to a thread.

```python { .api }
def create(
    self,
    thread_id: str,
    *,
    role: Literal["user", "assistant"],
    content: str | list[dict],
    attachments: list[dict] | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Message:
    """
    Add a message to a thread.

    Args:
        thread_id: The thread ID.

        role: Message role. "user" or "assistant".

        content: Message content. Can be:
            - String: "Hello"
            - List with text/images: [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {...}}]

        attachments: File attachments with tools.
            [{"file_id": "file-abc", "tools": [{"type": "code_interpreter"}]}]

        metadata: Key-value pairs.

    Returns:
        Message: Created message.
    """
```

Usage examples:

```python
# Simple text message
message = client.beta.threads.messages.create(
    thread_id="thread_abc123",
    role="user",
    content="What is the weather today?"
)

# With attachments
message = client.beta.threads.messages.create(
    thread_id="thread_abc123",
    role="user",
    content="Analyze this data",
    attachments=[
        {
            "file_id": "file-abc123",
            "tools": [{"type": "code_interpreter"}]
        }
    ]
)

# Multimodal message (text + image)
message = client.beta.threads.messages.create(
    thread_id="thread_abc123",
    role="user",
    content=[
        {"type": "text", "text": "What's in this image?"},
        {
            "type": "image_url",
            "image_url": {"url": "https://example.com/image.jpg"}
        }
    ]
)

# With metadata
message = client.beta.threads.messages.create(
    thread_id="thread_abc123",
    role="user",
    content="Question here",
    metadata={"source": "web_ui"}
)
```

### Retrieve Message

Get message details.

```python { .api }
def retrieve(
    self,
    thread_id: str,
    message_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Message:
    """Get message details."""
```

### Update Message

Modify message metadata.

```python { .api }
def update(
    self,
    thread_id: str,
    message_id: str,
    *,
    metadata: dict[str, str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Message:
    """Update message metadata."""
```

### List Messages

List messages in a thread.

```python { .api }
def list(
    self,
    thread_id: str,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    run_id: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[Message]:
    """
    List messages in a thread.

    Args:
        thread_id: The thread ID.
        after: Cursor for next page.
        before: Cursor for previous page.
        limit: Number to retrieve (max 100). Default 20.
        order: Sort order. "asc" or "desc". Default "desc" (newest first).
        run_id: Filter by run ID.

    Returns:
        SyncCursorPage[Message]: Paginated messages.
    """
```

Usage example:

```python
# List all messages
messages = client.beta.threads.messages.list(thread_id="thread_abc123")

for message in messages:
    print(f"{message.role}: {message.content[0].text.value}")

# List in chronological order
messages = client.beta.threads.messages.list(
    thread_id="thread_abc123",
    order="asc"
)

# Pagination
page1 = client.beta.threads.messages.list(thread_id="thread_abc123", limit=10)
page2 = client.beta.threads.messages.list(
    thread_id="thread_abc123",
    limit=10,
    after=page1.data[-1].id
)
```

### Delete Message

Delete a message.

```python { .api }
def delete(
    self,
    thread_id: str,
    message_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> MessageDeleted:
    """Delete a message."""
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Thread(BaseModel):
    """Conversation thread."""
    id: str
    created_at: int
    metadata: dict[str, str] | None
    object: Literal["thread"]
    tool_resources: dict | None

class ThreadDeleted(BaseModel):
    """Deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["thread.deleted"]

class Message(BaseModel):
    """Thread message."""
    id: str
    assistant_id: str | None
    attachments: list[dict] | None
    completed_at: int | None
    content: list[MessageContent]
    created_at: int
    incomplete_at: int | None
    incomplete_details: dict | None
    metadata: dict[str, str] | None
    object: Literal["thread.message"]
    role: Literal["user", "assistant"]
    run_id: str | None
    status: Literal["in_progress", "incomplete", "completed"]
    thread_id: str

class MessageContent(BaseModel):
    """Message content part."""
    type: Literal["text", "image_file", "image_url"]
    text: TextContent | None
    image_file: ImageFile | None
    image_url: ImageURL | None

class TextContent(BaseModel):
    """Text content."""
    value: str
    annotations: list[Annotation]

class ImageFile(BaseModel):
    """Image file reference."""
    file_id: str
    detail: Literal["auto", "low", "high"] | None

class ImageURL(BaseModel):
    """Image URL reference."""
    url: str
    detail: Literal["auto", "low", "high"] | None

class Annotation(BaseModel):
    """Content annotation (file citation/path)."""
    type: Literal["file_citation", "file_path"]
    text: str
    start_index: int
    end_index: int
    file_citation: dict | None
    file_path: dict | None

class MessageDeleted(BaseModel):
    """Deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["thread.message.deleted"]
```

## Complete Example

```python
from openai import OpenAI

client = OpenAI()

# 1. Create assistant
assistant = client.beta.assistants.create(
    name="Helper",
    model="gpt-4",
    instructions="You are helpful."
)

# 2. Create thread
thread = client.beta.threads.create()

# 3. Add user message
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Tell me a joke"
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

# 6. Get messages
messages = client.beta.threads.messages.list(thread_id=thread.id)

for message in messages:
    role = message.role
    content = message.content[0].text.value
    print(f"{role}: {content}")
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_conversation():
    client = AsyncOpenAI()

    thread = await client.beta.threads.create()

    message = await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Hello!"
    )

    return thread.id, message.id

thread_id, message_id = asyncio.run(create_conversation())
```
