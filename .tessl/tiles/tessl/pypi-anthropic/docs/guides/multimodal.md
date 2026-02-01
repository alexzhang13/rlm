# Multimodal Content Guide

Working with images, documents, and PDFs in Claude conversations.

## Image Input

### Base64 Images

```python
import base64

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
            {"type": "text", "text": "Describe this image"}
        ]
    }]
)
```

### Supported Image Formats

```python { .api }
# Supported MIME types
"image/jpeg"
"image/png"
"image/gif"
"image/webp"
```

### Multiple Images

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img1}},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img2}},
            {"type": "text", "text": "Compare these images"}
        ]
    }]
)
```

## PDF Documents

### Base64 PDF

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
            {"type": "text", "text": "Summarize this document"}
        ]
    }]
)
```

### PDF URL

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
            {"type": "text", "text": "Summarize this document"}
        ]
    }]
)
```

## Plain Text Documents

```python
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
                    "data": "Long text content..."
                }
            },
            {"type": "text", "text": "Analyze this text"}
        ]
    }]
)
```

## Mixed Content

Combine text, images, and documents:

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Review this presentation:"},
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
            {"type": "text", "text": "Here's the cover image:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_data}},
            {"type": "text", "text": "What are the key points?"}
        ]
    }]
)
```

## Image Analysis Tasks

### Object Detection

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {...}},
            {"type": "text", "text": "List all objects visible in this image"}
        ]
    }]
)
```

### Text Extraction (OCR)

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {...}},
            {"type": "text", "text": "Extract all text from this image"}
        ]
    }]
)
```

### Image Comparison

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Before:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": before_img}},
            {"type": "text", "text": "After:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": after_img}},
            {"type": "text", "text": "What changed?"}
        ]
    }]
)
```

## Document Analysis Tasks

### Summarization

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {...}},
            {"type": "text", "text": "Provide a brief summary"}
        ]
    }]
)
```

### Q&A on Documents

```python
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {...}},
            {"type": "text", "text": "What is the main conclusion?"}
        ]
    }]
)
```

### Citation Support (Beta)

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    citations={"type": "enabled"},
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {...}},
            {"type": "text", "text": "Summarize with citations"}
        ]
    }]
)

for block in message.content:
    if hasattr(block, 'citations'):
        for citation in block.citations:
            print(f"Citation: {citation.cited_text}")
```

## Best Practices

### 1. Optimize Image Size

```python
from PIL import Image
import io
import base64

def optimize_image(image_path, max_size=(1024, 1024)):
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.standard_b64encode(buffer.getvalue()).decode()

optimized_data = optimize_image("large_image.jpg")
```

### 2. Handle Large PDFs

For very large PDFs, consider splitting or summarizing sections.

### 3. Specify Context

Always provide clear instructions about what you want from the content.

## See Also

- [Messages API](../api/messages.md) - Content block types
- [Beta Features](../beta/index.md) - Citations feature
- [Getting Started](./getting-started.md) - Basic usage
