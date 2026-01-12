import json
from typing import Any

from rlm.core.types import RLMIteration


def build_trace_markdown(
    run_context: dict[str, Any],
    iterations: list[RLMIteration],
    *,
    include_subcalls: bool = True,
) -> str:
    lines: list[str] = []
    lines.append("## Run Context\n")
    payload = {
        "prompt": run_context.get("prompt"),
        "root_prompt": run_context.get("root_prompt"),
    }
    lines.append("```json\n")
    lines.append(safe_json(payload))
    lines.append("\n```\n")

    env_kwargs = run_context.get("environment_kwargs")
    if isinstance(env_kwargs, dict) and env_kwargs.get("setup_code"):
        lines.append("### Setup Code\n")
        lines.append("```python\n")
        lines.append(escape_fence(env_kwargs.get("setup_code", "")))
        lines.append("\n```\n")

    for index, iteration in enumerate(iterations, start=1):
        lines.append(f"## Iteration {index}\n\n")
        lines.append("### Model Response\n\n")
        lines.append(stringify(iteration.response))
        lines.append("\n\n")

        for block_index, code_block in enumerate(iteration.code_blocks, start=1):
            lines.append(f"### Code Block {block_index}\n\n")
            lines.append("```python\n")
            lines.append(escape_fence(stringify(code_block.code)))
            lines.append("\n```\n\n")

            stdout = code_block.result.stdout
            stderr = code_block.result.stderr
            if stdout:
                lines.append("**stdout**\n\n```\n")
                lines.append(escape_fence(stdout))
                lines.append("\n```\n\n")
            if stderr:
                lines.append("**stderr**\n\n```\n")
                lines.append(escape_fence(stderr))
                lines.append("\n```\n\n")

            if include_subcalls and code_block.result.rlm_calls:
                lines.append("### Sub-LM Calls\n\n")
                for call in code_block.result.rlm_calls:
                    lines.append("#### Prompt\n\n")
                    lines.append(stringify(call.prompt))
                    lines.append("\n\n")
                    lines.append("#### Response\n\n")
                    lines.append(stringify(call.response))
                    lines.append("\n\n")

    return "".join(lines).rstrip() + "\n"


def safe_json(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(payload, ensure_ascii=True, indent=2)
    except TypeError:
        return json.dumps(
            {key: stringify(value) for key, value in payload.items()},
            ensure_ascii=True,
            indent=2,
        )


def escape_fence(value: str) -> str:
    return value.replace("```", "``\\`")


def stringify(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)
