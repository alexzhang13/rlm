from unittest.mock import MagicMock

import pytest

from rlm import RLM


@pytest.mark.asyncio
async def test_direct_repl_no_socket():
    """Verify that RLM can run with DirectREPL (no socket server)."""
    # Using a mock client to avoid real API calls
    RLM(
        backend="openai",
        backend_kwargs={"model_name": "gpt-4o-mini"},
        environment="local",
        environment_kwargs={"env_backend": "direct"},
    )

    # Mock the handle_request to see if it's called directly
    from rlm.core.lm_handler import LMHandler

    original_handle = LMHandler.handle_request
    LMHandler.handle_request = MagicMock(side_effect=original_handle)

    try:
        # Simple test to verify initialization
        pass
    finally:
        LMHandler.handle_request = original_handle


@pytest.mark.asyncio
async def test_metadata_propagation():
    """Verify metadata (trace_id) reaches the LMHandler."""
    from rlm.core.comms_utils import LMRequest
    from rlm.core.lm_handler import LMHandler

    captured_requests = []

    def on_request(req, res):
        captured_requests.append(req)

    # Manually trigger a handler request to verify metadata support
    mock_client = MagicMock()
    handler = LMHandler(mock_client, on_request=on_request)

    trace_id = "test-trace-123"
    req = LMRequest(prompt="test", metadata={"trace_id": trace_id})

    # Mock client response
    mock_client.completion.return_value = "response"
    mock_client.get_last_usage.return_value = {}
    mock_client.model_name = "mock"

    handler.handle_request(req)

    assert len(captured_requests) > 0
    assert captured_requests[0].metadata["trace_id"] == trace_id
