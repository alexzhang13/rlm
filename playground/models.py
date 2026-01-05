"""Pydantic models for RLM playground API requests and responses."""

from typing import Any, Literal

from pydantic import BaseModel, Field

ClientBackend = Literal["openai", "portkey", "openrouter", "vllm", "litellm", "anthropic"]
EnvironmentType = Literal["local", "prime", "modal"]


class RunRequest(BaseModel):
    """Request model for running RLM completion."""

    prompt: str | dict[str, Any] = Field(..., description="Main prompt/context for the RLM")
    root_prompt: str | None = Field(None, description="Optional root prompt visible to the root LM")
    backend: ClientBackend = Field("openai", description="LM provider backend")
    backend_kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Backend-specific configuration (model_name, api_key, etc.)",
    )
    environment: EnvironmentType = Field("local", description="Execution environment type")
    environment_kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Environment-specific configuration"
    )
    max_iterations: int = Field(30, ge=1, le=100, description="Maximum number of RLM iterations")
    max_depth: int = Field(
        1, ge=0, le=1, description="Maximum recursion depth (currently only 0 or 1)"
    )
    other_backends: list[ClientBackend] | None = Field(
        None, description="Additional backends for sub-calls"
    )
    other_backend_kwargs: list[dict[str, Any]] | None = Field(
        None, description="Configuration for additional backends"
    )
    enable_logging: bool = Field(False, description="Whether to save logs to file")


class RunResponse(BaseModel):
    """Response model for RLM completion result."""

    success: bool = Field(..., description="Whether the completion succeeded")
    response: str | None = Field(None, description="Final answer from RLM")
    root_model: str | None = Field(None, description="Model name used")
    execution_time: float | None = Field(None, description="Total execution time in seconds")
    usage_summary: dict[str, Any] | None = Field(None, description="Token usage summary per model")
    error: str | None = Field(None, description="Error message if completion failed")
