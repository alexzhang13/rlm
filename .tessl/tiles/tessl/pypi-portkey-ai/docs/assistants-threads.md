# Assistants & Threads

OpenAI Assistants API implementation with thread management, message handling, and tool execution support.

## Capabilities

### Assistant Management

```python { .api }
class Assistants:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...

class Threads:
    def create(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...
    def delete(self, **kwargs): ...
    messages: Messages
    runs: Runs

class Messages:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def update(self, **kwargs): ...

class Runs:
    def create(self, **kwargs): ...
    def list(self, **kwargs): ...
    def retrieve(self, **kwargs): ...
    def cancel(self, **kwargs): ...
    steps: Steps
```

## Usage Examples

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Create assistant
assistant = portkey.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a helpful math tutor",
    model="gpt-4"
)

# Create thread
thread = portkey.beta.threads.create()

# Add message
portkey.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Solve 2x + 3 = 7"
)

# Create run
run = portkey.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)
```