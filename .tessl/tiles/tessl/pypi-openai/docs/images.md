# Images

Generate, edit, and create variations of images using DALL-E models. Supports creating images from text prompts, editing existing images with masks, and generating variations.

## Capabilities

### Generate Images

Create images from text descriptions using DALL-E or GPT-Image-1 models.

```python { .api }
def generate(
    self,
    *,
    prompt: str,
    background: Literal["transparent", "opaque", "auto"] | Omit = omit,
    model: str | ImageModel | Omit = omit,
    moderation: Literal["low", "auto"] | Omit = omit,
    n: int | Omit = omit,
    output_compression: int | Omit = omit,
    output_format: Literal["png", "jpeg", "webp"] | Omit = omit,
    partial_images: int | Omit = omit,
    quality: Literal["standard", "hd", "low", "medium", "high", "auto"] | Omit = omit,
    response_format: Literal["url", "b64_json"] | Omit = omit,
    size: Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"] | Omit = omit,
    stream: bool | Omit = omit,
    style: Literal["vivid", "natural"] | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ImagesResponse | Stream[ImageGenStreamEvent]:
    """
    Generate images from text prompts.

    Args:
        prompt: Text description of the desired image(s). Max length:
            - gpt-image-1: 32000 characters
            - dall-e-3: 4000 characters
            - dall-e-2: 1000 characters

        background: (gpt-image-1 only) Background transparency control. Options:
            - "transparent": Transparent background (requires png or webp output)
            - "opaque": Opaque background
            - "auto": Model determines best option (default)

        model: Model to use. Options:
            - "dall-e-3": Latest DALL-E, highest quality
            - "dall-e-2": Previous DALL-E generation
            - "gpt-image-1": Latest generation model with advanced features
            Defaults to dall-e-2 unless gpt-image-1 specific parameters are used.

        moderation: (gpt-image-1 only) Content moderation level. Options:
            - "auto": Standard filtering (default)
            - "low": Less restrictive filtering

        n: Number of images to generate. Default 1.
            - gpt-image-1: Supports 1-10
            - dall-e-3: Only supports n=1
            - dall-e-2: Supports 1-10

        output_compression: (gpt-image-1 only) Compression level (0-100%) for webp or jpeg
            output formats. Default 100. Higher values = better quality, larger file size.

        output_format: (gpt-image-1 only) Output image format. Options:
            - "png": PNG format (default), supports transparency
            - "jpeg": JPEG format, smaller files, no transparency
            - "webp": WebP format, good compression with quality

        partial_images: (gpt-image-1 only) Number of partial images for streaming (0-3).
            Set to 0 for single final image. Default returns progressive partial images.
            Final image may arrive before all partials if generation completes quickly.

        quality: Image quality. Options depend on model:
            - gpt-image-1: "auto" (default), "high", "medium", "low"
            - dall-e-3: "standard" (default), "hd"
            - dall-e-2: Only "standard"

        response_format: Response data format. Options:
            - "url": Returns URL (default), expires after 1 hour (dall-e-2 and dall-e-3 only)
            - "b64_json": Returns base64-encoded JSON
            Note: gpt-image-1 always returns base64-encoded images.

        size: Image dimensions. Options depend on model:
            - gpt-image-1: "auto" (default), "1024x1024", "1536x1024", "1024x1536"
            - dall-e-3: "1024x1024", "1792x1024", "1024x1792"
            - dall-e-2: "256x256", "512x512", "1024x1024"

        stream: (gpt-image-1 only) If true, returns Stream[ImageGenStreamEvent] for
            progressive image generation. Set partial_images to control streaming behavior.

        style: Visual style. Only for dall-e-3. Options:
            - "vivid": Hyper-real and dramatic (default)
            - "natural": More natural, less hyper-real

        user: Unique end-user identifier for abuse monitoring.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ImagesResponse: Contains generated image(s) when stream=False.
        Stream[ImageGenStreamEvent]: Streaming events when stream=True (gpt-image-1 only).

    Raises:
        BadRequestError: Invalid parameters or prompt violates content policy
        RateLimitError: Rate limit exceeded
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic image generation
response = client.images.generate(
    model="dall-e-3",
    prompt="A cute baby sea otter wearing a beret",
    n=1,
    size="1024x1024"
)

image_url = response.data[0].url
print(f"Image URL: {image_url}")

# HD quality
response = client.images.generate(
    model="dall-e-3",
    prompt="A serene mountain landscape at sunset",
    quality="hd",
    size="1792x1024"
)

# Natural style
response = client.images.generate(
    model="dall-e-3",
    prompt="A portrait of a programmer at work",
    style="natural"
)

# Base64 response (no expiration)
response = client.images.generate(
    model="dall-e-3",
    prompt="A futuristic cityscape",
    response_format="b64_json"
)

import base64
from pathlib import Path

# Save base64 image
image_data = base64.b64decode(response.data[0].b64_json)
Path("generated_image.png").write_bytes(image_data)

# Download from URL
import requests

response = client.images.generate(
    model="dall-e-3",
    prompt="A cat playing chess"
)

image_url = response.data[0].url
image_response = requests.get(image_url)
Path("cat_chess.png").write_bytes(image_response.content)

# Multiple images with DALL-E 2
response = client.images.generate(
    model="dall-e-2",
    prompt="Abstract art with geometric shapes",
    n=4,
    size="512x512"
)

for i, image in enumerate(response.data):
    print(f"Image {i+1}: {image.url}")

# Check revised prompt (DALL-E 3 may modify prompts)
response = client.images.generate(
    model="dall-e-3",
    prompt="A dog"
)

print(f"Original prompt: A dog")
print(f"Revised prompt: {response.data[0].revised_prompt}")
```

