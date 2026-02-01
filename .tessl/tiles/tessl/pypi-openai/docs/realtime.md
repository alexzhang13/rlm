# Realtime API

WebSocket-based realtime communication for low-latency conversational AI experiences with audio streaming, function calling, and interruption handling.

## Capabilities

### Create Realtime Session

Establish a WebSocket connection for realtime interaction.

```python { .api }
def create(
    self,
    *,
    model: str,
    modalities: list[str] | Omit = omit,
    instructions: str | Omit = omit,
    voice: str | Omit = omit,
    input_audio_format: str | Omit = omit,
    output_audio_format: str | Omit = omit,
    input_audio_transcription: dict | Omit = omit,
    turn_detection: dict | Omit = omit,
    tools: list[dict] | Omit = omit,
    tool_choice: str | Omit = omit,
    temperature: float | Omit = omit,
    max_response_output_tokens: int | str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RealtimeSession:
    """
    Create a realtime session for WebSocket communication.

    Args:
        model: Model to use (e.g., "gpt-4o-realtime-preview").

        modalities: Response modalities. Options: ["text", "audio"].

        instructions: System instructions for the session.

        voice: Voice for audio output. Options: "alloy", "echo", "fable",
            "onyx", "nova", "shimmer".

        input_audio_format: Input audio format. Options: "pcm16", "g711_ulaw",
            "g711_alaw".

        output_audio_format: Output audio format. Options: "pcm16", "g711_ulaw",
            "g711_alaw", "mp3", "opus".

        input_audio_transcription: Enable input transcription.
            {"model": "whisper-1"}

        turn_detection: Turn detection configuration.
            {"type": "server_vad", "threshold": 0.5, "prefix_padding_ms": 300,
             "silence_duration_ms": 200}

        tools: Function tools available to the model.

        tool_choice: Tool choice configuration. "auto", "none", "required".

        temperature: Sampling temperature.

        max_response_output_tokens: Maximum output tokens per response.

    Returns:
        RealtimeSession: WebSocket session configuration.
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Create realtime session
session = client.beta.realtime.sessions.create(
    model="gpt-4o-realtime-preview",
    modalities=["text", "audio"],
    voice="alloy",
    instructions="You are a helpful assistant.",
    input_audio_format="pcm16",
    output_audio_format="pcm16",
    turn_detection={
        "type": "server_vad",
        "threshold": 0.5,
        "silence_duration_ms": 500
    }
)

# Access WebSocket URL
ws_url = session.client_secret.value

# Use with WebSocket library (e.g., websockets)
import asyncio
import websockets
import json

async def realtime_conversation():
    async with websockets.connect(ws_url) as websocket:
        # Send audio input
        await websocket.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64_audio_data
        }))

        # Commit audio
        await websocket.send(json.dumps({
            "type": "input_audio_buffer.commit"
        }))

        # Receive responses
        async for message in websocket:
            event = json.loads(message)

            if event["type"] == "response.audio.delta":
                # Handle audio chunk
                audio_chunk = event["delta"]
                # Play or process audio

            elif event["type"] == "response.text.delta":
                # Handle text chunk
                text = event["delta"]
                print(text, end="", flush=True)

            elif event["type"] == "response.done":
                break

asyncio.run(realtime_conversation())
```

### Realtime Calls

Manage incoming and outgoing realtime voice calls with call control methods.

