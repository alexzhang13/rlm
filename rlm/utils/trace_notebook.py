import json
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Any


def create_trace_notebook(path: str, metadata: dict | None = None) -> None:
    nbformat, v4 = _get_nbformat()
    nb = v4.new_notebook(cells=[])

    title = v4.new_markdown_cell("# RLM Trace Notebook")
    _tag_cell(title, ["rlm", "rlm-title"])
    nb.cells.append(title)

    resume_cell = v4.new_code_cell(_resume_placeholder_source())
    _tag_cell(resume_cell, ["rlm", "rlm-resume"])
    nb.cells.append(resume_cell)

    if metadata:
        nb.cells.append(_make_metadata_cell(metadata))

    _write_notebook(nbformat, nb, path)


def append_metadata(path: str, metadata: dict) -> None:
    nbformat, v4 = _get_nbformat()
    nb = nbformat.read(path, as_version=4)
    nb.cells.append(_make_metadata_cell(metadata))
    _write_notebook(nbformat, nb, path)


def append_iteration(path: str, iteration: dict) -> None:
    nbformat, v4 = _get_nbformat()
    nb = nbformat.read(path, as_version=4)

    iteration_index = iteration.get("iteration")
    response = iteration.get("response", "")
    nb.cells.append(_make_response_cell(response, iteration_index))

    code_blocks = iteration.get("code_blocks", [])
    replay_calls = []
    for block in code_blocks:
        code = block.get("code", "")
        result = block.get("result", {})
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        nb.cells.append(_make_code_cell(code, stdout, stderr, iteration_index))

        rlm_calls = result.get("rlm_calls", [])
        if rlm_calls:
            replay_calls.extend(rlm_calls)
            nb.cells.append(_make_llm_calls_cell(rlm_calls, iteration_index))

    if replay_calls:
        _update_replay_block_in_notebook(nb, replay_calls)

    _write_notebook(nbformat, nb, path)


@dataclass
class TraceWriterHandle:
    log_path: str
    notebook_path: str
    thread: threading.Thread
    stop_event: threading.Event


def start_trace_writer(
    log_path: str, notebook_path: str, poll_interval: float = 0.25
) -> TraceWriterHandle:
    if not os.path.exists(notebook_path):
        create_trace_notebook(notebook_path)

    stop_event = threading.Event()
    thread = threading.Thread(
        target=_watch_log,
        args=(log_path, notebook_path, stop_event, poll_interval),
        daemon=True,
    )
    thread.start()
    return TraceWriterHandle(
        log_path=log_path,
        notebook_path=notebook_path,
        thread=thread,
        stop_event=stop_event,
    )


def stop_trace_writer(handle: TraceWriterHandle) -> None:
    handle.stop_event.set()
    if handle.thread.is_alive():
        handle.thread.join(timeout=2.0)


def enable_trace_notebook(
    log_dir: str,
    file_name: str = "rlm",
    notebook_path: str | None = None,
    poll_interval: float = 0.25,
):
    from rlm.logger import RLMLogger

    logger = RLMLogger(log_dir=log_dir, file_name=file_name)
    trace_path = notebook_path or f"{logger.log_file_path}.trace.ipynb"
    create_trace_notebook(trace_path)
    handle = start_trace_writer(logger.log_file_path, trace_path, poll_interval=poll_interval)
    return logger, handle


def _watch_log(
    log_path: str,
    notebook_path: str,
    stop_event: threading.Event,
    poll_interval: float,
) -> None:
    while not os.path.exists(log_path) and not stop_event.is_set():
        time.sleep(poll_interval)
    if stop_event.is_set():
        return

    with open(log_path) as f:
        while not stop_event.is_set():
            line = f.readline()
            if not line:
                time.sleep(poll_interval)
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            if entry_type == "metadata":
                append_metadata(notebook_path, entry)
            elif entry_type == "run_context":
                _update_resume_cell(notebook_path, entry)
            elif entry_type == "iteration":
                append_iteration(notebook_path, entry)


def _make_metadata_cell(metadata: dict) -> Any:
    _, v4 = _get_nbformat()
    lines = ["## Run Metadata", ""]
    for key, value in metadata.items():
        if key == "type":
            continue
        lines.append(f"- {key}: {value}")
    cell = v4.new_markdown_cell("\n".join(lines))
    _tag_cell(cell, ["rlm", "rlm-metadata"])
    return cell


