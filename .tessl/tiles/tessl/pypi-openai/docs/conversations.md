# Conversations

Create and manage conversations for structured multi-turn interactions. Conversations provide a lightweight alternative to Threads for managing conversational context with items that can include user inputs, system messages, and function outputs.

## Capabilities

### Create Conversation

Create a new conversation with optional initial items.

```python { .api }
def create(
    self,
    *,
    items: Iterable[dict] | None | Omit = omit,
    metadata: dict[str, str] | None | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation:
    """
    Create a conversation.

    Args:
        items: Initial items to include in the conversation context.
            You may add up to 20 items at a time. Each item can be:
            - Message: {"type": "message", "role": "user", "content": "..."}
            - System: {"type": "message", "role": "system", "content": "..."}
            - Function output: {"type": "function_call_output", "call_id": "...", "output": "..."}

        metadata: Up to 16 key-value pairs for storing additional information.
            Keys max 64 characters, values max 512 characters.
            Useful for storing user IDs, session info, etc.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Conversation: Created conversation object with unique ID.

    Notes:
        - Conversations are lightweight compared to Threads
        - No automatic message persistence - items must be explicitly managed
        - Use for scenarios requiring explicit context control
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Create empty conversation
conversation = client.conversations.create()
print(f"Created conversation: {conversation.id}")

# Create with initial items
conversation = client.conversations.create(
    items=[
        {
            "type": "message",
            "role": "system",
            "content": "You are a helpful coding assistant."
        },
        {
            "type": "message",
            "role": "user",
            "content": "How do I reverse a string in Python?"
        }
    ],
    metadata={
        "user_id": "user_123",
        "session": "session_abc"
    }
)

# Create with metadata
conversation = client.conversations.create(
    metadata={
        "purpose": "customer_support",
        "language": "en",
        "priority": "high"
    }
)
```

### Retrieve Conversation

Get a conversation by its ID.

```python { .api }
def retrieve(
    self,
    conversation_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation:
    """
    Get a conversation.

    Args:
        conversation_id: ID of the conversation to retrieve.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Conversation: Conversation object with current metadata and items.
    """
```

### Update Conversation

Update conversation metadata.

```python { .api }
def update(
    self,
    conversation_id: str,
    *,
    metadata: dict[str, str] | None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation:
    """
    Update a conversation.

    Args:
        conversation_id: ID of the conversation to update.

        metadata: New metadata dictionary. Replaces all existing metadata.
            Up to 16 key-value pairs, keys max 64 chars, values max 512 chars.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Conversation: Updated conversation object.

    Notes:
        - Metadata is completely replaced, not merged
        - To preserve existing metadata, retrieve first then update
    """
```

### Delete Conversation

Delete a conversation.

```python { .api }
def delete(
    self,
    conversation_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationDeleted:
    """
    Delete a conversation.

    Args:
        conversation_id: ID of the conversation to delete.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ConversationDeleted: Deletion confirmation with ID and status.

    Notes:
        - Items in the conversation will not be deleted
        - Deletion is permanent and cannot be undone
        - Items remain accessible if you have their IDs
    """
```

### Conversation Items

Manage items within a conversation.

```python { .api }
# Access via client.conversations.items

def create(
    self,
    conversation_id: str,
    *,
    items: Iterable[dict],
    include: list[Literal[
        "web_search_call.action.sources",
        "code_interpreter_call.outputs",
        "computer_call_output.output.image_url",
        "file_search_call.results",
        "message.input_image.image_url",
        "message.output_text.logprobs",
        "reasoning.encrypted_content"
    ]] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationItemList:
    """
    Create items in a conversation.

    Args:
        conversation_id: ID of the conversation.

        items: The items to add to the conversation. You may add up to 20 items at a time.
            Each item is a dict with one of these structures:
            - Message: {"type": "message", "role": "user"|"system"|"developer", "content": [...]}
            - Function call output: {"type": "function_call_output", "call_id": "...", "output": "..."}
            - Computer call output: {"type": "computer_call_output", "call_id": "...", "output": {...}}
            - Shell call output: {"type": "shell_call_output", "call_id": "...", "output": [...]}
            - And many other item types (see ResponseInputItemParam for full list)

        include: Additional fields to include in the response. Options:
            - "web_search_call.action.sources": Include web search sources
            - "code_interpreter_call.outputs": Include code execution outputs
            - "computer_call_output.output.image_url": Include computer call images
            - "file_search_call.results": Include file search results
            - "message.input_image.image_url": Include input message images
            - "message.output_text.logprobs": Include logprobs with assistant messages
            - "reasoning.encrypted_content": Include encrypted reasoning tokens

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ConversationItemList: List of created items with IDs and timestamps.
    """

def retrieve(
    self,
    item_id: str,
    *,
    conversation_id: str,
    include: list[Literal[
        "web_search_call.action.sources",
        "code_interpreter_call.outputs",
        "computer_call_output.output.image_url",
        "file_search_call.results",
        "message.input_image.image_url",
        "message.output_text.logprobs",
        "reasoning.encrypted_content"
    ]] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ConversationItem:
    """
    Retrieve a specific item from a conversation.

    Args:
        item_id: ID of the item to retrieve.
        conversation_id: ID of the conversation.

        include: Additional fields to include in the response. See create() for available options.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ConversationItem: Item with full content and metadata.
    """

def delete(
    self,
    item_id: str,
    *,
    conversation_id: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Conversation:
    """
    Delete an item from a conversation.

    Args:
        item_id: ID of the item to delete.
        conversation_id: ID of the conversation.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Conversation: Updated conversation after item deletion.

    Notes:
        - Deletion is permanent
        - Returns the conversation object (not a deletion confirmation)
    """

def list(
    self,
    conversation_id: str,
    *,
    after: str | Omit = omit,
    include: list[Literal[
        "web_search_call.action.sources",
        "code_interpreter_call.outputs",
        "computer_call_output.output.image_url",
        "file_search_call.results",
        "message.input_image.image_url",
        "message.output_text.logprobs",
        "reasoning.encrypted_content"
    ]] | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncConversationCursorPage[ConversationItem]:
    """
    List items in a conversation.

    Args:
        conversation_id: ID of the conversation.

        after: Cursor for pagination. Return items after this ID.

        include: Additional fields to include in the response. See create() for available options.

        limit: Maximum number of items to return (1-100). Default 20.

        order: Sort order by creation time:
            - "asc": Ascending (oldest first)
            - "desc": Descending (newest first, default)

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncConversationCursorPage[ConversationItem]: Paginated list of items.
    """
```

