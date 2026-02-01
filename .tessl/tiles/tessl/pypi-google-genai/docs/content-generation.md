# Content Generation

Generate text and multimodal content using Gemini models with support for streaming, function calling, structured output, safety controls, and extensive configuration options. Content generation is the primary capability for creating AI-generated responses from text, image, audio, video, and document inputs.

## Capabilities

### Generate Content

Generate content synchronously from text and multimodal inputs. Supports single or multiple content inputs, system instructions, function calling, structured output, and safety settings.

```python { .api }
def generate_content(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[GenerateContentConfig] = None
) -> GenerateContentResponse:
    """
    Generate content from the model.

    Parameters:
        model (str): Model identifier (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro').
        contents (Union[str, list[Content], Content]): Input content. Can be:
            - str: Simple text prompt
            - Content: Single content object with role and parts
            - list[Content]: Multiple content objects for conversation history
        config (GenerateContentConfig, optional): Generation configuration including:
            - system_instruction: System-level instructions for the model
            - generation_config: Parameters like temperature, top_p, max_tokens
            - safety_settings: Content safety filtering configuration
            - tools: Function declarations for function calling
            - tool_config: Function calling behavior configuration
            - cached_content: Reference to cached content for efficiency

    Returns:
        GenerateContentResponse: Response containing generated content, usage metadata,
            and safety ratings.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def generate_content(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[GenerateContentConfig] = None
) -> GenerateContentResponse:
    """Async version of generate_content."""
    ...
```

**Usage Example - Simple Text Generation:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Explain quantum computing in simple terms.'
)

print(response.text)
```

**Usage Example - With Configuration:**

```python
from google.genai import Client
from google.genai.types import GenerateContentConfig

client = Client(api_key='YOUR_API_KEY')

config = GenerateContentConfig(
    system_instruction='You are a helpful physics tutor.',
    temperature=0.7,
    top_p=0.95,
    max_output_tokens=1024,
    stop_sequences=['END']
)

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Explain relativity',
    config=config
)

print(response.text)
```

**Usage Example - Multimodal Input:**

```python
from google.genai import Client
from google.genai.types import Content, Part, Image

client = Client(api_key='YOUR_API_KEY')

# Create multimodal content
image = Image.from_file('photo.jpg')
content = Content(
    parts=[
        Part(text='What is in this image?'),
        Part(inline_data=image.blob)
    ]
)

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=content
)

