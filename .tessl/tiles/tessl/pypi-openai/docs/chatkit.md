# ChatKit (Beta)

ChatKit provides a simplified, high-level interface for building chat applications with OpenAI models. It abstracts away common patterns and provides session and thread management out of the box.

**Note**: ChatKit is a beta feature and the API may change.

## Capabilities

### Create ChatKit Session

Create a new ChatKit session for managing a chat conversation with a specified workflow.

```python { .api }
def create(
    self,
    *,
    user: str,
    workflow: ChatSessionWorkflowParam,
    chatkit_configuration: ChatSessionChatKitConfigurationParam | Omit = omit,
    expires_after: ChatSessionExpiresAfterParam | Omit = omit,
    rate_limits: ChatSessionRateLimitsParam | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatSession:
    """
    Create a ChatKit session with a workflow and configuration.

    Args:
        user: A free-form string that identifies your end user; ensures this Session can access other objects that have the same `user` scope.
        workflow: Workflow that powers the session. Must include an `id` field (workflow identifier) and optionally `state_variables`, `tracing`, and `version`.
        chatkit_configuration: Optional overrides for ChatKit runtime configuration features including automatic thread titling, file upload settings, and history management.
        expires_after: Optional override for session expiration timing in seconds from creation. Defaults to 10 minutes (600 seconds).
        rate_limits: Optional override for per-minute request limits. When omitted, defaults to 10 requests per minute.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ChatSession: Created session with configuration, client secret, and workflow metadata.
    """
```

### Cancel ChatKit Session

Cancel an active ChatKit session and release resources.

```python { .api }
def cancel(
    self,
    session_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatSession:
    """
    Cancel a ChatKit session.

    Args:
        session_id: The ID of the session to cancel.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ChatSession: Session with status "cancelled".
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Create a ChatKit session with a workflow
session = client.beta.chatkit.sessions.create(
    user="user_12345",
    workflow={
        "id": "workflow_abc123",
        "state_variables": {"context": "customer_support"},
        "version": "v1.0"
    }
)

print(f"Session ID: {session.id}")
print(f"Status: {session.status}")
print(f"User: {session.user}")
print(f"Expires at: {session.expires_at}")

# Cancel session when done
cancelled = client.beta.chatkit.sessions.cancel(session.id)
print(f"Cancelled: {cancelled.status}")
```

### Retrieve ChatKit Thread

Get details of a specific ChatKit thread.

```python { .api }
def retrieve(
    self,
    thread_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ChatKitThread:
    """
    Retrieve a ChatKit thread by ID.

    Args:
        thread_id: The ID of the thread to retrieve.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ChatKitThread: Thread object with messages and metadata.
    """
```

### List ChatKit Threads

List all ChatKit threads for the current organization.

```python { .api }
def list(
    self,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncConversationCursorPage[ChatKitThread]:
    """
    List ChatKit threads with pagination.

    Args:
        after: Return threads after this thread ID (for forward pagination).
        before: Return threads before this thread ID (for backward pagination).
        limit: Maximum number of threads to return (default 20, max 100).
        order: Sort order: "asc" (oldest first) or "desc" (newest first, default).
        user: Filter threads that belong to this user identifier (defaults to null for all users).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncConversationCursorPage[ChatKitThread]: Paginated list of threads with cursor-based navigation.
    """
```

### Delete ChatKit Thread

Delete a ChatKit thread and all its messages.

```python { .api }
def delete(
    self,
    thread_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ThreadDeleteResponse:
    """
    Delete a ChatKit thread.

    Args:
        thread_id: The ID of the thread to delete.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ThreadDeleteResponse: Deletion confirmation with deleted=True.
    """
```

### List Thread Items

List messages and events within a ChatKit thread.

```python { .api }
def list_items(
    self,
    thread_id: str,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncPage[ChatKitThreadItem]:
    """
    List items (messages and events) in a ChatKit thread.

    Args:
        thread_id: The ID of the thread.
        after: Return items after this item ID.
        before: Return items before this item ID.
        limit: Maximum number of items to return (default 20, max 100).
        order: Sort order: "asc" (chronological) or "desc" (reverse chronological).
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncPage[ChatKitThreadItem]: Paginated list of thread items.
    """
```

## Complete Usage Example

