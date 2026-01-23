"""
Communication utilities for RLM socket protocol.

Protocol: 4-byte big-endian length prefix + JSON payload.
Used for communication between LMHandler and environment subprocesses.
"""

import json
import socket
import struct
from dataclasses import dataclass
from typing import Any

from rlm.core.types import RLMChatCompletion

# =============================================================================
# Message Dataclasses
# =============================================================================


@dataclass
class LMRequest:
    """Request message sent to the LM Handler.

    Supports both single prompt (prompt field) and batched prompts (prompts field).
    """

    prompt: str | dict[str, Any] | None = None
    prompts: list[str | dict[str, Any]] | None = None
    model: str | None = None
    depth: int = 0

    @property
    def is_batched(self) -> bool:
        """Check if this is a batched request."""
        return self.prompts is not None and len(self.prompts) > 0

    def to_dict(self) -> dict:
        """Convert to dict, excluding None values."""
        d = {}
        if self.prompt is not None:
            d["prompt"] = self.prompt
        if self.prompts is not None:
            d["prompts"] = self.prompts
        if self.model is not None:
            d["model"] = self.model
        d["depth"] = self.depth
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "LMRequest":
        """Create from dict."""
        return cls(
            prompt=data.get("prompt"),
            prompts=data.get("prompts"),
            model=data.get("model"),
            depth=data.get("depth", -1),  # TODO: Default should throw an error
        )


@dataclass
class LMResponse:
    """Response message from the LM Handler.

    Supports both single response (chat_completion) and batched responses (chat_completions).
    """

    error: str | None = None
    chat_completion: RLMChatCompletion | None = None
    chat_completions: list[RLMChatCompletion] | None = None

    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return self.error is None

    @property
    def is_batched(self) -> bool:
        """Check if this is a batched response."""
        return self.chat_completions is not None

    def to_dict(self) -> dict:
        """Convert to dict, excluding None values."""
        if self.error is not None:
            return {
                "error": self.error,
                "chat_completion": None,
                "chat_completions": None,
            }
        if self.chat_completions is not None:
            return {
                "chat_completions": [c.to_dict() for c in self.chat_completions],
                "chat_completion": None,
                "error": None,
            }
        if self.chat_completion is not None:
            return {
                "chat_completion": self.chat_completion.to_dict(),
                "chat_completions": None,
                "error": None,
            }
        return {
            "error": "No chat completion or error provided.",
            "chat_completion": None,
            "chat_completions": None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LMResponse":
        """Create from dict."""
        chat_completions = None
        if data.get("chat_completions"):
            chat_completions = [RLMChatCompletion.from_dict(c) for c in data["chat_completions"]]

        chat_completion = None
        if data.get("chat_completion"):
            chat_completion = RLMChatCompletion.from_dict(data["chat_completion"])

        return cls(
            error=data.get("error"),
            chat_completion=chat_completion,
            chat_completions=chat_completions,
        )

    @classmethod
    def success_response(cls, chat_completion: RLMChatCompletion) -> "LMResponse":
        """Create a successful single response."""
        return cls(chat_completion=chat_completion)

    @classmethod
    def batched_success_response(cls, chat_completions: list[RLMChatCompletion]) -> "LMResponse":
        """Create a successful batched response."""
        return cls(chat_completions=chat_completions)

    @classmethod
    def error_response(cls, error: str) -> "LMResponse":
        """Create an error response."""
        return cls(error=error)


# =============================================================================
# Socket Protocol Helpers
# =============================================================================


def socket_send(sock: socket.socket, data: dict) -> None:
    """Send a length-prefixed JSON message over socket.

    Protocol: 4-byte big-endian length prefix + UTF-8 JSON payload.
    """
    payload = json.dumps(data).encode("utf-8")
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def socket_recv(sock: socket.socket) -> dict:
    """Receive a length-prefixed JSON message from socket.

    Protocol: 4-byte big-endian length prefix + UTF-8 JSON payload.
    Returns empty dict if connection closed before length received.

    Raises:
        ConnectionError: If connection closes mid-message.
    """
    raw_len = sock.recv(4)
    if not raw_len:
        return {}

    length = struct.unpack(">I", raw_len)[0]
    payload = b""
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            raise ConnectionError("Connection closed before message complete")
        payload += chunk

    return json.loads(payload.decode("utf-8"))


def socket_request(address: tuple[str, int], data: dict, timeout: int = 300) -> dict:
    """Send a request and receive a response over a new socket connection.

    Opens a new TCP connection, sends the request, waits for response, then closes.

    Args:
        address: (host, port) tuple to connect to.
        data: Dictionary to send as JSON.
        timeout: Socket timeout in seconds (default 300).

    Returns:
        Response dictionary.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(address)
        socket_send(sock, data)
        return socket_recv(sock)


# =============================================================================
# Typed Request Helpers
# =============================================================================


def send_lm_request(
    address: tuple[str, int], request: LMRequest, timeout: int = 300, depth: int | None = None
) -> LMResponse:
    """Send an LM request and return typed response.

    Args:
        address: (host, port) tuple of LM Handler server.
        request: LMRequest to send.
        timeout: Socket timeout in seconds.
        depth: Optional depth to override request depth.

    Returns:
        LMResponse with content or error.
    """
    try:
        if depth is not None:
            request.depth = depth
        response_data = socket_request(address, request.to_dict(), timeout)
        return LMResponse.from_dict(response_data)
    except Exception as e:
        return LMResponse.error_response(f"Request failed: {e}")


def send_lm_request_batched(
    address: tuple[str, int],
    prompts: list[str | dict[str, Any]],
    model: str | None = None,
    timeout: int = 300,
    depth: int = 0,
) -> list[LMResponse]:
    """Send a batched LM request and return a list of typed responses.

    Args:
        address: (host, port) tuple of LM Handler server.
        prompts: List of prompts to send.
        model: Optional model name to use.
        timeout: Socket timeout in seconds.
        depth: Depth for routing (default 0).

    Returns:
        List of LMResponse objects, one per prompt, in the same order.
    """
    try:
        request = LMRequest(prompts=prompts, model=model, depth=depth)
        response_data = socket_request(address, request.to_dict(), timeout)
        response = LMResponse.from_dict(response_data)

        if not response.success:
            # Return error responses for all prompts
            return [LMResponse.error_response(response.error)] * len(prompts)

        if response.chat_completions is None:
            return [LMResponse.error_response("No completions returned")] * len(prompts)

        # Convert batched response to list of individual responses
        return [
            LMResponse.success_response(chat_completion)
            for chat_completion in response.chat_completions
        ]
    except Exception as e:
        return [LMResponse.error_response(f"Request failed: {e}")] * len(prompts)