print(response.text)
```

### Generate Content Streaming

Generate content with streaming responses, allowing you to receive and process chunks as they are generated rather than waiting for the complete response.

```python { .api }
def generate_content_stream(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[GenerateContentConfig] = None
) -> Iterator[GenerateContentResponse]:
    """
    Generate content in streaming mode, yielding response chunks as they are generated.

    Parameters:
        model (str): Model identifier (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro').
        contents (Union[str, list[Content], Content]): Input content.
        config (GenerateContentConfig, optional): Generation configuration.

    Yields:
        GenerateContentResponse: Streaming response chunks. Each chunk contains:
            - Partial or complete candidates with generated content
            - Incremental usage metadata
            - Safety ratings

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def generate_content_stream(
    *,
    model: str,
    contents: Union[str, list[Content], Content],
    config: Optional[GenerateContentConfig] = None
) -> AsyncIterator[GenerateContentResponse]:
    """Async version of generate_content_stream."""
    ...
```

**Usage Example - Streaming:**

```python
from google.genai import Client

client = Client(api_key='YOUR_API_KEY')

stream = client.models.generate_content_stream(
    model='gemini-2.0-flash',
    contents='Write a short story about a robot.'
)

for chunk in stream:
    print(chunk.text, end='', flush=True)
print()  # New line after streaming completes
```

**Usage Example - Async Streaming:**

```python
import asyncio
from google.genai import Client

async def main():
    client = Client(api_key='YOUR_API_KEY')

    stream = await client.aio.models.generate_content_stream(
        model='gemini-2.0-flash',
        contents='Explain neural networks.'
    )

    async for chunk in stream:
        print(chunk.text, end='', flush=True)
    print()

asyncio.run(main())
```

### Function Calling

Enable the model to call functions you define, allowing it to access external tools, APIs, and data sources. The model generates function calls based on the conversation context, and you execute them and return results.

**Usage Example - Function Calling:**

```python
from google.genai import Client
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    FunctionDeclaration,
    Schema,
    Type,
    FunctionResponse,
    Content,
    Part
)

client = Client(api_key='YOUR_API_KEY')

# Define function declarations
get_weather = FunctionDeclaration(
    name='get_weather',
    description='Get the current weather for a location',
    parameters=Schema(
        type=Type.OBJECT,
        properties={
            'location': Schema(type=Type.STRING, description='City name'),
            'unit': Schema(
                type=Type.STRING,
                enum=['celsius', 'fahrenheit'],
                description='Temperature unit'
            )
        },
        required=['location']
    )
)

config = GenerateContentConfig(
    tools=[Tool(function_declarations=[get_weather])]
)

# Initial request
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the weather in Tokyo?',
    config=config
)

# Check if model wants to call function
if response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call

    # Execute function (example)
    if function_call.name == 'get_weather':
        weather_data = {'temperature': 22, 'condition': 'sunny'}

        # Send function response back
        function_response = FunctionResponse(
            name='get_weather',
            response=weather_data
        )

        # Continue conversation with function result
        response2 = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                response.candidates[0].content,
                Content(parts=[Part(function_response=function_response)])
            ],
            config=config
        )

        print(response2.text)
```

### Structured Output

Generate structured output conforming to a JSON schema, ensuring the model's response follows a specific format.

**Usage Example - Structured Output:**

```python
from google.genai import Client
from google.genai.types import (
    GenerateContentConfig,
    Schema,
    Type
)

client = Client(api_key='YOUR_API_KEY')

# Define output schema
recipe_schema = Schema(
    type=Type.OBJECT,
    properties={
        'recipe_name': Schema(type=Type.STRING),
        'ingredients': Schema(
            type=Type.ARRAY,
            items=Schema(type=Type.STRING)
        ),
        'steps': Schema(
            type=Type.ARRAY,
            items=Schema(type=Type.STRING)
        ),
        'prep_time_minutes': Schema(type=Type.INTEGER)
    },
    required=['recipe_name', 'ingredients', 'steps']
)

config = GenerateContentConfig(
    response_mime_type='application/json',
    response_schema=recipe_schema
)

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me a recipe for chocolate chip cookies',
    config=config
)

import json
recipe = json.loads(response.text)
print(recipe['recipe_name'])
print(f"Prep time: {recipe['prep_time_minutes']} minutes")
```

### Safety Settings

Configure content safety filtering to control what types of content are blocked or allowed in both inputs and outputs.

**Usage Example - Safety Settings:**

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
    safety_settings=[
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        )
    ]
)

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Your prompt here',
    config=config
)

# Check safety ratings
for rating in response.candidates[0].safety_ratings:
    print(f"{rating.category}: {rating.probability}")
```

## Types

```python { .api }
from typing import Optional, Union, List, Sequence, Any, Dict, Iterator, AsyncIterator
from enum import Enum

# Core content types
class Content:
    """
    Container for conversation content with role and parts.

    Attributes:
        parts (list[Part]): List of content parts (text, images, function calls, etc.)
        role (str, optional): Role of the content creator ('user' or 'model')
    """
    parts: list[Part]
    role: Optional[str] = None

class Part:
    """
    Individual content part within a Content object.

    Attributes:
        text (str, optional): Text content
        inline_data (Blob, optional): Inline binary data (images, audio, etc.)
        file_data (FileData, optional): Reference to uploaded file
        function_call (FunctionCall, optional): Function call from model
        function_response (FunctionResponse, optional): Function execution result
        executable_code (ExecutableCode, optional): Executable code from model
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
        mime_type (str): MIME type (e.g., 'image/jpeg', 'audio/wav')
        data (bytes): Binary data
    """
    mime_type: str
    data: bytes

class FileData:
    """
    Reference to an uploaded file.

    Attributes:
        file_uri (str): URI of the uploaded file (e.g., 'gs://bucket/file')
        mime_type (str): MIME type of the file
    """
    file_uri: str
    mime_type: str

class Image:
    """
    Image data supporting multiple input formats.

    Can be created from:
        - URL: Image.from_url('https://...')
        - File path: Image.from_file('path/to/image.jpg')
        - Bytes: Image.from_bytes(data, mime_type='image/jpeg')
        - PIL Image: Image.from_pil(pil_image)
        - FileData: Image(file_data=FileData(...))
    """
    pass

class Video:
    """
    Video data supporting multiple input formats.

    Can be created from:
        - URL: Video.from_url('https://...')
        - File path: Video.from_file('path/to/video.mp4')
        - Bytes: Video.from_bytes(data, mime_type='video/mp4')
        - FileData: Video(file_data=FileData(...))
    """
    pass

# Generation configuration
class GenerateContentConfig:
    """
    Configuration for content generation.

    Attributes:
        system_instruction (Union[str, Content], optional): System-level instructions
        contents (Union[str, list[Content], Content], optional): Override input contents
        temperature (float, optional): Sampling temperature (0.0-2.0). Higher = more random.
        top_p (float, optional): Nucleus sampling threshold (0.0-1.0)
        top_k (float, optional): Top-k sampling parameter
        candidate_count (int, optional): Number of response candidates to generate
        max_output_tokens (int, optional): Maximum tokens in generated response
        stop_sequences (list[str], optional): Sequences that stop generation
        response_mime_type (str, optional): MIME type for structured output ('application/json')
        response_schema (Schema, optional): JSON schema for structured output
        presence_penalty (float, optional): Penalty for token presence (-2.0 to 2.0)
        frequency_penalty (float, optional): Penalty for token frequency (-2.0 to 2.0)
        response_logprobs (bool, optional): Include log probabilities in response
        logprobs (int, optional): Number of top logprobs to return per token
        safety_settings (list[SafetySetting], optional): Safety filtering configuration
        tools (list[Tool], optional): Function declarations for function calling
        tool_config (ToolConfig, optional): Function calling behavior configuration
        cached_content (str, optional): Reference to cached content by name
    """
    system_instruction: Optional[Union[str, Content]] = None
    contents: Optional[Union[str, list[Content], Content]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[float] = None
    candidate_count: Optional[int] = None
    max_output_tokens: Optional[int] = None
    stop_sequences: Optional[list[str]] = None
    response_mime_type: Optional[str] = None
    response_schema: Optional[Schema] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    response_logprobs: Optional[bool] = None
    logprobs: Optional[int] = None
    safety_settings: Optional[list[SafetySetting]] = None
    tools: Optional[list[Tool]] = None
    tool_config: Optional[ToolConfig] = None
    cached_content: Optional[str] = None

class GenerationConfig:
    """
    NOTE: This type is not used directly. Generation parameters are passed directly
    to GenerateContentConfig, not as a nested GenerationConfig object.

    Core generation parameters controlling model behavior.

    Attributes:
        temperature (float, optional): Sampling temperature (0.0-2.0). Higher = more random.
        top_p (float, optional): Nucleus sampling threshold (0.0-1.0)
        top_k (int, optional): Top-k sampling parameter
        candidate_count (int, optional): Number of response candidates to generate
        max_output_tokens (int, optional): Maximum tokens in generated response
        stop_sequences (list[str], optional): Sequences that stop generation
        response_mime_type (str, optional): MIME type for structured output ('application/json')
        response_schema (Schema, optional): JSON schema for structured output
        presence_penalty (float, optional): Penalty for token presence (-2.0 to 2.0)
        frequency_penalty (float, optional): Penalty for token frequency (-2.0 to 2.0)
        response_logprobs (bool, optional): Include log probabilities in response
        logprobs (int, optional): Number of top logprobs to return per token
    """
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    candidate_count: Optional[int] = None
    max_output_tokens: Optional[int] = None
    stop_sequences: Optional[list[str]] = None
    response_mime_type: Optional[str] = None
    response_schema: Optional[Schema] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    response_logprobs: Optional[bool] = None
    logprobs: Optional[int] = None

# Response types
class GenerateContentResponse:
    """
    Response from content generation.

    Attributes:
        text (str): Convenience property returning text from first candidate
        candidates (list[Candidate]): Generated candidates with content and metadata
        usage_metadata (GenerateContentResponseUsageMetadata, optional): Token usage stats
        prompt_feedback (GenerateContentResponsePromptFeedback, optional): Prompt feedback
        model_version (str, optional): Model version used for generation
    """
    text: str
    candidates: list[Candidate]
    usage_metadata: Optional[GenerateContentResponseUsageMetadata] = None
    prompt_feedback: Optional[GenerateContentResponsePromptFeedback] = None
    model_version: Optional[str] = None

class Candidate:
    """
    Generated candidate with content and metadata.

    Attributes:
        content (Content): Generated content
        finish_reason (FinishReason, optional): Reason generation stopped
        safety_ratings (list[SafetyRating], optional): Safety ratings for content
        citation_metadata (CitationMetadata, optional): Citation information
        grounding_metadata (GroundingMetadata, optional): Grounding attribution
        token_count (int, optional): Number of tokens in candidate
        index (int, optional): Candidate index
        logprobs_result (LogprobsResult, optional): Log probabilities
    """
    content: Content
    finish_reason: Optional[FinishReason] = None
    safety_ratings: Optional[list[SafetyRating]] = None
    citation_metadata: Optional[CitationMetadata] = None
    grounding_metadata: Optional[GroundingMetadata] = None
    token_count: Optional[int] = None
    index: Optional[int] = None
    logprobs_result: Optional[LogprobsResult] = None

class GenerateContentResponseUsageMetadata:
    """
    Token usage statistics.

    Attributes:
        prompt_token_count (int): Tokens in the prompt
        candidates_token_count (int): Tokens in generated candidates
        total_token_count (int): Total tokens (prompt + candidates)
        cached_content_token_count (int, optional): Tokens from cached content
    """
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int
    cached_content_token_count: Optional[int] = None

class GenerateContentResponsePromptFeedback:
    """
    Feedback about the prompt.

    Attributes:
        block_reason (BlockedReason, optional): Reason prompt was blocked
        safety_ratings (list[SafetyRating], optional): Safety ratings for prompt
    """
    block_reason: Optional[BlockedReason] = None
    safety_ratings: Optional[list[SafetyRating]] = None

# Safety types
class SafetySetting:
    """
    Safety filter configuration.

    Attributes:
        category (HarmCategory): Harm category to configure
        threshold (HarmBlockThreshold): Blocking threshold for this category
        method (HarmBlockMethod, optional): Block based on probability or severity
    """
    category: HarmCategory
    threshold: HarmBlockThreshold
    method: Optional[HarmBlockMethod] = None

class SafetyRating:
    """
    Safety rating for content.

    Attributes:
        category (HarmCategory): Harm category
        probability (HarmProbability): Probability of harm
        severity (HarmSeverity, optional): Severity of harm
        blocked (bool): Whether content was blocked
    """
    category: HarmCategory
    probability: HarmProbability
    severity: Optional[HarmSeverity] = None
    blocked: bool

class HarmCategory(Enum):
    """Harm categories for safety filtering."""
    HARM_CATEGORY_UNSPECIFIED = 'HARM_CATEGORY_UNSPECIFIED'
    HARM_CATEGORY_HARASSMENT = 'HARM_CATEGORY_HARASSMENT'
    HARM_CATEGORY_HATE_SPEECH = 'HARM_CATEGORY_HATE_SPEECH'
    HARM_CATEGORY_SEXUALLY_EXPLICIT = 'HARM_CATEGORY_SEXUALLY_EXPLICIT'
    HARM_CATEGORY_DANGEROUS_CONTENT = 'HARM_CATEGORY_DANGEROUS_CONTENT'
    HARM_CATEGORY_CIVIC_INTEGRITY = 'HARM_CATEGORY_CIVIC_INTEGRITY'

class HarmBlockThreshold(Enum):
    """Blocking thresholds for safety filtering."""
    HARM_BLOCK_THRESHOLD_UNSPECIFIED = 'HARM_BLOCK_THRESHOLD_UNSPECIFIED'
    BLOCK_LOW_AND_ABOVE = 'BLOCK_LOW_AND_ABOVE'
    BLOCK_MEDIUM_AND_ABOVE = 'BLOCK_MEDIUM_AND_ABOVE'
    BLOCK_ONLY_HIGH = 'BLOCK_ONLY_HIGH'
    BLOCK_NONE = 'BLOCK_NONE'
    OFF = 'OFF'

class HarmProbability(Enum):
    """Harm probability levels."""
    HARM_PROBABILITY_UNSPECIFIED = 'HARM_PROBABILITY_UNSPECIFIED'
    NEGLIGIBLE = 'NEGLIGIBLE'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class HarmSeverity(Enum):
    """Harm severity levels."""
    HARM_SEVERITY_UNSPECIFIED = 'HARM_SEVERITY_UNSPECIFIED'
    HARM_SEVERITY_NEGLIGIBLE = 'HARM_SEVERITY_NEGLIGIBLE'
    HARM_SEVERITY_LOW = 'HARM_SEVERITY_LOW'
    HARM_SEVERITY_MEDIUM = 'HARM_SEVERITY_MEDIUM'
    HARM_SEVERITY_HIGH = 'HARM_SEVERITY_HIGH'

class HarmBlockMethod(Enum):
    """Block method for safety filtering."""
    HARM_BLOCK_METHOD_UNSPECIFIED = 'HARM_BLOCK_METHOD_UNSPECIFIED'
    SEVERITY = 'SEVERITY'
    PROBABILITY = 'PROBABILITY'

class FinishReason(Enum):
    """Reasons why model stopped generating."""
    FINISH_REASON_UNSPECIFIED = 'FINISH_REASON_UNSPECIFIED'
    STOP = 'STOP'
    MAX_TOKENS = 'MAX_TOKENS'
    SAFETY = 'SAFETY'
    RECITATION = 'RECITATION'
    LANGUAGE = 'LANGUAGE'
    OTHER = 'OTHER'
    BLOCKLIST = 'BLOCKLIST'
    PROHIBITED_CONTENT = 'PROHIBITED_CONTENT'
    SPII = 'SPII'
    MALFORMED_FUNCTION_CALL = 'MALFORMED_FUNCTION_CALL'

class BlockedReason(Enum):
    """Reasons why prompt was blocked."""
    BLOCKED_REASON_UNSPECIFIED = 'BLOCKED_REASON_UNSPECIFIED'
    SAFETY = 'SAFETY'
    OTHER = 'OTHER'
    BLOCKLIST = 'BLOCKLIST'
    PROHIBITED_CONTENT = 'PROHIBITED_CONTENT'

# Function calling types
class Tool:
    """
    Tool containing function declarations.

    Attributes:
        function_declarations (list[FunctionDeclaration], optional): Function definitions
        google_search (GoogleSearch, optional): Google Search tool
        code_execution (ToolCodeExecution, optional): Code execution tool
    """
    function_declarations: Optional[list[FunctionDeclaration]] = None
    google_search: Optional[GoogleSearch] = None
    code_execution: Optional[ToolCodeExecution] = None

class FunctionDeclaration:
    """
    Function schema definition for function calling.

    Attributes:
        name (str): Function name
        description (str): Function description for the model
        parameters (Schema, optional): JSON schema for function parameters
    """
    name: str
    description: str
    parameters: Optional[Schema] = None

class FunctionCall:
    """
    Function invocation from model.

    Attributes:
        name (str): Function name to call
        args (dict[str, Any]): Function arguments
        id (str, optional): Unique call identifier
    """
    name: str
    args: dict[str, Any]
    id: Optional[str] = None

class FunctionResponse:
    """
    Function execution response to send back to model.

    Attributes:
        name (str): Function name that was called
        response (dict[str, Any]): Function return value
        id (str, optional): Call identifier matching FunctionCall.id
    """
    name: str
    response: dict[str, Any]
    id: Optional[str] = None

class ToolConfig:
    """
    Configuration for function calling behavior.

    Attributes:
        function_calling_config (FunctionCallingConfig, optional): Function calling mode
    """
    function_calling_config: Optional[FunctionCallingConfig] = None

class FunctionCallingConfig:
    """
    Function calling mode configuration.

    Attributes:
        mode (FunctionCallingConfigMode): Calling mode (AUTO, ANY, NONE)
        allowed_function_names (list[str], optional): Restrict to specific functions
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
    """
    JSON schema for structured output and function parameters.

    Attributes:
        type (Type): Schema type (OBJECT, ARRAY, STRING, NUMBER, etc.)
        format (str, optional): Format specifier
        description (str, optional): Schema description
        nullable (bool, optional): Whether value can be null
        enum (list[str], optional): Allowed values for enums
        properties (dict[str, Schema], optional): Object properties
        required (list[str], optional): Required property names
        items (Schema, optional): Schema for array items
    """
    type: Type
    format: Optional[str] = None
    description: Optional[str] = None
    nullable: Optional[bool] = None
    enum: Optional[list[str]] = None
    properties: Optional[dict[str, Schema]] = None
    required: Optional[list[str]] = None
    items: Optional[Schema] = None

