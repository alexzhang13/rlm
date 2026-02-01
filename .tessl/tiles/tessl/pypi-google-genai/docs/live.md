# Live API

Real-time bidirectional streaming for interactive applications with support for audio, video, and function calling (Preview). The Live API enables continuous, low-latency communication with the model for conversational AI, voice assistants, and real-time collaboration tools.

## Capabilities

### Connect to Live Session

Establish a bidirectional streaming connection with the model. Returns an async context manager that yields a session for sending and receiving messages.

```python { .api }
class AsyncLive:
    """Asynchronous Live API (Preview)."""

    async def connect(
        self,
        *,
        model: str,
        config: Optional[LiveConnectConfig] = None
    ) -> AsyncIterator[AsyncSession]:
        """
        Connect to live server (async context manager).

        Parameters:
            model (str): Model identifier (e.g., 'gemini-2.0-flash-exp').
            config (LiveConnectConfig, optional): Connection configuration including:
                - system_instruction: System instruction for the session
                - generation_config: Generation parameters
                - tools: Function declarations for function calling
                - speech_config: Speech synthesis configuration

        Yields:
            AsyncSession: Active session for bidirectional communication.

        Raises:
            ClientError: For client errors
            ServerError: For server errors

        Usage:
            async with client.aio.live.connect(model='gemini-2.0-flash-exp') as session:
                # Send and receive messages
                pass
        """
        ...
```

**Usage Example - Basic Live Session:**

```python
import asyncio
from google.genai import Client

async def live_session():
    client = Client(api_key='YOUR_API_KEY')

    async with client.aio.live.connect(
        model='gemini-2.0-flash-exp'
    ) as session:
        # Send message
        await session.send_client_content(
            turns=[Content(parts=[Part(text='Hello, how are you?')])],
            turn_complete=True
        )

        # Receive responses
        async for message in session.receive():
            if message.server_content:
                if message.server_content.model_turn:
                    for part in message.server_content.model_turn.parts:
                        if part.text:
                            print(part.text, end='', flush=True)
                if message.server_content.turn_complete:
                    print()  # New line after turn completes
                    break

asyncio.run(live_session())
```

### Send Client Content

Send conversational content (text, images, etc.) to the model during a live session.

```python { .api }
class AsyncSession:
    """Live session for bidirectional streaming (Preview)."""

    async def send_client_content(
        self,
        *,
        turns: Optional[Union[Content, list[Content]]] = None,
        turn_complete: bool = False
    ) -> None:
        """
        Send client content to the model.

        Parameters:
            turns (Union[Content, list[Content]], optional): Content to send. Can be
                text, images, or other supported content types.
            turn_complete (bool): Whether this completes the current turn. If True,
                model will begin generating response. Default: False.

        Raises:
            RuntimeError: If session is closed or invalid state
        """
        ...
```

### Send Realtime Input

Send realtime media chunks (audio, video) for streaming input.

```python { .api }
class AsyncSession:
    """Live session for bidirectional streaming (Preview)."""

    async def send_realtime_input(
        self,
        *,
        media_chunks: Optional[Sequence[Blob]] = None
    ) -> None:
        """
        Send realtime media input (audio/video chunks).

        Parameters:
            media_chunks (Sequence[Blob], optional): Media chunks to send. Each Blob
                contains binary data with MIME type (e.g., 'audio/pcm' for raw audio).

        Raises:
            RuntimeError: If session is closed or invalid state
        """
        ...
```

**Usage Example - Audio Streaming:**

```python
import asyncio
from google.genai import Client
from google.genai.types import Blob

async def stream_audio():
    client = Client(api_key='YOUR_API_KEY')

    async with client.aio.live.connect(
        model='gemini-2.0-flash-exp'
    ) as session:
        # Stream audio chunks
        with open('audio.pcm', 'rb') as f:
            while chunk := f.read(4096):
                await session.send_realtime_input(
                    media_chunks=[Blob(
                        mime_type='audio/pcm',
                        data=chunk
                    )]
                )

        # Receive responses
        async for message in session.receive():
            # Process responses
            pass

asyncio.run(stream_audio())
```

### Send Tool Response

Send function execution results back to the model after it requests a function call.

```python { .api }
class AsyncSession:
    """Live session for bidirectional streaming (Preview)."""

    async def send_tool_response(
        self,
        *,
        function_responses: Sequence[FunctionResponse]
    ) -> None:
        """
        Send tool/function execution responses.

        Parameters:
            function_responses (Sequence[FunctionResponse]): Results from executing
                functions that the model requested.

        Raises:
            RuntimeError: If session is closed or invalid state
        """
        ...
```

### Receive Messages

Receive streaming messages from the model including content, function calls, and metadata.

```python { .api }
class AsyncSession:
    """Live session for bidirectional streaming (Preview)."""

    async def receive(self) -> AsyncIterator[LiveServerMessage]:
        """
        Receive messages from the model as an async iterator.

        Yields:
            LiveServerMessage: Server messages including:
                - setup_complete: Connection setup confirmation
                - server_content: Generated content from model
                - tool_call: Function call requests from model
                - tool_call_cancellation: Cancelled function calls

        Raises:
            RuntimeError: If session is closed
        """
        ...
```

### Close Session

Explicitly close the live session.

```python { .api }
class AsyncSession:
    """Live session for bidirectional streaming (Preview)."""

    async def close(self) -> None:
        """
        Close the live session.

        Note: Sessions are automatically closed when exiting the context manager.
        """
        ...
```

**Usage Example - Function Calling:**