Complete workflow example:

```python
from openai import OpenAI

client = OpenAI()

# 1. Create conversation
conversation = client.conversations.create(
    metadata={"user_id": "user_123"}
)

# 2. Add system and user messages (batch create)
items_response = client.conversations.items.create(
    conversation_id=conversation.id,
    items=[
        {
            "type": "message",
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful Python tutor."}]
        },
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "text", "text": "How do I read a file in Python?"}]
        }
    ]
)

system_item = items_response.data[0]
user_item = items_response.data[1]

# 4. List all items
items = client.conversations.items.list(
    conversation_id=conversation.id,
    order="asc"
)

for item in items:
    print(f"{item.role}: {item.content}")

# 5. Add assistant response
assistant_response = client.conversations.items.create(
    conversation_id=conversation.id,
    items=[
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "You can read a file using: with open('file.txt', 'r') as f: content = f.read()"}]
        }
    ]
)
assistant_item = assistant_response.data[0]

# 6. Update conversation metadata
client.conversations.update(
    conversation_id=conversation.id,
    metadata={
        "user_id": "user_123",
        "status": "resolved",
        "topic": "file_io"
    }
)

# 7. Get updated conversation
updated = client.conversations.retrieve(conversation_id=conversation.id)
print(f"Metadata: {updated.metadata}")

# 8. Delete specific item
client.conversations.items.delete(
    conversation_id=conversation.id,
    item_id=user_item.id
)

# 9. Clean up - delete conversation
client.conversations.delete(conversation_id=conversation.id)
```

Multi-modal conversation example:

```python
from openai import OpenAI

client = OpenAI()

# Create conversation with image
conversation = client.conversations.create()

# Add user message with image
client.conversations.items.create(
    conversation_id=conversation.id,
    items=[
        {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg"
                    }
                }
            ]
        }
    ]
)

# Add assistant response
client.conversations.items.create(
    conversation_id=conversation.id,
    items=[
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "I see a beautiful sunset over mountains."}]
        }
    ]
)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def manage_conversation():
    client = AsyncOpenAI()

    # Create conversation
    conversation = await client.conversations.create(
        metadata={"user_id": "user_123"}
    )

    # Add message
    await client.conversations.items.create(
        conversation_id=conversation.id,
        items=[
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "text", "text": "Hello!"}]
            }
        ]
    )

    # List items
    async for item in await client.conversations.items.list(
        conversation_id=conversation.id
    ):
        print(item.content)

    # Delete conversation
    await client.conversations.delete(conversation_id=conversation.id)

asyncio.run(manage_conversation())
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Conversation(BaseModel):
    """Conversation object."""
    id: str
    created_at: int
    object: Literal["conversation"]
    metadata: dict[str, str] | None

class ConversationItem(BaseModel):
    """Item within a conversation (union type - can be message, tool call, or tool output)."""
    id: str
    conversation_id: str
    created_at: int
    object: Literal["conversation.item"]
    # Type-specific fields vary by item type
    # See ResponseInputItemParam for complete type definitions

class ConversationItemList(BaseModel):
    """List of conversation items returned from batch create."""
    data: list[ConversationItem]
    object: Literal["list"]

class ConversationDeleted(BaseModel):
    """Deletion confirmation."""
    id: str
    deleted: bool
    object: Literal["conversation.deleted"]

class SyncConversationCursorPage[T]:
    """Cursor-based pagination for conversation items."""
    data: list[T]
    has_more: bool
    last_id: str | None
    def __iter__(self) -> Iterator[T]: ...

class Omit:
    """Sentinel value for omitted parameters."""
```

## Access Pattern

```python
# Synchronous
from openai import OpenAI
client = OpenAI()
client.conversations.create(...)
client.conversations.retrieve(...)
client.conversations.update(...)
client.conversations.delete(...)
client.conversations.items.create(...)
client.conversations.items.retrieve(...)
client.conversations.items.delete(...)
client.conversations.items.list(...)

# Asynchronous
from openai import AsyncOpenAI
client = AsyncOpenAI()
await client.conversations.create(...)
await client.conversations.retrieve(...)
await client.conversations.update(...)
await client.conversations.delete(...)
await client.conversations.items.create(...)
await client.conversations.items.retrieve(...)
await client.conversations.items.delete(...)
await client.conversations.items.list(...)
```
