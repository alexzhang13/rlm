# Multimodal Input Tasks

Practical patterns for working with images, PDFs, and documents. For complete reference, see **[Multimodal Guide](../guides/multimodal.md)**.

## Analyze Image from File

```python
import base64
from anthropic import Anthropic

client = Anthropic()

# Read and encode image
with open("image.jpg", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode()

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            },
            {"type": "text", "text": "What's in this image?"}
        ]
    }]
)

print(message.content[0].text)
```

## Supported Image Formats

```python
# JPEG
with open("photo.jpg", "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()
    source = {"type": "base64", "media_type": "image/jpeg", "data": data}

# PNG
with open("screenshot.png", "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()
    source = {"type": "base64", "media_type": "image/png", "data": data}

# GIF
with open("animation.gif", "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()
    source = {"type": "base64", "media_type": "image/gif", "data": data}

# WebP
with open("image.webp", "rb") as f:
    data = base64.standard_b64encode(f.read()).decode()
    source = {"type": "base64", "media_type": "image/webp", "data": data}
```

## Analyze Multiple Images

Compare or analyze multiple images together:

```python
import base64

def load_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()

img1 = load_image("before.jpg")
img2 = load_image("after.jpg")

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Before:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img1}},
            {"type": "text", "text": "After:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img2}},
            {"type": "text", "text": "What changed between these images?"}
        ]
    }]
)
```

## Optimize Large Images

Reduce token usage by resizing images:

```python
from PIL import Image
import io
import base64

def optimize_image(image_path: str, max_size=(1024, 1024)) -> str:
    """Resize and optimize image for API"""
    img = Image.open(image_path)

    # Resize maintaining aspect ratio
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Convert to JPEG with compression
    buffer = io.BytesIO()
    img = img.convert("RGB")  # Ensure RGB mode
    img.save(buffer, format="JPEG", quality=85, optimize=True)

    return base64.standard_b64encode(buffer.getvalue()).decode()

# Use optimized image
optimized_data = optimize_image("large_photo.jpg")

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": optimized_data}},
            {"type": "text", "text": "Analyze this image"}
        ]
    }]
)
```

## Process PDF Document

```python
import base64

with open("document.pdf", "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode()

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data
                }
            },
            {"type": "text", "text": "Summarize the key points in this document"}
        ]
    }]
)
```

## PDF from URL

Process publicly accessible PDFs without downloading:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "url",
                    "media_type": "application/pdf",
                    "url": "https://example.com/document.pdf"
                }
            },
            {"type": "text", "text": "Extract the main findings"}
        ]
    }]
)
```

## Process Plain Text Document

For large text content:

```python
long_text = """Very long text content..."""

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "text",
                    "media_type": "text/plain",
                    "data": long_text
                }
            },
            {"type": "text", "text": "Analyze the sentiment of this text"}
        ]
    }]
)
```

## Mix Text, Images, and Documents

Combine multiple content types:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Here's a presentation:"},
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data
                }
            },
            {"type": "text", "text": "And the cover image:"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            },
            {"type": "text", "text": "Review both and provide feedback"}
        ]
    }]
)
```

## Common Image Analysis Tasks

### Extract Text (OCR)

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
            {"type": "text", "text": "Extract all text from this image"}
        ]
    }]
)
```

### Identify Objects

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
            {"type": "text", "text": "List all objects visible in this image"}
        ]
    }]
)
```

### Answer Questions About Image

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
            {"type": "text", "text": "Is there a person in this image? If so, describe them."}
        ]
    }]
)
```

## Common Document Tasks

### Summarize Document

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
            {"type": "text", "text": "Provide a 3-paragraph summary"}
        ]
    }]
)
```

### Q&A on Document

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
            {"type": "text", "text": "What methodology was used in this study?"}
        ]
    }]
)
```

### Extract Specific Information

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
            {"type": "text", "text": "Extract all dates, names, and monetary amounts mentioned"}
        ]
    }]
)
```

## Use Citations (Beta)

Get source attribution for document-based responses:

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    citations={"type": "enabled"},
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
            {"type": "text", "text": "Summarize with citations"}
        ]
    }]
)

# Check citations
for block in message.content:
    if hasattr(block, 'citations'):
        for citation in block.citations:
            print(f"Cited: {citation.cited_text}")
```

## Helper Functions

### Load Multiple Images

```python
import base64
from pathlib import Path

def load_images(directory: str) -> list[dict]:
    """Load all images from directory"""
    content = []

    for path in Path(directory).glob("*.{jpg,jpeg,png}"):
        with open(path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode()

        # Determine media type from extension
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png"
        }[path.suffix.lower()]

        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data
            }
        })

    return content

# Use it
images = load_images("./photos")
images.append({"type": "text", "text": "Describe all these images"})

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{"role": "user", "content": images}]
)
```

## See Also

- **[Multimodal Guide](../guides/multimodal.md)** - Complete multimodal documentation
- **[Messages API Reference](../api/messages.md)** - API details
- **[Beta Citations](../beta/message-features.md#citations)** - Source attribution feature