class Type(Enum):
    """JSON schema types."""
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    INTEGER = 'INTEGER'
    BOOLEAN = 'BOOLEAN'
    ARRAY = 'ARRAY'
    OBJECT = 'OBJECT'
    NULL = 'NULL'

class GoogleSearch:
    """Google Search tool for web grounding."""
    pass

class ToolCodeExecution:
    """Code execution tool for running generated code."""
    pass

class ExecutableCode:
    """
    Executable code from model.

    Attributes:
        language (Language): Programming language
        code (str): Code to execute
    """
    language: Language
    code: str

class CodeExecutionResult:
    """
    Code execution result.

    Attributes:
        outcome (Outcome): Execution outcome (OK, FAILED, DEADLINE_EXCEEDED)
        output (str): Execution output
    """
    outcome: Outcome
    output: str

class Language(Enum):
    """Programming languages for code execution."""
    LANGUAGE_UNSPECIFIED = 'LANGUAGE_UNSPECIFIED'
    PYTHON = 'PYTHON'

class Outcome(Enum):
    """Code execution outcomes."""
    OUTCOME_UNSPECIFIED = 'OUTCOME_UNSPECIFIED'
    OUTCOME_OK = 'OUTCOME_OK'
    OUTCOME_FAILED = 'OUTCOME_FAILED'
    OUTCOME_DEADLINE_EXCEEDED = 'OUTCOME_DEADLINE_EXCEEDED'

