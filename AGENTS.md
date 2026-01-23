# AGENTS.md

This guide covers best practices for contributing to the core Recursive Language Models `rlm` library and developing new environments (in `rlm/environments/`) and LM clients (in `rlm/clients/`).

## Setup

We use `uv` for developing `rlm`.
```bash
# Install uv (first time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup blank project if needed
uv init && uv venv --python 3.12
source .venv/bin/activate

# Install in editable mode
uv pip install -e .

# For Modal sandbox support
uv pip install -e ".[modal]"

# For Prime sandbox support
uv pip install -e ".[prime]"
```

## General Guidelines

### Code Style & Typing
- **Formatting**: Strict `ruff` enforcement. All PRs must pass `ruff check --fix .`
- **Typing**: Explicit types preferred
  - **OK**: `cast(...)`, `assert ...` for type narrowing
  - **SOMETIMES OK**: Untyped args for simple cases (e.g., prompt handlers)
  - **NOT OK**: `# type: ignore` without strong justification

### Naming Conventions
- **Methods**: snake_case
- **Classes**: PascalCase (e.g., `LocalREPL`, `PortkeyClient`)
- **Variables**: snake_case
- **Constants**: UPPER_CASE (e.g., `_SAFE_BUILTINS`, `RLM_SYSTEM_PROMPT`)

Do NOT use `_` prefix for private methods unless explicitly requested.

### Error Handling Philosophy
- **Fail fast, fail loud** - No defensive programming or silent fallbacks
- **Minimize branching** - Prefer single code paths; every `if`/`try` needs justification
- **Example**: Missing API key → immediate `ValueError`, not graceful fallback

## Core Repository Development

For PRs to `rlm` core:
```bash
git clone https://github.com/alexzhang13/rlm.git
cd rlm

# Standard development:
uv sync

# Install dev + test dependencies:
uv sync --group dev --group test

# Install pre-commit hooks:
uv run pre-commit install
```

### Dependencies
- Avoid new core dependencies
- Use optional extras for non-essential features (e.g., `modal` extra)
- Exception: tiny deps that simplify widely-used code

### Testing
- `uv run pytest` with discovery under `tests/`
- Write simple, deterministic unit tests
- Update tests when changing functionality
- For isolated environments, mock external services

### Documentation
- Keep concise and actionable
- Update README when behavior changes
- Avoid content duplication

