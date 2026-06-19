from unittest.mock import patch

import pytest

from rlm.clients import get_client
from rlm.clients.mlx import MLXClient
from rlm.core.types import ModelUsageSummary, UsageSummary


def test_get_client_routes_mlx():
    client = get_client("mlx", {"model_name": "local-model"})

    assert isinstance(client, MLXClient)
    assert client.model_name == "local-model"


def test_mlx_completion_uses_configured_model_path_and_tracks_usage():
    with patch("rlm.clients.mlx.generate_mlx", return_value="hello from mlx") as generate:
        client = MLXClient(model_name="local-model", model_path="/models/local-model")
        result = client.completion(
            [{"role": "user", "content": "Say hello"}],
            max_tokens=7,
            temperature=0.2,
        )

    assert result == "hello from mlx"
    generate.assert_called_once()
    assert generate.call_args.kwargs["prompt"] == "user: Say hello"
    assert generate.call_args.kwargs["model_path"] == "/models/local-model"
    assert generate.call_args.kwargs["max_tokens"] == 7
    assert generate.call_args.kwargs["temperature"] == 0.2

    summary = client.get_usage_summary()
    assert isinstance(summary, UsageSummary)
    assert summary.total_cost == 0.0
    assert summary.model_usage_summaries["local-model"].total_calls == 1

    last_usage = client.get_last_usage()
    assert isinstance(last_usage, ModelUsageSummary)
    assert last_usage.total_calls == 1
    assert last_usage.total_cost == 0.0


def test_mlx_completion_can_override_model_path_per_call():
    with patch("rlm.clients.mlx.generate_mlx", return_value="override") as generate:
        client = MLXClient(model_name="local-model")
        result = client.completion("hello", model="other-model")

    assert result == "override"
    assert generate.call_args.kwargs["model_path"] == "other-model"
    assert client.get_usage_summary().model_usage_summaries["other-model"].total_calls == 1


def test_mlx_completion_tracks_model_path_override_usage():
    with patch("rlm.clients.mlx.generate_mlx", return_value="override") as generate:
        client = MLXClient(model_name="local-model")
        result = client.completion("hello", model_path="/models/override")

    assert result == "override"
    assert generate.call_args.kwargs["model_path"] == "/models/override"
    assert client.get_usage_summary().model_usage_summaries["/models/override"].total_calls == 1


def test_mlx_client_requires_model_configuration():
    with pytest.raises(ValueError, match="model_name or model_path"):
        MLXClient()


def test_mlx_completion_rejects_invalid_prompt():
    client = MLXClient(model_name="local-model")

    with pytest.raises(ValueError, match="Invalid prompt type"):
        client.completion(123)


def test_generate_mlx_missing_optional_dependency_message():
    with pytest.raises(ImportError, match=r"pip install 'rlms\[mlx\]'"):
        from rlm.clients.mlx import generate_mlx

        generate_mlx("hello", model_path="missing-model")
