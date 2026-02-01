# Multi-Turn Conversations

Create and manage chat sessions for multi-turn conversations with automatic history management. Chat sessions maintain conversation context and provide a convenient interface for back-and-forth interactions with the model.

## Capabilities

### Create Chat Session

Create a new chat session with optional configuration and initial history. The chat session automatically manages conversation history across multiple turns.

```python { .api }
class Chats:
    """Factory for creating synchronous chat sessions."""

    def create(
        self,
        *,
        model: str,
        config: Optional[GenerateContentConfig] = None,
        history: Optional[list[Content]] = None
    ) -> Chat:
        """
        Create a new chat session.

        Parameters:
            model (str): Model identifier (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro').
            config (GenerateContentConfig, optional): Default configuration for all messages
                in this chat. Includes system instructions, generation config, safety settings,
                tools, etc. Can be overridden per message.
            history (list[Content], optional): Initial conversation history. Each Content
                should have a role ('user' or 'model') and parts.

        Returns:
            Chat: New chat session instance for sending messages.
        """
        ...

class AsyncChats:
    """Factory for creating asynchronous chat sessions."""

    def create(
        self,
        *,
        model: str,
        config: Optional[GenerateContentConfig] = None,
        history: Optional[list[Content]] = None
    ) -> AsyncChat:
        """
        Create a new async chat session.

        Parameters:
            model (str): Model identifier.
            config (GenerateContentConfig, optional): Default configuration.
            history (list[Content], optional): Initial conversation history.

        Returns:
            AsyncChat: New async chat session instance.
        """
        ...
```

**Usage Example - Create Chat:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

# Create chat session
chat = client.chats.create(model='gemini-2.0-flash')

# Send messages
response1 = chat.send_message('What is machine learning?')
print(response1.text)

response2 = chat.send_message('Can you give me an example?')
print(response2.text)

# History is automatically maintained
history = chat.get_history()
print(f"Conversation has {len(history)} messages")
```

**Usage Example - With Configuration:**

```python
from google.genai import Client
from google.genai.types import (
    GenerateContentConfig,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold
)

client = Client(api_key='YOUR_API_KEY')

config = GenerateContentConfig(
    system_instruction='You are a helpful coding assistant.',
    temperature=0.3,
    max_output_tokens=512,
    safety_settings=[
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        )
    ]
)

chat = client.chats.create(
    model='gemini-2.0-flash',
    config=config
)

