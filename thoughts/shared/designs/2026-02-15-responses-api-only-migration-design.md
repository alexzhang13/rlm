---
date: 2026-02-15
topic: "Responses API Only Migration"
status: validated
---

# Problem Statement
We need to simplify the integration by moving RLM and rlm-service to OpenAI Responses API only. The current dual-path support (chat completions + responses) plus multi-provider backends creates inconsistent response shapes, fragile tool handling, and extra operational overhead.

# Constraints
- OpenAI Responses API only; no chat completions fallback
- OpenAI-only provider surface in the core RLM path
- Preserve tool calling, structured outputs, and usage summaries
- Keep service orchestration behavior stable

# Approach
We will standardize the client boundary on Responses API and normalize responses into a single canonical shape. Tool calling and structured outputs will consume the normalized output directly, eliminating chat-specific parsing.

# Architecture
A single OpenAI client path will handle request assembly, Responses API execution, and response normalization. Environments and services will operate on a stable response contract that includes content, tool calls, and usage.

# Components
- OpenAI client: always Responses API and normalizes outputs
- Response normalizer: stable contract for content, tool_calls, and usage
- Tool loop: consumes normalized tool calls without JSON-string parsing
- Backend registry: OpenAI-only in the core execution path
- Service adapters: rely on Responses output_format and normalized payloads

# Data Flow
1. RLM builds a request with tools and output format
2. OpenAI Responses API returns output items
3. Response is normalized into content + tool_calls + usage
4. Tool loop executes until no tool calls remain
5. Structured outputs are parsed from final content
6. rlm-service consumes the stable payload

# Error Handling
- Fail fast on unsupported providers or legacy chat-only paths
- Explicit errors for malformed Responses output
- Tool loop retains max-iteration guardrails

# Testing Strategy
- Update RLM tool-loop tests for normalized Responses outputs
- Validate usage tracking for Responses API
- Run service-level flows that depend on tool calls and structured outputs

# Open Questions
None.
