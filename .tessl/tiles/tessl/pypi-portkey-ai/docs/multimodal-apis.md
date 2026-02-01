# Multimodal APIs

Image generation, audio processing (speech-to-text, text-to-speech, translation), and content moderation capabilities with OpenAI compatibility.

## Capabilities

### Image Generation

```python { .api }
class Images:
    def generate(self, **kwargs): ...
    def create_variation(self, **kwargs): ...
    def edit(self, **kwargs): ...
```

### Audio Processing

```python { .api }
class Audio:
    transcriptions: Transcriptions
    translations: Translations
    speech: Speech

class Transcriptions:
    def create(self, **kwargs): ...

class Translations:
    def create(self, **kwargs): ...

class Speech:
    def create(self, **kwargs): ...
```

### Content Moderation

```python { .api }
class Moderations:
    def create(self, **kwargs): ...
```

## Usage Examples

```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="PORTKEY_API_KEY",
    virtual_key="VIRTUAL_KEY"
)

# Generate image
image = portkey.images.generate(
    prompt="A cat in a spacesuit",
    model="dall-e-3",
    size="1024x1024"
)

# Transcribe audio
transcription = portkey.audio.transcriptions.create(
    file=open("audio.mp3", "rb"),
    model="whisper-1"
)

# Moderate content
moderation = portkey.moderations.create(
    input="This is a test message"
)
```