def _make_response_cell(response: str, iteration_index: int | None) -> Any:
    _, v4 = _get_nbformat()
    header = "## Iteration"
    if iteration_index is not None:
        header = f"## Iteration {iteration_index}"
    text = f"{header}\n\n### Model Response\n\n{response}"
    cell = v4.new_markdown_cell(text)
    _tag_cell(cell, ["rlm", f"iteration-{iteration_index}", "role-assistant"])
    return cell


def _make_code_cell(code: str, stdout: str, stderr: str, iteration_index: int | None) -> Any:
    nbformat, v4 = _get_nbformat()
    outputs = []
    if stdout:
        outputs.append(v4.new_output(output_type="stream", name="stdout", text=stdout))
    if stderr:
        outputs.append(v4.new_output(output_type="stream", name="stderr", text=stderr))
    cell = v4.new_code_cell(source=code, outputs=outputs, execution_count=None)
    _tag_cell(cell, ["rlm", f"iteration-{iteration_index}", "role-code"])
    return cell


def _make_llm_calls_cell(rlm_calls: list[dict], iteration_index: int | None) -> Any:
    _, v4 = _get_nbformat()
    lines = ["### Sub-LM Calls", ""]
    for call in rlm_calls:
        prompt = _truncate_text(call.get("prompt", ""))
        response = _truncate_text(call.get("response", ""))
        lines.append("#### Prompt")
        lines.append("```")
        lines.append(prompt)
        lines.append("```")
        lines.append("#### Response")
        lines.append("```")
        lines.append(response)
        lines.append("```")
        lines.append("")
    cell = v4.new_markdown_cell("\n".join(lines))
    _tag_cell(cell, ["rlm", f"iteration-{iteration_index}", "role-llm-calls"])
    return cell


def _update_resume_cell(path: str, entry: dict) -> None:
    nbformat, _ = _get_nbformat()
    nb = nbformat.read(path, as_version=4)

    prompt = entry.get("prompt")
    root_prompt = entry.get("root_prompt")
    session_mode = entry.get("session_mode")
    env_kwargs = entry.get("environment_kwargs", {})
    setup_code = None
    if isinstance(env_kwargs, dict):
        setup_code = env_kwargs.get("setup_code")
    source = _resume_source(
        prompt,
        root_prompt,
        setup_code,
        replay_map=None,
        session_mode=session_mode,
    )

    for cell in nb.cells:
        tags = cell.get("metadata", {}).get("tags", [])
        if "rlm-resume" in tags:
            cell["source"] = source
            _write_notebook(nbformat, nb, path)
            return

    nb.cells.insert(0, _make_resume_cell(source))
    _write_notebook(nbformat, nb, path)


def _make_resume_cell(source: str) -> Any:
    _, v4 = _get_nbformat()
    cell = v4.new_code_cell(source)
    _tag_cell(cell, ["rlm", "rlm-resume"])
    return cell


def _resume_placeholder_source() -> str:
    return "\n".join(
        [
            "# RLM trace resume cell",
            "# Context payload will be injected when run_context is logged.",
            "completion_context = None",
            "session_context_0 = None",
            "context_history = None",
            "session_history = None",
            "root_prompt = None",
        ]
    )


def _resume_source(
    prompt: Any,
    root_prompt: str | None,
    setup_code: str | None,
    replay_map: dict | None,
    session_mode: bool | None,
) -> str:
    lines = [
        "# RLM trace resume cell",
        "import json",
        "",
    ]

    context_var = _context_var_name(session_mode)
    prompt_json = _safe_json_dumps(prompt)
    if prompt_json is None:
        lines.append("# NOTE: prompt was not JSON-serializable; fill in manually.")
        lines.append(f"{context_var} = {repr(prompt)}")
    else:
        lines.append(f"{context_var} = json.loads(r'''{prompt_json}''')")

    if session_mode:
        lines.append("context_history = [session_context_0]")
        lines.append("session_history = []")

    if root_prompt is None:
        lines.append("root_prompt = None")
    else:
        root_json = _safe_json_dumps(root_prompt)
        if root_json is None:
            lines.append(f"root_prompt = {repr(root_prompt)}")
        else:
            lines.append(f"root_prompt = json.loads(r'''{root_json}''')")

    if setup_code:
        lines.append("")
        lines.append("# Optional setup code from environment_kwargs")
        lines.append("exec(r'''{}''')".format(setup_code.replace("'''", "\\'\\'\\'")))

    lines.append("")
    lines.append(_build_replay_block(replay_map or {}))

    return "\n".join(lines)


