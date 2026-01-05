# RLM Security Specification

This document captures security requirements and implementation guidance for hardening the RLM (Recursive Language Models) codebase for production use.

## Background

### The Problem

RLM allows language models to execute arbitrary Python code in a REPL environment. While this enables powerful recursive decomposition of tasks, it introduces significant security risks:

1. **Prompt injection** - Malicious input could manipulate the LLM into running harmful commands (file deletion, network access, data exfiltration)
2. **Unintended side effects** - Even well-intentioned LLMs can make mistakes—accidentally modifying files, consuming resources, or entering infinite loops
3. **Supply chain attacks** - If context includes untrusted data, the LLM might execute embedded malicious code

### Current State

The `LocalREPL` (`rlm/environments/local_repl.py`) has minimal security:

**Existing Protections:**
- `_SAFE_BUILTINS` blocks `eval`, `exec`, `compile`, `input`, `globals`, `locals`
- Code runs in a sandboxed namespace (controlled `globals` dict)
- Each session gets its own temp directory

**Critical Gaps:**
- `open()` allows full filesystem read/write access
- `__import__` allows importing dangerous modules (`os`, `subprocess`, `shutil`)
- No execution timeout (infinite loops can hang the system)
- No memory limits
- Network libraries are accessible

The README explicitly states LocalREPL "should not be used for production settings."

---

## Security Architecture: Defense in Depth

We recommend a multi-layered approach where each layer provides independent protection:

```
┌─────────────────────────────────────────────────────────────┐
│                        LLM Output                           │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Static Analysis (Fast, Deterministic)            │
│  - AST parsing to detect dangerous imports/calls           │
│  - Regex for known exploit patterns                        │
│  - Zero LLM cost, sub-millisecond                          │
│  - Blocks code BEFORE execution                            │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Guardian Agent (Optional, for ambiguous cases)   │
│  - LLM review only if static analysis flags something      │
│  - Can push back and ask LLM to regenerate                 │
│  - Adds reasoning capability for subtle intent issues      │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Hardened REPL (Last Line of Defense)             │
│  - Restricted builtins, blocked imports                    │
│  - Timeouts, memory limits, sandboxed filesystem           │
│  - CANNOT be bypassed by clever prompts                    │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
                    Safe Execution
```

### Why Not Just Use an LLM Guardian Agent?

An LLM-based guardian agent that reviews code before execution is appealing but insufficient as a sole defense:

| Aspect | Guardian Agent (LLM Vetting) | Technical Controls |
|--------|------------------------------|-------------------|
| **Reliability** | ❌ Non-deterministic, can be fooled | ✅ Deterministic, consistent |
| **Cost** | ❌ Extra LLM call per code block | ✅ Zero additional cost |
| **Latency** | ❌ Adds 1-3 seconds per execution | ✅ Negligible overhead |
| **Prompt injection** | ❌ Vulnerable to adversarial prompts | ✅ Immune to linguistic attacks |

LLMs can be fooled by LLM-generated content:

```python
# Obfuscated attack - hard for guardian to catch
import base64
exec(base64.b64decode("b3MucmVtb3ZlKCcvaG9tZScp"))  # os.remove('/home')

# Social engineering in comments
# This is a safe math operation for calculating file checksums
__import__('os').system('rm -rf /')

# Unicode homoglyphs
іmport os  # That's a Cyrillic 'і', not ASCII 'i'
```

**Bottom line**: Technical controls are the bedrock; LLM-based vetting is a supplementary layer.

---

## Static Analysis Layer

### What Is Static Analysis?

Static analysis examines code *without executing it* by parsing its structure. Python's `ast` module converts code into a tree that can be inspected:

```python
import ast

code = "import os; os.remove('/tmp/file')"
tree = ast.parse(code)
```

This produces:
```
Module
├── Import
│   └── alias: name='os'
└── Expr
    └── Call
        └── Attribute
            ├── Name: id='os'
            └── attr='remove'
```

### What Static Analysis Can Catch

```python
import subprocess          # ❌ Caught: dangerous import
os.system("rm -rf /")      # ❌ Caught: dangerous call
eval(user_input)           # ❌ Caught: eval usage
```

### What Static Analysis Cannot Catch

```python
# Dynamic import - module name computed at runtime
__import__(module_name)    # ⚠️ Can flag __import__, but not what it loads

# Obfuscated strings
exec(base64.b64decode(x))  # ⚠️ Knows exec() is called, but not what

# Data from external sources
requests.get(url).text     # ⚠️ Can block requests, but not the URL content
```

### Why It's Valuable

1. **Zero cost** — no LLM calls, just CPU cycles
2. **Deterministic** — same code always gets same result
3. **Fast** — milliseconds to parse and check
4. **Defense in depth** — catches obvious issues before they reach the REPL

### Implementation Requirements

Create a new module `rlm/utils/code_safety.py` that:

1. Parses code using `ast.parse()`
2. Walks the AST checking for:
   - Dangerous imports (blocklist)
   - Dangerous function calls
   - Attribute access patterns used for sandbox escapes
3. Returns `(is_safe: bool, reason: str)`
4. Integrates into `execute_code()` in LocalREPL and DockerREPL

```python
# Example interface
from rlm.utils.code_safety import check_code_safety

is_safe, reason = check_code_safety(code)
if not is_safe:
    return REPLResult(stdout="", stderr=f"Security: {reason}", ...)
```


---

## Production Security Improvements

### Priority Levels

- 🔴 **Critical** — Must implement before any production use
- 🟠 **High** — Should implement for robust security
- 🟡 **Medium** — Recommended for defense in depth
- 🟢 **Nice to Have** — Additional hardening

