"""
LMHandler - Routes LLM requests from the RLM process and environment subprocesses.

Uses a multi-threaded socket server. Protocol: 4-byte length prefix + JSON payload.
"""

import asyncio
import time
from socketserver import StreamRequestHandler, ThreadingTCPServer
from threading import Thread

from rlm.clients.base_lm import BaseLM
from rlm.core.comms_utils import LMRequest, LMResponse, socket_recv, socket_send
from rlm.core.types import RLMChatCompletion, UsageSummary


class LMRequestHandler(StreamRequestHandler):
    """Socket handler for LLM completion requests."""

    def handle(self):
        try:
            request_data = socket_recv(self.connection)
            if not isinstance(request_data, dict):
                response = LMResponse.error_response("Request must be a JSON object")
                self._safe_send(response)
                return

            request = LMRequest.from_dict(request_data)
            handler: LMHandler = self.server.lm_handler  # type: ignore

            if request.is_batched:
                # Batched request: process multiple prompts concurrently
                response = self._handle_batched(request, handler)
            elif request.prompt:
                # Single request: process one prompt
                response = self._handle_single(request, handler)
            else:
                response = LMResponse.error_response("Missing 'prompt' or 'prompts' in request.")

            self._safe_send(response)

        except (BrokenPipeError, ConnectionError, ConnectionResetError, OSError):
            # Client disconnected - this is expected during parallel execution
            # when workers complete and close their sockets. Silently ignore.
            pass

        except Exception as e:
            # Try to send error response, but don't fail if socket is broken
            response = LMResponse.error_response(str(e))
            self._safe_send(response)

    def _safe_send(self, response: LMResponse) -> bool:
        """Send response, returning False if the socket is broken."""
        try:
            socket_send(self.connection, response.to_dict())
            return True
        except (BrokenPipeError, ConnectionError, ConnectionResetError, OSError):
            # Client disconnected - silently ignore
            return False

    def _handle_single(self, request: LMRequest, handler: "LMHandler") -> LMResponse:
        """Handle a single prompt request."""
        client = handler.get_client(request.model, request.depth)

        start_time = time.perf_counter()
        content = client.completion(request.prompt)
        end_time = time.perf_counter()

        model_usage = client.get_last_usage()
        root_model = request.model or client.model_name
        usage_summary = UsageSummary(model_usage_summaries={root_model: model_usage})
        return LMResponse.success_response(
            chat_completion=RLMChatCompletion(
                root_model=root_model,
                prompt=request.prompt,
                response=content,
                usage_summary=usage_summary,
                execution_time=end_time - start_time,
            )
        )

    def _handle_batched(self, request: LMRequest, handler: "LMHandler") -> LMResponse:
        """Handle a batched prompts request using async for concurrency."""
        client = handler.get_client(request.model, request.depth)

        start_time = time.perf_counter()

        async def run_all():
            tasks = [client.acompletion(prompt) for prompt in request.prompts]
            return await asyncio.gather(*tasks)

        results = asyncio.run(run_all())
        end_time = time.perf_counter()

        total_time = end_time - start_time
        model_usage = client.get_last_usage()
        root_model = request.model or client.model_name
        usage_summary = UsageSummary(model_usage_summaries={root_model: model_usage})

        chat_completions = [
            RLMChatCompletion(
                root_model=root_model,
                prompt=prompt,
                response=content,
                usage_summary=usage_summary,
                execution_time=total_time / len(request.prompts),  # approximate per-prompt time
            )
            for prompt, content in zip(request.prompts, results, strict=True)
        ]

        return LMResponse.batched_success_response(chat_completions=chat_completions)


class ThreadingLMServer(ThreadingTCPServer):
    """Multi-threaded TCP server for LM requests."""

    daemon_threads = True
    allow_reuse_address = True


class LMHandler:
    """
    Handles all LM calls from the RLM main process and environment subprocesses.

    Uses a multi-threaded socket server for concurrent requests.
    Protocol: 4-byte big-endian length prefix + JSON payload.
    """

    def __init__(
        self,
        client: BaseLM,
        host: str = "127.0.0.1",
        port: int = 0,  # auto-assign available port
        other_backend_client: BaseLM | None = None,
    ):
        self.default_client = client
        self.other_backend_client = other_backend_client
        self.clients: dict[str, BaseLM] = {}
        self.host = host
        self._server: ThreadingLMServer | None = None
        self._thread: Thread | None = None
        self._port = port

        self.register_client(client.model_name, client)

    def register_client(self, model_name: str, client: BaseLM) -> None:
        """Register a client for a specific model name."""
        self.clients[model_name] = client

    def get_client(self, model: str | None = None, depth: int = 0) -> BaseLM:
        """Get client by model name or depth, or return default.

        Routing logic:
        - depth=0: use default_client (main backend)
        - depth=1: use other_backend_client if it exists, otherwise default_client
        - If model is specified and exists in clients, use that (overrides depth routing)
        """
        if model and model in self.clients:
            return self.clients[model]

        # Route based on depth
        if depth == 1 and self.other_backend_client is not None:
            return self.other_backend_client

        return self.default_client

    @property
    def port(self) -> int:
        """Get the actual port (useful when auto-assigned)."""
        if self._server:
            return self._server.server_address[1]
        return self._port

    @property
    def address(self) -> tuple[str, int]:
        """Get (host, port) tuple for connecting."""
        return (self.host, self.port)

    def start(self) -> tuple[str, int]:
        """Start the socket server in a background thread. Returns (host, port)."""
        if self._server is not None:
            return self.address

        self._server = ThreadingLMServer((self.host, self._port), LMRequestHandler)
        self._server.lm_handler = self  # type: ignore

        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

        return self.address

    def stop(self):
        """Stop the socket server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            self._thread = None

    def completion(self, prompt: str, model: str | None = None) -> str:
        """Direct completion call (for main process use)."""
        return self.get_client(model).completion(prompt)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def get_usage_summary(self) -> UsageSummary:
        """Get the usage summary for all clients, merged into a single dict."""
        merged = {}
        # Include default client
        default_summary = self.default_client.get_usage_summary()
        merged.update(default_summary.model_usage_summaries)
        # Include other backend client if it exists
        if self.other_backend_client is not None:
            other_summary = self.other_backend_client.get_usage_summary()
            merged.update(other_summary.model_usage_summaries)
        # Include all registered clients
        for client in self.clients.values():
            client_summary = client.get_usage_summary()
            merged.update(client_summary.model_usage_summaries)
        return UsageSummary(model_usage_summaries=merged)
