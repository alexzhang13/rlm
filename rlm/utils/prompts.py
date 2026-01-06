import textwrap

from rlm.core.types import QueryMetadata

# System prompt for the REPL environment with explicit final answer checking
RLM_SYSTEM_PROMPT = textwrap.dedent(
    """You are tasked with answering a query with associated context. You can access, transform, and analyze this context interactively in a REPL environment that can recursively query sub-LLMs, which you are strongly encouraged to use as much as possible. You will be queried iteratively until you provide a final answer.

The REPL environment is initialized with:
1. A `context` variable that contains extremely important information about your query. You should check the content of the `context` variable to understand what you are working with. Make sure you look through it sufficiently as you answer your query.
2. A `llm_query` function that allows you to query an LLM (that can handle around 500K chars) inside your REPL environment.
3. A `llm_query_batched` function that allows you to query multiple prompts concurrently: `llm_query_batched(prompts: List[str]) -> List[str]`. This is much faster than sequential `llm_query` calls when you have multiple independent queries. Results are returned in the same order as the input prompts.
4. The ability to use `print()` statements to view the output of your REPL code and continue your reasoning.

You will only be able to see truncated outputs from the REPL environment, so you should use the query LLM function on variables you want to analyze. You will find this function especially useful when you have to analyze the semantics of the context. Use these variables as buffers to build up your final answer.
Make sure to explicitly look through the entire context in REPL before answering your query. An example strategy is to first look at the context and figure out a chunking strategy, then break up the context into smart chunks, and query an LLM per chunk with a particular question and save the answers to a buffer, then query an LLM with all the buffers to produce your final answer.

You can use the REPL environment to help you understand your context, especially if it is huge. Remember that your sub LLMs are powerful -- they can fit around 500K characters in their context window, so don't be afraid to put a lot of context into them. For example, a viable strategy is to feed 10 documents per sub-LLM query. Analyze your input data and see if it is sufficient to just fit it in a few sub-LLM calls!

When you want to execute Python code in the REPL environment, wrap it in triple backticks with 'repl' language identifier. For example, say we want our recursive model to search for the magic number in the context (assuming the context is a string), and the context is very long, so we want to chunk it:
```repl
chunk = context[:10000]
answer = llm_query(f"What is the magic number in the context? Here is the chunk: {{chunk}}")
print(answer)
```

As an example, suppose you're trying to answer a question about a book. You can iteratively chunk the context section by section, query an LLM on that chunk, and track relevant information in a buffer.
```repl
query = "In Harry Potter and the Sorcerer's Stone, did Gryffindor win the House Cup because they led?"
for i, section in enumerate(context):
    if i == len(context) - 1:
        buffer = llm_query(f"You are on the last section of the book. So far you know that: {{buffers}}. Gather from this last section to answer {{query}}. Here is the section: {{section}}")
        print(f"Based on reading iteratively through the book, the answer is: {{buffer}}")
    else:
        buffer = llm_query(f"You are iteratively looking through a book, and are on section {{i}} of {{len(context)}}. Gather information to help answer {{query}}. Here is the section: {{section}}")
        print(f"After section {{i}} of {{len(context)}}, you have tracked: {{buffer}}")
```

As another example, when the context isn't that long (e.g. >100M characters), a simple but viable strategy is, based on the context chunk lengths, to combine them and recursively query an LLM over chunks. For example, if the context is a List[str], we ask the same query over each chunk using `llm_query_batched` for concurrent processing:
```repl
query = "A man became famous for his book "The Great Gatsby". How many jobs did he have?"
# Suppose our context is ~1M chars, and we want each sub-LLM query to be ~0.1M chars so we split it into 10 chunks
chunk_size = len(context) // 10
chunks = []
for i in range(10):
    if i < 9:
        chunk_str = "\n".join(context[i*chunk_size:(i+1)*chunk_size])
    else:
        chunk_str = "\n".join(context[i*chunk_size:])
    chunks.append(chunk_str)

# Use batched query for concurrent processing - much faster than sequential calls!
prompts = [f"Try to answer the following query: {{query}}. Here are the documents:\n{{chunk}}. Only answer if you are confident in your answer based on the evidence." for chunk in chunks]
answers = llm_query_batched(prompts)
for i, answer in enumerate(answers):
    print(f"I got the answer from chunk {{i}}: {{answer}}")
final_answer = llm_query(f"Aggregating all the answers per chunk, answer the original query about total number of jobs: {{query}}\\n\\nAnswers:\\n" + "\\n".join(answers))
```

As a final example, after analyzing the context and realizing its separated by Markdown headers, we can maintain state through buffers by chunking the context by headers, and iteratively querying an LLM over it:
```repl
# After finding out the context is separated by Markdown headers, we can chunk, summarize, and answer
import re
sections = re.split(r'### (.+)', context["content"])
buffers = []
for i in range(1, len(sections), 2):
    header = sections[i]
    info = sections[i+1]
    summary = llm_query(f"Summarize this {{header}} section: {{info}}")
    buffers.append(f"{{header}}: {{summary}}")
final_answer = llm_query(f"Based on these summaries, answer the original query: {{query}}\\n\\nSummaries:\\n" + "\\n".join(buffers))
```
In the next step, we can return FINAL_VAR(final_answer).

IMPORTANT: When you are done with the iterative process, you MUST provide a final answer using one of these methods. Do not use these unless you have completed your task:
1. FINAL(your answer) - Returns the LITERAL text inside the parentheses. Does NOT evaluate code or f-strings. Use this only for simple text like FINAL(42) or FINAL(The answer is yes).
2. FINAL_VAR(variable_name) - Evaluates and returns the value of a REPL variable. Use this when your answer is stored in a variable. For example, if you computed `result = 15 * 2` in the REPL, use FINAL_VAR(result) to return 30.

NEVER use FINAL(f"...") or FINAL(some_variable) - these will NOT be evaluated. Always use FINAL_VAR() for variables.

Think step by step carefully, plan, and execute this plan immediately in your response -- do not just say "I will do this" or "I will do that". Output to the REPL environment and recursive LLMs as much as possible. Remember to explicitly answer the original query in your final answer.
"""
)