```python { .api }
# Accessed via: client.realtime.calls or client.beta.realtime.calls
def create(
    self,
    *,
    model: str,
    modalities: list[str] | Omit = omit,
    instructions: str | Omit = omit,
    voice: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RealtimeCall:
    """
    Initiate an outgoing realtime call.

    Args:
        model: Model to use for the call.
        modalities: Response modalities (["audio"] recommended).
        instructions: System instructions for the call.
        voice: Voice for audio output.

    Returns:
        RealtimeCall: Call object with connection details.
    """

def accept(
    self,
    call_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RealtimeCall:
    """
    Accept an incoming realtime call.

    Args:
        call_id: The ID of the incoming call to accept.

    Returns:
        RealtimeCall: Call object with status "active".
    """

def hangup(
    self,
    call_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RealtimeCall:
    """
    End an active realtime call.

    Args:
        call_id: The ID of the call to hang up.

    Returns:
        RealtimeCall: Call object with status "completed".
    """

def refer(
    self,
    call_id: str,
    *,
    refer_to: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RealtimeCall:
    """
    Transfer a realtime call to another destination.

    Args:
        call_id: The ID of the call to transfer.
        refer_to: Destination identifier to transfer the call to.

    Returns:
        RealtimeCall: Call object with status "referred".
    """

def reject(
    self,
    call_id: str,
    *,
    reason: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> RealtimeCall:
    """
    Reject an incoming realtime call.

    Args:
        call_id: The ID of the incoming call to reject.
        reason: Optional reason for rejection.

    Returns:
        RealtimeCall: Call object with status "rejected".
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Create an outgoing call (available at both paths)
call = client.realtime.calls.create(
    model="gpt-4o-realtime-preview",
    modalities=["audio"],
    voice="alloy",
    instructions="You are a helpful phone assistant."
)

print(f"Call ID: {call.id}, Status: {call.status}")

# Accept an incoming call
accepted_call = client.realtime.calls.accept("call_abc123")

# Transfer a call
referred_call = client.realtime.calls.refer(
    call.id,
    refer_to="destination_id"
)

# End a call
ended_call = client.realtime.calls.hangup(call.id)
print(f"Call ended: {ended_call.status}")

# Reject an incoming call
rejected_call = client.realtime.calls.reject(
    "call_xyz789",
    reason="User unavailable"
)
```

### Client Secrets

Create ephemeral client secrets for secure realtime session establishment.

```python { .api }
# Access via client.realtime.client_secrets

def create(
    self,
    *,
    expires_after: dict | Omit = omit,
    session: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ClientSecretCreateResponse:
    """
    Create a Realtime client secret with an associated session configuration.

    Args:
        expires_after: Configuration for the client secret expiration.
            Expiration refers to the time after which a client secret will
            no longer be valid for creating sessions. The session itself may
            continue after that time once started. A secret can be used to
            create multiple sessions until it expires.
            Example: {"anchor": "created_at", "seconds": 3600}

        session: Session configuration to use for the client secret.
            Choose either a realtime session or a transcription session.
            Example for realtime: {
                "type": "realtime",
                "model": "gpt-4o-realtime-preview",
                "voice": "alloy",
                "modalities": ["text", "audio"]
            }
            Example for transcription: {
                "type": "transcription",
                "model": "whisper-1"
            }

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ClientSecretCreateResponse: Created client secret with value and
            expiration time. Use the secret value to establish WebSocket
            connections from client-side applications.

    Notes:
        - Client secrets enable secure browser-based realtime connections
        - Secrets expire after specified duration
        - One secret can establish multiple sessions until expiration
        - Use for temporary, client-side authentication
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Create client secret for realtime session
secret = client.realtime.client_secrets.create(
    expires_after={
        "anchor": "created_at",
        "seconds": 3600  # Expires in 1 hour
    },
    session={
        "type": "realtime",
        "model": "gpt-4o-realtime-preview",
        "voice": "alloy",
        "modalities": ["text", "audio"],
        "instructions": "You are a helpful voice assistant."
    }
)

print(f"Client Secret: {secret.value}")
print(f"Expires At: {secret.expires_at}")

# Create client secret for transcription session
transcription_secret = client.realtime.client_secrets.create(
    expires_after={
        "anchor": "created_at",
        "seconds": 1800  # Expires in 30 minutes
    },
    session={
        "type": "transcription",
        "model": "whisper-1",
        "input_audio_format": "pcm16",
        "input_audio_transcription": {
            "model": "whisper-1"
        }
    }
)

# Use the secret client-side for WebSocket connection
# The secret value is passed as authentication to establish the connection
```

### Transcription Sessions

Create ephemeral API tokens for client-side realtime transcription applications.

