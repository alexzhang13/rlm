import copy
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv

# =============================================================================
# Safe Builtins
# =============================================================================

# Safe builtins - blocks dangerous operations like eval/exec/input
_SAFE_BUILTINS = {
    # Core types and functions
    "print": print,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "bool": bool,
    "type": type,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "reversed": reversed,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "any": any,
    "all": all,
    "pow": pow,
    "divmod": divmod,
    "chr": chr,
    "ord": ord,
    "hex": hex,
    "bin": bin,
    "oct": oct,
    "repr": repr,
    "ascii": ascii,
    "format": format,
    "hash": hash,
    "id": id,
    "iter": iter,
    "next": next,
    "slice": slice,
    "callable": callable,
    "hasattr": hasattr,
    "getattr": getattr,
    "setattr": setattr,
    "delattr": delattr,
    "dir": dir,
    "vars": vars,
    "bytes": bytes,
    "bytearray": bytearray,
    "memoryview": memoryview,
    "complex": complex,
    "object": object,
    "super": super,
    "property": property,
    "staticmethod": staticmethod,
    "classmethod": classmethod,
    "__import__": __import__,
    "open": open,
    # Exceptions
    "Exception": Exception,
    "BaseException": BaseException,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "AttributeError": AttributeError,
    "FileNotFoundError": FileNotFoundError,
    "OSError": OSError,
    "IOError": IOError,
    "RuntimeError": RuntimeError,
    "NameError": NameError,
    "ImportError": ImportError,
    "StopIteration": StopIteration,
    "AssertionError": AssertionError,
    "NotImplementedError": NotImplementedError,
    "ArithmeticError": ArithmeticError,
    "LookupError": LookupError,
    "Warning": Warning,
    # Blocked
    "input": None,
    "eval": None,
    "exec": None,
    "compile": None,
    "globals": None,
    "locals": None,
}


