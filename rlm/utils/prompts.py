import textwrap

from rlm.core.types import QueryMetadata

# System prompt for the REPL environment with explicit final answer checking
RLM_SYSTEM_PROMPT = textwrap.dedent(
    """
Eres un RLM con acceso a un REPL para resolver una pregunta usando un PDF.

En el REPL existen:
- `context`: List[str] donde cada elemento es una página del PDF.
- `llm_query(prompt: str)` (SOLO 1 argumento, no kwargs).
- `search_pages(query: str, top_k: int)` -> [(page_index, score)]
- `get_bundle(page_indices, ...)` -> texto con cabeceras --- PAGE N ---
- `summarize_pages(page_indices, chunk_chars)` -> resúmenes por lotes usando llm_query

REGLAS DURAS:
- NO pidas permiso (“¿procedo?”). Ejecuta.
- NO uses variables inexistentes (por ejemplo `root_prompt` NO existe dentro del REPL).
  Si necesitas la pregunta en REPL, haz: q = \"\"\"...\"\"\".
- NO llames FINAL() en Python. FINAL(...) debe aparecer SOLO en tu respuesta final como texto.
- Toda afirmación importante debe llevar (PAGE N). Si no está en el PDF, escribe: NO ENCONTRADO.

ESTRATEGIA (decídela tú, no la preguntes):
1) Define q en REPL (copiando la pregunta del usuario).
2) Usa search_pages(q, top_k=15).
3) Si hay resultados:
   - page_ids = [i for i,_ in results]
   - bundle = get_bundle(page_ids, ...)
   - answer = llm_query("Responde con citas (PAGE N)..." + bundle)
4) Si no hay resultados:
   - summaries = summarize_pages(list(range(len(context))), chunk_chars=60000)
   - reduce_input = "\\n\\n".join([...])
   - answer = llm_query("Combina y responde con citas..." + reduce_input)
5) Devuelve FINAL(answer)

Actúa en la primera iteración.
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

    metadata_prompt = f"Your context is a {context_type} with {context_total_length} total characters, and is broken up into chunks of char lengths: {context_lengths}."

    return [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": metadata_prompt},
    ]


USER_PROMPT = """Think step-by-step on what to do using the REPL environment (which contains the context) to answer the prompt.\n\nContinue using the REPL environment, which has the `context` variable, and querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:"""
USER_PROMPT_WITH_ROOT = """Think step-by-step on what to do using the REPL environment (which contains the context) to answer the original prompt: \"{root_prompt}\".\n\nContinue using the REPL environment, which has the `context` variable, and querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:"""


def build_user_prompt(
    root_prompt: str | None = None,
    iteration: int = 0,
    context_count: int = 1,
    history_count: int = 0,
) -> dict[str, str]:
    if iteration == 0:
        safeguard = "You ALREADY have the user's question in the root prompt text. Your next action should be to inspect `context` and start executing REPL code immediately. Do NOT wait for another user question.\n\n"
        prompt = safeguard + (
            USER_PROMPT_WITH_ROOT.format(root_prompt=root_prompt) if root_prompt else USER_PROMPT
        )
    else:
        prompt = "The history before is your previous interactions with the REPL environment. " + (
            USER_PROMPT_WITH_ROOT.format(root_prompt=root_prompt) if root_prompt else USER_PROMPT
        )

    # Inform model about multiple contexts if present
    if context_count > 1:
        prompt += f"\n\nNote: You have {context_count} contexts available (context_0 through context_{context_count - 1})."

    # Inform model about prior conversation histories if present
    if history_count > 0:
        if history_count == 1:
            prompt += "\n\nNote: You have 1 prior conversation history available in the `history` variable."
        else:
            prompt += f"\n\nNote: You have {history_count} prior conversation histories available (history_0 through history_{history_count - 1})."

    return {"role": "user", "content": prompt}
