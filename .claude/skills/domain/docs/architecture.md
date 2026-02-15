# Architecture Domain

How environments communicate with the LM Handler for sub-LM calls during REPL execution.

## Socket Protocol (Non-Isolated Environments)

Non-isolated environments like `LocalREPL` communicate directly with the `LMHandler` via TCP sockets using a length-prefixed JSON protocol.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Host Machine                                                       │
│  ┌─────────────┐       Socket (TCP)        ┌──────────────────────┐ │
│  │   RLM       │◄──────────────────────────►  LMHandler           │ │
│  │  (main)     │                           │  (ThreadingTCPServer)│ │
│  └─────────────┘                           └──────────────────────┘ │
│        │                                            ▲               │
│        ▼                                            │               │
│  ┌─────────────┐       Socket (TCP)                 │               │
│  │ LocalREPL   │────────────────────────────────────┘               │
│  │ (exec code) │  llm_query() → send_lm_request()                   │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Protocol Format

`4-byte big-endian length prefix + UTF-8 JSON payload`

```python
# From rlm/core/comms_utils.py
def socket_send(sock: socket.socket, data: dict) -> None:
    payload = json.dumps(data).encode("utf-8")
    sock.sendall(struct.pack(">I", len(payload)) + payload)
```

### Request Flow

1. Environment's `llm_query(prompt)` is called during code execution
2. Creates `LMRequest` dataclass and calls `send_lm_request(address, request)`
3. Opens TCP connection to `LMHandler` at `(host, port)`
4. Sends length-prefixed JSON request
5. `LMHandler` processes via `LMRequestHandler.handle()`
6. Returns `LMResponse` with `RLMChatCompletion` or error

### Key Components

- `LMHandler` (`rlm/core/lm_handler.py`): Multi-threaded TCP server wrapping LM clients
- `LMRequest` / `LMResponse` (`rlm/core/comms_utils.py`): Typed request/response dataclasses
- `send_lm_request()` / `send_lm_request_batched()`: Helper functions for socket communication

## HTTP Broker Pattern (Isolated Environments)

Isolated environments (Modal, E2B, Prime, Daytona) cannot directly connect to the host's socket server. They use an HTTP broker:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Host Machine                                                               │
│  ┌─────────┐    Socket    ┌────────────┐    HTTP Poll    ┌────────────────┐ │
│  │   RLM   │◄────────────►│  LMHandler │◄────────────────│   ModalREPL    │ │
│  └─────────┘              └────────────┘                 │  (poller)      │ │
│                                                          └────────────────┘ │
│                                                                  │          │
│                                                          HTTP (tunnel)      │
│                                                                  │          │
└──────────────────────────────────────────────────────────────────┼──────────┘
                                                                   │
┌──────────────────────────────────────────────────────────────────┼──────────┐
│  Cloud Sandbox (Modal/E2B/Prime/Daytona)                         ▼          │
│  ┌─────────────┐     HTTP (localhost)     ┌─────────────────────────────┐   │
│  │ Exec Script │◄────────────────────────►│   Broker Server (Flask)     │   │
│  │ (exec code) │     /enqueue, etc.       │   - /enqueue (submit req)   │   │
│  └─────────────┘                          │   - /pending (poll reqs)    │   │
│                                           │   - /respond (return resp)  │   │
│                                           └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Sandbox Setup**: Environment creates a cloud sandbox with an HTTP broker server inside
2. **Tunnel Exposure**: Broker is exposed via encrypted tunnel (e.g., Modal's `encrypted_ports`)
3. **Code Execution**: When `llm_query()` is called inside sandbox, it POSTs to `http://localhost:8080/enqueue`
4. **Request Queuing**: Broker queues the request and blocks waiting for response
5. **Host Polling**: REPL on host polls `{tunnel_url}/pending` for new requests
6. **LM Forwarding**: Host forwards requests to `LMHandler` via socket, gets response
7. **Response Delivery**: Host POSTs response to `{tunnel_url}/respond`
8. **Unblocking**: Broker unblocks the original `/enqueue` call with the response

### Key Implementation Details

- Broker runs as a Flask server inside the sandbox
- Uses `threading.Event` for request/response synchronization
- Poller thread on host runs in background with 100ms polling interval
- State persistence via `dill` serialization to `/tmp/rlm_state.dill`

## Learnings

<!-- Claude: Add discoveries here as you work with the architecture -->