### Scope
- Small, focused diffs
- One change per PR
- Backward compatibility is only desirable if it can be done without introducing excessive maintenance burden
- Delete dead code (don't guard it)

### Checklist

Before a PR:

```bash
# Run style + lint checks:
uv run ruff check --fix .
uv run ruff format .
uv run pre-commit run --all-files

# Run tests:
uv run pytest
```

Ensure docs and tests are updated if necessary, and dead code is deleted. Strive for minimal, surgical diffs.

## Developing LM Clients

LM client implementations live in `rlm/clients/`. All clients must inherit from `BaseLM`.

### Client Pattern

| Base Class | When to Use | Key Methods |
|------------|-------------|-------------|
| `BaseLM` | All LM integrations | `completion`, `acompletion`, `get_usage_summary`, `get_last_usage` |

### Requirements
- Inherit from `BaseLM` in `rlm/clients/base_lm.py`
- Implement all abstract methods: `completion`, `acompletion`, `get_usage_summary`, `get_last_usage`
- Track per-model usage (calls, input/output tokens)
- Handle both string and message list prompts
- Register client in `rlm/clients/__init__.py`

### Example Structure
```python
from rlm.clients.base_lm import BaseLM
from rlm.core.types import ModelUsageSummary, UsageSummary

class MyClient(BaseLM):
    def __init__(self, api_key: str, model_name: str, **kwargs):
        super().__init__(model_name=model_name, **kwargs)
        # Initialize your client
        
    def completion(self, prompt: str | list[dict[str, Any]], model: str | None = None) -> str:
        # Handle both str and message list formats
        # Track usage with _track_cost()
        # Return response string
        
    def get_usage_summary(self) -> UsageSummary:
        # Return aggregated usage across all calls
```

### Configuration Guidelines
- **Environment variables**: ONLY for API keys (document in README)
- **Hardcode**: Default base URLs, reasonable defaults
- **Arguments**: Essential customization via `__init__()`

## Developing Environments

Environment implementations live in `rlm/environments/`. Choose the appropriate base class.

### Environment Pattern

| Pattern | Base Class | When to Use | Key Methods |
|---------|------------|-------------|-------------|
| **Non-isolated** | `NonIsolatedEnv` | Local execution, same machine | `setup`, `load_context`, `execute_code` |
| **Isolated** | `IsolatedEnv` | Cloud sandboxes (Modal, Prime) | `setup`, `load_context`, `execute_code` |

### Requirements
- Inherit from `NonIsolatedEnv` or `IsolatedEnv` in `rlm/environments/base_env.py`
- Implement all abstract methods: `setup`, `load_context`, `execute_code`
- Return `REPLResult` from `execute_code`
- Handle `lm_handler_address` for sub-LM calls via `llm_query()`
- Implement `cleanup()` for resource management
- Register environment in `rlm/environments/__init__.py`

### Key Implementation Details
- `setup()`: Initialize globals, locals, and helper functions
- `load_context()`: Make context available as `context` variable
- `execute_code()`: Execute code, capture stdout/stderr, return `REPLResult`
- Always provide `llm_query` and `llm_query_batched` functions in environment globals

### State Management
Environments must provide these globals to executed code:
- `context`: The loaded context payload
- `llm_query(prompt, model=None)`: For sub-LM calls
- `llm_query_batched(prompts, model=None)`: For batched sub-LM calls
- `FINAL_VAR(variable_name)`: For returning final answers

### Example Structure
```python
from rlm.environments.base_env import NonIsolatedEnv
from rlm.core.types import REPLResult

class MyEnvironment(NonIsolatedEnv):
    def __init__(self, lm_handler_address: tuple[str, int] | None = None, 
                 context_payload: dict | list | str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.lm_handler_address = lm_handler_address
        self.setup()
        if context_payload:
            self.load_context(context_payload)
            
    def setup(self):
        # Initialize execution namespace
        
    def load_context(self, context_payload: dict | list | str):
        # Make context available to executed code
        
    def execute_code(self, code: str) -> REPLResult:
        # Execute code and return REPLResult
        
    def cleanup(self):
        # Clean up resources
```

### Checklist
- Guidelines here are followed
- Environment works with basic RLM completion calls
- `cleanup()` properly releases all resources
- Sub-LM calls work via `llm_query()`

## Architecture: Environment ↔ LM Handler Communication

Understanding how environments communicate with the LM Handler is essential for developing new environments.

### Overview

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

### Socket Protocol (Non-Isolated Environments)

Non-isolated environments like `LocalREPL` communicate directly with the `LMHandler` via TCP sockets using a length-prefixed JSON protocol:

**Protocol Format**: `4-byte big-endian length prefix + UTF-8 JSON payload`

```python
# Sending a message (from rlm/core/comms_utils.py)
def socket_send(sock: socket.socket, data: dict) -> None:
    payload = json.dumps(data).encode("utf-8")
    sock.sendall(struct.pack(">I", len(payload)) + payload)
```

**Request Flow**:
1. Environment's `llm_query(prompt)` is called during code execution
2. Creates `LMRequest` dataclass and calls `send_lm_request(address, request)`
3. Opens TCP connection to `LMHandler` at `(host, port)`
4. Sends length-prefixed JSON request
5. `LMHandler` processes via `LMRequestHandler.handle()`
6. Returns `LMResponse` with `RLMChatCompletion` or error

**Key Components**:
- `LMHandler` (`rlm/core/lm_handler.py`): Multi-threaded TCP server wrapping LM clients
- `LMRequest` / `LMResponse` (`rlm/core/comms_utils.py`): Typed request/response dataclasses
- `send_lm_request()` / `send_lm_request_batched()`: Helper functions for socket communication

### HTTP Broker Pattern (Isolated Environments)

Isolated environments (Modal, Prime) cannot directly connect to the host's socket server. They use an HTTP broker pattern:

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
│  Cloud Sandbox (Modal/Prime)                                     ▼          │
│  ┌─────────────┐     HTTP (localhost)     ┌─────────────────────────────┐   │
│  │ Exec Script │◄────────────────────────►│   Broker Server (Flask)     │   │
│  │ (exec code) │     /enqueue, etc.       │   - /enqueue (submit req)   │   │
│  └─────────────┘                          │   - /pending (poll reqs)    │   │
│                                           │   - /respond (return resp)  │   │
│                                           └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**How It Works**:

1. **Sandbox Setup**: Environment creates a cloud sandbox with an HTTP broker server running inside
2. **Tunnel Exposure**: Broker server is exposed via encrypted tunnel (e.g., Modal's `encrypted_ports`)
3. **Code Execution**: When `llm_query()` is called inside sandbox, it POSTs to `http://localhost:8080/enqueue`
4. **Request Queuing**: Broker queues the request and blocks waiting for response
5. **Host Polling**: `ModalREPL` on host polls `{tunnel_url}/pending` for new requests
6. **LM Forwarding**: Host forwards requests to `LMHandler` via socket, gets response
7. **Response Delivery**: Host POSTs response to `{tunnel_url}/respond`
8. **Unblocking**: Broker unblocks the original `/enqueue` call with the response

**Broker Endpoints**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/enqueue` | POST | Submit LLM request from sandbox code (blocks until response) |
| `/pending` | GET | Get list of pending requests (called by host poller) |
| `/respond` | POST | Submit response for a request ID (called by host poller) |
| `/health` | GET | Health check |

**Key Implementation Details**:
- Broker runs as a Flask server inside the sandbox
- Uses `threading.Event` for request/response synchronization
- Poller thread on host runs in background with 100ms polling interval
- State persistence via `dill` serialization to `/tmp/rlm_state.dill`

### Implementing a New Isolated Environment

When building a new isolated environment (e.g., for a new cloud provider):

1. **Create broker server** - Flask/HTTP server with `/enqueue`, `/pending`, `/respond` endpoints
2. **Expose tunnel** - Use provider's tunnel/port forwarding to expose broker to host
3. **Implement poller** - Background thread on host to poll and forward requests
4. **Build exec script** - Script that runs inside sandbox with `llm_query()` calling broker
5. **Handle state** - Serialize/deserialize execution state between code blocks

See `rlm/environments/modal_repl.py` as the canonical reference implementation.

