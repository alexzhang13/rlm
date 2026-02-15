# ADR Template

## Format

```markdown
# ADR-{number}: {Title}

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[Describe the situation and forces at play. What is the problem?
What constraints exist? What are we trying to achieve?]

## Decision
[State the decision clearly. What are we going to do?]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Drawback 1]
- [Drawback 2]

### Neutral
- [Side effect that is neither good nor bad]

## Alternatives Considered
[What other options were evaluated and why were they rejected?]

## References
- [Link to relevant documentation]
```

## Example: Environment Communication

```markdown
# ADR-001: Use HTTP broker for isolated environment communication

## Status
Accepted

## Context
Isolated environments (Modal, E2B, Prime) run code in cloud sandboxes
that cannot directly connect to the host's TCP socket server. We need a
way for sandbox code to make sub-LM calls back to the host.

Options:
- WebSocket connection from sandbox to host
- HTTP broker with polling
- gRPC bidirectional streaming

## Decision
Use an HTTP broker pattern with Flask inside the sandbox and a polling
thread on the host.

## Consequences

### Positive
- Works through any tunnel/port forwarding mechanism
- Simple HTTP -- no special protocol support needed
- Each cloud provider's tunnel mechanism works (Modal encrypted_ports, etc.)
- Easy to debug with standard HTTP tools

### Negative
- Polling adds latency (~100ms intervals)
- State management across HTTP requests requires threading.Event
- More moving parts than direct socket

### Neutral
- Broker server adds Flask as a dependency inside sandbox
- Pattern is consistent across all isolated environments

## Alternatives Considered

**WebSocket**
- Rejected: Not all cloud sandbox tunnels support WebSocket upgrades
- Would require additional dependency management inside sandboxes

**gRPC**
- Rejected: Heavy dependency, complex setup inside sandboxes
- Overkill for request-response pattern

## References
- rlm/environments/modal_repl.py (reference implementation)
- rlm/core/comms_utils.py (socket protocol for comparison)
```

## Naming Convention

```
docs/adr/
├── 0001-http-broker-for-isolated-envs.md
├── 0002-length-prefixed-socket-protocol.md
└── README.md
```
