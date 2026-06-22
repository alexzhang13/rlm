import base64
import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

TOKEN_EXPIRY_SKEW_SECONDS = 60


class LiteLLMResponsesClient(BaseLM):
    """LiteLLM Responses API client.

    This is primarily used for LiteLLM's ``chatgpt/`` provider, which can spend
    an existing ChatGPT/Codex session quota without an OpenAI API key.
    """

    def __init__(
        self,
        model_name: str | None = None,
        sampling_args: dict[str, Any] | None = None,
        use_codex_auth: bool = True,
        codex_auth_file: str | None = None,
        **kwargs,
    ):
        if not model_name:
            raise ValueError("Model name is required for LiteLLM Responses client.")
        super().__init__(model_name=model_name, sampling_args=sampling_args, **kwargs)
        self.use_codex_auth = use_codex_auth
        self.codex_auth_file = codex_auth_file

        self.model_call_counts: dict[str, int] = defaultdict(int)
        self.model_input_tokens: dict[str, int] = defaultdict(int)
        self.model_output_tokens: dict[str, int] = defaultdict(int)
        self.model_costs: dict[str, float] = defaultdict(float)
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_cost: float | None = None

    def completion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        litellm = _import_litellm()
        model = model or self.model_name
        self._install_auth_patch_if_needed(model)

        response = litellm.responses(
            model=model,
            input=_to_responses_input(prompt),
            timeout=self.timeout,
            **self._responses_kwargs(),
        )
        self._track_usage(response, model)
        return _response_text(response)

    async def acompletion(
        self, prompt: str | list[dict[str, Any]], model: str | None = None
    ) -> str:
        litellm = _import_litellm()
        model = model or self.model_name
        self._install_auth_patch_if_needed(model)

        response = await litellm.aresponses(
            model=model,
            input=_to_responses_input(prompt),
            timeout=self.timeout,
            **self._responses_kwargs(),
        )
        self._track_usage(response, model)
        return _response_text(response)

    def get_usage_summary(self) -> UsageSummary:
        model_summaries = {}
        for model in self.model_call_counts:
            cost = self.model_costs.get(model)
            model_summaries[model] = ModelUsageSummary(
                total_calls=self.model_call_counts[model],
                total_input_tokens=self.model_input_tokens[model],
                total_output_tokens=self.model_output_tokens[model],
                total_cost=cost if cost else None,
            )
        return UsageSummary(model_usage_summaries=model_summaries)

    def get_last_usage(self) -> ModelUsageSummary:
        return ModelUsageSummary(
            total_calls=1,
            total_input_tokens=self.last_prompt_tokens,
            total_output_tokens=self.last_completion_tokens,
            total_cost=self.last_cost,
        )

    def _responses_kwargs(self) -> dict[str, Any]:
        kwargs = _normalize_sampling_args(self.sampling_args)
        for key in ("api_key", "base_url", "custom_llm_provider"):
            value = self.kwargs.get(key)
            if value:
                kwargs[key] = value
        return kwargs

    def _install_auth_patch_if_needed(self, model: str) -> None:
        if self.use_codex_auth and model.startswith("chatgpt/"):
            _install_codex_auth_patch(self.codex_auth_file)

    def _track_usage(self, response: Any, model: str) -> None:
        usage = _get_value(response, "usage")
        prompt_tokens = int(_first_value(usage, "input_tokens", "prompt_tokens") or 0)
        completion_tokens = int(
            _first_value(usage, "output_tokens", "completion_tokens") or 0
        )
        cost = _optional_float(_get_value(usage, "cost", default=None))

        self.model_call_counts[model] += 1
        self.model_input_tokens[model] += prompt_tokens
        self.model_output_tokens[model] += completion_tokens
        if cost is not None and cost > 0:
            self.model_costs[model] += cost

        self.last_prompt_tokens = prompt_tokens
        self.last_completion_tokens = completion_tokens
        self.last_cost = cost


def _import_litellm():
    try:
        import litellm
    except ImportError as exc:
        raise RuntimeError(
            "LiteLLM is required for backend='litellm_responses'. Install the "
            "benchmark extra with `uv sync --extra benchmark --extra dev`, or "
            "run with `uv run --with litellm ...`."
        ) from exc
    return litellm


