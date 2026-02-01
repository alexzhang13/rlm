# Video Generation

Generate videos from text prompts, images, or existing videos using Veo models. Video generation is a long-running operation that returns immediately with an operation handle that can be polled for completion status.

## Capabilities

### Generate Videos

Generate videos from text prompts, optionally with reference images or videos. Returns a long-running operation that must be polled for completion.

```python { .api }
def generate_videos(
    *,
    model: str,
    prompt: Optional[str] = None,
    image: Optional[Image] = None,
    video: Optional[Video] = None,
    config: Optional[GenerateVideosConfig] = None
) -> GenerateVideosOperation:
    """
    Generate videos (returns long-running operation).

    Parameters:
        model (str): Model identifier (e.g., 'veo-2.0-generate-001', 'veo-001').
        prompt (str, optional): Text description of the video to generate. At least one
            of prompt, image, or video must be provided.
        image (Image, optional): Reference image for image-to-video generation.
        video (Video, optional): Reference video for video-to-video generation.
        config (GenerateVideosConfig, optional): Generation configuration including:
            - aspect_ratio: Video aspect ratio ('16:9', '9:16', '1:1')
            - duration: Video duration in seconds
            - negative_prompt: What to avoid
            - safety_filter_level: Safety filtering level
            - person_generation: Control person generation
            - compressed: Use compressed output format

    Returns:
        GenerateVideosOperation: Long-running operation handle. Use client.operations.get()
            to poll for completion and retrieve the generated videos.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def generate_videos(
    *,
    model: str,
    prompt: Optional[str] = None,
    image: Optional[Image] = None,
    video: Optional[Video] = None,
    config: Optional[GenerateVideosConfig] = None
) -> GenerateVideosOperation:
    """Async version of generate_videos."""
    ...
```

**Usage Example - Text to Video:**

```python
import time
from google.genai import Client
from google.genai.types import GenerateVideosConfig

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Start video generation
config = GenerateVideosConfig(
    aspect_ratio='16:9',
    duration=5,  # 5 seconds
    negative_prompt='blurry, low quality'
)

operation = client.models.generate_videos(
    model='veo-2.0-generate-001',
    prompt='A dog running through a field of flowers at sunset',
    config=config
)

print(f"Operation started: {operation.name}")

# Poll for completion
while True:
    operation = client.operations.get(operation)

    if operation.done:
        if operation.error:
            print(f"Error: {operation.error}")
        else:
            response = operation.response
            print(f"Generated {len(response.generated_videos)} video(s)")

            # Save videos
            for i, video in enumerate(response.generated_videos):
                with open(f'generated_{i}.mp4', 'wb') as f:
                    f.write(video.video.data)
        break

    print("Still generating...")
    time.sleep(10)  # Wait 10 seconds before polling again
```

**Usage Example - Image to Video:**

```python
from google.genai import Client
from google.genai.types import Image, GenerateVideosConfig

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Load reference image
image = Image.from_file('landscape.jpg')

config = GenerateVideosConfig(
    aspect_ratio='16:9',
    duration=8
)

# Generate video from image
operation = client.models.generate_videos(
    model='veo-2.0-generate-001',
    prompt='Camera slowly pans across the landscape',
    image=image,
    config=config
)

print(f"Operation: {operation.name}")
# Poll operation.done until complete
```

**Usage Example - Async with Polling:**

```python
import asyncio
from google.genai import Client

async def generate_and_wait():
    client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

    # Start generation
    operation = await client.aio.models.generate_videos(
        model='veo-2.0-generate-001',
        prompt='A cat playing with a ball of yarn'
    )

    print(f"Started operation: {operation.name}")

    # Poll until complete
    while not operation.done:
        await asyncio.sleep(10)
        operation = await client.aio.operations.get(operation)
        print("Checking status...")

    if operation.error:
        print(f"Error: {operation.error}")
    else:
        print(f"Success! {len(operation.response.generated_videos)} videos generated")

asyncio.run(generate_and_wait())
```

## Types

