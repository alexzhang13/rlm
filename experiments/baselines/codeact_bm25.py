"""Baseline 3 — CodeAct + BM25.

Retrieval-agent baseline from RLM paper §3.2: give the model a BM25
retriever over the input context + a Python REPL. The model can call
`search(query)` to pull relevant chunks. This simulates a retrieval-
augmented agent without any memory-management policy.

Implementation choice: the REPL we give the model is VIRTUAL — we run a
ReAct-style loop where the model emits either
  SEARCH("query string")
  CODE\n```python\n...\n```
  FINAL("answer")
and we execute the action, feed the result back, repeat.

This lets us cleanly attribute cost per-iteration without needing a real
sandboxed Python (which the RLM scaffold already handles). Our Python
execution is ast.literal_eval + a few allowed operations — since the goal
is to measure the *retrieval + reasoning* baseline, not give the model a
full coding harness. The RLM paper itself runs their CodeAct baseline in
a restricted sandbox; this matches.
"""
from __future__ import annotations

import re
import time
from typing import Any

import tiktoken
from rank_bm25 import BM25Okapi

from experiments.baselines._llm import sonnet_call
from experiments.baselines.base import Baseline, RunResult
from experiments.benchmarks.base import Query

_TOK = tiktoken.get_encoding("cl100k_base")
_MAX_ITER = 8
_CHUNK_TOKENS_FOR_BM25 = 400


_SYSTEM_PROMPT = (
    "You are a retrieval agent. You have access to:\n"
    "  - A BM25 search index over the user's context (built from 400-token "
    "chunks of the input).\n"
    "  - A simple Python evaluator for short arithmetic/string ops.\n\n"
    "On each step you MUST emit EXACTLY ONE of:\n"
    "  SEARCH(\"your query\")           # returns top-5 matching chunks\n"
    "  PYTHON\\n```python\\n<expr>\\n```   # evaluates the expression and returns str(value)\n"
    "  FINAL(\"your final answer\")     # ends the loop\n"
    "Do not include anything else. Reason briefly in a single sentence before "
    "the directive if useful. You have at most 8 steps."
)


def _chunk(text: str, n_tokens: int = _CHUNK_TOKENS_FOR_BM25) -> list[str]:
    toks = _TOK.encode(text)
    return [_TOK.decode(toks[i : i + n_tokens]) for i in range(0, len(toks), n_tokens)]


def _safe_eval(code: str) -> str:
    """Very restricted eval — literals, arithmetic, str methods, len(), min/max."""
    try:
        import ast
        tree = ast.parse(code, mode="eval")
        allowed_calls = {"len", "min", "max", "sum", "abs", "int", "float", "str"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fname = getattr(node.func, "id", None)
                if fname not in allowed_calls:
                    return f"ERROR: call to '{fname}' not allowed"
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute)):
                if isinstance(node, ast.Attribute):
                    continue  # str methods OK
                return "ERROR: imports not allowed"
        return str(eval(compile(tree, "<input>", "eval"), {"__builtins__": {"len": len, "min": min, "max": max, "sum": sum, "abs": abs, "int": int, "float": float, "str": str}}, {}))
    except Exception as e:
        return f"ERROR: {e}"


def _parse_action(text: str) -> tuple[str, str]:
    """Return (kind, arg). Kind in {'search','python','final','invalid'}."""
    m = re.search(r'SEARCH\(\s*"(.*?)"\s*\)', text, re.DOTALL)
    if m:
        return "search", m.group(1)
    m = re.search(r'FINAL\(\s*"(.*?)"\s*\)', text, re.DOTALL)
    if m:
        return "final", m.group(1)
    m = re.search(r"PYTHON\s*```(?:python)?\n(.*?)```", text, re.DOTALL)
    if m:
        return "python", m.group(1).strip()
    return "invalid", text


class CodeActBM25Baseline(Baseline):
    name = "codeact_bm25"

    def run(self, query: Query) -> RunResult:
        t0 = time.perf_counter()

        chunks = _chunk(query.prompt)
        bm25 = BM25Okapi([c.lower().split() for c in chunks])

        def search(q: str, k: int = 5) -> str:
            scores = bm25.get_scores(q.lower().split())
            order = sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]
            return "\n\n".join(f"[chunk {i} score={scores[i]:.2f}]\n{chunks[i]}" for i in order)

        in_tok = out_tok = cr = cc = 0
        cost = 0.0
        num_calls = 0
        transcript: list[str] = [f"QUESTION:\n{query.prompt[:500]}...\n"]
        final_answer = ""
        iters = 0

        for _ in range(_MAX_ITER):
            iters += 1
            user = "\n\n".join(transcript) + "\n\nYour next step:"
            call = sonnet_call(user=user, system=_SYSTEM_PROMPT)
            in_tok += call.input_tokens
            out_tok += call.output_tokens
            cr += call.cache_read_tokens
            cc += call.cache_creation_tokens
            cost += call.cost_usd
            num_calls += 1

            transcript.append(f"ASSISTANT:\n{call.text}")
            kind, arg = _parse_action(call.text)
            if kind == "final":
                final_answer = arg
                break
            elif kind == "search":
                obs = search(arg)
                transcript.append(f"OBSERVATION (top-5 from BM25):\n{obs}")
            elif kind == "python":
                val = _safe_eval(arg)
                transcript.append(f"OBSERVATION (python):\n{val}")
            else:
                # Model didn't follow protocol — push back and let it retry
                transcript.append(
                    "OBSERVATION: Your last response didn't match the required "
                    "SEARCH/PYTHON/FINAL format. Try again."
                )

        if not final_answer:
            # Ran out of iterations — take the last assistant message as the answer
            final_answer = call.text if num_calls > 0 else ""

        return RunResult(
            benchmark=query.metadata.get("benchmark", "unknown"),
            method=self.name,
            query_id=query.id,
            prediction=final_answer,
            duration_sec=time.perf_counter() - t0,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_tokens=cr,
            cache_creation_tokens=cc,
            cost_usd=cost,
            num_iterations=iters,
            num_subcalls=num_calls,
            extras={"num_chunks_indexed": len(chunks)},
        )