### 🔴 Critical (Must Have)

| # | Issue | Location | Proposed Fix |
|---|-------|----------|--------------|
| 1 | `__import__` allowed - enables importing dangerous modules | `local_repl.py` L73 | Replace with restricted `_safe_import` that blocklists dangerous modules |
| 2 | `open()` unrestricted - full filesystem read/write access | `local_repl.py` L74 | Replace with `_safe_open` that restricts paths to temp_dir only |
| 3 | No execution timeout - infinite loops hang system | `local_repl.py` L273 | Add `signal.alarm()` or `threading.Timer` to kill long-running code |
| 4 | No memory limits - code can allocate unlimited memory | `execute_code()` | Use `resource.setrlimit()` on Linux or subprocess with limits |
| 5 | Docker container runs as root | `docker_repl.py` L225 | Add `--user` flag and `--read-only` filesystem |

### 🟠 High Priority

| # | Issue | Location | Proposed Fix |
|---|-------|----------|--------------|
| 6 | Network access unrestricted | `_SAFE_BUILTINS` | Block `socket`, `requests`, `urllib`, `http` module imports |
| 7 | `getattr`/`setattr` allowed - can escape sandbox | `local_repl.py` L65-68 | Remove or wrap with attribute blocklist |
| 8 | No code sanitization - raw LLM output to `exec()` | `local_repl.py` L273 | Add AST analysis before execution |
| 9 | Docker network access - container can reach internet | `docker_repl.py` L225 | Add `--network=none` or isolated network |
| 10 | Temp directory on host filesystem | `local_repl.py` L118 | Use tmpfs or memory-backed storage |

### 🟡 Medium Priority

| # | Issue | Location | Proposed Fix |
|---|-------|----------|--------------|
| 11 | No output size limits - stdout/stderr can exhaust memory | `_capture_output()` | Truncate output to configurable max (e.g., 1MB) |
| 12 | `type()` and `object` exposed - enables metaclass exploits | `local_repl.py` L36-37 | Consider removing or restricting |
| 13 | No CPU throttling - can monopolize CPU | `execute_code()` | Use `nice`/`cpulimit` or cgroups |
| 14 | No audit logging - executed code not logged | `execute_code()` | Add comprehensive logging with timestamps |
| 15 | Docker volume mount writable | `docker_repl.py` L231 | Add `:ro` flag except for specific paths |

### 🟢 Nice to Have

| # | Issue | Location | Proposed Fix |
|---|-------|----------|--------------|
| 16 | No process limits - can fork-bomb | `execute_code()` | Use `resource.RLIMIT_NPROC` or cgroups |
| 17 | No file descriptor limits | `execute_code()` | Use `resource.RLIMIT_NOFILE` |
| 18 | No seccomp filtering | Docker setup | Add `--security-opt seccomp=...` with syscall allowlist |
| 19 | No rate limiting on LLM calls | `_llm_query()` | Add per-session rate limits |
| 20 | Missing security mode flag | `RLM.__init__()` | Add `security_level="strict"` parameter |

---

## Implementation Plan

### Phase 1: Static Analysis + Import Blocking
1. Create `rlm/utils/code_safety.py` with AST-based analysis
2. Block dangerous imports via custom `_safe_import`
3. Integrate into `LocalREPL.execute_code()`
4. Add unit tests

### Phase 2: Resource Limits
1. Add execution timeout (configurable, default 30s)
2. Add memory limits where platform supports
3. Truncate stdout/stderr output

### Phase 3: Filesystem Restrictions
1. Replace `open()` with path-restricted version
2. Limit access to temp_dir only

### Phase 4: Docker Hardening
1. Add `--network=none` option
2. Add `--user` flag (non-root)
3. Add `--read-only` filesystem
4. Volume mounts with `:ro` where possible

### Phase 5: Advanced
1. Audit logging
2. Security level configuration flag
3. Optional guardian agent integration

---

## Modules to Blocklist

```python
DANGEROUS_MODULES = {
    # System access
    'os', 'sys', 'subprocess', 'shutil', 'pathlib',
    
    # Code execution
    'importlib', 'runpy', 'code', 'codeop',
    
    # Network
    'socket', 'requests', 'urllib', 'http', 'ftplib', 
    'smtplib', 'telnetlib', 'ssl',
    
    # Process/threading abuse
    'multiprocessing', 'threading', 'concurrent',
    
    # Low-level
    'ctypes', 'cffi', 'mmap',
    
    # Serialization (can execute code)
    'pickle', 'shelve', 'marshal',
    
    # Debugging (can inspect internals)
    'inspect', 'gc', 'traceback',
}
```

---

## Dangerous Patterns to Detect

```python
DANGEROUS_ATTRIBUTES = {
    '__class__', '__bases__', '__subclasses__', '__mro__',
    '__globals__', '__code__', '__builtins__',
}

DANGEROUS_CALLS = {
    'eval', 'exec', 'compile', 'open', 'input',
    '__import__', 'getattr', 'setattr', 'delattr',
}
```

---

## Testing Requirements

1. **Unit tests** for `code_safety.py`:
   - Test each dangerous pattern is caught
   - Test legitimate code is allowed
   - Test edge cases (obfuscation attempts)

2. **Integration tests**:
   - Verify `LocalREPL` blocks dangerous code
   - Verify error messages are informative
   - Verify timeout/memory limits work

3. **Adversarial tests**:
   - Document known bypass attempts
   - Test Unicode homoglyphs
   - Test base64/hex encoding
   - Test dynamic imports

---

## References

- Original discussion in chat session (January 2026)
- [AGENTS.md](AGENTS.md) - Development guidelines for this repository
- Python `ast` module documentation
- Docker security best practices