def _update_replay_block_in_notebook(nb, replay_calls: list[dict]) -> None:
    resume_cell = None
    for cell in nb.cells:
        tags = cell.get("metadata", {}).get("tags", [])
        if "rlm-resume" in tags:
            resume_cell = cell
            break
    if resume_cell is None:
        return

    source = resume_cell.get("source", "")
    if isinstance(source, list):
        source = "".join(source)

    replay_map = _extract_replay_map(source)
    replay_map = _merge_replay_calls(replay_map, replay_calls)
    resume_cell["source"] = _insert_or_replace_replay_block(source, replay_map)


def _context_var_name(session_mode: bool | None) -> str:
    return "session_context_0" if session_mode else "completion_context"


def _merge_replay_calls(replay_map: dict, replay_calls: list[dict]) -> dict:
    for call in replay_calls:
        prompt = call.get("prompt")
        response = call.get("response")
        if response is None:
            continue
        key = _prompt_key(prompt)
        replay_map.setdefault(key, []).append(response)
    return replay_map


def _prompt_key(prompt: Any) -> str:
    if isinstance(prompt, str):
        return prompt
    try:
        return json.dumps(prompt, ensure_ascii=True, sort_keys=True)
    except TypeError:
        return repr(prompt)


def _extract_replay_map(source: str) -> dict:
    match = re.search(
        r"# BEGIN RLM REPLAY MAP\s+_rlm_replay = json.loads\(r'''(.*?)'''\)\s+# END RLM REPLAY MAP",
        source,
        re.DOTALL,
    )
    if not match:
        return {}
    raw = match.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _insert_or_replace_replay_block(source: str, replay_map: dict) -> str:
    block = _build_replay_block(replay_map)
    pattern = re.compile(
        r"# BEGIN RLM REPLAY MAP\s+.*?# END RLM REPLAY MAP",
        re.DOTALL,
    )
    if pattern.search(source):
        return pattern.sub(lambda _: block, source)
    return source.rstrip() + "\n\n" + block


def _build_replay_block(replay_map: dict) -> str:
    replay_json = json.dumps(replay_map, ensure_ascii=True)
    lines = [
        "# BEGIN RLM REPLAY MAP",
        f"_rlm_replay = json.loads(r'''{replay_json}''')",
        "",
        "def _prompt_key(prompt):",
        "    if isinstance(prompt, str):",
        "        return prompt",
        "    try:",
        "        return json.dumps(prompt, ensure_ascii=True, sort_keys=True)",
        "    except TypeError:",
        "        return repr(prompt)",
        "",
        "def llm_query(prompt, model=None):",
        "    key = _prompt_key(prompt)",
        "    if key not in _rlm_replay or not _rlm_replay[key]:",
        '        raise RuntimeError("No replay available for this prompt.")',
        "    return _rlm_replay[key].pop(0)",
        "",
        "def llm_query_batched(prompts, model=None):",
        "    return [llm_query(prompt, model=model) for prompt in prompts]",
        "# END RLM REPLAY MAP",
    ]
    return "\n".join(lines)


def _safe_json_dumps(value: Any) -> str | None:
    try:
        return json.dumps(value, ensure_ascii=True)
    except TypeError:
        return None


def _truncate_text(value: Any, limit: int = 2000) -> str:
    text = value if isinstance(value, str) else str(value)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"


def _tag_cell(cell: Any, tags: list[str]) -> None:
    metadata = cell.setdefault("metadata", {})
    existing = metadata.get("tags", [])
    metadata["tags"] = list(dict.fromkeys(existing + tags))


def _get_nbformat():
    try:
        import nbformat
        from nbformat import v4
    except Exception as exc:
        raise ValueError("Trace notebook requires nbformat to be installed.") from exc
    return nbformat, v4


def _write_notebook(nbformat, nb, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    nbformat.write(nb, path)