# Additional metadata types
class CitationMetadata:
    """
    Citation information for generated content.

    Attributes:
        citations (list[Citation]): List of citations
    """
    citations: list[Citation]

class Citation:
    """
    Individual citation.

    Attributes:
        start_index (int): Start character index in generated text
        end_index (int): End character index in generated text
        uri (str): Citation source URI
        title (str, optional): Citation source title
        license (str, optional): Content license
        publication_date (GoogleTypeDate, optional): Publication date
    """
    start_index: int
    end_index: int
    uri: str
    title: Optional[str] = None
    license: Optional[str] = None
    publication_date: Optional[GoogleTypeDate] = None

class GroundingMetadata:
    """
    Grounding attribution metadata.

    Attributes:
        grounding_chunks (list[GroundingChunk], optional): Grounding sources
        grounding_supports (list[GroundingSupport], optional): Support scores
        web_search_queries (list[str], optional): Web search queries used
        search_entry_point (SearchEntryPoint, optional): Search entry point
    """
    grounding_chunks: Optional[list[GroundingChunk]] = None
    grounding_supports: Optional[list[GroundingSupport]] = None
    web_search_queries: Optional[list[str]] = None
    search_entry_point: Optional[SearchEntryPoint] = None

class GroundingChunk:
    """Grounding source chunk (web, retrieved context, etc.)."""
    pass

