"""
Example: Multimodal RLM - Audio Support (TTS and Transcription)

This demonstrates the audio capabilities of RLM:
- speak() for text-to-speech
- audio_query() for audio transcription/analysis
"""

import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger

load_dotenv()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

logger = RLMLogger(log_dir="./logs")

# Use Gemini which supports audio
rlm = RLM(
    backend="gemini",
    backend_kwargs={
        "model_name": "gemini-2.5-flash",
        "api_key": os.getenv("GEMINI_API_KEY"),
    },
    environment="local",
    environment_kwargs={},
    max_depth=1,
    logger=logger,
    verbose=True,
    enable_multimodal=True,  # Enable multimodal functions (vision_query, audio_query, speak)
)

# Example 1: Text-to-Speech
# Ask RLM to generate speech
context = {
    "task": "Generate a spoken greeting",
    "message": "Hello! This is a test of the RLM text-to-speech capability.",
    "output_path": os.path.join(SCRIPT_DIR, "generated_speech.aiff"),
}

result = rlm.completion(
    prompt=context,
    root_prompt="Use speak(text, output_path) to convert context['message'] to audio and save it to context['output_path']. Return the path.",
)

print("\n" + "=" * 50)
print("TTS RESULT:")
print("=" * 50)
print(result.response)


# Example 2: Audio Analysis (if you have an audio file)
# Uncomment this section if you have an audio file to analyze:
"""
audio_context = {
    "task": "Transcribe the audio",
    "audio_file": "/path/to/your/audio.mp3",
}

result = rlm.completion(
    prompt=audio_context,
    root_prompt="Use audio_query to transcribe the audio file.",
)
print(result.response)
"""
