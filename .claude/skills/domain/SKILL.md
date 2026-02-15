---
name: domain
description: Load domain-specific context for RLM library areas. Use PROACTIVELY when working on core RLM logic, environments, LM clients, or the communication architecture. Saves significant context window by loading only what's needed.
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Domain Context Loader

Loads focused domain knowledge before working on specific library areas. Keeps context lean by loading only what's needed.

## Usage

```
/domain core           # RLM completion flow, REPL, FINAL_VAR, context reduction
/domain environments   # Environment development: LocalREPL, sandboxes, broker pattern
/domain clients        # LM client development: BaseLM, usage tracking, providers
/domain architecture   # Socket protocol, HTTP broker, environment ↔ LM Handler comms
/domain                # Auto-detect from conversation context
```

## Auto-Detection Rules

When invoked without argument, detect domain from context:

| Keywords in Conversation | Domain to Load |
|-------------------------|----------------|
| completion, prompt, root_prompt, context, FINAL_VAR, depth, iteration | core |
| environment, repl, sandbox, execute_code, setup, cleanup, modal, e2b, docker, daytona, prime | environments |
| client, lm, openai, anthropic, gemini, portkey, litellm, completion, acompletion, usage | clients |
| socket, handler, broker, comms, tunnel, protocol, lm_handler, polling | architecture |

## Multi-Domain Loading

Some tasks span domains. Load multiple when needed:

| Task | Domains to Load |
|------|-----------------|
| "Add a new LM client" | clients |
| "Build a new sandbox environment" | environments + architecture |
| "Debug sub-LM call routing" | core + architecture |
| "Fix FINAL_VAR parsing" | core |
| "Add batched completion support" | core + clients |

## Action Steps

1. **Identify domain(s)** from argument or auto-detection
2. **Read the domain doc(s)** from `.claude/skills/domain/docs/`
3. **Check the Learnings section** for recent discoveries
4. **Summarize key points** relevant to the current task
5. **Proceed with the task** using loaded context

## Available Domain Docs

| Domain | File | Coverage |
|--------|------|----------|
| core | `docs/core.md` | RLM completion flow, REPL execution, FINAL_VAR, context reduction, depth routing |
| environments | `docs/environments.md` | Base classes, LocalREPL, isolated sandboxes, broker pattern, state management |
| clients | `docs/clients.md` | BaseLM interface, provider implementations, usage tracking, configuration |
| architecture | `docs/architecture.md` | Socket protocol, HTTP broker, environment ↔ LM Handler communication |

## Continuous Improvement

These docs are **living documents**. Help them evolve:

### When You Discover Something New

If you find domain knowledge NOT in the docs:

1. **Complete your task** using what you discovered
2. **Add to Learnings** in the relevant doc:
   ```markdown
   ## Learnings
   - [YYYY-MM-DD] Your discovery here
   ```

### When Docs Are Wrong or Outdated

1. **Note the issue** in your response
2. **Add to Learnings** with correction
3. **Suggest the fix** for user approval