class GroundingSupport:
    """
    Grounding support score.

    Attributes:
        segment (Segment): Text segment
        grounding_chunk_indices (list[int]): Indices of supporting chunks
        confidence_scores (list[float]): Confidence scores
    """
    segment: Segment
    grounding_chunk_indices: list[int]
    confidence_scores: list[float]

class SearchEntryPoint:
    """
    Search entry point for web grounding.

    Attributes:
        rendered_content (str): Rendered search content
        sdk_blob (bytes, optional): SDK blob data
    """
    rendered_content: str
    sdk_blob: Optional[bytes] = None

class Segment:
    """
    Content segment.

    Attributes:
        part_index (int): Part index in content
        start_index (int): Start character index
        end_index (int): End character index
        text (str, optional): Segment text
    """
    part_index: int
    start_index: int
    end_index: int
    text: Optional[str] = None

class LogprobsResult:
    """
    Log probabilities result.

    Attributes:
        top_candidates (list[LogprobsResultTopCandidates]): Top candidates per token
        chosen_candidates (list[LogprobsResultCandidate]): Chosen candidates
    """
    top_candidates: list[LogprobsResultTopCandidates]
    chosen_candidates: list[LogprobsResultCandidate]

class LogprobsResultTopCandidates:
    """
    Top candidate tokens and probabilities.

    Attributes:
        candidates (list[LogprobsResultCandidate]): Candidate tokens
    """
    candidates: list[LogprobsResultCandidate]

class LogprobsResultCandidate:
    """
    Individual token candidate.

    Attributes:
        token (str): Token string
        token_id (int): Token ID
        log_probability (float): Log probability
    """
    token: str
    token_id: int
    log_probability: float

class GoogleTypeDate:
    """
    Date representation.

    Attributes:
        year (int): Year
        month (int): Month (1-12)
        day (int): Day (1-31)
    """
    year: int
    month: int
    day: int
```