```python { .api }
from typing import Optional, Literal, TypedDict
from enum import Enum

# Configuration types
class GenerateVideosConfig:
    """
    Configuration for video generation.

    Attributes:
        aspect_ratio (str, optional): Video aspect ratio. Options: '16:9', '9:16', '1:1'.
            Default varies by model.
        duration (int, optional): Video duration in seconds. Valid range depends on model.
            Typical: 4-8 seconds.
        negative_prompt (str, optional): What to avoid in the video.
        safety_filter_level (str, optional): Safety filtering level ('block_most', 'block_some', 'block_few').
        person_generation (PersonGeneration, optional): Control person generation in video.
        compressed (bool, optional): Use compressed output format for smaller file size.
        generation_mode (str, optional): Generation mode (e.g., 'fast', 'quality').
    """
    aspect_ratio: Optional[str] = None
    duration: Optional[int] = None
    negative_prompt: Optional[str] = None
    safety_filter_level: Optional[str] = None
    person_generation: Optional[PersonGeneration] = None
    compressed: Optional[bool] = None
    generation_mode: Optional[str] = None

# Response types
class GenerateVideosResponse:
    """
    Response from completed video generation.

    Accessed via operation.response after operation completes.

    Attributes:
        generated_videos (list[GeneratedVideo]): Generated videos with metadata.
        rai_media_filtered_count (int, optional): Number of videos filtered by safety.
        rai_media_filtered_reasons (list[str], optional): Safety filtering reasons.
    """
    generated_videos: list[GeneratedVideo]
    rai_media_filtered_count: Optional[int] = None
    rai_media_filtered_reasons: Optional[list[str]] = None

class GeneratedVideo:
    """
    Generated video with metadata.

    Attributes:
        video (Video): Video object with data.
        generation_seed (int, optional): Seed used for generation (for reproducibility).
    """
    video: Video
    generation_seed: Optional[int] = None

# Operation types
class GenerateVideosOperation:
    """
    Long-running operation for video generation.

    Attributes:
        name (str): Operation name/identifier for polling.
        done (bool): Whether operation is complete.
        error (OperationError, optional): Error if operation failed.
        response (GenerateVideosResponse, optional): Response if operation succeeded.
        metadata (dict, optional): Operation metadata including progress.
    """
    name: str
    done: bool
    error: Optional[OperationError] = None
    response: Optional[GenerateVideosResponse] = None
    metadata: Optional[dict] = None

class OperationError:
    """
    Operation error information.

    Attributes:
        code (int): Error code.
        message (str): Error message.
        details (list, optional): Additional error details.
    """
    code: int
    message: str
    details: Optional[list] = None

# Input types
class Video:
    """
    Video data supporting multiple formats.

    Can be created from:
        - File: Video.from_file('path.mp4')
        - URL: Video.from_url('https://...')
        - Bytes: Video.from_bytes(data, mime_type='video/mp4')
        - FileData: Video(file_data=FileData(...))

    Attributes:
        data (bytes, optional): Video binary data.
        mime_type (str, optional): MIME type (e.g., 'video/mp4').
        file_data (FileData, optional): Reference to uploaded file.
    """
    data: Optional[bytes] = None
    mime_type: Optional[str] = None
    file_data: Optional[FileData] = None

    @staticmethod
    def from_file(path: str) -> Video:
        """Load video from file path."""
        ...

    @staticmethod
    def from_url(url: str) -> Video:
        """Load video from URL."""
        ...

    @staticmethod
    def from_bytes(data: bytes, mime_type: str) -> Video:
        """Create video from bytes."""
        ...

class Image:
    """Image data for image-to-video generation."""
    @staticmethod
    def from_file(path: str) -> Image: ...

class FileData:
    """
    Reference to uploaded file.

    Attributes:
        file_uri (str): URI (e.g., 'gs://bucket/file')
        mime_type (str): MIME type
    """
    file_uri: str
    mime_type: str

# Enum types
class PersonGeneration(Enum):
    """Person generation control."""
    DONT_ALLOW = 'dont_allow'
    ALLOW_ADULT = 'allow_adult'
    ALLOW_ALL = 'allow_all'

# TypedDict variants
class GenerateVideosConfigDict(TypedDict, total=False):
    """TypedDict variant of GenerateVideosConfig."""
    aspect_ratio: str
    duration: int
    negative_prompt: str
    safety_filter_level: str
    person_generation: PersonGeneration
    compressed: bool
    generation_mode: str
```
