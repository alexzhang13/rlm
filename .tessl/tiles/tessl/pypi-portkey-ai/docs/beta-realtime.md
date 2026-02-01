# Beta Realtime API

Real-time audio and WebSocket-based AI interactions for building conversational applications with low-latency voice communication. Supports real-time session management and WebSocket connections for streaming audio communication.

## Capabilities

### Real-Time Connection Management

Establishes WebSocket connections for real-time communication with AI models, enabling low-latency voice and audio interactions.

```python { .api }
class BetaRealtime:
    def connect(
        self,
        *,
        model: str,
        websocket_connection_options: WebsocketConnectionOptions = {},
        **kwargs
    ) -> RealtimeConnectionManager:
        """
        Create a real-time WebSocket connection to an AI model.

        Args:
            model: Model identifier for real-time communication
            websocket_connection_options: WebSocket configuration options
            **kwargs: Additional connection parameters

        Returns:
            RealtimeConnectionManager: Connection manager for real-time communication
        """

    sessions: BetaSessions

class AsyncBetaRealtime:
    def connect(
        self,
        *,
        model: str,
        websocket_connection_options: WebsocketConnectionOptions = {},
        **kwargs
    ) -> AsyncRealtimeConnectionManager:
        """Async version of connect method."""

    sessions: AsyncBetaSessions
```

### Real-Time Session Management

Create and manage real-time sessions with configurable audio formats, voice settings, and interaction parameters.

```python { .api }
class BetaSessions:
    def create(
        self,
        *,
        model: Any = "portkey-default",
        input_audio_format: Union[Any, NotGiven] = NOT_GIVEN,
        input_audio_transcription: Union[Any, NotGiven] = NOT_GIVEN,
        instructions: Union[str, NotGiven] = NOT_GIVEN,
        max_response_output_tokens: Union[int, Any, NotGiven] = NOT_GIVEN,
        modalities: Union[List[Any], NotGiven] = NOT_GIVEN,
        output_audio_format: Union[Any, NotGiven] = NOT_GIVEN,
        temperature: Union[float, NotGiven] = NOT_GIVEN,
        tool_choice: Union[str, NotGiven] = NOT_GIVEN,
        tools: Union[Iterable[Any], NotGiven] = NOT_GIVEN,
        turn_detection: Union[Any, NotGiven] = NOT_GIVEN,
        voice: Union[Any, NotGiven] = NOT_GIVEN
    ) -> SessionCreateResponse:
        """
        Create a real-time session for voice communication.

        Args:
            model: Model to use for the session
            input_audio_format: Format for input audio (e.g., "pcm16", "g711_ulaw")
            input_audio_transcription: Configuration for input audio transcription
            instructions: System instructions for the AI assistant
            max_response_output_tokens: Maximum tokens in response
            modalities: Supported modalities (audio, text)
            output_audio_format: Format for output audio
            temperature: Response randomness (0.0 to 2.0)
            tool_choice: Tool selection strategy
            tools: Available tools for the assistant
            turn_detection: Turn detection configuration
            voice: Voice model for audio output

        Returns:
            SessionCreateResponse: Session configuration and connection details
        """

class AsyncBetaSessions:
    async def create(
        self,
        *,
        model: Any = "portkey-default",
        input_audio_format: Union[Any, NotGiven] = NOT_GIVEN,
        input_audio_transcription: Union[Any, NotGiven] = NOT_GIVEN,
        instructions: Union[str, NotGiven] = NOT_GIVEN,
        max_response_output_tokens: Union[int, Any, NotGiven] = NOT_GIVEN,
        modalities: Union[List[Any], NotGiven] = NOT_GIVEN,
        output_audio_format: Union[Any, NotGiven] = NOT_GIVEN,
        temperature: Union[float, NotGiven] = NOT_GIVEN,
        tool_choice: Union[str, NotGiven] = NOT_GIVEN,
        tools: Union[Iterable[Any], NotGiven] = NOT_GIVEN,
        turn_detection: Union[Any, NotGiven] = NOT_GIVEN,
        voice: Union[Any, NotGiven] = NOT_GIVEN
    ) -> SessionCreateResponse:
        """Async version of session creation."""
```

### Usage Examples

