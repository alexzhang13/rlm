# Audio

Convert audio to text (transcription and translation) and text to speech using Whisper and TTS models. Supports multiple audio formats and languages.

## Capabilities

### Transcription

Convert audio to text in the original language using the Whisper model.

```python { .api }
def create(
    self,
    *,
    file: FileTypes,
    model: str | AudioModel,
    chunking_strategy: dict | str | Omit = omit,
    include: list[str] | Omit = omit,
    known_speaker_names: list[str] | Omit = omit,
    known_speaker_references: list[str] | Omit = omit,
    language: str | Omit = omit,
    prompt: str | Omit = omit,
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt", "diarized_json"] | Omit = omit,
    stream: bool | Omit = omit,
    temperature: float | Omit = omit,
    timestamp_granularities: list[Literal["word", "segment"]] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Transcription | TranscriptionVerbose:
    """
    Transcribe audio to text in the original language.

    Args:
        file: Audio file to transcribe. Supported formats: flac, mp3, mp4, mpeg,
            mpga, m4a, ogg, wav, webm. Max file size: 25 MB.
            Can be file path string, file object, or tuple.

        model: Model ID. Options:
            - "gpt-4o-transcribe": Advanced transcription with streaming support
            - "gpt-4o-mini-transcribe": Faster, cost-effective transcription
            - "gpt-4o-transcribe-diarize": Speaker diarization model
            - "whisper-1": Powered by open source Whisper V2 model

        chunking_strategy: Controls how audio is cut into chunks. Options:
            - "auto": Server normalizes loudness and uses voice activity detection (VAD)
            - {"type": "server_vad", ...}: Manually configure VAD parameters
            - If unset: Audio transcribed as a single block
            - Required for gpt-4o-transcribe-diarize with inputs >30 seconds

        include: Additional information to include. Options:
            - "logprobs": Returns log probabilities for confidence analysis
            - Only works with response_format="json"
            - Only supported for gpt-4o-transcribe and gpt-4o-mini-transcribe
            - Not supported with gpt-4o-transcribe-diarize

        known_speaker_names: List of speaker names for diarization (e.g., ["customer", "agent"]).
            Corresponds to audio samples in known_speaker_references. Up to 4 speakers.
            Used with gpt-4o-transcribe-diarize model.

        known_speaker_references: List of audio samples (as data URLs) containing known speaker
            references. Each sample must be 2-10 seconds. Matches known_speaker_names.
            Used with gpt-4o-transcribe-diarize model.

        language: Language of the audio in ISO-639-1 format (e.g., "en", "fr", "de").
            Providing language improves accuracy and latency.

        prompt: Optional text to guide the model's style or continue previous segment.
            Should match audio language.

        response_format: Output format. Options:
            - "json": JSON with text (default)
            - "text": Plain text only
            - "srt": SubRip subtitle format
            - "verbose_json": JSON with segments, timestamps, confidence
            - "vtt": WebVTT subtitle format
            - "diarized_json": JSON with speaker annotations (for gpt-4o-transcribe-diarize)
            Note: gpt-4o-transcribe/mini only support "json". gpt-4o-transcribe-diarize
            supports "json", "text", and "diarized_json" (required for speaker annotations).

        stream: If true, model response will be streamed using server-sent events.
            Returns Stream[TranscriptionStreamEvent]. Not supported for whisper-1.

        temperature: Sampling temperature between 0 and 1. Higher values increase
            randomness. Default is 0.

        timestamp_granularities: Timestamp precision options.
            - ["segment"]: Segment-level timestamps (default)
            - ["word"]: Word-level timestamps
            - ["segment", "word"]: Both levels

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Transcription: Basic response with text
        TranscriptionVerbose: Detailed response with segments and timestamps

    Raises:
        BadRequestError: Invalid file format or size
        AuthenticationError: Invalid API key
    """
```

Usage examples:

