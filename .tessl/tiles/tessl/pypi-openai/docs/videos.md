# Videos

Generate and manage videos using video generation models. Create videos from text prompts, retrieve video status, and manage video files.

## Capabilities

### Create Video

Generate a video from a text prompt.

```python { .api }
def create(
    self,
    *,
    prompt: str,
    input_reference: FileTypes | Omit = omit,
    model: VideoModel | Omit = omit,
    seconds: VideoSeconds | Omit = omit,
    size: VideoSize | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video:
    """
    Create a video generation request.

    Args:
        prompt: Text description of the desired video.
        input_reference: Optional image reference that guides generation (FileTypes).
        model: Video model to use (e.g., "sora-2"). Defaults to "sora-2".
        seconds: Clip duration in seconds. Defaults to 4 seconds.
        size: Output resolution formatted as width x height (e.g., "720x1280").
            Defaults to "720x1280".
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Video: Created video object with initial status.
    """
```

### Retrieve Video

Get video status and details.

```python { .api }
def retrieve(
    self,
    video_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video:
    """Retrieve video details and status."""
```

### Poll for Completion

Poll a video until it finishes processing (either completed or failed status).

```python { .api }
def poll(
    self,
    video_id: str,
    *,
    poll_interval_ms: int | Omit = omit,
) -> Video:
    """
    Wait for a video to finish processing.

    This method blocks until the video reaches "completed" or "failed" status.
    It automatically retries with appropriate polling intervals.

    Args:
        video_id: The ID of the video to poll.
        poll_interval_ms: Custom polling interval in milliseconds. If not provided,
            uses server-suggested interval or defaults to 1000ms.

    Returns:
        Video: The video object with final status ("completed" or "failed").

    Note:
        This method returns even if the video failed to process. Check
        video.status and video.error to handle failed cases.
    """
```

### List Videos

List all videos with pagination.

```python { .api }
def list(
    self,
    *,
    after: str | Omit = omit,
    limit: int | Omit = omit,
    order: Literal["asc", "desc"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> SyncConversationCursorPage[Video]:
    """
    List videos with pagination.

    Args:
        after: Identifier for the last item from the previous pagination request.
        limit: Number of items to retrieve.
        order: Sort order by timestamp ("asc" or "desc").
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        SyncConversationCursorPage[Video]: Paginated list of videos.
    """
```

### Delete Video

Delete a video.

```python { .api }
def delete(
    self,
    video_id: str,
    *,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> VideoDeleteResponse:
    """Delete a video."""
```

### Download Video Content

Download the generated video file.

```python { .api }
def download_content(
    self,
    video_id: str,
    *,
    variant: Literal["video", "thumbnail", "spritesheet"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> HttpxBinaryResponseContent:
    """
    Download video content as binary data.

    Args:
        video_id: The ID of the video to download.
        variant: The type of content to download. Options:
            - "video": The full video file (default)
            - "thumbnail": A thumbnail image of the video
            - "spritesheet": A spritesheet of video frames

    Returns:
        HttpxBinaryResponseContent: Binary video file content.
    """
```

### Remix Video

Create a new video by remixing an existing video with a new prompt.

```python { .api }
def remix(
    self,
    video_id: str,
    *,
    prompt: str,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video:
    """
    Create a remix of an existing video with a new prompt.

    Remixing uses the original video's model, duration, and size settings.
    Only the prompt can be changed to create variations.

    Args:
        video_id: The ID of the video to remix.
        prompt: New creative prompt to guide the remix.

    Returns:
        Video: Remix video object (status "queued" initially).
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Create initial video
video = client.videos.create_and_poll(
    prompt="A serene sunset over mountains"
)

# Download the generated video
content = client.videos.download_content(video.id)
with open("sunset.mp4", "wb") as f:
    f.write(content.content)

# Create a remix with different prompt
remix = client.videos.remix(
    video.id,
    prompt="Transform the sunset to a dramatic thunderstorm"
)

# Poll for remix completion
while remix.status != "completed":
    time.sleep(5)
    remix = client.videos.retrieve(remix.id)

# Download remix
remix_content = client.videos.download_content(remix.id)
with open("storm.mp4", "wb") as f:
    f.write(remix_content.content)
```

### Create and Poll

Create video and wait for completion.

```python { .api }
def create_and_poll(
    self,
    *,
    prompt: str,
    input_reference: FileTypes | Omit = omit,
    model: VideoModel | Omit = omit,
    seconds: VideoSeconds | Omit = omit,
    size: VideoSize | Omit = omit,
    poll_interval_ms: int | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Video:
    """
    Create video and poll until generation completes.

    Args:
        prompt: Text description of the desired video.
        input_reference: Optional image reference that guides generation.
        model: Video model to use. Defaults to "sora-2".
        seconds: Clip duration in seconds.
        size: Output resolution.
        poll_interval_ms: Polling interval in milliseconds.
        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Video: Completed video object.
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Create video
video = client.videos.create(
    prompt="A serene mountain landscape at sunset",
    model="sora-2",
    seconds=5,
    size="720x1280"
)

print(f"Video ID: {video.id}")
print(f"Status: {video.status}")

# Create and wait for completion
video = client.videos.create_and_poll(
    prompt="Waves crashing on a beach",
    model="sora-2"
)

print(f"Final status: {video.status}")
if video.status == "completed" and video.url:
    print(f"Video URL: {video.url}")

# Check status
video = client.videos.retrieve("video_abc123")

# List videos
videos = client.videos.list(limit=10)

for video in videos.data:
    print(f"{video.id}: {video.status}")

# Delete video
result = client.videos.delete("video_abc123")
print(f"Deleted: {result.deleted}")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

class Video(BaseModel):
    """Video object."""
    id: str
    created_at: int
    model: str
    prompt: str
    status: Literal["queued", "processing", "completed", "failed"]
    url: str | None  # Available when completed
    error: dict | None  # Present if failed
    duration: int | None
    size: str | None

class VideoDeleteResponse(BaseModel):
    """Deletion confirmation."""
    id: str
    deleted: bool

VideoModel = Literal["sora-2", "sora-2-pro"]
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def create_video():
    client = AsyncOpenAI()

    video = await client.videos.create(
        model="video-gen-1",
        prompt="A futuristic city"
    )

    return video.id

video_id = asyncio.run(create_video())
```