class LocalREPL(NonIsolatedEnv):
    """
    Local REPL environment with persistent Python namespace.
    Executes code in a sandboxed namespace with access to context data.
    """

    def __init__(
        self,
        lm_handler_address: tuple[str, int] | None = None,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        enable_multimodal: bool = False,
        **kwargs,
    ):
        super().__init__(persistent=persistent, depth=depth, **kwargs)

        self.lm_handler_address = lm_handler_address
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(prefix=f"repl_env_{uuid.uuid4()}_")
        self._lock = threading.Lock()
        self._context_count: int = 0
        self._history_count: int = 0
        self.enable_multimodal = enable_multimodal

        # Setup globals, locals, and modules in environment.
        self.setup()

        # Load context if provided
        if context_payload is not None:
            self.load_context(context_payload)

        # Run setup code if provided
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        """Setup the environment."""
        # Create sandboxed globals
        self.globals: dict[str, Any] = {
            "__builtins__": _SAFE_BUILTINS.copy(),
            "__name__": "__main__",
        }
        self.locals: dict[str, Any] = {}

        # Track LLM calls made during code execution
        self._pending_llm_calls: list[RLMChatCompletion] = []

        # Add core helper functions (always available)
        self.globals["FINAL_VAR"] = self._final_var
        self.globals["SHOW_VARS"] = self._show_vars
        self.globals["llm_query"] = self._llm_query
        self.globals["llm_query_batched"] = self._llm_query_batched
        
        # Add multimodal helper functions only if multimodal is enabled
        if self.enable_multimodal:
            self.globals["vision_query"] = self._vision_query
            self.globals["vision_query_batched"] = self._vision_query_batched
            self.globals["audio_query"] = self._audio_query
            self.globals["speak"] = self._speak

    def _final_var(self, variable_name: str) -> str:
        """Return the value of a variable as a final answer."""
        variable_name = variable_name.strip().strip("\"'")
        if variable_name in self.locals:
            return str(self.locals[variable_name])

        # Provide helpful error message with available variables
        available = [k for k in self.locals.keys() if not k.startswith("_")]
        if available:
            return (
                f"Error: Variable '{variable_name}' not found. "
                f"Available variables: {available}. "
                f"You must create and assign a variable BEFORE calling FINAL_VAR on it."
            )
        return (
            f"Error: Variable '{variable_name}' not found. "
            f"No variables have been created yet. "
            f"You must create and assign a variable in a REPL block BEFORE calling FINAL_VAR on it."
        )

    def _show_vars(self) -> str:
        """Show all available variables in the REPL environment."""
        available = {k: type(v).__name__ for k, v in self.locals.items() if not k.startswith("_")}
        if not available:
            return "No variables created yet. Use ```repl``` blocks to create variables."
        return f"Available variables: {available}"

    def _llm_query(self, prompt: str, model: str | None = None) -> str:
        """Query the LM via socket connection to the handler.

        Args:
            prompt: The prompt to send to the LM.
            model: Optional model name to use (if handler has multiple clients).
        """
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            request = LMRequest(prompt=prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            # Track this LLM call
            self._pending_llm_calls.append(
                response.chat_completion,
            )

            return response.chat_completion.response
        except Exception as e:
            return f"Error: LM query failed - {e}"

    def _llm_query_batched(self, prompts: list[str], model: str | None = None) -> list[str]:
        """Query the LM with multiple prompts concurrently.

        Args:
            prompts: List of prompts to send to the LM.
            model: Optional model name to use (if handler has multiple clients).

        Returns:
            List of responses in the same order as input prompts.
        """
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)

        try:
            responses = send_lm_request_batched(
                self.lm_handler_address, prompts, model=model, depth=self.depth
            )

            results = []
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                else:
                    # Track this LLM call in list of all calls -- we may want to do this hierarchically
                    self._pending_llm_calls.append(response.chat_completion)
                    results.append(response.chat_completion.response)

            return results
        except Exception as e:
            return [f"Error: LM query failed - {e}"] * len(prompts)

    def _vision_query(
        self, prompt: str, images: list[str], model: str | None = None
    ) -> str:
        """Query a vision-capable LM with text and images.

        Args:
            prompt: The text prompt describing what to analyze.
            images: List of image paths or URLs to analyze.
            model: Optional model name to use (if handler has multiple clients).

        Returns:
            The LM's response analyzing the images.
        
        Example:
            description = vision_query("What objects are in this image?", ["photo.jpg"])
        """
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            # Build multimodal content list
            content = [{"type": "text", "text": prompt}]
            for img in images:
                if img.startswith(("http://", "https://")):
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": img}
                    })
                else:
                    content.append({
                        "type": "image_path",
                        "path": img
                    })

            # Send as a message with multimodal content
            multimodal_prompt = [{"role": "user", "content": content}]
            request = LMRequest(prompt=multimodal_prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            # Track this LLM call
            self._pending_llm_calls.append(response.chat_completion)
            return response.chat_completion.response
        except Exception as e:
            return f"Error: Vision query failed - {e}"

    def _vision_query_batched(
        self, prompts: list[str], images_list: list[list[str]], model: str | None = None
    ) -> list[str]:
        """Query a vision-capable LM with multiple prompts and images concurrently.

        Args:
            prompts: List of text prompts.
            images_list: List of image lists, one per prompt.
            model: Optional model name to use.

        Returns:
            List of responses in the same order as input prompts.
        
        Example:
            results = vision_query_batched(
                ["What's in image 1?", "What's in image 2?"],
                [["img1.jpg"], ["img2.jpg"]]
            )
        """
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)

        if len(prompts) != len(images_list):
            return ["Error: prompts and images_list must have same length"] * len(prompts)

        try:
            # Build multimodal prompts
            multimodal_prompts = []
            for prompt, images in zip(prompts, images_list):
                content = [{"type": "text", "text": prompt}]
                for img in images:
                    if img.startswith(("http://", "https://")):
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": img}
                        })
                    else:
                        content.append({
                            "type": "image_path",
                            "path": img
                        })
                multimodal_prompts.append([{"role": "user", "content": content}])

            responses = send_lm_request_batched(
                self.lm_handler_address, multimodal_prompts, model=model, depth=self.depth
            )

            results = []
            for response in responses:
                if not response.success:
                    results.append(f"Error: {response.error}")
                else:
                    self._pending_llm_calls.append(response.chat_completion)
                    results.append(response.chat_completion.response)

            return results
        except Exception as e:
            return [f"Error: Vision query failed - {e}"] * len(prompts)

    def _audio_query(
        self, prompt: str, audio_files: list[str], model: str | None = None
    ) -> str:
        """Query an LM with audio files for transcription or analysis.

        Args:
            prompt: The text prompt describing what to do with the audio.
            audio_files: List of audio file paths or URLs to analyze.
            model: Optional model name to use (if handler has multiple clients).

        Returns:
            The LM's response analyzing or transcribing the audio.
        
        Example:
            transcript = audio_query("Transcribe this audio", ["recording.mp3"])
            analysis = audio_query("What is the speaker's tone?", ["speech.wav"])
        """
        if not self.lm_handler_address:
            return "Error: No LM handler configured"

        try:
            # Build multimodal content list with audio
            content = [{"type": "text", "text": prompt}]
            for audio_file in audio_files:
                if audio_file.startswith(("http://", "https://")):
                    content.append({
                        "type": "audio_url",
                        "url": audio_file
                    })
                else:
                    content.append({
                        "type": "audio_path",
                        "path": audio_file
                    })

            # Send as a message with multimodal content
            multimodal_prompt = [{"role": "user", "content": content}]
            request = LMRequest(prompt=multimodal_prompt, model=model, depth=self.depth)
            response = send_lm_request(self.lm_handler_address, request)

            if not response.success:
                return f"Error: {response.error}"

            # Track this LLM call
            self._pending_llm_calls.append(response.chat_completion)
            return response.chat_completion.response
        except Exception as e:
            return f"Error: Audio query failed - {e}"

    def _speak(self, text: str, output_path: str | None = None) -> str:
        """Generate speech from text using text-to-speech.

        Args:
            text: The text to convert to speech.
            output_path: Optional path to save the audio file. 
                        If not provided, saves to temp directory.

        Returns:
            Path to the generated audio file.
        
        Example:
            audio_path = speak("Hello, this is a test.")
            print(f"Audio saved to: {audio_path}")
        
        Note: This uses the system's TTS capabilities or Gemini's TTS if available.
        """
        import subprocess
        
        # Generate output path if not provided
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f"speech_{uuid.uuid4().hex[:8]}.aiff")
        
        try:
            # Use macOS 'say' command for TTS (works on Mac)
            # This is a fallback - ideally we'd use Gemini's TTS API
            result = subprocess.run(
                ["say", "-o", output_path, text],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return output_path
            else:
                return f"Error: TTS failed - {result.stderr}"
        except FileNotFoundError:
            # 'say' command not available (not macOS)
            # Try using pyttsx3 or other TTS libraries
            try:
                import pyttsx3
                engine = pyttsx3.init()
                if output_path is None:
                    output_path = os.path.join(self.temp_dir, f"speech_{uuid.uuid4().hex[:8]}.mp3")
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                return output_path
            except ImportError:
                return "Error: TTS not available. Install pyttsx3 or use macOS."
        except Exception as e:
            return f"Error: TTS failed - {e}"

    def load_context(self, context_payload: dict | list | str):
        """Load context into the environment as context_0 (and 'context' alias)."""
        self.add_context(context_payload, 0)

    def add_context(
        self, context_payload: dict | list | str, context_index: int | None = None
    ) -> int:
        """
        Add a context with versioned variable name.

        Args:
            context_payload: The context data to add
            context_index: Optional explicit index. If None, auto-increments.

        Returns:
            The context index used.
        """
        if context_index is None:
            context_index = self._context_count

        var_name = f"context_{context_index}"

        if isinstance(context_payload, str):
            context_path = os.path.join(self.temp_dir, f"context_{context_index}.txt")
            with open(context_path, "w") as f:
                f.write(context_payload)
            self.execute_code(f"with open(r'{context_path}', 'r') as f:\n    {var_name} = f.read()")
        else:
            context_path = os.path.join(self.temp_dir, f"context_{context_index}.json")
            with open(context_path, "w") as f:
                json.dump(context_payload, f)
            self.execute_code(
                f"import json\nwith open(r'{context_path}', 'r') as f:\n    {var_name} = json.load(f)"
            )

        # Alias context_0 as 'context' for backward compatibility
        if context_index == 0:
            self.execute_code(f"context = {var_name}")

        self._context_count = max(self._context_count, context_index + 1)
        return context_index

    def update_handler_address(self, address: tuple[str, int]) -> None:
        """Update the LM handler address for a new completion call."""
        self.lm_handler_address = address

    def get_context_count(self) -> int:
        """Return the number of contexts loaded."""
        return self._context_count

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        """
        Store a conversation's message history as a versioned variable.

        Args:
            message_history: The list of message dicts from a completion call
            history_index: Optional explicit index. If None, auto-increments.

        Returns:
            The history index used.
        """
        if history_index is None:
            history_index = self._history_count

        var_name = f"history_{history_index}"

        # Store deep copy to avoid reference issues with nested dicts
        self.locals[var_name] = copy.deepcopy(message_history)

        # Alias history_0 as 'history' for convenience
        if history_index == 0:
            self.locals["history"] = self.locals[var_name]

        self._history_count = max(self._history_count, history_index + 1)
        return history_index

    def get_history_count(self) -> int:
        """Return the number of conversation histories stored."""
        return self._history_count

    @contextmanager
    def _capture_output(self):
        """Thread-safe context manager to capture stdout/stderr."""
        with self._lock:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
            try:
                sys.stdout, sys.stderr = stdout_buf, stderr_buf
                yield stdout_buf, stderr_buf
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

    @contextmanager
    def _temp_cwd(self):
        """Temporarily change to temp directory for execution."""
        old_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            yield
        finally:
            os.chdir(old_cwd)

    def execute_code(self, code: str) -> REPLResult:
        """Execute code in the persistent namespace and return result."""
        start_time = time.perf_counter()

        # Clear pending LLM calls from previous execution
        self._pending_llm_calls = []

        with self._capture_output() as (stdout_buf, stderr_buf), self._temp_cwd():
            try:
                combined = {**self.globals, **self.locals}
                exec(code, combined, combined)

                # Update locals with new variables
                for key, value in combined.items():
                    if key not in self.globals and not key.startswith("_"):
                        self.locals[key] = value

                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue()
            except Exception as e:
                stdout = stdout_buf.getvalue()
                stderr = stderr_buf.getvalue() + f"\n{type(e).__name__}: {e}"

        return REPLResult(
            stdout=stdout,
            stderr=stderr,
            locals=self.locals.copy(),
            execution_time=time.perf_counter() - start_time,
            rlm_calls=self._pending_llm_calls.copy(),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    def cleanup(self):
        """Clean up temp directory and reset state."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        self.globals.clear()
        self.locals.clear()

    def __del__(self):
        self.cleanup()