```python
from openai import OpenAI

client = OpenAI()

# Basic transcription
with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
print(transcript.text)

# With language hint for better accuracy
with open("french_audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="fr"
    )

# Verbose JSON with detailed information
with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"]
    )

print(f"Duration: {transcript.duration}")
print(f"Language: {transcript.language}")

for segment in transcript.segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")

for word in transcript.words:
    print(f"{word.word} ({word.start:.2f}s)")

# SRT subtitle format
with open("video_audio.mp3", "rb") as audio_file:
    srt = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="srt"
    )
# Save to file
with open("subtitles.srt", "w") as f:
    f.write(srt)

# With prompt for context/style
with open("continuation.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        prompt="Previous text for context..."
    )

# Using file_from_path helper
from openai import OpenAI
from openai import file_from_path

client = OpenAI()

transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=file_from_path("audio.mp3")
)

# Advanced: Using gpt-4o-transcribe with streaming
with open("audio.mp3", "rb") as audio_file:
    stream = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file,
        stream=True
    )
    for event in stream:
        print(event.text, end="", flush=True)

# Advanced: Speaker diarization with gpt-4o-transcribe-diarize
with open("meeting.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe-diarize",
        file=audio_file,
        response_format="diarized_json",
        chunking_strategy="auto"
    )
    for segment in transcript.segments:
        print(f"[{segment.speaker}]: {segment.text}")

# Advanced: With known speaker references
with open("call.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe-diarize",
        file=audio_file,
        response_format="diarized_json",
        known_speaker_names=["customer", "agent"],
        known_speaker_references=[
            "data:audio/mp3;base64,...",  # Customer voice sample
            "data:audio/mp3;base64,..."   # Agent voice sample
        ]
    )

# Advanced: Using include for confidence scores
with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file,
        response_format="json",
        include=["logprobs"]
    )
    # Access logprobs for confidence analysis
```

### Translation

Translate audio to English text using the Whisper model.

```python { .api }
def create(
    self,
    *,
    file: FileTypes,
    model: str | AudioModel,
    prompt: str | Omit = omit,
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] | Omit = omit,
    temperature: float | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> Translation | TranslationVerbose | str:
    """
    Translate audio to English text.

    Args:
        file: Audio file to translate. Supported formats: flac, mp3, mp4, mpeg,
            mpga, m4a, ogg, wav, webm. Max file size: 25 MB.

        model: Model ID. Currently only "whisper-1" is available.

        prompt: Optional text to guide the model's style.

        response_format: Output format. Options:
            - "json": JSON with text (default)
            - "text": Plain text only
            - "srt": SubRip subtitle format
            - "verbose_json": JSON with segments and details
            - "vtt": WebVTT subtitle format

        temperature: Sampling temperature between 0 and 1.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        Translation: Basic response with English text (for json format)
        TranslationVerbose: Detailed response with segments (for verbose_json format)
        str: Plain text string (for text, srt, vtt formats)

    Raises:
        BadRequestError: Invalid file format or size
    """
```

Usage example:

```python
from openai import OpenAI

client = OpenAI()

# Translate French audio to English
with open("french_audio.mp3", "rb") as audio_file:
    translation = client.audio.translations.create(
        model="whisper-1",
        file=audio_file
    )
print(translation.text)

# Verbose format with segments
with open("spanish_audio.mp3", "rb") as audio_file:
    translation = client.audio.translations.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json"
    )

for segment in translation.segments:
    print(f"[{segment.start:.2f}s]: {segment.text}")
```

### Text-to-Speech

Convert text to spoken audio using TTS models.

```python { .api }
def create(
    self,
    *,
    input: str,
    model: str | SpeechModel,
    voice: Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"],
    instructions: str | Omit = omit,
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] | Omit = omit,
    speed: float | Omit = omit,
    stream_format: Literal["sse", "audio"] | Omit = omit,
    extra_headers: dict[str, str] | None = None,
    extra_query: dict[str, object] | None = None,
    extra_body: dict[str, object] | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
) -> HttpxBinaryResponseContent:
    """
    Convert text to spoken audio.

    Args:
        input: Text to convert to audio. Max length: 4096 characters.

        model: TTS model to use. Options:
            - "tts-1": Standard quality, faster, lower cost
            - "tts-1-hd": High definition quality, slower, higher cost
            - "gpt-4o-mini-tts": Advanced model with instruction support

        voice: Voice to use for generation. Options:
            - "alloy": Neutral, balanced
            - "ash": Clear and articulate
            - "ballad": Warm and expressive
            - "coral": Bright and engaging
            - "echo": Calm and measured
            - "sage": Wise and authoritative
            - "shimmer": Soft and gentle
            - "verse": Dynamic and versatile
            - "marin": Smooth and professional
            - "cedar": Rich and grounded

        instructions: Control the voice with additional instructions.
            Does not work with tts-1 or tts-1-hd. Only supported by gpt-4o-mini-tts.

        response_format: Audio format. Options:
            - "mp3": Default, good compression
            - "opus": Best for streaming, lower latency
            - "aac": Good compression, widely supported
            - "flac": Lossless compression
            - "wav": Uncompressed
            - "pcm": Raw 16-bit PCM audio

        speed: Playback speed between 0.25 and 4.0. Default 1.0.

        stream_format: Format to stream the audio in. Options:
            - "sse": Server-sent events streaming
            - "audio": Raw audio streaming
            Note: "sse" not supported for tts-1 or tts-1-hd.

        extra_headers: Additional HTTP headers.
        extra_query: Additional query parameters.
        extra_body: Additional JSON fields.
        timeout: Request timeout in seconds.

    Returns:
        HttpxBinaryResponseContent: Audio file content. Use .content for bytes,
            .read() for streaming, .stream_to_file(path) for direct save.

    Raises:
        BadRequestError: Invalid parameters or text too long
    """
```