### Edit Images

Modify an existing image using a mask and text prompt. Supports both DALL-E 2 and GPT-Image-1 models.

```python { .api }
def edit(
    self,
    *,
    image: FileTypes | list[FileTypes],
    prompt: str,
    background: Literal["transparent", "opaque", "auto"] | Omit = omit,
    input_fidelity: Literal["high", "low"] | Omit = omit,
    mask: FileTypes | Omit = omit,
    model: str | ImageModel | Omit = omit,
    n: int | Omit = omit,
    output_compression: int | Omit = omit,
    output_format: Literal["png", "jpeg", "webp"] | Omit = omit,
    partial_images: int | Omit = omit,
    quality: Literal["standard", "low", "medium", "high", "auto"] | Omit = omit,
    response_format: Literal["url", "b64_json"] | Omit = omit,
    size: Literal["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "auto"] | Omit = omit,
    stream: bool | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ImagesResponse | Stream[ImageEditStreamEvent]:
    """
    Edit or extend an image using a mask and prompt. Supports dall-e-2 and gpt-image-1.

    Args:
        image: Image(s) to edit.
            - dall-e-2: Single PNG image, must be square, less than 4MB
            - gpt-image-1: Single image or list of up to 16 images (png/webp/jpg), less than 50MB each
            Transparent areas indicate where to edit if no mask provided.

        prompt: Text description of desired edits.
            - dall-e-2: Max 1000 characters
            - gpt-image-1: Max 32000 characters

        background: (gpt-image-1 only) Background transparency control. Options:
            - "transparent": Transparent background (requires png or webp output)
            - "opaque": Opaque background
            - "auto": Model determines best option (default)

        input_fidelity: (gpt-image-1 only, not supported for gpt-image-1-mini) Control how much
            the model matches input image style and features, especially facial features. Options:
            - "low": Less strict matching (default)
            - "high": Stricter matching of input features

        mask: Optional mask image. Must be PNG, same dimensions as image, less than 4MB.
            Fully transparent areas (alpha=0) indicate where to edit. If multiple input images
            are provided, mask applies to the first image.

        model: Model to use. Options:
            - "dall-e-2": Original model, limited features
            - "gpt-image-1": Latest model with advanced features (default if gpt-image-1
              specific parameters are used)

        n: Number of variations to generate (1-10). Default 1.

        output_compression: (gpt-image-1 only) Compression level (0-100%) for webp or jpeg
            output formats. Default 100. Higher values = better quality, larger file size.

        output_format: (gpt-image-1 only) Output image format. Options:
            - "png": PNG format (default), supports transparency
            - "jpeg": JPEG format, smaller files, no transparency
            - "webp": WebP format, good compression with quality

        partial_images: (gpt-image-1 only) Number of partial images for streaming (0-3).
            Set to 0 for single final image. Default returns progressive partial images.
            Final image may arrive before all partials if generation completes quickly.

        quality: (gpt-image-1 only) Output quality level. Options:
            - "standard": Standard quality
            - "low": Lower quality, faster
            - "medium": Medium quality
            - "high": High quality, slower
            - "auto": Model determines best quality

        response_format: Response data format. Options:
            - "url": Returns URL (default), expires after 1 hour
            - "b64_json": Returns base64-encoded JSON

        size: Output dimensions. Options:
            - dall-e-2: "256x256", "512x512", "1024x1024" (default)
            - gpt-image-1: Same as dall-e-2 plus "1536x1024", "1024x1536", "auto"

        stream: (gpt-image-1 only) If true, returns Stream[ImageEditStreamEvent] for
            progressive image generation. Set partial_images to control streaming behavior.

        user: Unique end-user identifier for abuse monitoring.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ImagesResponse: Contains edited image(s) when stream=False.
        Stream[ImageEditStreamEvent]: Streaming events when stream=True (gpt-image-1 only).

    Raises:
        BadRequestError: Invalid image format, size, or prompt
    """
```

