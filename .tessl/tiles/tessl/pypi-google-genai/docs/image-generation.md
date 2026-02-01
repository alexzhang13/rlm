# Image Generation

Generate, edit, upscale, and segment images using Imagen models. Provides comprehensive image generation and manipulation capabilities including text-to-image generation, image editing with masks, upscaling for enhanced resolution, image recontextualization, and semantic segmentation.

## Capabilities

### Generate Images

Generate images from text prompts using Imagen models. Supports various aspect ratios, safety filtering, and configuration options.

```python { .api }
def generate_images(
    *,
    model: str,
    prompt: str,
    config: Optional[GenerateImagesConfig] = None
) -> GenerateImagesResponse:
    """
    Generate images from a text prompt.

    Parameters:
        model (str): Model identifier (e.g., 'imagen-3.0-generate-001', 'imagen-3.0-fast-generate-001').
        prompt (str): Text description of the image to generate. More detailed prompts
            typically produce better results.
        config (GenerateImagesConfig, optional): Generation configuration including:
            - number_of_images: Number of images to generate (1-8)
            - aspect_ratio: Image aspect ratio ('1:1', '16:9', '9:16', '4:3', '3:4')
            - negative_prompt: What to avoid in the image
            - safety_filter_level: Safety filtering level
            - person_generation: Control person generation in images
            - language: Language of the prompt

    Returns:
        GenerateImagesResponse: Response containing generated images and metadata.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def generate_images(
    *,
    model: str,
    prompt: str,
    config: Optional[GenerateImagesConfig] = None
) -> GenerateImagesResponse:
    """Async version of generate_images."""
    ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import GenerateImagesConfig

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

config = GenerateImagesConfig(
    number_of_images=4,
    aspect_ratio='16:9',
    negative_prompt='blurry, low quality',
    safety_filter_level='block_some'
)

response = client.models.generate_images(
    model='imagen-3.0-generate-001',
    prompt='A serene mountain landscape at sunset with a lake',
    config=config
)

for i, image in enumerate(response.generated_images):
    image.pil_image.save(f'generated_{i}.png')
```

### Edit Image

Edit existing images using text prompts and optional masks to specify editing regions.

```python { .api }
def edit_image(
    *,
    model: str,
    prompt: str,
    reference_images: Sequence[ReferenceImage],
    config: Optional[EditImageConfig] = None
) -> EditImageResponse:
    """
    Edit an image using a text prompt and reference images.

    Parameters:
        model (str): Model identifier (e.g., 'imagen-3.0-capability-001').
        prompt (str): Text description of desired edits.
        reference_images (Sequence[ReferenceImage]): Reference images for editing.
            Can include base image, mask image, and control images.
        config (EditImageConfig, optional): Editing configuration including:
            - number_of_images: Number of edited variations
            - negative_prompt: What to avoid
            - edit_mode: Editing mode (INPAINT, OUTPAINT, etc.)
            - mask_mode: Mask interpretation mode
            - mask_dilation: Mask dilation amount
            - guidance_scale: Prompt adherence strength
            - safety_filter_level: Safety filtering

    Returns:
        EditImageResponse: Response containing edited images.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def edit_image(
    *,
    model: str,
    prompt: str,
    reference_images: Sequence[ReferenceImage],
    config: Optional[EditImageConfig] = None
) -> EditImageResponse:
    """Async version of edit_image."""
    ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import (
    EditImageConfig,
    ReferenceImage,
    Image,
    EditMode
)

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

# Load images
base_image = Image.from_file('photo.jpg')
mask_image = Image.from_file('mask.png')  # White areas will be edited

reference_images = [
    ReferenceImage(reference_type='reference_image', reference_image=base_image),
    ReferenceImage(reference_type='mask_image', reference_image=mask_image)
]

config = EditImageConfig(
    number_of_images=2,
    edit_mode=EditMode.INPAINT_INSERTION,
    negative_prompt='distorted, blurry'
)

response = client.models.edit_image(
    model='imagen-3.0-capability-001',
    prompt='A red sports car',
    reference_images=reference_images,
    config=config
)

for i, image in enumerate(response.generated_images):
    image.pil_image.save(f'edited_{i}.png')
```