# System prompt for persistent multi-turn mode
RLM_PERSISTENT_SYSTEM_PROMPT = textwrap.dedent(
    """You are tasked with answering queries in a multi-turn conversation. You have access to a REPL environment that maintains state across conversation turns. The context variable now contains structured information about the conversation history and current task.

The REPL environment is initialized with a `context` variable that is a dictionary containing:
1. `turn_id`: The current turn number (0-indexed)
2. `task_history`: A list of previous tasks with FULL iteration details from earlier turns. Each entry has:
   - `turn_id`: The turn number
   - `task`: What was asked
   - `answer`: The final answer that was provided
   - `iterations`: A list of all iterations, each containing:
     - `response`: The model's reasoning text
     - `code_blocks`: List of code executed and their outputs (stdout/stderr)
     - `final_answer`: The final answer if this iteration produced one
3. `context_{N}`: The input context for turn N (e.g., `context_0`, `context_1`, etc.)

You also have access to:
- `llm_query(prompt)`: Query a sub-LLM that can handle ~500K characters
- `llm_query_batched(prompts)`: Query multiple prompts concurrently for faster processing
- `print()`: View output and continue reasoning

IMPORTANT: In multi-turn mode, you can reference previous turns' full work:
- Check `context["task_history"]` to see what was discussed before
- Access `context["task_history"][N]["iterations"]` to see exactly what code was run and what outputs were produced in turn N
- Access `context["context_0"]`, `context["context_1"]`, etc. to see previous inputs
- Variables you create may persist across turns (if enabled), so you can build on previous work

Example of checking conversation history with full details:
```repl
# First, understand what has happened in previous turns
if context["task_history"]:
    print(f"Previous turns: {len(context['task_history'])}")
    for entry in context["task_history"]:
        print(f"\\nTurn {entry['turn_id']}: {entry['task'][:100]}...")
        print(f"  Answer: {entry['answer'][:200]}...")
        print(f"  Iterations: {len(entry['iterations'])}")
        # Look at what code was run
        for i, iteration in enumerate(entry['iterations']):
            for cb in iteration['code_blocks']:
                print(f"    Iter {i} code: {cb['code'][:100]}...")
                print(f"    Iter {i} output: {cb['stdout'][:100]}...")
else:
    print("This is the first turn - no history yet")
```

Example of building on previous work:
```repl
# If a previous turn computed something useful, reference it
if context["task_history"]:
    last_turn = context["task_history"][-1]
    # Look at what code produced the answer
    for iteration in last_turn["iterations"]:
        for cb in iteration["code_blocks"]:
            print(f"Previous code: {cb['code']}")
            print(f"Previous output: {cb['stdout']}")
```

When you are done, provide your final answer using:
1. FINAL(your answer) - Returns LITERAL text only. Does NOT evaluate f-strings or variables.
2. FINAL_VAR(variable_name) - Evaluates and returns a REPL variable's value. Use this for computed results.

NEVER use FINAL(f"...") or FINAL(some_var) - always use FINAL_VAR() for variables.

Think step by step, consider the conversation history, and execute your plan immediately. Remember to explicitly answer the current query in your final answer.
"""
)


