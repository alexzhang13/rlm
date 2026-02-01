# Moderations

Check content against OpenAI's usage policies to detect potentially harmful content across multiple categories including hate speech, violence, sexual content, and self-harm. Supports both text and image inputs for multi-modal moderation.

## Capabilities

### Create Moderation

Classify text and/or image content for policy violations.

```python { .api }
def create(
    self,
    *,
    input: str | list[str] | list[ModerationMultiModalInputParam],
    model: str | ModerationModel | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> ModerationCreateResponse:
    """
    Classify text and/or image inputs against OpenAI's usage policies.

    Args:
        input: Content to classify. Can be:
            - Single string: "Text to moderate"
            - List of strings: ["Text 1", "Text 2"]
            - List of multi-modal inputs: [{"type": "text", "text": "..."},
              {"type": "image_url", "image_url": {"url": "..."}}]
            Maximum 32,768 characters per text input.

        model: Moderation model to use. Options:
            - "text-moderation-latest": Latest text model, automatically updated
            - "text-moderation-stable": Stable text model, less frequent updates
            - "omni-moderation-latest": Latest multi-modal model (supports text + images, default)
            - "omni-moderation-2024-09-26": Specific omni model version

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        ModerationCreateResponse: Contains flagged status and category scores
            for each input.

    Raises:
        BadRequestError: Input exceeds maximum length
        AuthenticationError: Invalid API key
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Check single text
response = client.moderations.create(
    input="I want to hurt someone"
)

result = response.results[0]
print(f"Flagged: {result.flagged}")

if result.flagged:
    print("Violated categories:")
    for category, flagged in result.categories.model_dump().items():
        if flagged:
            score = getattr(result.category_scores, category)
            print(f"  {category}: {score:.4f}")

# Check multiple texts
texts = [
    "Hello, how are you?",
    "This is inappropriate content",
    "What's the weather like today?"
]

response = client.moderations.create(input=texts)

for i, result in enumerate(response.results):
    print(f"Text {i + 1}: {'Flagged' if result.flagged else 'Safe'}")

# Use latest omni model
response = client.moderations.create(
    model="omni-moderation-latest",
    input="Check this message for violations"
)

# Use stable model for consistent behavior
response = client.moderations.create(
    model="text-moderation-stable",
    input="Testing moderation"
)

# Multi-modal moderation with text and images
response = client.moderations.create(
    model="omni-moderation-latest",
    input=[
        {"type": "text", "text": "Check this message"},
        {
            "type": "image_url",
            "image_url": {"url": "https://example.com/image.jpg"}
        }
    ]
)

# Moderate image from base64
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.moderations.create(
    model="omni-moderation-latest",
    input=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
        }
    ]
)

# Detailed category analysis
response = client.moderations.create(
    input="Potentially problematic text"
)

result = response.results[0]

# All categories and scores
categories = result.categories
scores = result.category_scores

print("Category Analysis:")
print(f"  Hate: {scores.hate:.4f} (flagged: {categories.hate})")
print(f"  Hate/Threatening: {scores.hate_threatening:.4f} (flagged: {categories.hate_threatening})")
print(f"  Harassment: {scores.harassment:.4f} (flagged: {categories.harassment})")
print(f"  Harassment/Threatening: {scores.harassment_threatening:.4f} (flagged: {categories.harassment_threatening})")
print(f"  Self-Harm: {scores.self_harm:.4f} (flagged: {categories.self_harm})")
print(f"  Self-Harm/Intent: {scores.self_harm_intent:.4f} (flagged: {categories.self_harm_intent})")
print(f"  Self-Harm/Instructions: {scores.self_harm_instructions:.4f} (flagged: {categories.self_harm_instructions})")
print(f"  Sexual: {scores.sexual:.4f} (flagged: {categories.sexual})")
print(f"  Sexual/Minors: {scores.sexual_minors:.4f} (flagged: {categories.sexual_minors})")
print(f"  Violence: {scores.violence:.4f} (flagged: {categories.violence})")
print(f"  Violence/Graphic: {scores.violence_graphic:.4f} (flagged: {categories.violence_graphic})")

# Filter user content example
def is_safe_content(text: str) -> tuple[bool, list[str]]:
    """
    Check if content is safe to use.
    Returns (is_safe, violated_categories)
    """
    response = client.moderations.create(input=text)
    result = response.results[0]

    if not result.flagged:
        return True, []

    violated = [
        category for category, flagged in result.categories.model_dump().items()
        if flagged
    ]

    return False, violated

# Use in application
user_input = "Some user-generated content"
is_safe, violations = is_safe_content(user_input)

if is_safe:
    print("Content approved")
else:
    print(f"Content rejected. Violations: {', '.join(violations)}")
```

## Types

