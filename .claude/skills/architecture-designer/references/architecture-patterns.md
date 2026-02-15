# Architecture Patterns Reference

## Pattern Comparison

| Pattern | Best For | Trade-offs |
|---------|----------|------------|
| **Non-Isolated Exec** | Local dev, simple setup | Fast; no sandboxing |
| **Isolated Sandbox** | Untrusted code, cloud | Safe; operational complexity |
| **Direct Socket** | Same-machine comms | Low latency; no network boundary |
| **HTTP Broker** | Cross-boundary comms | Works anywhere; polling overhead |
| **Plugin/Registry** | Extensibility | Clean API; discovery complexity |

## RLM Environment Patterns

### Non-Isolated (LocalREPL)

```
┌──────────────┐
│   RLM Core   │
│   ┌────────┐ │       TCP Socket
│   │ REPL   │─┼──────────────────► LMHandler
│   │ exec() │ │
│   └────────┘ │
└──────────────┘
```

**When to use**: Development, trusted code, low-latency needs
**Pros**: Simple, fast, no external deps
**Cons**: No isolation, code runs in same process

### Isolated (Modal/E2B/Prime/Daytona)

```
┌─────────────────┐          ┌──────────────────┐
│   Host          │          │   Cloud Sandbox  │
│   ┌───────────┐ │  HTTP    │   ┌────────────┐ │
│   │ Poller    │─┼──────────┼──►│ Broker     │ │
│   │           │ │  tunnel  │   │ /enqueue   │ │
│   └─────┬─────┘ │          │   │ /pending   │ │
│         │       │          │   │ /respond   │ │
│   ┌─────▼─────┐ │          │   └─────┬──────┘ │
│   │ LMHandler │ │          │   ┌─────▼──────┐ │
│   └───────────┘ │          │   │ Exec Script│ │
└─────────────────┘          │   └────────────┘ │
                             └──────────────────┘
```

**When to use**: Untrusted code, cloud execution, resource isolation
**Pros**: Safe, scalable, any cloud provider
**Cons**: Latency (polling), state serialization, tunnel setup

### Docker (hybrid)

```
┌──────────────────┐
│   Host           │
│   ┌────────────┐ │       ┌───────────────┐
│   │ DockerREPL │─┼──────►│   Container   │
│   └──────┬─────┘ │       │   exec code   │
│   ┌──────▼─────┐ │       └───────────────┘
│   │ LMHandler  │ │
│   └────────────┘ │
└──────────────────┘
```

**When to use**: Local isolation without cloud dependency
**Pros**: Isolated, reproducible, local
**Cons**: Docker required, container overhead

## Client Patterns

### Provider Abstraction

```
         BaseLM (abstract)
        ┌───────────────────┐
        │ completion()      │
        │ acompletion()     │
        │ get_usage_summary()│
        │ get_last_usage()  │
        └───────┬───────────┘
                │
    ┌───────────┼───────────┬────────────┐
    │           │           │            │
OpenAI    Anthropic    Gemini      Portkey
```

**Pattern**: Template Method / Strategy
**Extension**: Add new client by inheriting BaseLM, implementing abstract methods, registering in `__init__.py`

### Usage Tracking

All clients must track per-model usage internally and expose via standard interface. This enables cost monitoring and optimization across providers.

## Communication Patterns

### Length-Prefixed Protocol (TCP)

```
┌──────────┬──────────────────────┐
│ 4 bytes  │   UTF-8 JSON payload │
│ (length) │                      │
└──────────┴──────────────────────┘
```

**When to use**: Same-machine, low-latency, reliable
**Pros**: Simple, fast, no HTTP overhead
**Cons**: Custom protocol, no built-in auth

### HTTP Broker (REST)

```
POST /enqueue   → Submit LLM request (blocks)
GET  /pending   → Poll for requests
POST /respond   → Submit response
GET  /health    → Health check
```

**When to use**: Cross-network boundary, cloud sandboxes
**Pros**: Standard HTTP, works through firewalls/tunnels
**Cons**: Polling latency, more complex state management

## Decision Matrix

| Need | Pattern | Example |
|------|---------|---------|
| New LM provider | Client abstraction | Add `rlm/clients/new_provider.py` |
| New cloud sandbox | Isolated environment | Add `rlm/environments/new_sandbox.py` |
| New local executor | Non-isolated environment | Add `rlm/environments/new_local.py` |
| Protocol change | Socket/HTTP modification | Modify `rlm/core/comms_utils.py` |
| New REPL function | Environment globals | Add to `setup()` in environment |