### Upscale Image

Upscale images to higher resolutions while preserving quality and details.

```python { .api }
def upscale_image(
    *,
    model: str,
    image: Image,
    upscale_factor: str,
    config: Optional[UpscaleImageConfig] = None
) -> UpscaleImageResponse:
    """
    Upscale an image to higher resolution.

    Parameters:
        model (str): Model identifier (e.g., 'imagen-3.0-capability-001').
        image (Image): Image to upscale.
        upscale_factor (str): Upscaling factor ('x2' or 'x4').
        config (UpscaleImageConfig, optional): Upscaling configuration including:
            - number_of_images: Number of upscaled variations
            - safety_filter_level: Safety filtering level

    Returns:
        UpscaleImageResponse: Response containing upscaled images.

    Raises:
        ClientError: For client errors (4xx status codes)
        ServerError: For server errors (5xx status codes)
    """
    ...

async def upscale_image(
    *,
    model: str,
    image: Image,
    upscale_factor: str,
    config: Optional[UpscaleImageConfig] = None
) -> UpscaleImageResponse:
    """Async version of upscale_image."""
    ...
```

**Usage Example:**

```python
from google.genai import Client
from google.genai.types import Image, UpscaleImageConfig

client = Client(vertexai=True, project='PROJECT_ID', location='us-central1')

image = Image.from_file('low_res.jpg')

config = UpscaleImageConfig(
    number_of_images=1
)

response = client.models.upscale_image(
    model='imagen-3.0-capability-001',
    image=image,
    upscale_factor='x4',
    config=config
)

response.generated_images[0].pil_image.save('upscaled_4x.png')
```

### Recontext Image

Recontextualize product images by changing their backgrounds or settings while preserving the main subject.

```python { .api }
def recontext_image(
    *,
    model: str,
    prompt: str,
    source: RecontextImageSource,
    config: Optional[RecontextImageConfig] = None
) -> RecontextImageResponse:
    """
    Recontextualize a product image with a new background.

    Parameters:
        model (str): Model identifier (e.g., 'imagen-3.0-capability-001').
        prompt (str): Description of the new context/background.
        source (RecontextImageSource): Source containing product image and optional mask.
        config (RecontextImageConfig, optional): Configuration including:
            - number_of_images: Number of variations
            - negative_prompt: What to avoid
            - safety_filter_level: Safety filtering

    Returns:
        RecontextImageResponse: Response with recontextualized images.
    """
    ...

async def recontext_image(
    *,
    model: str,
    prompt: str,
    source: RecontextImageSource,
    config: Optional[RecontextImageConfig] = None
) -> RecontextImageResponse:
    """Async version of recontext_image."""
    ...
```

### Segment Image

Perform semantic segmentation on images to identify and isolate different objects and regions.

```python { .api }
def segment_image(
    *,
    model: str,
    source: SegmentImageSource,
    config: Optional[SegmentImageConfig] = None
) -> SegmentImageResponse:
    """
    Segment an image to identify objects and regions.

    Parameters:
        model (str): Model identifier (e.g., 'imagen-3.0-capability-001').
        source (SegmentImageSource): Source image and optional entity labels.
        config (SegmentImageConfig, optional): Segmentation configuration including:
            - segment_mode: Segmentation mode (FOREGROUND, ENTITY)

    Returns:
        SegmentImageResponse: Response with segmentation masks.
    """
    ...

async def segment_image(
    *,
    model: str,
    source: SegmentImageSource,
    config: Optional[SegmentImageConfig] = None
) -> SegmentImageResponse:
    """Async version of segment_image."""
    ...
```

## Types