```python { .api }
from typing import Literal, Union
from typing_extensions import TypedDict
from pydantic import BaseModel

class ModerationCreateResponse(BaseModel):
    """Moderation response."""
    id: str
    model: str
    results: list[ModerationResult]

class ModerationResult(BaseModel):
    """Single moderation result."""
    flagged: bool
    categories: ModerationCategories
    category_scores: ModerationCategoryScores
    category_applied_input_types: ModerationCategoryAppliedInputTypes

class ModerationCategories(BaseModel):
    """Category flags (true if violated)."""
    hate: bool
    hate_threatening: bool
    harassment: bool
    harassment_threatening: bool
    self_harm: bool
    self_harm_intent: bool
    self_harm_instructions: bool
    sexual: bool
    sexual_minors: bool
    violence: bool
    violence_graphic: bool
    illicit: bool
    illicit_violent: bool

class ModerationCategoryScores(BaseModel):
    """Confidence scores (0-1) for each category."""
    hate: float
    hate_threatening: float
    harassment: float
    harassment_threatening: float
    self_harm: float
    self_harm_intent: float
    self_harm_instructions: float
    sexual: float
    sexual_minors: float
    violence: float
    violence_graphic: float
    illicit: float
    illicit_violent: float

class ModerationCategoryAppliedInputTypes(BaseModel):
    """Input types that triggered each category."""
    hate: list[str]
    hate_threatening: list[str]
    harassment: list[str]
    harassment_threatening: list[str]
    self_harm: list[str]
    self_harm_intent: list[str]
    self_harm_instructions: list[str]
    sexual: list[str]
    sexual_minors: list[str]
    violence: list[str]
    violence_graphic: list[str]
    illicit: list[str]
    illicit_violent: list[str]

# Model type
ModerationModel = Literal[
    "text-moderation-latest",
    "text-moderation-stable",
    "omni-moderation-latest",
    "omni-moderation-2024-09-26"
]

# Multi-modal input types
class ModerationTextInputParam(TypedDict):
    """Text input for moderation."""
    text: str  # Required: Text content to moderate
    type: Literal["text"]  # Required: Always "text"

class ImageURL(TypedDict):
    """Image URL or base64 data."""
    url: str  # Required: URL or data:image/...;base64,... string

class ModerationImageURLInputParam(TypedDict):
    """Image input for moderation."""
    image_url: ImageURL  # Required: Image URL or base64 data
    type: Literal["image_url"]  # Required: Always "image_url"

# Union type for multi-modal inputs
ModerationMultiModalInputParam = Union[
    ModerationTextInputParam,
    ModerationImageURLInputParam
]
```

## Category Descriptions

| Category | Description |
|----------|-------------|
| hate | Content expressing, inciting, or promoting hate based on protected characteristics |
| hate/threatening | Hateful content that also includes violence or serious harm |
| harassment | Content harassing, bullying, or abusing an individual |
| harassment/threatening | Harassing content that also includes violence or serious harm |
| self-harm | Content promoting, encouraging, or depicting acts of self-harm |
| self-harm/intent | Content indicating intent to engage in self-harm |
| self-harm/instructions | Content providing instructions or advice for self-harm |
| sexual | Content meant to arouse sexual excitement |
| sexual/minors | Sexual content involving individuals under 18 |
| violence | Content depicting death, violence, or physical injury |
| violence/graphic | Graphic violent content with extreme detail |
| illicit | Content promoting illicit substances or illegal activities |
| illicit/violent | Illicit content involving violence |

## Best Practices

```python
from openai import OpenAI

client = OpenAI()

# 1. Moderate user-generated content before processing
def moderate_before_processing(user_text: str):
    response = client.moderations.create(input=user_text)

    if response.results[0].flagged:
        return None, "Content violates policies"

    # Safe to process
    return process_safe_content(user_text), None

# 2. Batch moderation for efficiency
user_messages = ["msg1", "msg2", "msg3"]
response = client.moderations.create(input=user_messages)

safe_messages = [
    msg for msg, result in zip(user_messages, response.results)
    if not result.flagged
]

# 3. Log violations for analysis
for i, result in enumerate(response.results):
    if result.flagged:
        violated_categories = [
            cat for cat, flagged in result.categories.model_dump().items()
            if flagged
        ]
        log_violation(user_messages[i], violated_categories)

# 4. Use thresholds for borderline content
def is_definitely_safe(text: str, threshold: float = 0.5) -> bool:
    response = client.moderations.create(input=text)
    result = response.results[0]

    # Check if any score exceeds threshold
    scores = result.category_scores.model_dump()
    return all(score < threshold for score in scores.values())
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def moderate_content(text: str):
    client = AsyncOpenAI()

    response = await client.moderations.create(input=text)
    return response.results[0].flagged

# Run async
is_flagged = asyncio.run(moderate_content("Check this text"))
```