Usage examples:

```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

# Basic edit with DALL-E 2
with open("base_image.png", "rb") as image_file, \
     open("mask.png", "rb") as mask_file:

    response = client.images.edit(
        image=image_file,
        mask=mask_file,
        prompt="Add a red hat",
        model="dall-e-2",
        n=1,
        size="1024x1024"
    )

# Save result
import requests
image_url = response.data[0].url
image_data = requests.get(image_url).content
Path("edited_image.png").write_bytes(image_data)

# Edit with GPT-Image-1 - multiple images
with open("image1.png", "rb") as img1, \
     open("image2.png", "rb") as img2:

    response = client.images.edit(
        image=[img1, img2],  # Multiple images for context
        prompt="Blend these images together with a sunset background",
        model="gpt-image-1",
        output_format="webp",
        quality="high",
        background="auto"
    )

# GPT-Image-1 with high input fidelity
with open("portrait.png", "rb") as image_file:
    response = client.images.edit(
        image=image_file,
        prompt="Change the background to a beach scene, keep facial features",
        model="gpt-image-1",
        input_fidelity="high",  # Preserve facial features
        output_format="png",
        size="1536x1024"
    )

# GPT-Image-1 with transparent background
with open("object.png", "rb") as image_file:
    response = client.images.edit(
        image=image_file,
        prompt="Remove the background",
        model="gpt-image-1",
        background="transparent",
        output_format="png"  # Must use png or webp for transparency
    )

# Streaming edit with GPT-Image-1
with open("base_image.png", "rb") as image_file:
    stream = client.images.edit(
        image=image_file,
        prompt="Add dramatic lighting",
        model="gpt-image-1",
        stream=True,
        partial_images=3  # Get 3 progressive partial images
    )

    for event in stream:
        if event.type == "image":
            print(f"Received image chunk: {len(event.data)} bytes")
        elif event.type == "done":
            print("Final image complete")

# Compressed output for web use
with open("large_image.png", "rb") as image_file:
    response = client.images.edit(
        image=image_file,
        prompt="Enhance colors",
        model="gpt-image-1",
        output_format="webp",
        output_compression=85,  # 85% quality for smaller file size
        quality="medium"
    )

# Edit using transparency (no mask) - works with both models
with open("image_with_transparency.png", "rb") as image_file:
    response = client.images.edit(
        image=image_file,
        prompt="Fill transparent areas with flowers"
    )
```

### Create Variations

Generate variations of an existing image (DALL-E 2 only).

```python { .api }
def create_variation(
    self,
    *,
    image: FileTypes,
    model: str | ImageModel | Omit = omit,
    n: int | Omit = omit,
    response_format: Literal["url", "b64_json"] | Omit = omit,
    size: Literal["256x256", "512x512", "1024x1024"] | Omit = omit,
    user: str | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ImagesResponse:
    """
    Create variations of an existing image. Only supports dall-e-2.

    Args:
        image: Base image for variations. Must be valid PNG, less than 4MB, and square.

        model: Model to use. Only "dall-e-2" is supported for variations.

        n: Number of variations to generate (1-10). Default 1.

        response_format: Output format.
            - "url": Returns URL (default), expires after 1 hour
            - "b64_json": Returns base64-encoded JSON

        size: Output dimensions. Options: "256x256", "512x512", "1024x1024".
            Default "1024x1024".

        user: Unique end-user identifier.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ImagesResponse: Contains variation image(s).

    Raises:
        BadRequestError: Invalid image format or size
    """
```

Usage example:

