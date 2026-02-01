# Runs

Execute assistants on threads and handle tool calls. Runs represent the execution of an assistant on a thread, managing the conversation flow and tool interactions.

## Capabilities

### Create Run

Execute an assistant on a thread.

```python { .api }
def create(
    self,
    thread_id: str,
    *,
    assistant_id: str,
    additional_instructions: str | Omit = omit,
    additional_messages: list[dict] | Omit = omit,
    instructions: str | Omit = omit,
    max_completion_tokens: int | Omit = omit,
    max_prompt_tokens: int | Omit = omit,
    metadata: dict[str, str] | Omit = omit,
    model: str | Omit = omit,
    parallel_tool_calls: bool | Omit = omit,
    response_format: dict | Omit = omit,
    stream: bool | Omit = omit,
    temperature: float | Omit = omit,
    tool_choice: str | dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    top_p: float | Omit = omit,
    truncation_strategy: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """
    Run an assistant on a thread.

    Args:
        thread_id: The thread ID.
        assistant_id: The assistant ID.
        additional_instructions: Append to assistant instructions.
        additional_messages: Add messages before run.
        instructions: Override assistant instructions.
        max_completion_tokens: Maximum completion tokens.
        max_prompt_tokens: Maximum prompt tokens.
        metadata: Key-value pairs (max 16).
        model: Override assistant model.
        parallel_tool_calls: Enable parallel tool calls.
        response_format: Override response format.
        stream: Enable streaming.
        temperature: Sampling temperature.
        tool_choice: Tool choice configuration.
        tools: Override assistant tools.
        top_p: Nucleus sampling.
        truncation_strategy: Message truncation config.

    Returns:
        Run: Created run.
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic run
run = client.beta.threads.runs.create(
    thread_id="thread_abc123",
    assistant_id="asst_abc123"
)

print(f"Run ID: {run.id}")
print(f"Status: {run.status}")

# With additional instructions
run = client.beta.threads.runs.create(
    thread_id="thread_abc123",
    assistant_id="asst_abc123",
    additional_instructions="Be concise."
)

# Override model
run = client.beta.threads.runs.create(
    thread_id="thread_abc123",
    assistant_id="asst_abc123",
    model="gpt-4-turbo"
)

# With streaming
stream = client.beta.threads.runs.create(
    thread_id="thread_abc123",
    assistant_id="asst_abc123",
    stream=True
)

for event in stream:
    print(event)
```

### Retrieve Run

Get run status and details.

```python { .api }
def retrieve(
    self,
    thread_id: str,
    run_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """Get run details."""
```

Usage example:

```python
run = client.beta.threads.runs.retrieve(
    thread_id="thread_abc123",
    run_id="run_abc123"
)

print(f"Status: {run.status}")
print(f"Model: {run.model}")
```

### Update Run

Update a run's metadata.

```python { .api }
def update(
    self,
    run_id: str,
    *,
    thread_id: str,
    metadata: dict[str, str] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """
    Modify a run's metadata.

    Args:
        run_id: The run ID to update.
        thread_id: The thread ID containing the run.
        metadata: Set of 16 key-value pairs for storing additional information.
            Keys max 64 characters, values max 512 characters.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Run: Updated run object.
    """
```

Usage example:

```python
# Update run metadata
run = client.beta.threads.runs.update(
    run_id="run_abc123",
    thread_id="thread_abc123",
    metadata={
        "user_id": "user-456",
        "priority": "high"
    }
)

print(f"Updated metadata: {run.metadata}")
```

### List Runs

List runs for a thread.

```python { .api }
def list(
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
) -> SyncCursorPage[Run]:
    """List runs for a thread."""
```

### Cancel Run

Cancel an in-progress run.

```python { .api }
def cancel(
    self,
    thread_id: str,
    run_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """Cancel a run."""
```

Usage example:

```python
run = client.beta.threads.runs.cancel(
    thread_id="thread_abc123",
    run_id="run_abc123"
)

print(f"Status: {run.status}")  # "cancelling" or "cancelled"
```

### Submit Tool Outputs

Submit results of tool calls back to the run.

```python { .api }
def submit_tool_outputs(
    self,
    thread_id: str,
    run_id: str,
    *,
    tool_outputs: list[dict],
    stream: bool | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Run:
    """
    Submit tool call results.

    Args:
        thread_id: The thread ID.
        run_id: The run ID.
        tool_outputs: List of tool outputs.
            [{"tool_call_id": "call_abc", "output": "result"}]
        stream: Enable streaming.

    Returns:
        Run: Updated run.
    """
```