response = chat.send_message('How do I sort a list in Python?')
print(response.text)
```

### Send Message

Send a message to the chat session and receive a response. The message and response are automatically added to the conversation history.

```python { .api }
class Chat:
    """Synchronous chat session for multi-turn conversations."""

    def send_message(
        self,
        message: Union[str, Part, Image, list[Part]],
        config: Optional[GenerateContentConfig] = None
    ) -> GenerateContentResponse:
        """
        Send a message to the chat and receive a response.

        Parameters:
            message (Union[str, Part, Image, list[Part]]): Message to send. Can be:
                - str: Simple text message
                - Part: Single part (text, inline_data, etc.)
                - Image: Image to send with implicit question
                - list[Part]: Multiple parts (e.g., text + image)
            config (GenerateContentConfig, optional): Configuration override for this
                message only. Merged with chat's default config.

        Returns:
            GenerateContentResponse: Model response containing generated content,
                usage metadata, and safety ratings.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncChat:
    """Asynchronous chat session for multi-turn conversations."""

    async def send_message(
        self,
        message: Union[str, Part, Image, list[Part]],
        config: Optional[GenerateContentConfig] = None
    ) -> GenerateContentResponse:
        """
        Async version of send_message.

        Parameters:
            message (Union[str, Part, Image, list[Part]]): Message to send.
            config (GenerateContentConfig, optional): Configuration override.

        Returns:
            GenerateContentResponse: Model response.
        """
        ...
```

**Usage Example - Send Text Message:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')
chat = client.chats.create(model='gemini-2.0-flash')

# Send text messages
response1 = chat.send_message('Tell me about Python.')
print(response1.text)

response2 = chat.send_message('What are its main features?')
print(response2.text)
```

**Usage Example - Send Multimodal Message:**

```python
from google.genai import Client
from google.genai.types import Part, Image

client = Client(api_key='YOUR_API_KEY')
chat = client.chats.create(model='gemini-2.0-flash')

# Send image with question
image = Image.from_file('diagram.png')
message_parts = [
    Part(text='What does this diagram show?'),
    Part(inline_data=image.blob)
]

response = chat.send_message(message_parts)
print(response.text)

# Continue conversation
followup = chat.send_message('Can you explain it in more detail?')
print(followup.text)
```

### Send Message Streaming

Send a message and receive the response as a stream of chunks, allowing for real-time display of the model's output.

```python { .api }
class Chat:
    """Synchronous chat session for multi-turn conversations."""

    def send_message_stream(
        self,
        message: Union[str, Part, Image, list[Part]],
        config: Optional[GenerateContentConfig] = None
    ) -> Iterator[GenerateContentResponse]:
        """
        Send a message to the chat and receive a streaming response.

        Parameters:
            message (Union[str, Part, Image, list[Part]]): Message to send.
            config (GenerateContentConfig, optional): Configuration override for this message.

        Yields:
            GenerateContentResponse: Streaming response chunks as they are generated.

        Raises:
            ClientError: For client errors (4xx status codes)
            ServerError: For server errors (5xx status codes)
        """
        ...

class AsyncChat:
    """Asynchronous chat session for multi-turn conversations."""

    async def send_message_stream(
        self,
        message: Union[str, Part, Image, list[Part]],
        config: Optional[GenerateContentConfig] = None
    ) -> AsyncIterator[GenerateContentResponse]:
        """
        Async version of send_message_stream.

        Parameters:
            message (Union[str, Part, Image, list[Part]]): Message to send.
            config (GenerateContentConfig, optional): Configuration override.

        Yields:
            GenerateContentResponse: Streaming response chunks.
        """
        ...
```

**Usage Example - Streaming:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')
chat = client.chats.create(model='gemini-2.0-flash')

# First message
response1 = chat.send_message('What is neural network?')
print(response1.text)

# Streaming follow-up
print('\nModel response (streaming):')
stream = chat.send_message_stream('Explain backpropagation.')
for chunk in stream:
    print(chunk.text, end='', flush=True)
print()  # New line
```

**Usage Example - Async Streaming:**

```python
import asyncio
from google.genai import Client

async def main():
    client = Client(api_key='YOUR_API_KEY')
    chat = client.aio.chats.create(model='gemini-2.0-flash')

    # First message
    response = await chat.send_message('Hello!')
    print(response.text)

    # Streaming follow-up
    print('\nStreaming response:')
    stream = await chat.send_message_stream('Tell me about AI.')
    async for chunk in stream:
        print(chunk.text, end='', flush=True)
    print()

asyncio.run(main())
```

### Get History

Retrieve the conversation history for the chat session.

```python { .api }
class Chat:
    """Synchronous chat session for multi-turn conversations."""

    def get_history(self, curated: bool = False) -> list[Content]:
        """
        Get the chat conversation history.

        Parameters:
            curated (bool): If True, returns only user and model messages, filtering out
                intermediate function calls and responses. If False, returns complete
                history including all function calling interactions. Defaults to False.

        Returns:
            list[Content]: List of Content objects representing the conversation history
                in chronological order. Each Content has a role ('user' or 'model') and
                list of parts.
        """
        ...

class AsyncChat:
    """Asynchronous chat session for multi-turn conversations."""

    def get_history(self, curated: bool = False) -> list[Content]:
        """
        Get the chat conversation history.

        Note: This is a synchronous method even in AsyncChat as it doesn't require I/O.

        Parameters:
            curated (bool): If True, returns curated history without function calls.

        Returns:
            list[Content]: Conversation history.
        """
        ...
```

**Usage Example - Get History:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')
chat = client.chats.create(model='gemini-2.0-flash')

# Have a conversation
chat.send_message('What is Python?')
chat.send_message('What are its uses?')
chat.send_message('Is it beginner-friendly?')

# Get full history
history = chat.get_history()
print(f"Total messages: {len(history)}")

for i, content in enumerate(history):
    role = content.role or 'unknown'
    text = content.parts[0].text if content.parts else ''
    print(f"{i+1}. {role}: {text[:50]}...")

# Get curated history (without function call details)
curated_history = chat.get_history(curated=True)
print(f"Curated messages: {len(curated_history)}")
```

## Types

```python { .api }
from typing import Optional, Union, List, Iterator, AsyncIterator, Any
from enum import Enum

# Core types (shared with content-generation.md)
class Content:
    """
    Container for conversation content with role and parts.

    Attributes:
        parts (list[Part]): List of content parts
        role (str, optional): Role ('user' or 'model')
    """
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """
    Individual content part.

    Attributes:
        text (str, optional): Text content
        inline_data (Blob, optional): Inline binary data
        file_data (FileData, optional): Reference to uploaded file
        function_call (FunctionCall, optional): Function call from model
        function_response (FunctionResponse, optional): Function execution result
        executable_code (ExecutableCode, optional): Executable code
        code_execution_result (CodeExecutionResult, optional): Code execution output
    """
    text: Optional[str] = None
    inline_data: Optional[Blob] = None
    file_data: Optional[FileData] = None
    function_call: Optional[FunctionCall] = None
    function_response: Optional[FunctionResponse] = None
    executable_code: Optional[ExecutableCode] = None
    code_execution_result: Optional[CodeExecutionResult] = None

class Blob:
    """
    Binary data with MIME type.

    Attributes:
        mime_type (str): MIME type
        data (bytes): Binary data
    """
    mime_type: str
    data: bytes

class FileData:
    """
    Reference to uploaded file.

    Attributes:
        file_uri (str): URI of uploaded file
        mime_type (str): MIME type
    """
    file_uri: str
    mime_type: str

class Image:
    """Image data supporting multiple input formats."""
    pass

class GenerateContentConfig:
    """
    Configuration for content generation.

    Attributes:
        system_instruction (Union[str, Content], optional): System instructions
        contents (Union[str, list[Content], Content], optional): Override contents
        generation_config (GenerationConfig, optional): Generation parameters
        safety_settings (list[SafetySetting], optional): Safety filtering
        tools (list[Tool], optional): Function declarations
        tool_config (ToolConfig, optional): Function calling config
        cached_content (str, optional): Cached content reference
    """
    system_instruction: Optional[Union[str, Content]] = None
    contents: Optional[Union[str, list[Content], Content]] = None
    generation_config: Optional[GenerationConfig] = None
    safety_settings: Optional[list[SafetySetting]] = None
    tools: Optional[list[Tool]] = None
    tool_config: Optional[ToolConfig] = None
    cached_content: Optional[str] = None

class GenerationConfig:
    """
    Core generation parameters.

    Attributes:
        temperature (float, optional): Sampling temperature (0.0-2.0)
        top_p (float, optional): Nucleus sampling (0.0-1.0)
        top_k (int, optional): Top-k sampling
        max_output_tokens (int, optional): Maximum response tokens
        stop_sequences (list[str], optional): Stop sequences
    """
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_output_tokens: Optional[int] = None
    stop_sequences: Optional[list[str]] = None

class GenerateContentResponse:
    """
    Response from content generation.

    Attributes:
        text (str): Text from first candidate
        candidates (list[Candidate]): Generated candidates
        usage_metadata (GenerateContentResponseUsageMetadata, optional): Usage stats
        prompt_feedback (GenerateContentResponsePromptFeedback, optional): Prompt feedback
        model_version (str, optional): Model version
    """
    text: str
    candidates: list[Candidate]
    usage_metadata: Optional[GenerateContentResponseUsageMetadata] = None
    prompt_feedback: Optional[GenerateContentResponsePromptFeedback] = None
    model_version: Optional[str] = None

class Candidate:
    """
    Generated candidate.

    Attributes:
        content (Content): Generated content
        finish_reason (FinishReason, optional): Reason generation stopped
        safety_ratings (list[SafetyRating], optional): Safety ratings
        citation_metadata (CitationMetadata, optional): Citations
        grounding_metadata (GroundingMetadata, optional): Grounding attribution
    """
    content: Content
    finish_reason: Optional[FinishReason] = None
    safety_ratings: Optional[list[SafetyRating]] = None
    citation_metadata: Optional[CitationMetadata] = None
    grounding_metadata: Optional[GroundingMetadata] = None

class GenerateContentResponseUsageMetadata:
    """
    Token usage statistics.

    Attributes:
        prompt_token_count (int): Prompt tokens
        candidates_token_count (int): Generated tokens
        total_token_count (int): Total tokens
        cached_content_token_count (int, optional): Cached tokens
    """
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int
    cached_content_token_count: Optional[int] = None

class GenerateContentResponsePromptFeedback:
    """
    Prompt feedback.

    Attributes:
        block_reason (BlockedReason, optional): Block reason
        safety_ratings (list[SafetyRating], optional): Safety ratings
    """
    block_reason: Optional[BlockedReason] = None
    safety_ratings: Optional[list[SafetyRating]] = None

class SafetySetting:
    """
    Safety filter configuration.

    Attributes:
        category (HarmCategory): Harm category
        threshold (HarmBlockThreshold): Blocking threshold
    """
    category: HarmCategory
    threshold: HarmBlockThreshold

class SafetyRating:
    """
    Safety rating.

    Attributes:
        category (HarmCategory): Harm category
        probability (HarmProbability): Harm probability
        blocked (bool): Whether blocked
    """
    category: HarmCategory
    probability: HarmProbability
    blocked: bool

class Tool:
    """
    Tool with function declarations.

    Attributes:
        function_declarations (list[FunctionDeclaration], optional): Functions
        google_search (GoogleSearch, optional): Google Search tool
        code_execution (ToolCodeExecution, optional): Code execution tool
    """
    function_declarations: Optional[list[FunctionDeclaration]] = None
    google_search: Optional[GoogleSearch] = None
    code_execution: Optional[ToolCodeExecution] = None

class FunctionDeclaration:
    """
    Function definition.

    Attributes:
        name (str): Function name
        description (str): Function description
        parameters (Schema, optional): Parameter schema
    """
    name: str
    description: str
    parameters: Optional[Schema] = None

class FunctionCall:
    """
    Function call from model.

    Attributes:
        name (str): Function name
        args (dict[str, Any]): Arguments
        id (str, optional): Call ID
    """
    name: str
    args: dict[str, Any]
    id: Optional[str] = None

class FunctionResponse:
    """
    Function execution result.

    Attributes:
        name (str): Function name
        response (dict[str, Any]): Return value
        id (str, optional): Call ID
    """
    name: str
    response: dict[str, Any]
    id: Optional[str] = None

class ToolConfig:
    """Function calling configuration."""
    function_calling_config: Optional[FunctionCallingConfig] = None

class FunctionCallingConfig:
    """
    Function calling mode.

    Attributes:
        mode (FunctionCallingConfigMode): Calling mode
        allowed_function_names (list[str], optional): Allowed functions
    """
    mode: FunctionCallingConfigMode
    allowed_function_names: Optional[list[str]] = None

class FunctionCallingConfigMode(Enum):
    """Function calling modes."""
    MODE_UNSPECIFIED = 'MODE_UNSPECIFIED'
    AUTO = 'AUTO'
    ANY = 'ANY'
    NONE = 'NONE'

class Schema:
    """JSON schema for parameters."""
    type: Type
    properties: Optional[dict[str, Schema]] = None
    required: Optional[list[str]] = None

class Type(Enum):
    """JSON schema types."""
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    INTEGER = 'INTEGER'
    BOOLEAN = 'BOOLEAN'
    ARRAY = 'ARRAY'
    OBJECT = 'OBJECT'

class FinishReason(Enum):
    """Finish reasons."""
    FINISH_REASON_UNSPECIFIED = 'FINISH_REASON_UNSPECIFIED'
    STOP = 'STOP'
    MAX_TOKENS = 'MAX_TOKENS'
    SAFETY = 'SAFETY'
    RECITATION = 'RECITATION'

class BlockedReason(Enum):
    """Blocked reasons."""
    BLOCKED_REASON_UNSPECIFIED = 'BLOCKED_REASON_UNSPECIFIED'
    SAFETY = 'SAFETY'
    OTHER = 'OTHER'

class HarmCategory(Enum):
    """Harm categories."""
    HARM_CATEGORY_UNSPECIFIED = 'HARM_CATEGORY_UNSPECIFIED'
    HARM_CATEGORY_HARASSMENT = 'HARM_CATEGORY_HARASSMENT'
    HARM_CATEGORY_HATE_SPEECH = 'HARM_CATEGORY_HATE_SPEECH'
    HARM_CATEGORY_SEXUALLY_EXPLICIT = 'HARM_CATEGORY_SEXUALLY_EXPLICIT'
    HARM_CATEGORY_DANGEROUS_CONTENT = 'HARM_CATEGORY_DANGEROUS_CONTENT'

class HarmBlockThreshold(Enum):
    """Block thresholds."""
    HARM_BLOCK_THRESHOLD_UNSPECIFIED = 'HARM_BLOCK_THRESHOLD_UNSPECIFIED'
    BLOCK_LOW_AND_ABOVE = 'BLOCK_LOW_AND_ABOVE'
    BLOCK_MEDIUM_AND_ABOVE = 'BLOCK_MEDIUM_AND_ABOVE'
    BLOCK_ONLY_HIGH = 'BLOCK_ONLY_HIGH'
    BLOCK_NONE = 'BLOCK_NONE'

class HarmProbability(Enum):
    """Harm probabilities."""
    HARM_PROBABILITY_UNSPECIFIED = 'HARM_PROBABILITY_UNSPECIFIED'
    NEGLIGIBLE = 'NEGLIGIBLE'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class CitationMetadata:
    """Citation information."""
    citations: list[Citation]

class Citation:
    """Individual citation."""
    start_index: int
    end_index: int
    uri: str

class GroundingMetadata:
    """Grounding attribution."""
    grounding_chunks: Optional[list[GroundingChunk]] = None

class GroundingChunk:
    """Grounding chunk."""
    pass

class GoogleSearch:
    """Google Search tool."""
    pass

class ToolCodeExecution:
    """Code execution tool."""
    pass

class ExecutableCode:
    """Executable code from model."""
    language: Language
    code: str

class Language(Enum):
    """Programming languages."""
    LANGUAGE_UNSPECIFIED = 'LANGUAGE_UNSPECIFIED'
    PYTHON = 'PYTHON'

class CodeExecutionResult:
    """Code execution result."""
    outcome: Outcome
    output: str

class Outcome(Enum):
    """Execution outcomes."""
    OUTCOME_UNSPECIFIED = 'OUTCOME_UNSPECIFIED'
    OUTCOME_OK = 'OUTCOME_OK'
    OUTCOME_FAILED = 'OUTCOME_FAILED'
```