Usage examples:

```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

# Basic TTS
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello! This is a test of text to speech."
)

# Save to file
speech_file = Path("output.mp3")
response.stream_to_file(speech_file)

# Different voices
voices = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]
for voice in voices:
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input="Testing different voices."
    )
    response.stream_to_file(f"voice_{voice}.mp3")

# High quality audio (using marin or cedar recommended for best quality)
response = client.audio.speech.create(
    model="tts-1-hd",
    voice="marin",
    input="High definition audio output."
)
response.stream_to_file("hd_output.mp3")

# Streaming optimized format (Opus)
response = client.audio.speech.create(
    model="tts-1",
    voice="shimmer",
    input="Optimized for streaming.",
    response_format="opus"
)
response.stream_to_file("output.opus")

# Adjust playback speed
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="This will play faster.",
    speed=1.5
)
response.stream_to_file("fast_speech.mp3")

# Get raw bytes
response = client.audio.speech.create(
    model="tts-1",
    voice="echo",
    input="Getting raw audio bytes."
)
audio_bytes = response.content
# Process bytes as needed

# Streaming response
response = client.audio.speech.create(
    model="tts-1",
    voice="ballad",
    input="Streaming audio data."
)

with open("streaming.mp3", "wb") as f:
    for chunk in response.iter_bytes():
        f.write(chunk)

# Advanced: Using gpt-4o-mini-tts with instructions
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="sage",
    input="This is a test of voice control.",
    instructions="Speak in a warm, friendly tone with slight enthusiasm."
)
response.stream_to_file("instructed_speech.mp3")

# Advanced: Server-sent events streaming
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="coral",
    input="Real-time audio streaming.",
    stream_format="sse"
)
response.stream_to_file("sse_output.mp3")
```

## Types

```python { .api }
from typing import Literal
from pydantic import BaseModel

# Transcription types
class Transcription(BaseModel):
    text: str

class TranscriptionVerbose(BaseModel):
    text: str
    language: str
    duration: float
    segments: list[TranscriptionSegment] | None
    words: list[TranscriptionWord] | None

class TranscriptionSegment(BaseModel):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: list[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float

class TranscriptionWord(BaseModel):
    word: str
    start: float
    end: float

class TranscriptionDiarized(BaseModel):
    """Transcription with speaker diarization."""
    text: str
    language: str
    duration: float
    segments: list[DiarizedSegment]

class DiarizedSegment(BaseModel):
    """Segment with speaker information."""
    speaker: str  # Speaker identifier
    start: float
    end: float
    text: str

# Translation types
class Translation(BaseModel):
    text: str

class TranslationVerbose(BaseModel):
    text: str
    language: str
    duration: float
    segments: list[TranscriptionSegment] | None

# Model types
AudioModel = Literal["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "gpt-4o-transcribe-diarize", "whisper-1"]
SpeechModel = Literal["tts-1", "tts-1-hd", "gpt-4o-mini-tts"]

# File types
FileTypes = Union[
    FileContent,  # File-like object
    tuple[str | None, FileContent],  # (filename, content)
    tuple[str | None, FileContent, str | None]  # (filename, content, content_type)
]

# Response type for TTS
class HttpxBinaryResponseContent:
    content: bytes
    def read(self) -> bytes: ...
    def iter_bytes(self, chunk_size: int = None) -> Iterator[bytes]: ...
    def stream_to_file(self, file_path: str | Path) -> None: ...
```

## Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def transcribe_audio():
    client = AsyncOpenAI()

    with open("audio.mp3", "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

async def generate_speech():
    client = AsyncOpenAI()

    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="Async text to speech"
    )
    response.stream_to_file("async_output.mp3")

# Run async operations
text = asyncio.run(transcribe_audio())
asyncio.run(generate_speech())
```