```python
import asyncio
from google.genai import Client
from google.genai.types import (
    LiveConnectConfig,
    Tool,
    FunctionDeclaration,
    Schema,
    Type,
    Content,
    Part,
    FunctionResponse
)

async def live_with_functions():
    client = Client(api_key='YOUR_API_KEY')

    # Define function
    weather_func = FunctionDeclaration(
        name='get_weather',
        description='Get weather for a location',
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                'location': Schema(type=Type.STRING)
            }
        )
    )

    config = LiveConnectConfig(
        tools=[Tool(function_declarations=[weather_func])]
    )

    async with client.aio.live.connect(
        model='gemini-2.0-flash-exp',
        config=config
    ) as session:
        # Ask for weather
        await session.send_client_content(
            turns=[Content(parts=[Part(text='What is the weather in Tokyo?')])],
            turn_complete=True
        )

        # Handle responses
        async for message in session.receive():
            if message.tool_call:
                # Execute function
                if message.tool_call.function_calls:
                    for fc in message.tool_call.function_calls:
                        if fc.name == 'get_weather':
                            # Execute and return result
                            await session.send_tool_response(
                                function_responses=[FunctionResponse(
                                    name='get_weather',
                                    response={'temperature': 22, 'condition': 'sunny'},
                                    id=fc.id
                                )]
                            )

            if message.server_content:
                if message.server_content.model_turn:
                    for part in message.server_content.model_turn.parts:
                        if part.text:
                            print(part.text)
                if message.server_content.turn_complete:
                    break

asyncio.run(live_with_functions())
```

## Types

```python { .api }
from typing import Optional, Union, Sequence, AsyncIterator, Any
from enum import Enum

# Configuration types
class LiveConnectConfig:
    """
    Configuration for live connection.

    Attributes:
        system_instruction (Union[str, Content], optional): System instruction.
        generation_config (GenerationConfig, optional): Generation parameters.
        tools (list[Tool], optional): Function declarations.
        speech_config (SpeechConfig, optional): Speech synthesis configuration.
        response_modalities (list[str], optional): Desired response modalities ('TEXT', 'AUDIO').
    """
    system_instruction: Optional[Union[str, Content]] = None
    generation_config: Optional[GenerationConfig] = None
    tools: Optional[list[Tool]] = None
    speech_config: Optional[SpeechConfig] = None
    response_modalities: Optional[list[str]] = None

class SpeechConfig:
    """
    Speech synthesis configuration.

    Attributes:
        voice_config (VoiceConfig, optional): Voice settings.
    """
    voice_config: Optional[VoiceConfig] = None

class VoiceConfig:
    """
    Voice configuration.

    Attributes:
        prebuilt_voice_config (PrebuiltVoiceConfig, optional): Prebuilt voice.
    """
    prebuilt_voice_config: Optional[PrebuiltVoiceConfig] = None

class PrebuiltVoiceConfig:
    """
    Prebuilt voice settings.

    Attributes:
        voice_name (str, optional): Voice name (e.g., 'Aoede', 'Charon').
    """
    voice_name: Optional[str] = None

# Message types
class LiveServerMessage:
    """
    Message from server in live session.

    Attributes:
        setup_complete (LiveServerSetupComplete, optional): Setup confirmation.
        server_content (LiveServerContent, optional): Generated content.
        tool_call (LiveServerToolCall, optional): Function call request.
        tool_call_cancellation (LiveServerToolCallCancellation, optional): Cancelled call.
    """
    setup_complete: Optional[LiveServerSetupComplete] = None
    server_content: Optional[LiveServerContent] = None
    tool_call: Optional[LiveServerToolCall] = None
    tool_call_cancellation: Optional[LiveServerToolCallCancellation] = None

class LiveServerSetupComplete:
    """Setup complete confirmation."""
    pass

class LiveServerContent:
    """
    Server content message.

    Attributes:
        model_turn (Content, optional): Model's turn content.
        turn_complete (bool, optional): Whether turn is complete.
        interrupted (bool, optional): Whether turn was interrupted.
        grounding_metadata (GroundingMetadata, optional): Grounding information.
    """
    model_turn: Optional[Content] = None
    turn_complete: Optional[bool] = None
    interrupted: Optional[bool] = None
    grounding_metadata: Optional[GroundingMetadata] = None

class LiveServerToolCall:
    """
    Tool call request from server.

    Attributes:
        function_calls (list[FunctionCall], optional): Requested function calls.
    """
    function_calls: Optional[list[FunctionCall]] = None

class LiveServerToolCallCancellation:
    """
    Tool call cancellation.

    Attributes:
        ids (list[str], optional): IDs of cancelled calls.
    """
    ids: Optional[list[str]] = None

# Core types (shared with other capabilities)
class Content:
    """Content container."""
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """Content part."""
    text: Optional[str] = None
    inline_data: Optional[Blob] = None
    function_call: Optional[FunctionCall] = None
    function_response: Optional[FunctionResponse] = None

class Blob:
    """Binary data."""
    mime_type: str
    data: bytes

class FunctionCall:
    """Function call from model."""
    name: str
    args: dict[str, Any]
    id: Optional[str] = None

class FunctionResponse:
    """Function execution result."""
    name: str
    response: dict[str, Any]
    id: Optional[str] = None

class Tool:
    """Tool with function declarations."""
    function_declarations: Optional[list[FunctionDeclaration]] = None

class FunctionDeclaration:
    """Function definition."""
    name: str
    description: str
    parameters: Optional[Schema] = None

class Schema:
    """JSON schema."""
    type: Type
    properties: Optional[dict[str, Schema]] = None

class Type(Enum):
    """JSON schema types."""
    OBJECT = 'OBJECT'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    INTEGER = 'INTEGER'
    BOOLEAN = 'BOOLEAN'
    ARRAY = 'ARRAY'

class GenerationConfig:
    """Generation configuration."""
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_output_tokens: Optional[int] = None

class GroundingMetadata:
    """Grounding metadata."""
    pass
```