```python { .api }
def create(
    self,
    *,
    client_secret: dict | Omit = omit,
    include: list[str] | Omit = omit,
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | Omit = omit,
    input_audio_noise_reduction: dict | Omit = omit,
    input_audio_transcription: dict | Omit = omit,
    modalities: list[Literal["text", "audio"]] | Omit = omit,
    turn_detection: dict | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> TranscriptionSession:
    """
    Create an ephemeral API token for client-side realtime transcriptions.

    Returns a session object with a client_secret containing an ephemeral
    API token for authenticating browser clients.

    Args:
        client_secret: Configuration options for the generated client secret.

        include: Items to include in the transcription. Options:
            - "item.input_audio_transcription.logprobs"

        input_audio_format: Input audio format. Options: "pcm16", "g711_ulaw",
            "g711_alaw". For pcm16, audio must be 16-bit PCM at 24kHz sample rate,
            single channel (mono), little-endian byte order.

        input_audio_noise_reduction: Configuration for input audio noise reduction.
            Filters audio added to the input buffer before VAD and model processing.
            Can improve VAD accuracy and model performance.

        input_audio_transcription: Configuration for input audio transcription.
            Can optionally set language and prompt for additional guidance.

        modalities: Response modalities. Options: ["text"], ["audio"], or both.
            To disable audio, set to ["text"].

        turn_detection: Configuration for turn detection (Server VAD or Semantic VAD).
            Set to null to turn off, requiring manual trigger of model response.
            Server VAD detects speech based on audio volume. Semantic VAD uses
            a turn detection model to estimate turn completion and dynamically
            sets timeout based on probability.

    Returns:
        TranscriptionSession: Session with client_secret for browser authentication.
    """
```

**Usage Example:**

```python
from openai import OpenAI

client = OpenAI()

# Create transcription session for client-side use
session = client.beta.realtime.transcription_sessions.create(
    input_audio_format="pcm16",
    input_audio_transcription={
        "model": "whisper-1",
        "language": "en",
        "prompt": "Technical discussion"
    },
    input_audio_noise_reduction={
        "type": "default"
    },
    turn_detection={
        "type": "semantic_vad",
        "threshold": 0.6
    },
    modalities=["text", "audio"],
    include=["item.input_audio_transcription.logprobs"]
)

# Use the client_secret in browser/client application
ephemeral_token = session.client_secret.value
print(f"Session ID: {session.id}")
print(f"Token expires: {session.client_secret.expires_at}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class RealtimeSession(BaseModel):
    """Realtime session configuration."""
    id: str
    model: str
    modalities: list[str]
    instructions: str | None
    voice: str | None
    input_audio_format: str
    output_audio_format: str
    input_audio_transcription: dict | None
    turn_detection: dict | None
    tools: list[dict] | None
    tool_choice: str
    temperature: float | None
    max_response_output_tokens: int | str | None
    client_secret: ClientSecret

class ClientSecret(BaseModel):
    """WebSocket client secret."""
    value: str
    expires_at: int

class ClientSecretCreateResponse(BaseModel):
    """Response from creating a client secret."""
    id: str
    created_at: int
    expires_at: int
    value: str  # The ephemeral client secret value
    session: dict  # Session configuration associated with this secret
```

## Event Types

WebSocket events for realtime communication:

- `session.created` - Session established
- `input_audio_buffer.append` - Add audio data
- `input_audio_buffer.commit` - Process buffered audio
- `input_audio_buffer.clear` - Clear buffer
- `conversation.item.create` - Add conversation item
- `response.create` - Request response
- `response.cancel` - Cancel current response
- `response.audio.delta` - Audio chunk received
- `response.text.delta` - Text chunk received
- `response.done` - Response completed
- `conversation.item.input_audio_transcription.completed` - Transcription ready
- `error` - Error occurred

## Best Practices

```python
import asyncio
import websockets
import json
import base64

async def realtime_session(session_url: str):
    async with websockets.connect(session_url) as ws:
        # Handle incoming events
        async def receive_events():
            async for message in ws:
                event = json.loads(message)

                if event["type"] == "response.audio.delta":
                    # Stream audio to speaker
                    audio_data = base64.b64decode(event["delta"])
                    play_audio(audio_data)

                elif event["type"] == "response.text.delta":
                    # Display text
                    print(event["delta"], end="", flush=True)

        # Send audio input
        async def send_audio():
            while True:
                audio_chunk = record_audio_chunk()
                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": base64.b64encode(audio_chunk).decode()
                }))
                await asyncio.sleep(0.1)

        # Run both tasks
        await asyncio.gather(
            receive_events(),
            send_audio()
        )
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_session():
    client = AsyncOpenAI()

    session = await client.beta.realtime.sessions.create(
        model="gpt-4o-realtime-preview",
        modalities=["audio"]
    )

    return session.client_secret.value

ws_url = asyncio.run(create_session())
```
