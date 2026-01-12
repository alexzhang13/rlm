from html import escape
from pprint import pformat

from rlm.core.types import REPLResult, RLMChatCompletion, RLMIteration


def render_completion(completion: RLMChatCompletion, *, show_usage: bool = True) -> None:
    """Render a final RLM completion in a notebook."""
    display, Markdown, HTML = get_display_helpers()

    display(Markdown("### Final Answer"))
    display(HTML(f"<pre>{escape(stringify(completion.response))}</pre>"))

    if show_usage:
        display(Markdown("### Usage Summary"))
        display(HTML(f"<pre>{escape(format_usage_summary(completion))}</pre>"))


def render_iteration(
    iteration: RLMIteration,
    *,
    show_code: bool = True,
    show_locals: bool = False,
    show_subcalls: bool = True,
) -> None:
    """Render a single RLM iteration in a notebook."""
    display, Markdown, HTML = get_display_helpers()

    display(Markdown("### Iteration"))
    display(Markdown("**Model Response**"))
    display(HTML(f"<pre>{escape(stringify(iteration.response))}</pre>"))

    for index, code_block in enumerate(iteration.code_blocks, start=1):
        display(Markdown(f"**Code Block {index}**"))
        if show_code:
            display(HTML(f"<pre>{escape(stringify(code_block.code))}</pre>"))
        render_repl_result(
            code_block.result,
            show_locals=show_locals,
            show_subcalls=show_subcalls,
        )


def render_trace(
    iterations: list[RLMIteration],
    *,
    show_code: bool = True,
    show_locals: bool = False,
    show_subcalls: bool = True,
) -> None:
    """Render multiple iterations in a notebook."""
    display, Markdown, _ = get_display_helpers()

    for index, iteration in enumerate(iterations, start=1):
        display(Markdown(f"## Iteration {index}"))
        render_iteration(
            iteration,
            show_code=show_code,
            show_locals=show_locals,
            show_subcalls=show_subcalls,
        )


def render_repl_result(
    result: REPLResult,
    *,
    show_locals: bool = False,
    show_subcalls: bool = True,
) -> None:
    """Render a REPLResult in a notebook."""
    display, Markdown, HTML = get_display_helpers()

    if result.stdout:
        display(Markdown("**stdout**"))
        display(HTML(f"<pre>{escape(stringify(result.stdout))}</pre>"))
    if result.stderr:
        display(Markdown("**stderr**"))
        display(HTML(f"<pre>{escape(stringify(result.stderr))}</pre>"))
    if show_locals:
        display(Markdown("**locals**"))
        display(HTML(f"<pre>{escape(stringify(pformat(result.locals)))}</pre>"))
    if show_subcalls and result.rlm_calls:
        display(Markdown("**sub-lm calls**"))
        for call in result.rlm_calls:
            display(HTML(f"<pre>{escape(stringify(call.response))}</pre>"))


def format_usage_summary(completion: RLMChatCompletion) -> str:
    parts = []
    for model, usage in completion.usage_summary.model_usage_summaries.items():
        parts.append(
            f"{model}: calls={usage.total_calls}, "
            f"input_tokens={usage.total_input_tokens}, "
            f"output_tokens={usage.total_output_tokens}"
        )
    return "\n".join(parts) if parts else "No usage data"


def stringify(value) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def get_display_helpers():
    try:
        from IPython.display import HTML, Markdown, display
    except Exception as exc:
        raise ValueError("Notebook rendering requires IPython to be installed.") from exc

    return display, Markdown, HTML