```python
from openai import OpenAI
import requests
from pathlib import Path

client = OpenAI()

# Create multiple variations
with open("base_image.png", "rb") as image_file:
    response = client.images.create_variation(
        image=image_file,
        n=3,
        size="1024x1024"
    )

# Save all variations
for i, image in enumerate(response.data):
    image_data = requests.get(image.url).content
    Path(f"variation_{i+1}.png").write_bytes(image_data)

# Base64 format
with open("base_image.png", "rb") as image_file:
    response = client.images.create_variation(
        image=image_file,
        response_format="b64_json"
    )

import base64
image_data = base64.b64decode(response.data[0].b64_json)
Path("variation.png").write_bytes(image_data)
```

## Types

```python { .api }
from typing import Literal, Union
from pydantic import BaseModel

class ImagesResponse(BaseModel):
    """Response from image endpoints."""
    created: int
    data: list[Image]

class Image(BaseModel):
    """Single generated/edited image."""
    url: str | None  # Present when response_format="url"
    b64_json: str | None  # Present when response_format="b64_json"
    revised_prompt: str | None  # Only for dall-e-3 generations

class ImageEditStreamEvent(BaseModel):
    """Streaming event from images.edit() with stream=True (gpt-image-1 only)."""
    type: Literal["image", "done", "error"]
    data: bytes | None  # Image data for type="image"
    error: str | None  # Error message for type="error"

class ImageGenStreamEvent(BaseModel):
    """Streaming event from images.generate() with stream=True (gpt-image-1 only)."""
    type: Literal["image", "done", "error"]
    data: bytes | None  # Image data for type="image"
    error: str | None  # Error message for type="error"

# Model types
ImageModel = Literal["dall-e-2", "dall-e-3", "gpt-image-1", "gpt-image-1-mini"]

# File types
FileTypes = Union[
    FileContent,  # File-like object
    tuple[str | None, FileContent],  # (filename, content)
    tuple[str | None, FileContent, str | None]  # (filename, content, content_type)
]
```

## Model Comparison

| Feature | DALL-E 3 | GPT-Image-1 | DALL-E 2 |
|---------|----------|-------------|----------|
| Generation Quality | Highest | Very High | Good |
| Max Prompt Length (generate) | 4000 chars | N/A | 1000 chars |
| Max Prompt Length (edit) | N/A | 32000 chars | 1000 chars |
| Images per Request (generate) | 1 only | N/A | 1-10 |
| Images per Request (edit) | N/A | Up to 16 input | 1 input |
| Generation Sizes | 1024x1024, 1792x1024, 1024x1792 | N/A | 256x256, 512x512, 1024x1024 |
| Edit Sizes | N/A | 256x256-1536x1024, auto | 256x256-1024x1024 |
| Quality Options | standard, hd | standard, low, medium, high, auto | N/A |
| Style Options | vivid, natural | N/A | N/A |
| Prompt Revision | Yes | N/A | No |
| Image Generation | Yes | No | Yes |
| Image Editing | No | Yes | Yes |
| Variations | No | No | Yes |
| Multiple Input Images | N/A | Yes (up to 16) | No |
| Output Formats | png | png, jpeg, webp | png |
| Transparency Control | N/A | Yes | Limited |
| Input Fidelity Control | N/A | Yes | No |
| Streaming Support | No | Yes | No |
| Compression Control | No | Yes | No |

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Use detailed, specific prompts
response = client.images.generate(
    model="dall-e-3",
    prompt="A photorealistic portrait of a golden retriever wearing "
           "aviator sunglasses, sitting in a red vintage convertible, "
           "with a sunny beach in the background, shot on 35mm film"
)

# 2. Check revised prompts (DALL-E 3)
response = client.images.generate(
    model="dall-e-3",
    prompt="A dog"
)
print(f"Revised: {response.data[0].revised_prompt}")

# 3. Use appropriate quality for use case
# Standard for drafts/iterations
response = client.images.generate(
    model="dall-e-3",
    prompt="Concept art",
    quality="standard"
)

# HD for final production
response = client.images.generate(
    model="dall-e-3",
    prompt="Final poster design",
    quality="hd"
)

# 4. Handle errors gracefully
from openai import BadRequestError

try:
    response = client.images.generate(
        prompt="inappropriate content"
    )
except BadRequestError as e:
    if "content_policy_violation" in str(e):
        print("Prompt violated content policy")
    else:
        print(f"Error: {e}")
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def generate_image():
    client = AsyncOpenAI()

    response = await client.images.generate(
        model="dall-e-3",
        prompt="A futuristic robot",
        size="1024x1024"
    )

    return response.data[0].url

# Run async
image_url = asyncio.run(generate_image())
```
