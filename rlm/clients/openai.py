import asyncio
import logging
import os
import threading
import time as _time
from collections import defaultdict
from typing import Any

import httpx
import openai
from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# Request Tracker — logs every OpenAI API call for diagnostics
# =============================================================================


class RequestTracker:
    """Thread-safe tracker for all OpenAI API call attempts including token usage."""

    def __init__(self):
        self._lock = threading.Lock()
        self.total = 0
        self.successful = 0
        self.rate_limited = 0
        self.timed_out = 0
        self.connection_errors = 0
        self.other_errors = 0
        self._active = 0
        self.peak_concurrent = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.model_stats: dict[str, dict[str, int]] = {}

    def _ensure_model(self, model: str) -> None:
        if model not in self.model_stats:
            self.model_stats[model] = {
                "total": 0,
                "success": 0,
                "rate_limited": 0,
                "timed_out": 0,
                "conn_error": 0,
                "other_error": 0,
                "input_tokens": 0,
                "output_tokens": 0,
            }

    def start_request(self, model: str) -> float:
        """Record a new API call attempt. Returns start timestamp."""
        with self._lock:
            self.total += 1
            self._active += 1
            self.peak_concurrent = max(self.peak_concurrent, self._active)
            self._ensure_model(model)
            self.model_stats[model]["total"] += 1
        return _time.perf_counter()

    def end_request(
        self,
        model: str,
        start: float,
        error: BaseException | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record completion of an API call attempt with optional token usage."""
        duration = _time.perf_counter() - start
        with self._lock:
            self._active -= 1
            concurrent = self._active
            self._ensure_model(model)
            if error is None:
                self.successful += 1
                self.model_stats[model]["success"] += 1
                status = "SUCCESS"
            elif isinstance(error, RateLimitError):
                self.rate_limited += 1
                self.model_stats[model]["rate_limited"] += 1
                status = "RATE_LIMITED"
            elif isinstance(error, APITimeoutError):
                self.timed_out += 1
                self.model_stats[model]["timed_out"] += 1
                status = "TIMEOUT"
            elif isinstance(error, APIConnectionError):
                self.connection_errors += 1
                self.model_stats[model]["conn_error"] += 1
                status = "CONN_ERROR"
            else:
                self.other_errors += 1
                self.model_stats[model]["other_error"] += 1
                status = "ERROR"
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.model_stats[model]["input_tokens"] += input_tokens
            self.model_stats[model]["output_tokens"] += output_tokens

        log_fn = logger.debug if error is None else logger.warning
        tok_detail = f" | in={input_tokens} out={output_tokens}" if input_tokens else ""
        err_detail = f" | {type(error).__name__}: {str(error)[:200]}" if error else ""
        log_fn(
            "OpenAI %s | model=%s | %.2fs | active=%d%s%s",
            status,
            model,
            duration,
            concurrent,
            tok_detail,
            err_detail,
        )

    @property
    def active(self) -> int:
        return self._active

    def summary(self) -> str:
        with self._lock:
            total_tokens = self.total_input_tokens + self.total_output_tokens
            lines = [
                f"OpenAI Requests: {self.total} total, {self.successful} ok, "
                f"{self.rate_limited} rate-limited, {self.timed_out} timed-out, "
                f"{self.connection_errors} conn-errors, {self.other_errors} other-errors, "
                f"peak_concurrent={self.peak_concurrent}, "
                f"tokens={total_tokens:,} (in={self.total_input_tokens:,} out={self.total_output_tokens:,})",
            ]
            for model, s in sorted(self.model_stats.items()):
                mtok = s["input_tokens"] + s["output_tokens"]
                lines.append(
                    f"  {model}: {s['total']} total, {s['success']} ok, "
                    f"{s['rate_limited']} rate-limited, {s['timed_out']} timed-out, "
                    f"{s['conn_error']} conn-errors, {s['other_error']} other-errors, "
                    f"tokens={mtok:,} (in={s['input_tokens']:,} out={s['output_tokens']:,})"
                )
            return "\n".join(lines)


request_tracker = RequestTracker()


# Per-model concurrency limiters — caps simultaneous OpenAI API calls across all threads.
# threading.BoundedSemaphore is used (not asyncio.Semaphore) because _handle_batched()
# runs asyncio.run() in separate threads, each with its own event loop.
_MAX_CONCURRENT_DEFAULT = max(1, min(int(os.getenv("OPENAI_MAX_CONCURRENT_REQUESTS", "50")), 500))
_MAX_CONCURRENT_MINI = max(
    1, min(int(os.getenv("OPENAI_MAX_CONCURRENT_REQUESTS_MINI", "150")), 1000)
)
_semaphores: dict[str, threading.BoundedSemaphore] = {}
_semaphore_lock = threading.Lock()


def _get_semaphore(model: str) -> threading.BoundedSemaphore:
    """Get or create a per-model semaphore. Mini models get a higher limit."""
    if model not in _semaphores:
        with _semaphore_lock:
            if model not in _semaphores:
                limit = _MAX_CONCURRENT_MINI if "mini" in model.lower() else _MAX_CONCURRENT_DEFAULT
                _semaphores[model] = threading.BoundedSemaphore(limit)
                logger.info("Created semaphore for %s: max_concurrent=%d", model, limit)
    return _semaphores[model]


def _synthetic_rate_limit_error(message: str) -> RateLimitError:
    """Create a synthetic RateLimitError for semaphore timeouts."""
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(status_code=429, text=message, request=request)
    return RateLimitError(message=message, response=response, body=None)


# Retry configuration for rate limits and timeouts
_RETRY_CONFIG = {
    "retry": retry_if_exception_type((RateLimitError, APITimeoutError)),
    "wait": wait_exponential_jitter(initial=1, max=60, jitter=5),
    "stop": stop_after_attempt(5),
    "reraise": True,
    "before_sleep": before_sleep_log(logger, logging.WARNING),
}

# Load API keys from environment variables
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_VERCEL_API_KEY = os.getenv("AI_GATEWAY_API_KEY")
DEFAULT_PRIME_INTELLECT_BASE_URL = "https://api.pinference.ai/api/v1/"


class OpenAIClient(BaseLM):
    """
    LM Client for running models with the OpenAI API. Works with vLLM as well.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        reasoning_effort: str | None = None,
        **kwargs,
    ):
        super().__init__(model_name=model_name, **kwargs)
        self.reasoning_effort = reasoning_effort  # none, minimal, low, medium, high, xhigh

        if api_key is None:
            if base_url == "https://api.openai.com/v1" or base_url is None:
                api_key = DEFAULT_OPENAI_API_KEY
            elif base_url == "https://openrouter.ai/api/v1":
                api_key = DEFAULT_OPENROUTER_API_KEY
            elif base_url == "https://ai-gateway.vercel.sh/v1":
                api_key = DEFAULT_VERCEL_API_KEY

        # For vLLM, set base_url to local vLLM server address.
        import httpx

        _timeout = httpx.Timeout(600.0, connect=10.0)
        self.client = openai.OpenAI(
            api_key=api_key, base_url=base_url, timeout=_timeout, max_retries=3
        )
        self.async_client = openai.AsyncOpenAI(
            api_key=api_key, base_url=base_url, timeout=_timeout, max_retries=3
        )
        self.model_name = model_name

        # Per-model usage tracking
        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_total_tokens: dict[str, int] = defaultdict(int)

    @retry(**_RETRY_CONFIG)
    def completion(
        self,
        prompt: str | list[dict[str, Any]],
        model: str | None = None,
        response_format: dict | None = None,
    ) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for OpenAI client.")

        extra_body = {}
        if self.client.base_url == DEFAULT_PRIME_INTELLECT_BASE_URL:
            extra_body["usage"] = {"include": True}

        kwargs = {"model": model, "messages": messages}
        if extra_body:
            kwargs["extra_body"] = extra_body
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if response_format is not None:
            kwargs["response_format"] = response_format

        sem = _get_semaphore(model)
        if not sem.acquire(timeout=120):
            raise _synthetic_rate_limit_error(f"Semaphore timeout waiting for {model} slot")
        try:
            t0 = request_tracker.start_request(model)
            try:
                response = self.client.chat.completions.create(**kwargs)
                self._track_cost(response, model)
                usage = getattr(response, "usage", None)
                request_tracker.end_request(
                    model,
                    t0,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                )
                return response.choices[0].message.content
            except BaseException as exc:
                request_tracker.end_request(model, t0, error=exc)
                raise
        finally:
            sem.release()

    @retry(**_RETRY_CONFIG)
    async def acompletion(
        self,
        prompt: str | list[dict[str, Any]],
        model: str | None = None,
        response_format: dict | None = None,
    ) -> str:
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            messages = prompt
        else:
            raise ValueError(f"Invalid prompt type: {type(prompt)}")

        model = model or self.model_name
        if not model:
            raise ValueError("Model name is required for OpenAI client.")

        extra_body = {}
        if self.client.base_url == DEFAULT_PRIME_INTELLECT_BASE_URL:
            extra_body["usage"] = {"include": True}

        kwargs = {"model": model, "messages": messages}
        if extra_body:
            kwargs["extra_body"] = extra_body
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        if response_format is not None:
            kwargs["response_format"] = response_format

        sem = _get_semaphore(model)
        acquired = await asyncio.to_thread(sem.acquire, timeout=120)
        if not acquired:
            raise _synthetic_rate_limit_error(f"Semaphore timeout waiting for {model} slot")
        try:
            t0 = request_tracker.start_request(model)
            try:
                response = await self.async_client.chat.completions.create(**kwargs)
                self._track_cost(response, model)
                usage = getattr(response, "usage", None)
                request_tracker.end_request(
                    model,
                    t0,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                )
                return response.choices[0].message.content
            except BaseException as exc:
                request_tracker.end_request(model, t0, error=exc)
                raise
        finally:
            sem.release()

    def _track_cost(self, response: openai.ChatCompletion, model: str):
        self.model_call_counts[model] += 1

        usage = getattr(response, "usage", None)
        if usage is None:
            raise ValueError("No usage data received. Tracking tokens not possible.")

        self.model_input_tokens[model] += usage.prompt_tokens
        self.model_output_tokens[model] += usage.completion_tokens
        self.model_total_tokens[model] += usage.total_tokens

        # Track last call for handler to read
        self.last_prompt_tokens = usage.prompt_tokens
        self.last_completion_tokens = usage.completion_tokens

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