```python { .api }
from typing import Optional, List, Sequence, Literal
from enum import Enum
import PIL.Image

# Configuration types
class GenerateImagesConfig:
    """
    Configuration for image generation.

    Attributes:
        number_of_images (int, optional): Number of images to generate (1-8). Default: 1.
        aspect_ratio (str, optional): Aspect ratio ('1:1', '16:9', '9:16', '4:3', '3:4'). Default: '1:1'.
        negative_prompt (str, optional): What to avoid in generated images.
        safety_filter_level (str, optional): Safety filtering ('block_most', 'block_some', 'block_few').
        person_generation (PersonGeneration, optional): Control person generation.
        include_safety_attributes (bool, optional): Include safety attributes in response.
        language (str, optional): Language of the prompt.
        add_watermark (bool, optional): Add watermark to images.
    """
    number_of_images: Optional[int] = None
    aspect_ratio: Optional[str] = None
    negative_prompt: Optional[str] = None
    safety_filter_level: Optional[str] = None
    person_generation: Optional[PersonGeneration] = None
    include_safety_attributes: Optional[bool] = None
    language: Optional[str] = None
    add_watermark: Optional[bool] = None

class EditImageConfig:
    """
    Configuration for image editing.

    Attributes:
        number_of_images (int, optional): Number of edited variations.
        negative_prompt (str, optional): What to avoid.
        edit_mode (EditMode, optional): Editing mode.
        mask_mode (MaskMode, optional): Mask interpretation.
        mask_dilation (float, optional): Mask dilation amount.
        guidance_scale (float, optional): Prompt adherence (1-20).
        safety_filter_level (str, optional): Safety filtering.
        person_generation (PersonGeneration, optional): Person generation control.
        include_safety_attributes (bool, optional): Include safety attributes.
    """
    number_of_images: Optional[int] = None
    negative_prompt: Optional[str] = None
    edit_mode: Optional[EditMode] = None
    mask_mode: Optional[MaskMode] = None
    mask_dilation: Optional[float] = None
    guidance_scale: Optional[float] = None
    safety_filter_level: Optional[str] = None
    person_generation: Optional[PersonGeneration] = None
    include_safety_attributes: Optional[bool] = None

class UpscaleImageConfig:
    """
    Configuration for image upscaling.

    Attributes:
        number_of_images (int, optional): Number of upscaled variations.
        safety_filter_level (str, optional): Safety filtering.
        include_safety_attributes (bool, optional): Include safety attributes.
    """
    number_of_images: Optional[int] = None
    safety_filter_level: Optional[str] = None
    include_safety_attributes: Optional[bool] = None

class RecontextImageConfig:
    """Configuration for image recontextualization."""
    number_of_images: Optional[int] = None
    negative_prompt: Optional[str] = None
    safety_filter_level: Optional[str] = None
    include_safety_attributes: Optional[bool] = None

class SegmentImageConfig:
    """
    Configuration for image segmentation.

    Attributes:
        segment_mode (SegmentMode, optional): Segmentation mode.
    """
    segment_mode: Optional[SegmentMode] = None

# Response types
class GenerateImagesResponse:
    """
    Response from image generation.

    Attributes:
        generated_images (list[GeneratedImage]): Generated images with metadata.
        rai_filtered_reason (str, optional): Reason if filtered by safety.
    """
    generated_images: list[GeneratedImage]
    rai_filtered_reason: Optional[str] = None

class EditImageResponse:
    """Response from image editing."""
    generated_images: list[GeneratedImage]
    rai_filtered_reason: Optional[str] = None

class UpscaleImageResponse:
    """Response from image upscaling."""
    generated_images: list[GeneratedImage]
    rai_filtered_reason: Optional[str] = None

class RecontextImageResponse:
    """Response from image recontextualization."""
    generated_images: list[GeneratedImage]
    rai_filtered_reason: Optional[str] = None

class SegmentImageResponse:
    """
    Response from image segmentation.

    Attributes:
        generated_masks (list[GeneratedImageMask]): Segmentation masks.
    """
    generated_masks: list[GeneratedImageMask]

class GeneratedImage:
    """
    Generated or edited image.

    Attributes:
        image (Image): Image object.
        pil_image (PIL.Image.Image): PIL Image for easy manipulation.
        generation_seed (int, optional): Seed used for generation.
        rai_info (str, optional): RAI information.
        safety_attributes (SafetyAttributes, optional): Safety attributes.
    """
    image: Image
    pil_image: PIL.Image.Image
    generation_seed: Optional[int] = None
    rai_info: Optional[str] = None
    safety_attributes: Optional[SafetyAttributes] = None

class GeneratedImageMask:
    """
    Segmentation mask.

    Attributes:
        mask_image (Image): Mask image.
        entity_label (EntityLabel, optional): Entity label.
    """
    mask_image: Image
    entity_label: Optional[EntityLabel] = None

# Input types
class ReferenceImage:
    """
    Reference image for editing.

    Attributes:
        reference_type (str): Type ('reference_image', 'mask_image', 'control_image', etc.).
        reference_image (Image): The reference image.
        reference_id (int, optional): Reference identifier.
    """
    reference_type: str
    reference_image: Image
    reference_id: Optional[int] = None

class RecontextImageSource:
    """
    Source for recontextualization.

    Attributes:
        product_image (Image): Product image.
        product_mask (Image, optional): Product mask.
    """
    product_image: Image
    product_mask: Optional[Image] = None

class SegmentImageSource:
    """
    Source for segmentation.

    Attributes:
        image (Image): Image to segment.
        entity_labels (list[EntityLabel], optional): Entity labels to identify.
    """
    image: Image
    entity_labels: Optional[list[EntityLabel]] = None

class Image:
    """
    Image data supporting multiple formats.

    Can be created from:
        - File: Image.from_file('path.jpg')
        - URL: Image.from_url('https://...')
        - Bytes: Image.from_bytes(data, mime_type='image/jpeg')
        - PIL: Image.from_pil(pil_image)
    """
    @staticmethod
    def from_file(path: str) -> Image: ...

    @staticmethod
    def from_url(url: str) -> Image: ...

    @staticmethod
    def from_bytes(data: bytes, mime_type: str) -> Image: ...

    @staticmethod
    def from_pil(pil_image: PIL.Image.Image) -> Image: ...

# Enum types
class PersonGeneration(Enum):
    """Person generation control."""
    DONT_ALLOW = 'dont_allow'
    ALLOW_ADULT = 'allow_adult'
    ALLOW_ALL = 'allow_all'

class EditMode(Enum):
    """Image editing modes."""
    EDIT_MODE_UNSPECIFIED = 'EDIT_MODE_UNSPECIFIED'
    INPAINT_INSERTION = 'INPAINT_INSERTION'
    INPAINT_REMOVAL = 'INPAINT_REMOVAL'
    OUTPAINT = 'OUTPAINT'
    PRODUCT_IMAGE = 'PRODUCT_IMAGE'

class MaskMode(Enum):
    """Mask interpretation modes."""
    MASK_MODE_UNSPECIFIED = 'MASK_MODE_UNSPECIFIED'
    MASK_MODE_BACKGROUND = 'MASK_MODE_BACKGROUND'
    MASK_MODE_FOREGROUND = 'MASK_MODE_FOREGROUND'
    MASK_MODE_SEMANTIC = 'MASK_MODE_SEMANTIC'

class SegmentMode(Enum):
    """Segmentation modes."""
    SEGMENT_MODE_UNSPECIFIED = 'SEGMENT_MODE_UNSPECIFIED'
    FOREGROUND = 'FOREGROUND'
    ENTITY = 'ENTITY'

class SafetyAttributes:
    """Safety attributes for images."""
    blocked: bool
    scores: dict[str, float]

class EntityLabel:
    """Entity label for segmentation."""
    label: str
    score: Optional[float] = None
```
