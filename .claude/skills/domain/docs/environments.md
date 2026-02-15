# Environments Domain

Environment implementations live in `rlm/environments/`. They provide the execution context where LLM-generated code runs.

## Base Classes

**File**: `rlm/environments/base_env.py`

| Base Class | When to Use | Key Methods |
|------------|-------------|-------------|
| `NonIsolatedEnv` | Local execution, same machine | `setup`, `load_context`, `execute_code` |
| `IsolatedEnv` | Cloud sandboxes (Modal, E2B, Prime, Daytona) | `setup`, `load_context`, `execute_code` |

## Available Environments

| Environment | File | Type | Sandbox |
|-------------|------|------|---------|
| `LocalREPL` | `local_repl.py` | NonIsolated | Local Python exec() |
| `ModalREPL` | `modal_repl.py` | Isolated | Modal cloud sandbox |
| `E2BREPL` | `e2b_repl.py` | Isolated | E2B sandbox |
| `PrimeREPL` | `prime_repl.py` | Isolated | Prime sandbox |
| `DaytonaREPL` | `daytona_repl.py` | Isolated | Daytona workspace |
| `DockerREPL` | `docker_repl.py` | Isolated | Local Docker container |

## Implementing a New Environment

### Requirements
- Inherit from `NonIsolatedEnv` or `IsolatedEnv`
- Implement all abstract methods: `setup`, `load_context`, `execute_code`
- Return `REPLResult` from `execute_code`
- Handle `lm_handler_address` for sub-LM calls via `llm_query()`
- Implement `cleanup()` for resource management
- Register in `rlm/environments/__init__.py`

### State Management
Environments must provide these globals to executed code:
- `context`: The loaded context payload
- `llm_query(prompt, model=None)`: For sub-LM calls
- `llm_query_batched(prompts, model=None)`: For batched sub-LM calls
- `FINAL_VAR(variable_name)`: For returning final answers

### Non-Isolated Example

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
        # Initialize execution namespace with llm_query, FINAL_VAR, etc.

    def load_context(self, context_payload: dict | list | str):
        # Make context available to executed code

    def execute_code(self, code: str) -> REPLResult:
        # Execute code and return REPLResult

    def cleanup(self):
        # Clean up resources
```

### Isolated Environment Pattern (HTTP Broker)

Isolated environments can't directly connect to the host's socket server. They use an HTTP broker:

1. **Create broker server** - Flask/HTTP server with `/enqueue`, `/pending`, `/respond` endpoints
2. **Expose tunnel** - Use provider's tunnel/port forwarding to expose broker to host
3. **Implement poller** - Background thread on host to poll and forward requests
4. **Build exec script** - Script that runs inside sandbox with `llm_query()` calling broker
5. **Handle state** - Serialize/deserialize execution state between code blocks (typically via `dill`)

See `rlm/environments/modal_repl.py` as the canonical reference implementation.

### Broker Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/enqueue` | POST | Submit LLM request from sandbox code (blocks until response) |
| `/pending` | GET | Get list of pending requests (called by host poller) |
| `/respond` | POST | Submit response for a request ID (called by host poller) |
| `/health` | GET | Health check |

## Constants

**File**: `rlm/environments/constants.py`

Shared constants like safe builtins, default timeouts, and execution limits.

## Testing Environments

- Test `setup()` initializes correct globals
- Test `execute_code()` returns proper `REPLResult` (stdout, stderr, success)
- Test `load_context()` makes data accessible as `context` variable
- Test `cleanup()` releases resources
- Test `llm_query()` routing through LM Handler
- Use `tests/mock_lm.py` for mock LM client

## Learnings

<!-- Claude: Add discoveries here as you work with environments -->