```python
from portkey_ai import Portkey

# Initialize client
portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Create a real-time session
session = portkey.beta.realtime.sessions.create(
    model="gpt-4-realtime-preview",
    modalities=["text", "audio"],
    instructions="You are a helpful voice assistant.",
    voice="alloy",
    input_audio_format="pcm16",
    output_audio_format="pcm16",
    turn_detection={
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 200
    }
)

print(f"Session ID: {session.id}")
print(f"Model: {session.model}")

# Establish WebSocket connection
connection = portkey.beta.realtime.connect(
    model="gpt-4-realtime-preview",
    websocket_connection_options={
        "timeout": 30,
        "additional_headers": {
            "Authorization": f"Bearer {portkey.api_key}"
        }
    }
)

# Use connection for real-time communication
# Note: Actual usage would involve WebSocket event handling
with connection as conn:
    # Send audio data
    conn.send_audio_data(audio_bytes)
    
    # Handle responses
    for event in conn.listen():
        if event.type == "response.audio.delta":
            # Process audio response
            process_audio_chunk(event.delta)
        elif event.type == "response.text.delta":
            # Process text response
            print(event.delta, end="")
```

### Async Usage

```python
import asyncio
from portkey_ai import AsyncPortkey

async def create_realtime_session():
    portkey = AsyncPortkey(
        api_key="PORTKEY_API_KEY",
        virtual_key="VIRTUAL_KEY"
    )
    
    # Create session asynchronously
    session = await portkey.beta.realtime.sessions.create(
        model="gpt-4-realtime-preview",
        modalities=["text", "audio"],
        instructions="You are a voice assistant for customer support.",
        voice="nova",
        temperature=0.7,
        max_response_output_tokens=150
    )
    
    # Establish async connection
    connection = portkey.beta.realtime.connect(
        model="gpt-4-realtime-preview"
    )
    
    return session, connection

# Run async function
session, connection = asyncio.run(create_realtime_session())
```

### Advanced Configuration

```python
# Configure detailed session parameters
session = portkey.beta.realtime.sessions.create(
    model="gpt-4-realtime-preview",
    modalities=["text", "audio"],
    instructions="""
    You are an AI assistant for a language learning app.
    Help users practice pronunciation and provide feedback.
    Speak clearly and at a moderate pace.
    """,
    voice="shimmer",
    input_audio_format="pcm16",
    output_audio_format="pcm16",
    input_audio_transcription={
        "model": "whisper-1"
    },
    turn_detection={
        "type": "server_vad",
        "threshold": 0.6,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 500
    },
    tools=[
        {
            "type": "function",
            "name": "pronunciation_feedback",
            "description": "Provide pronunciation feedback",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {"type": "string"},
                    "accuracy": {"type": "number"},
                    "feedback": {"type": "string"}
                }
            }
        }
    ],
    tool_choice="auto",
    temperature=0.3,
    max_response_output_tokens=100
)
```

## Types

```python { .api }
class SessionCreateResponse:
    """Response from real-time session creation"""
    id: str  # Session identifier
    object: str  # "realtime.session"
    model: str  # Model used for the session
    modalities: List[str]  # Supported modalities
    instructions: str  # System instructions
    voice: str  # Voice model
    input_audio_format: str  # Input audio format
    output_audio_format: str  # Output audio format
    input_audio_transcription: dict  # Transcription settings
    turn_detection: dict  # Turn detection configuration
    tools: List[dict]  # Available tools
    tool_choice: str  # Tool selection strategy
    temperature: float  # Response temperature
    max_response_output_tokens: int  # Token limit
    _headers: Optional[dict]  # Response headers

class RealtimeConnectionManager:
    """Synchronous WebSocket connection manager"""
    def send_audio_data(self, audio_bytes: bytes) -> None: ...
    def listen(self) -> Iterator[RealtimeEvent]: ...
    def close(self) -> None: ...

class AsyncRealtimeConnectionManager:
    """Asynchronous WebSocket connection manager"""
    async def send_audio_data(self, audio_bytes: bytes) -> None: ...
    async def listen(self) -> AsyncIterator[RealtimeEvent]: ...
    async def close(self) -> None: ...

class WebsocketConnectionOptions:
    """WebSocket connection configuration"""
    timeout: Optional[int]  # Connection timeout in seconds
    additional_headers: Optional[dict]  # Additional headers
    # Additional WebSocket-specific options

class RealtimeEvent:
    """Real-time event from WebSocket connection"""
    type: str  # Event type
    delta: Optional[str]  # Content delta for streaming
    audio: Optional[bytes]  # Audio data
    # Additional event-specific fields
```