Usage example:

```python
# Check for required actions
run = client.beta.threads.runs.retrieve(
    thread_id="thread_abc123",
    run_id="run_abc123"
)

if run.status == "requires_action":
    tool_calls = run.required_action.submit_tool_outputs.tool_calls

    # Execute tool calls
    tool_outputs = []
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = tool_call.function.arguments

        # Call your function
        result = execute_function(function_name, arguments)

        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": str(result)
        })

    # Submit outputs
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id="thread_abc123",
        run_id="run_abc123",
        tool_outputs=tool_outputs
    )
```

### Polling Helpers

Wait for run completion with automatic polling.

```python { .api }
def create_and_poll(
    self,
    thread_id: str,
    *,
    assistant_id: str,
    poll_interval_ms: int = 1000,
    **kwargs
) -> Run:
    """Create run and poll until completion."""

def poll(
    self,
    thread_id: str,
    run_id: str,
    *,
    poll_interval_ms: int = 1000,
) -> Run:
    """Poll run until completion."""

def submit_tool_outputs_and_poll(
    self,
    thread_id: str,
    run_id: str,
    *,
    tool_outputs: list[dict],
    poll_interval_ms: int = 1000,
) -> Run:
    """Submit tool outputs and poll until completion."""
```

Usage examples:

```python
# Create and wait for completion
run = client.beta.threads.runs.create_and_poll(
    thread_id="thread_abc123",
    assistant_id="asst_abc123"
)

print(f"Final status: {run.status}")

# Poll existing run
run = client.beta.threads.runs.poll(
    thread_id="thread_abc123",
    run_id="run_abc123"
)

# Submit and wait
run = client.beta.threads.runs.submit_tool_outputs_and_poll(
    thread_id="thread_abc123",
    run_id="run_abc123",
    tool_outputs=[{"tool_call_id": "call_abc", "output": "42"}]
)
```

### Streaming

Stream run events in real-time.

```python { .api }
def stream(
    self,
    thread_id: str,
    *,
    assistant_id: str,
    **kwargs
) -> AssistantStreamManager:
    """Stream run events with event handler."""

def create_and_stream(
    self,
    thread_id: str,
    *,
    assistant_id: str,
    **kwargs
) -> AssistantStreamManager:
    """Create run and stream events."""
```

Usage example:

```python
from openai import AssistantEventHandler

# Define event handler
class EventHandler(AssistantEventHandler):
    def on_text_created(self, text):
        print(f"\\nassistant > ", end="", flush=True)

    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\\nassistant > {tool_call.type}\\n", flush=True)

# Stream events
with client.beta.threads.runs.stream(
    thread_id="thread_abc123",
    assistant_id="asst_abc123",
    event_handler=EventHandler()
) as stream:
    stream.until_done()
```

### Submit Tool Outputs with Streaming

Submit tool outputs and stream the run to completion in real-time.

```python { .api }
def submit_tool_outputs_stream(
    self,
    *,
    tool_outputs: list[dict],
    run_id: str,
    thread_id: str,
    event_handler: AssistantEventHandler | None = None,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> AssistantStreamManager[AssistantEventHandler]:
    """
    Submit tool outputs and stream the run to terminal state.

    Helper method that submits tool call results and streams run events in real-time
    until the run reaches a terminal state. More information on Run lifecycles:
    https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps

    Args:
        tool_outputs: List of tool call outputs.
            [{"tool_call_id": "call_abc", "output": "result"}]
        run_id: The run ID requiring tool outputs.
        thread_id: The thread ID containing the run.
        event_handler: Optional custom event handler for processing stream events.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        AssistantStreamManager: Stream manager for handling assistant events.
    """
```

Usage example:

```python
from openai import AssistantEventHandler

# Stream tool output submission
with client.beta.threads.runs.submit_tool_outputs_stream(
    thread_id="thread_abc123",
    run_id="run_abc123",
    tool_outputs=[
        {"tool_call_id": "call_abc", "output": "42"},
        {"tool_call_id": "call_def", "output": "Hello"}
    ]
) as stream:
    for event in stream:
        if event.event == 'thread.run.completed':
            print("Run completed!")

# With custom event handler
class ToolOutputHandler(AssistantEventHandler):
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end='', flush=True)

    def on_run_step_done(self, run_step):
        print(f"\nStep {run_step.id} completed")

with client.beta.threads.runs.submit_tool_outputs_stream(
    thread_id="thread_abc123",
    run_id="run_abc123",
    tool_outputs=[{"tool_call_id": "call_abc", "output": "result"}],
    event_handler=ToolOutputHandler()
) as stream:
    stream.until_done()
```

