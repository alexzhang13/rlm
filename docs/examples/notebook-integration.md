# RLM Jupyter Integration: Working Documentation

This notebook demonstrates the new RLM features for Jupyter environments:
1. **Core Interfaces**: `completion()` vs `session.chat()`
2. **Persistence**: Maintaining state across independent calls
3. **Synchronization**: Sharing variables between the Notebook and RLM (One-way, Selective, and Bidirectional)


```python
import sys
from rlm import RLM
from rlm.utils.notebook import render_completion
from rlm.utils.trace_notebook import enable_trace_notebook

# Optional: Enable trace logging to generate .trace.ipynb files for debugging
logger, trace_handle = enable_trace_notebook(log_dir="logs")
```

## 1. Core Interfaces: Completions vs Sessions

RLM distinguishes between *one-off tasks* and *conversational workflows*.

### A. Completions (Stateless/One-off)
Use `rlm.completion()` for independent tasks where history doesn't matter. By default, each call starts fresh.


```python
rlm = RLM(
    environment="jupyter",
    logger=logger,
    backend_kwargs={"model_name": "gpt-4o"}
)

# This call happens in isolation
result = rlm.completion("Generate a random number between 1 and 100.")
print(f"Result 1: {result.response}")

# This call knows nothing about the previous one
result = rlm.completion("What was the number you just generated?")
print(f"Result 2: {result.response}")
```

    Result 1: random_number
    Result 2: 15


### B. Sessions (Multi-turn/Conversational)
Use `rlm.start_session()` for workflows where the model needs to see previous turns.


```python
session = rlm.start_session()

result = session.chat("Pick a color.")
print(f"Turn 1: {result.response}")

result = session.chat("Why did you pick that one?")
print(f"Turn 2: {result.response}")

result.render_trace() # View the cumulative trace of the session
```

    Turn 1: "Blue"
    Turn 2: "I pick the color blue."



## Run Context
```json
{
  "prompt": "Pick a color.",
  "root_prompt": null
}
```
## Iteration 1

### Model Response

To begin, I will inspect the contents of `session_context_0` to understand the prompt and the associated context so that I can determine the necessary steps to answer the query.

## Iteration 2

### Model Response

Let's inspect the contents of `session_context_0` to understand what information it contains and what query needs to be answered.

```repl
print(session_context_0)
```

### Code Block 1

```python
print(session_context_0)
```

**stdout**

```
Pick a color.

```

## Iteration 3

### Model Response

The prompt "Pick a color." is straightforward and doesn't require any complex analysis or additional context inspection. I will respond to the query directly.

FINAL("Blue")


---

## Run Context
```json
{
  "prompt": "Why did you pick that one?",
  "root_prompt": null
}
```
## Iteration 1

### Model Response

The context in `session_context_0` simply contains the phrase "Pick a color." This appears to be a prompt or directive but lacks additional context or a specific question to answer. 

Since there is no additional information or instructions included with "Pick a color," it seems the task is to select a color based on this prompt.

I will proceed with a response based on this context.

FINAL("I pick the color blue.")



## 2. Persistence

Sometimes you want the *REPL state* (variables defined by the model) to persist across completely separate `completion()` calls, even if you don't want to pass the full conversation history.

Enable this with `persistent=True`.


```python
persistent_rlm = RLM(
    environment="jupyter",
    persistent=True,
    logger=logger,
    backend_kwargs={"model_name": "gpt-5.2"}
)

# Call 1: Define a variable in the RLM's environment
persistent_rlm.completion("Set x = 500 in the repl")

# Call 2: Use that variable (even though this is a fresh completion call)
result = persistent_rlm.completion("Read the value of x from the repl. do not assume the value. Then set x to the double of its value.")
print(result.response)
```

    1000


## 3. Jupyter Synchronization

The `jupyter` environment allows sharing variables between the Notebook kernel (where you are) and the RLM execution environment.

### Mode A: One-Way Sync (RLM → Notebook)
Useful when you want RLM to compute something and leave the result for you to use.


```python
rlm_out = RLM(
    environment="jupyter", 
    environment_kwargs={"sync_to_user_ns": True}, # Push RLM vars to Notebook
    backend_kwargs={"model_name": "gpt-4o"}
)

rlm_out.completion("computed_value = 12345 * 6789")

# Now the variable is available in your notebook
print(f"Value from RLM: {computed_value}") # noqa: F821
```

    Value from RLM: 83810205


### Mode B: Selective Sync (Notebook → RLM)
Useful when you have specific data (config, datasets) you want to securely pass to RLM, without exposing your entire namespace.


```python
# Define sensitive/heavy data in notebook
api_key = "sk-12345"
user_data = {"id": 1, "name": "Petros"}
irrelevant_var = "Do not see this"

rlm_dev = RLM(
    environment="jupyter",
    environment_kwargs={
        "sync_from_user_ns": True,
        "sync_vars": ["user_data"] # Only sync this variable
    },
    backend_kwargs={"model_name": "gpt-4o"}
)

result = rlm_dev.completion("Check if 'user_data' is defined. Check if 'api_key' is defined.")
print(result.response)
```

    "user_data is defined, but api_key is not defined."


### Mode C: Full Bidirectional Sync (Zero-Copy)
The "Co-pilot" mode. RLM shares your exact karnel state. It can read your variables, modify them, and create new ones. 
**Note:** No serialization is performed; objects are passed by reference.


```python
# Setup data
import pandas as pd
df = pd.DataFrame({"Name": ["A", "B"], "Score": [10, 20]})

print("Original DataFrame:")
print(df)
```

    Original DataFrame:
      Name  Score
    0    A     10
    1    B     20



```python
rlm_full = RLM(
    environment="jupyter",
    environment_kwargs={
        "sync_to_user_ns": True,
        "sync_from_user_ns": True
        # No 'sync_vars' means sync everything
    },
    backend_kwargs={"model_name": "gpt-5.2"}
)

# RLM modifies 'df' in place
rlm_full.completion("Add 5 to the Score column of df.")

print("\nModified DataFrame (in Notebook):")
print(df)
```

    
    Modified DataFrame (in Notebook):
      Name  Score
    0    A     15
    1    B     25



```python

```
