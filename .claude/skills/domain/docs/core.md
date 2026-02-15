# Core Domain

The RLM (Reasoning Language Model) framework provides recursive LLM reasoning with a Python REPL execution environment. The root LLM writes Python code in `` ```repl `` blocks, which execute in a sandboxed REPL. The LLM sees truncated outputs, iterates, and returns results via `FINAL_VAR()`.

## Entry Point

**File**: `rlm/core/rlm.py` -> `RLM` class

```python
from rlm import RLM

rlm = RLM(
    lm=client,              # BaseLM client instance
    environment="local",    # or "modal", "e2b", "docker", "prime", "daytona"
    max_iterations=30,      # max REPL iterations before stopping
    setup_code="",          # Python code executed before LLM starts
    other_backends=[],      # sub-model backend names for depth routing
    other_backend_kwargs=[], # kwargs for sub-model backends
)

result, usage = rlm.completion(prompt=data, root_prompt="instructions")
result, usage = await rlm.acompletion(prompt=data, root_prompt="instructions")
```

## Completion Flow

```
rlm.completion(prompt, root_prompt)
    |
    v
1. Serialize `prompt` (dict/list/string) to JSON file
2. Load into REPL namespace as `context` variable
3. Execute `setup_code` in REPL (pre-loaded helpers)
4. System prompt + context metadata -> LLM
5. User prompt includes root_prompt quoted
6. LLM writes ```repl code -> executes -> output fed back
7. LLM iterates until FINAL_VAR(variable_name)
8. RLM extracts value from REPL namespace -> returns
```

## Key Principle: Context Reduction

Large data goes into `context` (REPL variable loaded from JSON), NOT into the prompt. The root LLM only sees metadata like "Your context is a dict with 330061 total characters, broken into chunks: [2120, 16516, ...]". Data is accessed via REPL code (`context["key"]`, etc.).

### DO:
- Put all data in `prompt` arg (becomes `context` in REPL) -- frames, schemas, datasets
- Put helper functions in `setup_code` -- executed before LLM starts
- Keep `root_prompt` small -- describe the task, list available functions, show output format

### DON'T:
- Put large data in `root_prompt` -- it bloats the LLM context window
- Rely on the LLM to execute code verbatim from the prompt

## REPL Environment Functions

Functions injected into REPL globals:

| Function | Purpose |
|----------|---------|
| `context` | The data payload (dict loaded from JSON) |
| `llm_query(prompt)` | Query sub-LLM (~500K char capacity) |
| `llm_query_batched(prompts: List[str])` | Concurrent sub-LLM queries, much faster |
| `FINAL_VAR(variable_name)` | Return a REPL variable's value as final answer |
| `print()` | Output visible to root LLM (truncated to 20K chars) |
| Setup code functions | Defined in `setup_code`, immutable |

## Setup Code Pattern

```python
setup_code = '''
def my_helper(data, key):
    """Helper the LLM calls during REPL execution."""
    return data.get(key, "default")
'''
```

Setup code runs via `exec()` before the LLM's first iteration. Functions are in the namespace but the root LLM cannot see their source -- it only knows they exist if told in the `root_prompt`.

## FINAL_VAR Mechanism

**File**: `rlm/utils/parsing.py`

- Regex-parsed from LLM response: `^\s*FINAL_VAR\((.*?)\)`
- Must be at start of a line, outside code blocks
- When found, executes `print(FINAL_VAR('varname'))` in REPL to retrieve value
- The variable must exist in REPL namespace

## Depth Routing

**File**: `rlm/core/lm_handler.py`

- `depth=0` -> default backend (root LLM)
- `depth=1` -> `other_backend_client` (sub-model)
- Environment is created with `depth = rlm.depth + 1`
- So REPL calls to `llm_query()`/`llm_query_batched()` auto-route to sub-model
- Configure via: `RLM(other_backends=["openai"], other_backend_kwargs=[...])`

## Debugging

- Set `RLM_LOG_DIR=/path/to/logs` to write REPL execution logs
- Set `RLM_VERBOSE=true` for verbose output
- Logs include: REPL code executed, outputs, LLM responses per iteration
- Check `max_iterations` setting (default 30) if RLM seems stuck

## Common Issues

1. **Context too large**: Move data to chunked format in `context`, let LLM process iteratively
2. **FINAL_VAR not found**: Check it's at start of line, outside code blocks
3. **Sub-model routing wrong**: Verify `other_backends` config and depth settings
4. **Recursion limit**: May need increasing for large context serialization

## Key Files

| File | Purpose |
|------|---------|
| `rlm/core/rlm.py` | Main RLM class, completion orchestration |
| `rlm/core/lm_handler.py` | LM Handler, depth routing, TCP server |
| `rlm/core/types.py` | Dataclasses: REPLResult, UsageSummary, etc. |
| `rlm/core/comms_utils.py` | Socket protocol, LMRequest/LMResponse |
| `rlm/utils/parsing.py` | FINAL_VAR extraction, code block parsing |
| `rlm/utils/prompts.py` | System prompt construction |
| `rlm/utils/rlm_utils.py` | Context serialization utilities |

## Learnings

<!-- Claude: Add discoveries here as you work with RLM core -->
