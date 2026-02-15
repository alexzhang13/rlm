import copy
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any

try:
    import dill
except ImportError:
    dill = None

from rlm.core.comms_utils import LMRequest, send_lm_request, send_lm_request_batched
from rlm.core.types import REPLResult, RLMChatCompletion
from rlm.environments.base_env import NonIsolatedEnv
from rlm.utils.openai_utils import (
    parse_pydantic_response,
    pydantic_to_response_format,
    pydantic_to_tool,
)

# Rate limit detection markers for error strings returned by the LM handler
_RATE_LIMIT_MARKERS = ("rate_limit", "rate limit", "ratelimit", "429", "[rate_limited]")

# Markers for error text that leaks into "successful" response content
_LEAKED_ERROR_MARKERS = (
    "[rate_limited]",
    "[llm_error]",
    "[generation_failed]",
    "error: request failed",
    "error: lm query failed",
)

# Maximum iterations for tool-calling loop (prevents infinite loops)
MAX_TOOL_ITERATIONS = 10


def _is_rate_limit_error(error_str: str) -> bool:
    """Check if an error string indicates a rate limit failure."""
    lower = error_str.lower()
    return any(marker in lower for marker in _RATE_LIMIT_MARKERS)


def _content_is_leaked_error(content: str) -> bool:
    """Check if response content contains error text that leaked through as 'successful'."""
    if not content or len(content) > 5000:
        return False
    lower = content.lower()
    return any(marker in lower for marker in _LEAKED_ERROR_MARKERS)


# Safe builtins - blocks dangerous operations like eval/exec/input
_SAFE_BUILTINS = {
    "print": print,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "bool": bool,
    "type": type,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "reversed": reversed,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "any": any,
    "all": all,
    "pow": pow,
    "divmod": divmod,
    "chr": chr,
    "ord": ord,
    "hex": hex,
    "bin": bin,
    "oct": oct,
    "repr": repr,
    "ascii": ascii,
    "format": format,
    "hash": hash,
    "id": id,
    "iter": iter,
    "next": next,
    "slice": slice,
    "callable": callable,
    "hasattr": hasattr,
    "getattr": getattr,
    "setattr": setattr,
    "delattr": delattr,
    "dir": dir,
    "vars": vars,
    "bytes": bytes,
    "bytearray": bytearray,
    "memoryview": memoryview,
    "complex": complex,
    "object": object,
    "super": super,
    "property": property,
    "staticmethod": staticmethod,
    "classmethod": classmethod,
    "__import__": __import__,
    "open": open,
    "Exception": Exception,
    "BaseException": BaseException,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "AttributeError": AttributeError,
    "FileNotFoundError": FileNotFoundError,
    "OSError": OSError,
    "IOError": IOError,
    "RuntimeError": RuntimeError,
    "NameError": NameError,
    "ImportError": ImportError,
    "StopIteration": StopIteration,
    "AssertionError": AssertionError,
    "NotImplementedError": NotImplementedError,
    "ArithmeticError": ArithmeticError,
    "LookupError": LookupError,
    "Warning": Warning,
    "input": None,
    "eval": None,
    "exec": None,
    "compile": None,
    "globals": None,
    "locals": None,
}


