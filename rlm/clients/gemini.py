import base64
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()


def _load_image_as_part(image_source: str | dict) -> types.Part:
    """Load an image and return a Gemini Part object.
    
    Args:
        image_source: Either a file path (str), URL (str starting with http), 
                      or a dict with 'type' and 'data' keys for base64 images.
    
    Returns:
        A Gemini Part object containing the image.
    """
    if isinstance(image_source, dict):
        # Base64 encoded image: {"type": "base64", "media_type": "image/png", "data": "..."}
        if image_source.get("type") == "base64":
            image_bytes = base64.b64decode(image_source["data"])
            mime_type = image_source.get("media_type", "image/png")
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        # URL format from OpenAI-style: {"type": "image_url", "image_url": {"url": "..."}}
        elif image_source.get("type") == "image_url":
            url = image_source["image_url"]["url"]
            if url.startswith("data:"):
                # Data URL: data:image/png;base64,...
                header, data = url.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                image_bytes = base64.b64decode(data)
                return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            else:
                return types.Part.from_uri(file_uri=url, mime_type="image/jpeg")
    elif isinstance(image_source, str):
        if image_source.startswith(("http://", "https://")):
            # URL
            return types.Part.from_uri(file_uri=image_source, mime_type="image/jpeg")
        else:
            # Local file path
            path = Path(image_source)
            if path.exists():
                mime_type = _get_mime_type(path)
                with open(path, "rb") as f:
                    return types.Part.from_bytes(data=f.read(), mime_type=mime_type)
            else:
                raise FileNotFoundError(f"Image file not found: {image_source}")
    raise ValueError(f"Unsupported image source type: {type(image_source)}")


def _get_mime_type(path: Path) -> str:
    """Get MIME type from file extension."""
    suffix = path.suffix.lower()
    mime_types = {
        # Images
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        # Audio
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".webm": "audio/webm",
        # Video
        ".mp4": "video/mp4",
        ".mpeg": "video/mpeg",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska",
    }
    return mime_types.get(suffix, "application/octet-stream")


def _load_audio_as_part(audio_source: str | dict) -> types.Part:
    """Load an audio file and return a Gemini Part object.
    
    Args:
        audio_source: Either a file path (str), URL (str starting with http), 
                      or a dict with 'type' and 'data' keys for base64 audio.
    
    Returns:
        A Gemini Part object containing the audio.
    """
    if isinstance(audio_source, dict):
        # Base64 encoded audio
        if audio_source.get("type") == "base64":
            audio_bytes = base64.b64decode(audio_source["data"])
            mime_type = audio_source.get("media_type", "audio/mpeg")
            return types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        # Path format
        elif audio_source.get("type") == "audio_path":
            path = Path(audio_source.get("path", ""))
            if path.exists():
                mime_type = _get_mime_type(path)
                with open(path, "rb") as f:
                    return types.Part.from_bytes(data=f.read(), mime_type=mime_type)
            else:
                raise FileNotFoundError(f"Audio file not found: {audio_source.get('path')}")
    elif isinstance(audio_source, str):
        if audio_source.startswith(("http://", "https://")):
            # URL - let Gemini fetch it
            return types.Part.from_uri(file_uri=audio_source, mime_type="audio/mpeg")
        else:
            # Local file path
            path = Path(audio_source)
            if path.exists():
                mime_type = _get_mime_type(path)
                with open(path, "rb") as f:
                    return types.Part.from_bytes(data=f.read(), mime_type=mime_type)
            else:
                raise FileNotFoundError(f"Audio file not found: {audio_source}")
    raise ValueError(f"Unsupported audio source type: {type(audio_source)}")

DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiClient(BaseLM):
    """
    LM Client for running models with the Google Gemini API.
    Uses the official google-genai SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = "gemini-2.5-flash",
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)

        if api_key is None:
            api_key = DEFAULT_GEMINI_API_KEY

        if api_key is None:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY env var or pass api_key."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

        # Last call tracking
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0

    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        contents, system_instruction = self._prepare_contents(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(system_instruction=system_instruction)

        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        self._track_cost(response, model)
        return response.text

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        contents, system_instruction = self._prepare_contents(prompt)

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for Gemini client.")

        config = None
        if system_instruction:
            config = types.GenerateContentConfig(system_instruction=system_instruction)

        # google-genai SDK supports async via aio interface
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        self._track_cost(response, model)
        return response.text

    def _prepare_contents(
        self, prompt: str | list[dict[str, Any]]
    ) -> tuple[list[types.Content] | str, str | None]:
        """Prepare contents and extract system instruction for Gemini API.
        
        Supports multimodal content where message content can be:
        - A string (text only)
        - A list of content items (text and images mixed)
        
        Image items can be:
        - {"type": "text", "text": "..."}
        - {"type": "image_url", "image_url": {"url": "..."}}
        - {"type": "image_path", "path": "/path/to/image.png"}
        - {"type": "base64", "media_type": "image/png", "data": "..."}
        """
        system_instruction = None

        if isinstance(prompt, str):
            return prompt, None

        if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            # Convert OpenAI-style messages to Gemini format
            contents = []
            for msg in prompt:
                role = msg.get("role")
                content = msg.get("content", "")

                if role == "system":
                    # Gemini handles system instruction separately
                    if isinstance(content, str):
                        system_instruction = content
                    elif isinstance(content, list):
                        # Extract text from system message list
                        system_parts = []
                        for item in content:
                            if isinstance(item, str):
                                system_parts.append(item)
                            elif isinstance(item, dict) and item.get("type") == "text":
                                system_parts.append(item.get("text", ""))
                        system_instruction = "\n".join(system_parts)
                elif role in ("user", "assistant"):
                    gemini_role = "user" if role == "user" else "model"
                    parts = self._content_to_parts(content)
                    if parts:
                        contents.append(types.Content(role=gemini_role, parts=parts))
                else:
                    # Default to user role for unknown roles
                    parts = self._content_to_parts(content)
                    if parts:
                        contents.append(types.Content(role="user", parts=parts))

            return contents, system_instruction

        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def _content_to_parts(self, content: str | list) -> list[types.Part]:
        """Convert message content to Gemini Parts.
        
        Args:
            content: Either a string or a list of content items.
            
        Returns:
            List of Gemini Part objects.
        """
        if isinstance(content, str):
            return [types.Part(text=content)]
        
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(types.Part(text=item))
                elif isinstance(item, dict):
                    item_type = item.get("type", "text")
                    if item_type == "text":
                        parts.append(types.Part(text=item.get("text", "")))
                    elif item_type in ("image_url", "image_path", "base64"):
                        try:
                            # Use image_path for local files
                            if item_type == "image_path":
                                image_part = _load_image_as_part(item.get("path", ""))
                            else:
                                image_part = _load_image_as_part(item)
                            parts.append(image_part)
                        except Exception as e:
                            # If image loading fails, add error as text
                            parts.append(types.Part(text=f"[Image load error: {e}]"))
                    elif item_type == "audio_path":
                        try:
                            audio_part = _load_audio_as_part(item.get("path", ""))
                            parts.append(audio_part)
                        except Exception as e:
                            parts.append(types.Part(text=f"[Audio load error: {e}]"))
                    elif item_type == "audio_url":
                        try:
                            audio_part = _load_audio_as_part(item.get("url", ""))
                            parts.append(audio_part)
                        except Exception as e:
                            parts.append(types.Part(text=f"[Audio load error: {e}]"))
            return parts
        
        return [types.Part(text=str(content))]

    def _track_cost(self, response: types.GenerateContentResponse, model: str):
        self.model_call_counts[model] += 1

        # Extract token usage from response
        usage = response.usage_metadata
        if usage:
            input_tokens = usage.prompt_token_count or 0
            output_tokens = usage.candidates_token_count or 0

            self.model_input_tokens[model] += input_tokens
            self.model_output_tokens[model] += output_tokens
            self.model_total_tokens[model] += input_tokens + output_tokens

            # Track last call for handler to read
            self.last_prompt_tokens = input_tokens
            self.last_completion_tokens = output_tokens
        else:
            self.last_prompt_tokens = 0
            self.last_completion_tokens = 0

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
        )