### Run Steps

View detailed steps of a run.

```python { .api }
def retrieve(
    self,
    thread_id: str,
    run_id: str,
    step_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RunStep:
    """Retrieve run step details."""

def list(
    self,
    thread_id: str,
    run_id: str,
    *,
    after: str | Omit = omit,
    before: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncCursorPage[RunStep]:
    """List run steps."""
```

Usage example:

```python
# List steps
steps = client.beta.threads.runs.steps.list(
    thread_id="thread_abc123",
    run_id="run_abc123"
)

for step in steps:
    print(f"Step: {step.type}")
    print(f"Status: {step.status}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Run(BaseModel):
    """Assistant run."""
    id: str
    assistant_id: str
    cancelled_at: int | None
    completed_at: int | None
    created_at: int
    expires_at: int
    failed_at: int | None
    incomplete_details: dict | None
    instructions: str
    last_error: dict | None
    max_completion_tokens: int | None
    max_prompt_tokens: int | None
    metadata: dict[str, str] | None
    model: str
    object: Literal["thread.run"]
    parallel_tool_calls: bool
    required_action: RequiredAction | None
    response_format: dict | None
    started_at: int | None
    status: Literal[
        "queued", "in_progress", "requires_action",
        "cancelling", "cancelled", "failed",
        "completed", "incomplete", "expired"
    ]
    thread_id: str
    tool_choice: dict | str
    tools: list[dict]
    truncation_strategy: dict | None
    usage: Usage | None
    temperature: float | None
    top_p: float | None

class RequiredAction(BaseModel):
    """Required action for run."""
    type: Literal["submit_tool_outputs"]
    submit_tool_outputs: SubmitToolOutputs

class SubmitToolOutputs(BaseModel):
    """Tool outputs to submit."""
    tool_calls: list[ToolCall]

class ToolCall(BaseModel):
    """Tool call from assistant."""
    id: str
    type: Literal["function"]
    function: Function

class Function(BaseModel):
    """Function call details."""
    name: str
    arguments: str  # JSON string

class Usage(BaseModel):
    """Token usage."""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class RunStep(BaseModel):
    """Individual run step."""
    id: str
    assistant_id: str
    cancelled_at: int | None
    completed_at: int | None
    created_at: int
    expired_at: int | None
    failed_at: int | None
    last_error: dict | None
    metadata: dict[str, str] | None
    object: Literal["thread.run.step"]
    run_id: str
    status: Literal[
        "in_progress", "cancelled", "failed",
        "completed", "expired"
    ]
    step_details: StepDetails
    thread_id: str
    type: Literal["message_creation", "tool_calls"]
    usage: Usage | None

class StepDetails(BaseModel):
    """Step details (message or tool calls)."""
    type: Literal["message_creation", "tool_calls"]
    message_creation: dict | None
    tool_calls: list[dict] | None
```

## Complete Example with Tool Calls

```python
from openai import OpenAI
import json

client = OpenAI()

# 1. Create assistant with function
assistant = client.beta.assistants.create(
    name="Weather Assistant",
    instructions="Help with weather queries.",
    model="gpt-4",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }]
)

# 2. Create thread and message
thread = client.beta.threads.create()

client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="What's the weather in San Francisco?"
)

# 3. Run assistant
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id
)

# 4. Handle tool calls
if run.status == "requires_action":
    tool_calls = run.required_action.submit_tool_outputs.tool_calls

    tool_outputs = []
    for tool_call in tool_calls:
        if tool_call.function.name == "get_weather":
            args = json.loads(tool_call.function.arguments)
            # Call actual weather API
            result = {"temp": 72, "condition": "sunny"}

            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            })

    # Submit and wait
    run = client.beta.threads.runs.submit_tool_outputs_and_poll(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs
    )

# 5. Get final response
messages = client.beta.threads.messages.list(thread_id=thread.id)
print(messages.data[0].content[0].text.value)
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def run_assistant():
    client = AsyncOpenAI()

    run = await client.beta.threads.runs.create(
        thread_id="thread_abc123",
        assistant_id="asst_abc123"
    )

    while run.status not in ["completed", "failed"]:
        await asyncio.sleep(1)
        run = await client.beta.threads.runs.retrieve(
            thread_id="thread_abc123",
            run_id=run.id
        )

    return run

run = asyncio.run(run_assistant())
```
