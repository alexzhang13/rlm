---
date: 2026-02-15
topic: "OpenAI-Only Package Improvements"
status: validated
---

# Problem Statement
The repo currently carries multi-provider complexity, duplicated client logic, and inconsistent response/tool handling. This makes packaging, observability, and integration with rlm-service harder than it needs to be, especially if we only support OpenAI.

# Constraints
- OpenAI-only execution path in the core library
- Responses API as the single request/response format
- Preserve tool calling and structured outputs
- Minimize dependency footprint and reduce config surface

# Approach
Standardize on one OpenAI client path with a single normalized response contract (content, tool_calls, usage). Remove non-OpenAI providers and consolidate duplicated logic (prompt normalization, usage accounting, retry/throttle). Simplify environments and tooling to rely on the normalized response shape, not JSON-string heuristics.

# Architecture
The OpenAI client becomes the sole backend and is responsible for response normalization. Environments and the tool loop consume the normalized contract directly. Packaging is simplified to a single core install with optional extras only for isolated environments.

# Components
- OpenAI client: Responses API only, normalized output contract
- Response normalizer: stable fields (content, tool_calls, usage)
- Tool loop: consumes structured tool_calls; no JSON string heuristics
- Environment layer: uses normalized responses; consistent error handling
- Packaging: remove unused providers; optional extras for isolated envs only

# Data Flow
1. Build OpenAI Responses request with tools/output schema
2. Execute request via the single OpenAI client
3. Normalize output into content + tool_calls + usage
4. Tool loop executes and appends tool results
5. Final answer produced from normalized content

# Error Handling
- Fail fast on unsupported providers or legacy chat paths
- Structured error types instead of leaked error strings
- Strict validation of normalized response contract

# Testing Strategy
- Replace provider tests with Responses-only tests
- Add tool-calling tests using normalized outputs
- Validate usage tracking and retry/throttle behavior

# Open Questions
None.