class BaseLocalREPL(NonIsolatedEnv):
    """Base class for local REPL environments with persistent Python namespace."""

    def __init__(
        self,
        context_payload: dict | list | str | None = None,
        setup_code: str | None = None,
        persistent: bool = False,
        depth: int = 1,
        **kwargs,
    ):
        super().__init__(persistent=persistent, depth=depth, **kwargs)
        base_dir = os.path.join(tempfile.gettempdir(), "rlm_repl_envs")
        os.makedirs(base_dir, exist_ok=True)
        self.temp_dir = os.path.join(base_dir, str(uuid.uuid4()))
        os.makedirs(self.temp_dir, exist_ok=True)
        self._lock = threading.Lock()
        self._context_count: int = 0
        self._history_count: int = 0
        self.metadata: dict[str, Any] = kwargs.get("metadata", {})

        self.setup()
        if context_payload is not None:
            self.load_context(context_payload)
        if setup_code:
            self.execute_code(setup_code)

    def setup(self):
        self.globals: dict[str, Any] = {
            "__builtins__": _SAFE_BUILTINS.copy(),
            "__name__": "__main__",
        }
        self.locals: dict[str, Any] = {}
        self._pending_llm_calls: list[RLMChatCompletion] = []
        self.globals["FINAL_VAR"] = self._final_var
        self.globals["llm_query"] = self._llm_query
        self.globals["llm_query_batched"] = self._llm_query_batched

    def _final_var(self, variable_name: str) -> str:
        variable_name = variable_name.strip().strip("\"'")
        if variable_name in self.locals:
            return str(self.locals[variable_name])
        return f"Error: Variable '{variable_name}' not found"

    def _ensure_messages_format(self, prompt: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        if isinstance(prompt, list) and all(isinstance(item, dict) for item in prompt):
            return prompt
        raise ValueError(f"Invalid prompt type: {type(prompt)}")

    def load_context(self, context_payload: dict | list | str):
        self.add_context(context_payload, 0)

    def add_context(
        self, context_payload: dict | list | str, context_index: int | None = None
    ) -> int:
        if context_index is None:
            context_index = self._context_count
        var_name = f"context_{context_index}"
        if isinstance(context_payload, str):
            context_path = os.path.join(self.temp_dir, f"{var_name}.txt")
            with open(context_path, "w") as f:
                f.write(context_payload)
            self.execute_code(f"with open(r'{context_path}', 'r') as f:\n    {var_name} = f.read()")
        else:
            context_path = os.path.join(self.temp_dir, f"{var_name}.json")
            with open(context_path, "w") as f:
                json.dump(context_payload, f)
            self.execute_code(
                f"import json\nwith open(r'{context_path}', 'r') as f:\n    {var_name} = json.load(f)"
            )
        if context_index == 0:
            self.execute_code(f"context = {var_name}")
        self._context_count = max(self._context_count, context_index + 1)
        return context_index

    def get_context_count(self) -> int:
        return self._context_count

    def add_history(
        self, message_history: list[dict[str, Any]], history_index: int | None = None
    ) -> int:
        if history_index is None:
            history_index = self._history_count
        var_name = f"history_{history_index}"
        self.locals[var_name] = copy.deepcopy(message_history)
        if history_index == 0:
            self.locals["history"] = self.locals[var_name]
        self._history_count = max(self._history_count, history_index + 1)
        return history_index

    def get_history_count(self) -> int:
        return self._history_count

    @contextmanager
    def _capture_output(self):
        with self._lock:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
            try:
                sys.stdout, sys.stderr = stdout_buf, stderr_buf
                yield stdout_buf, stderr_buf
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

    def execute_code(self, code: str) -> REPLResult:
        start_time = time.perf_counter()
        self._pending_llm_calls = []
        with self._capture_output() as (stdout_buf, stderr_buf):
            try:
                combined = {**self.globals, **self.locals}
                exec(code, combined, combined)
                for key, value in combined.items():
                    if key not in self.globals and not key.startswith("_"):
                        self.locals[key] = value
                stdout, stderr = stdout_buf.getvalue(), stderr_buf.getvalue()
            except Exception as e:
                stdout, stderr = (
                    stdout_buf.getvalue(),
                    stderr_buf.getvalue() + f"\n{type(e).__name__}: {e}",
                )
        return REPLResult(
            stdout=stdout,
            stderr=stderr,
            locals=self.locals.copy(),
            execution_time=time.perf_counter() - start_time,
            rlm_calls=self._pending_llm_calls.copy(),
        )

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        self.globals.clear()
        self.locals.clear()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
        return False

    def __del__(self):
        self.cleanup()

    @property
    def trace_id(self) -> str | None:
        return self.metadata.get("trace_id")

    def _llm_query(self, *args, **kwargs):
        raise NotImplementedError

    def _llm_query_batched(self, *args, **kwargs):
        raise NotImplementedError


class DirectREPL(BaseLocalREPL):
    """Local REPL that calls the LMHandler directly (socket-less)."""

    def __init__(self, lm_handler: Any, **kwargs):
        self.lm_handler = lm_handler
        super().__init__(**kwargs)

    def update_handler_address(self, address):
        return None

    def _llm_query(
        self,
        prompt,
        model=None,
        response_format=None,
        tools=None,
        tool_handler=None,
        response_model=None,
    ) -> Any:
        if tools is not None and tool_handler is None:
            raise ValueError("tool_handler is required")
        if tools is not None:
            assert tool_handler is not None
            tool_handler_fn = tool_handler
        else:
            tool_handler_fn = None
        if response_model and not response_format:
            response_format = pydantic_to_response_format(response_model)
        if tools:
            processed = []
            for t in tools:
                if isinstance(t, type) and hasattr(t, "model_json_schema"):
                    processed.append(pydantic_to_tool(t))
                else:
                    processed.append(t)
            tools = processed

        messages = self._ensure_messages_format(prompt)
        for _ in range(MAX_TOOL_ITERATIONS):
            request = LMRequest(
                prompt=messages,
                model=model,
                depth=self.depth,
                response_format=response_format,
                tools=tools,
                metadata=self.metadata,
            )
            response = self.lm_handler.handle_request(request)
            if not response.success:
                return f"__LLM_ERROR__|handler_error|0|{response.error}"
            cc = response.chat_completion
            if cc is None:
                return "__LLM_ERROR__|handler_error|0|Missing completion"
            if cc.error:
                return f"__LLM_ERROR__|{cc.error_type}|{cc.status_code}|{cc.error}"
            content = cc.response
            if tools and isinstance(content, dict):
                tool_calls = content.get("tool_calls", [])
                if not tool_calls:
                    self._pending_llm_calls.append(cc)
                    final = str(content.get("content") or "")
                    return (
                        parse_pydantic_response(response_model, final) if response_model else final
                    )
                messages.append(
                    {
                        "role": "assistant",
                        "content": content.get("content"),
                        "tool_calls": [
                            {
                                "id": t["id"],
                                "type": "function",
                                "function": {
                                    "name": t["name"],
                                    "arguments": (
                                        t["arguments"]
                                        if isinstance(t["arguments"], str)
                                        else json.dumps(t["arguments"])
                                    ),
                                },
                            }
                            for t in tool_calls
                        ],
                    }
                )
                for t in tool_calls:
                    arguments = t.get("arguments")
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {"raw": arguments}
                    if tool_handler_fn is None:
                        raise ValueError("tool_handler is required")
                    try:
                        res = tool_handler_fn(t["name"], arguments)
                    except Exception as e:
                        res = f"Error: {e}"
                    messages.append({"role": "tool", "tool_call_id": t["id"], "content": res})
                continue
            if isinstance(content, dict):
                content = content.get("content", "")
            if _content_is_leaked_error(content):
                return "__LLM_ERROR__|leaked_error|0|Leaked error"
            self._pending_llm_calls.append(cc)
            if response_model:
                try:
                    return parse_pydantic_response(response_model, content)
                except Exception as e:
                    return f"__LLM_ERROR__|pydantic_error|0|{e}"
            return content
        return "__LLM_ERROR__|tool_loop_error|0|Max iterations"

    def _llm_query_batched(
        self,
        prompts,
        model=None,
        response_formats=None,
        tools=None,
        tool_handler=None,
        response_models=None,
    ) -> list[Any]:
        if tools or response_models:
            return [
                self._llm_query(
                    p,
                    model,
                    response_formats[i] if response_formats else None,
                    tools,
                    tool_handler,
                    response_models[i] if response_models else None,
                )
                for i, p in enumerate(prompts)
            ]
        request = LMRequest(
            prompts=prompts,
            model=model,
            depth=self.depth,
            response_formats=response_formats,
            metadata=self.metadata,
        )
        response = self.lm_handler.handle_request(request)
        if not response.success:
            return [f"Error: {response.error}"] * len(prompts)
        res = []
        for cc in response.chat_completions:
            if cc.error:
                res.append(f"Error: {cc.error}")
            else:
                self._pending_llm_calls.append(cc)
                res.append(cc.response)
        return res


class SocketREPL(BaseLocalREPL):
    """Local REPL that communicates via sockets."""

    def __init__(self, lm_handler_address=None, **kwargs):
        self.lm_handler_address = lm_handler_address
        super().__init__(**kwargs)

    def _llm_query(
        self,
        prompt,
        model=None,
        response_format=None,
        tools=None,
        tool_handler=None,
        response_model=None,
    ) -> Any:
        if tools is not None and tool_handler is None:
            raise ValueError("tool_handler is required")
        if not self.lm_handler_address:
            return "Error: No LM handler configured"
        if tools is not None:
            assert tool_handler is not None
            tool_handler_fn = tool_handler
        else:
            tool_handler_fn = None
        if response_model and not response_format:
            response_format = pydantic_to_response_format(response_model)
        if tools:
            processed = []
            for t in tools:
                if isinstance(t, type) and hasattr(t, "model_json_schema"):
                    processed.append(pydantic_to_tool(t))
                else:
                    processed.append(t)
            tools = processed

        messages = self._ensure_messages_format(prompt)
        for _ in range(MAX_TOOL_ITERATIONS):
            req = LMRequest(
                prompt=messages,
                model=model,
                depth=self.depth,
                response_format=response_format,
                tools=tools,
                metadata=self.metadata,
            )
            resp = send_lm_request(self.lm_handler_address, req)
            if not resp.success:
                return f"__LLM_ERROR__|socket_error|0|{resp.error}"
            cc = resp.chat_completion
            if cc is None:
                return "__LLM_ERROR__|socket_error|0|Missing completion"
            if cc.error:
                return f"__LLM_ERROR__|{cc.error_type}|{cc.status_code}|{cc.error}"
            content = cc.response
            if tools and isinstance(content, dict):
                tool_calls = content.get("tool_calls", [])
                if not tool_calls:
                    self._pending_llm_calls.append(cc)
                    final = str(content.get("content") or "")
                    return (
                        parse_pydantic_response(response_model, final) if response_model else final
                    )
                messages.append(
                    {
                        "role": "assistant",
                        "content": content.get("content"),
                        "tool_calls": [
                            {
                                "id": t["id"],
                                "type": "function",
                                "function": {
                                    "name": t["name"],
                                    "arguments": (
                                        t["arguments"]
                                        if isinstance(t["arguments"], str)
                                        else json.dumps(t["arguments"])
                                    ),
                                },
                            }
                            for t in tool_calls
                        ],
                    }
                )
                for t in tool_calls:
                    arguments = t.get("arguments")
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {"raw": arguments}
                    if tool_handler_fn is None:
                        raise ValueError("tool_handler is required")
                    try:
                        res = tool_handler_fn(t["name"], arguments)
                    except Exception as e:
                        res = f"Error: {e}"
                    messages.append({"role": "tool", "tool_call_id": t["id"], "content": res})
                continue
            if isinstance(content, dict):
                content = content.get("content", "")
            if _content_is_leaked_error(content):
                return "__LLM_ERROR__|leaked_error|0|Leaked error"
            self._pending_llm_calls.append(cc)
            if response_model:
                try:
                    return parse_pydantic_response(response_model, content)
                except Exception as e:
                    return f"__LLM_ERROR__|pydantic_error|0|{e}"
            return content
        return "__LLM_ERROR__|tool_loop_error|0|Max iterations"

    def _llm_query_batched(
        self,
        prompts,
        model=None,
        response_formats=None,
        tools=None,
        tool_handler=None,
        response_models=None,
    ) -> list[Any]:
        if tools or response_models:
            return [
                self._llm_query(
                    p,
                    model,
                    response_formats[i] if response_formats else None,
                    tools,
                    tool_handler,
                    response_models[i] if response_models else None,
                )
                for i, p in enumerate(prompts)
            ]
        if not self.lm_handler_address:
            return ["Error: No LM handler configured"] * len(prompts)
        try:
            resps = send_lm_request_batched(
                self.lm_handler_address,
                prompts,
                model=model,
                depth=self.depth,
                response_formats=response_formats,
            )
            res = []
            for r in resps:
                if not r.success:
                    res.append(f"Error: {r.error}")
                else:
                    cc = r.chat_completion
                    if cc is None:
                        res.append("Error: Missing completion")
                        continue
                    if cc.error:
                        res.append(f"Error: {cc.error}")
                    else:
                        self._pending_llm_calls.append(cc)
                        res.append(cc.response)
            return res
        except Exception as e:
            return [f"Error: {e}"] * len(prompts)

    def update_handler_address(self, address):
        self.lm_handler_address = address


class DillREPL(DirectREPL):
    def save_state(self, path):
        if dill is None:
            raise ImportError("dill required")
        clean = {k: v for k, v in self.locals.items() if not k.startswith("_") and not callable(v)}
        with open(path, "wb") as f:
            dill.dump(clean, f)

    def load_state(self, path):
        if dill is None:
            raise ImportError("dill required")
        if os.path.exists(path):
            with open(path, "rb") as f:
                self.locals.update(dill.load(f))


LocalREPL = SocketREPL