def _normalize_sampling_args(sampling_args: dict[str, Any]) -> dict[str, Any]:
    args = {k: v for k, v in dict(sampling_args or {}).items() if v is not None}
    if "max_tokens" in args and "max_output_tokens" not in args:
        args["max_output_tokens"] = args.pop("max_tokens")
    return args


def _to_responses_input(
    prompt: str | list[dict[str, Any]],
) -> str | list[dict[str, Any]]:
    if isinstance(prompt, str):
        return [{"role": "user", "content": prompt}]
    if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
        return prompt
    raise ValueError(f"Invalid prompt type: {type(prompt)}")


def _response_text(response: Any) -> str:
    output_text = _get_value(response, "output_text", default=None)
    if isinstance(output_text, str) and output_text:
        return output_text

    parts: list[str] = []
    for output_item in _get_value(response, "output", default=[]) or []:
        for content_item in _get_value(output_item, "content", default=[]) or []:
            text = _get_value(content_item, "text", default=None)
            if isinstance(text, str):
                parts.append(text)
    if parts:
        return "".join(parts)

    if hasattr(response, "model_dump"):
        dumped = response.model_dump()
        if isinstance(dumped, dict):
            return _response_text(dumped)

    return str(response)


def _get_value(value: Any, *keys: str, default: Any = None) -> Any:
    current = value
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            current = getattr(current, key, default)
    return current


def _first_value(value: Any, *keys: str) -> Any:
    for key in keys:
        candidate = _get_value(value, key, default=None)
        if candidate is not None:
            return candidate
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _install_codex_auth_patch(codex_auth_file: str | None) -> None:
    from litellm.llms.chatgpt import authenticator as auth_module

    authenticator = auth_module.Authenticator
    if codex_auth_file:
        authenticator._rlm_codex_auth_file = codex_auth_file
    elif not getattr(authenticator, "_rlm_codex_auth_file", None):
        default_auth_file = _default_codex_auth_file()
        if default_auth_file is not None:
            authenticator._rlm_codex_auth_file = str(default_auth_file)

    if getattr(authenticator, "_rlm_codex_auth_patch", False):
        return

    original_get_access_token = authenticator.get_access_token
    original_get_account_id = authenticator.get_account_id

    def get_access_token(self) -> str:
        auth_file = getattr(authenticator, "_rlm_codex_auth_file", None)
        tokens = _read_codex_tokens(auth_file)
        access_token = tokens.get("access_token")
        if access_token:
            if _token_expired(access_token):
                default_auth = Path(getattr(self, "auth_file", ""))
                if default_auth.exists():
                    return original_get_access_token(self)
                raise RuntimeError(
                    "Codex ChatGPT access token is expired. Run "
                    "`codex doctor --summary` or refresh Codex auth, then retry."
                )
            return access_token
        return original_get_access_token(self)

    def get_account_id(self) -> str | None:
        auth_file = getattr(authenticator, "_rlm_codex_auth_file", None)
        tokens = _read_codex_tokens(auth_file)
        account_id = tokens.get("account_id")
        if account_id:
            return account_id
        token = tokens.get("id_token") or tokens.get("access_token")
        derived = self._extract_account_id(token)
        if derived:
            return derived
        return original_get_account_id(self)

    authenticator.get_access_token = get_access_token
    authenticator.get_account_id = get_account_id
    authenticator._rlm_codex_auth_patch = True


def _default_codex_auth_file() -> Path | None:
    candidates = []
    for env_name in ("RLM_BENCHMARK_CODEX_AUTH_FILE", "CODEX_AUTH_FILE"):
        value = os.getenv(env_name)
        if value:
            candidates.append(Path(value).expanduser())

    codex_home = os.getenv("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home).expanduser() / "auth.json")
    candidates.append(Path("~/.codex/auth.json").expanduser())

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _read_codex_tokens(auth_file: str | None) -> dict[str, str]:
    if not auth_file:
        return {}
    path = Path(auth_file).expanduser()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}
    tokens = data.get("tokens") if isinstance(data.get("tokens"), dict) else data
    values: dict[str, str] = {}
    for key in ("access_token", "refresh_token", "id_token", "account_id"):
        value = tokens.get(key)
        if isinstance(value, str) and value:
            values[key] = value
    return values


def _token_expired(token: str) -> bool:
    claims = _decode_jwt_claims(token)
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)):
        return False
    return time.time() >= float(exp) - TOKEN_EXPIRY_SKEW_SECONDS


def _decode_jwt_claims(token: str) -> dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except Exception:
        return {}