```python
from openai import OpenAI

client = OpenAI()

# Create a session with a workflow
session = client.beta.chatkit.sessions.create(
    user="user_12345",
    workflow={
        "id": "workflow_xyz",
        "state_variables": {"mode": "qa"}
    },
    rate_limits={"per_minute": 20}
)

print(f"Session created: {session.id}")
print(f"Client secret: {session.client_secret}")

# List all threads
threads = client.beta.chatkit.threads.list(limit=10)
for thread in threads.data:
    print(f"Thread: {thread.id}, Created: {thread.created_at}")

# Retrieve a specific thread
if threads.data:
    thread = client.beta.chatkit.threads.retrieve(threads.data[0].id)
    print(f"Thread metadata: {thread.metadata}")

    # List items in the thread
    items = client.beta.chatkit.threads.list_items(thread.id, order="asc")
    for item in items.data:
        print(f"Item: {item.type} - {item.content}")

    # Delete thread when no longer needed
    deleted = client.beta.chatkit.threads.delete(thread.id)
    print(f"Deleted: {deleted.deleted}")

# Cancel session
client.beta.chatkit.sessions.cancel(session.id)
```

## Types

```python { .api }
from typing import Literal, Dict, Union
from pydantic import BaseModel

# Session related types
class ChatSessionWorkflowParam:
    """Workflow parameter for ChatKit session."""
    id: str  # Required: Identifier for the workflow
    state_variables: Dict[str, Union[str, bool, float]] | None  # State variables forwarded to workflow
    tracing: dict | None  # Optional tracing overrides (enabled by default)
    version: str | None  # Specific workflow version (defaults to latest)

class ChatSessionChatKitConfigurationParam:
    """Optional ChatKit runtime configuration."""
    automatic_thread_titling: dict | None  # Configuration for automatic thread title generation
    file_upload: dict | None  # File upload settings
    history: dict | None  # History management settings

class ChatSessionExpiresAfterParam:
    """Session expiration configuration."""
    # Typically a dict with duration in seconds

class ChatSessionRateLimitsParam:
    """Rate limiting configuration."""
    per_minute: int | None  # Requests per minute limit

class ChatSession(BaseModel):
    """ChatKit session object."""
    id: str
    """Identifier for the ChatKit session."""

    object: Literal["chatkit.session"]
    """Type discriminator that is always `chatkit.session`."""

    chatkit_configuration: dict
    """Resolved ChatKit feature configuration for the session."""

    client_secret: str
    """Ephemeral client secret that authenticates session requests."""

    expires_at: int
    """Unix timestamp (in seconds) for when the session expires."""

    max_requests_per_1_minute: int
    """Convenience copy of the per-minute request limit."""

    rate_limits: dict
    """Resolved rate limit values."""

    status: str
    """Current lifecycle state of the session (e.g., "active", "cancelled")."""

    user: str
    """User identifier associated with the session."""

    workflow: dict
    """Workflow metadata for the session."""

class ChatKitThread(BaseModel):
    """ChatKit thread object."""
    id: str
    object: Literal["chatkit.thread"]
    created_at: int
    metadata: dict[str, str] | None
    session_id: str | None

class ThreadDeleteResponse(BaseModel):
    """Thread deletion confirmation."""
    id: str
    object: Literal["chatkit.thread"]
    deleted: bool

class ChatKitThreadItem(BaseModel):
    """Item within a ChatKit thread (message or event)."""
    id: str
    object: Literal["chatkit.thread.item"]
    type: Literal["message", "event"]
    content: str | dict
    role: Literal["user", "assistant", "system"] | None
    created_at: int
    metadata: dict[str, str] | None

# Pagination
class SyncPage[T](BaseModel):
    data: list[T]
    object: str
    first_id: str | None
    last_id: str | None
    has_more: bool
    def __iter__(self) -> Iterator[T]: ...
```

## Best Practices

1. **Session Management**: Create one session per conversation context and cancel when done to free resources.

2. **Thread Organization**: Use separate threads for distinct conversation topics or user contexts.

3. **Metadata**: Leverage metadata for tracking user IDs, session types, or application-specific data.

4. **Pagination**: When listing threads or items, use pagination parameters to efficiently handle large datasets.

5. **Error Handling**: Always wrap ChatKit calls in try-except blocks to handle API errors gracefully.

6. **Resource Cleanup**: Always cancel sessions and delete threads when they're no longer needed.

```python
from openai import OpenAI, APIError

client = OpenAI()

try:
    session = client.beta.chatkit.sessions.create(
        user="user_abc",
        workflow={"id": "workflow_123"}
    )

    # Use session...

finally:
    # Clean up
    try:
        client.beta.chatkit.sessions.cancel(session.id)
    except APIError:
        pass  # Session may already be cancelled
```