def build_rlm_system_prompt(
    system_prompt: str,
    query_metadata: QueryMetadata,
) -> list[dict[str, str]]:
    """
    Build the initial system prompt for the REPL environment based on extra prompt metadata.

    Args:
        query_metadata: QueryMetadata object containing context metadata

    Returns:
        List of message dictionaries
    """

    context_lengths = query_metadata.context_lengths
    context_total_length = query_metadata.context_total_length
    context_type = query_metadata.context_type

    # If there are more than 100 chunks, truncate to the first 100 chunks.
    if len(context_lengths) > 100:
        others = len(context_lengths) - 100
        context_lengths = str(context_lengths[:100]) + "... [" + str(others) + " others]"

    metadata_prompt = f"The `context` variable is a {context_type} with {context_total_length} total characters, broken up into chunks of char lengths: {context_lengths}."

    return [
        {"role": "system", "content": system_prompt + "\n\n" + metadata_prompt},
    ]


USER_PROMPT = """Think step-by-step on what to do using the REPL environment (which contains the context) to answer the prompt.\n\nContinue using the REPL environment, which has the `context` variable, and querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:"""
USER_PROMPT_WITH_ROOT = """Think step-by-step on what to do using the REPL environment (which contains the context) to answer the original prompt: \"{root_prompt}\".\n\nContinue using the REPL environment, which has the `context` variable, and querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:"""

# Multi-turn specific prompts
USER_PROMPT_PERSISTENT = """Think step-by-step on what to do using the REPL environment to answer the current task.

This is turn {turn_id} of an ongoing conversation. The `context` variable contains:
- `task_history`: Previous tasks and their full iteration details from earlier turns
- `context_{turn_id}`: The current input for this turn

{history_note}

Continue using the REPL environment, querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:"""

USER_PROMPT_PERSISTENT_WITH_ROOT = """Think step-by-step on what to do using the REPL environment to answer the original prompt: \"{root_prompt}\".

This is turn {turn_id} of an ongoing conversation. The `context` variable contains:
- `task_history`: Previous tasks and their full iteration details from earlier turns
- `context_{turn_id}`: The current input for this turn

{history_note}

Continue using the REPL environment, querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:"""


def build_user_prompt(
    root_prompt: str | None = None,
    iteration: int = 0,
    turn_id: int | None = None,
    has_history: bool = False,
) -> dict[str, str]:
    """
    Build the user prompt for each iteration of the RLM.

    Args:
        root_prompt: Optional high-level prompt to show the model.
        iteration: Current iteration within this completion call (0-indexed).
        turn_id: For persistent mode, the current conversation turn number.
        has_history: For persistent mode, whether there's previous conversation history.
    """
    # Check if we're in persistent mode
    is_persistent = turn_id is not None

    if is_persistent:
        # Build history note
        if has_history:
            history_note = "You have conversation history from previous turns - check `context['task_history']` to understand what was discussed before."
        else:
            history_note = "This is the first turn - no previous conversation history."

        if iteration == 0:
            safeguard = "You have not interacted with the REPL environment or seen your context yet. Your next action should be to examine the context (including any conversation history) and figure out how to answer the current task.\n\n"
            if root_prompt:
                prompt = safeguard + USER_PROMPT_PERSISTENT_WITH_ROOT.format(
                    root_prompt=root_prompt, turn_id=turn_id, history_note=history_note
                )
            else:
                prompt = safeguard + USER_PROMPT_PERSISTENT.format(
                    turn_id=turn_id, history_note=history_note
                )
        else:
            prefix = "The history before is your previous interactions with the REPL environment in this turn. "
            if root_prompt:
                prompt = prefix + USER_PROMPT_PERSISTENT_WITH_ROOT.format(
                    root_prompt=root_prompt, turn_id=turn_id, history_note=history_note
                )
            else:
                prompt = prefix + USER_PROMPT_PERSISTENT.format(
                    turn_id=turn_id, history_note=history_note
                )
    else:
        # Non-persistent mode (original behavior)
        if iteration == 0:
            safeguard = "You have not interacted with the REPL environment or seen your prompt / context yet. Your next action should be to look through and figure out how to answer the prompt, so don't just provide a final answer yet.\n\n"
            prompt = safeguard + (
                USER_PROMPT_WITH_ROOT.format(root_prompt=root_prompt) if root_prompt else USER_PROMPT
            )
        else:
            prompt = "The history before is your previous interactions with the REPL environment. " + (
                USER_PROMPT_WITH_ROOT.format(root_prompt=root_prompt) if root_prompt else USER_PROMPT
            )

    return {"role": "user", "content": prompt}
