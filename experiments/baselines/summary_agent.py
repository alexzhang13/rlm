"""Baseline 2 — "Summary Agent": iterative context compaction.

This is the baseline Juncheng explicitly flagged in his Apr 3 proposal
comment: the RLM paper's main competitor. Algorithm (Sun/Wu/Yu-style):

1. Tokenize input. If it fits in the model budget, call once and return.
2. Otherwise chunk the input (~80K tokens / chunk), summarize each chunk in
   parallel with a Sonnet call that also sees the original question. Keep
   only each chunk's extracted-relevant-content.
3. Concatenate summaries. If still too large, recurse (summarize summaries).
4. Run the final question against the reduced context.

We record per-round cost + token counts so Table 1 can compare against RLM
on both accuracy and cost.
"""
from __future__ import annotations

import time

import tiktoken

from experiments.baselines._llm import sonnet_call
from experiments.baselines.base import Baseline, RunResult
from experiments.benchmarks.base import Query

_TOK = tiktoken.get_encoding("cl100k_base")
_CHUNK_TOKENS = 80_000   # per-chunk context size for summarization round
_FINAL_BUDGET = 150_000  # final question+context must fit under this

_COMPACT_TEMPLATE = (
    "You are compressing a long document for another model that will answer "
    "the following question.\n\n"
    "QUESTION: {question}\n\n"
    "Write a tight summary of the CHUNK below that preserves every detail "
    "that could possibly be relevant to the QUESTION above (names, numbers, "
    "quotes, dates, identifiers, relationships). Omit filler. Prefer specific "
    "extracted text over paraphrase. If the chunk is irrelevant, write "
    "'NOTHING RELEVANT'.\n\n"
    "----- CHUNK -----\n"
    "{chunk}\n"
    "----- END CHUNK -----"
)

_FINAL_TEMPLATE = (
    "{question}\n\n"
    "You have been given the following compacted evidence summaries in place "
    "of the full documents:\n\n"
    "----- EVIDENCE -----\n"
    "{evidence}\n"
    "----- END EVIDENCE -----\n\n"
    "Answer the question directly, using only the evidence above."
)


def _split_question(prompt: str) -> tuple[str, str]:
    """Heuristic — treat the LAST 2000 tokens as the question/instruction
    section, everything before as context. Works for our 5 benchmarks
    because question text is always near the end or the top of the prompt.
    We take the shorter of (head 2K, tail 2K) as "question"."""
    toks = _TOK.encode(prompt)
    if len(toks) <= _FINAL_BUDGET:
        # No split needed
        return prompt, ""
    # Use the first 500 tokens as question banner (contains instructions
    # from our benchmark adapters like "A secret key has been hidden...").
    # Everything else is context.
    question = _TOK.decode(toks[:500])
    context = _TOK.decode(toks[500:])
    return question, context


def _chunk_tokens(text: str, chunk_tokens: int) -> list[str]:
    toks = _TOK.encode(text)
    chunks: list[str] = []
    for start in range(0, len(toks), chunk_tokens):
        chunks.append(_TOK.decode(toks[start : start + chunk_tokens]))
    return chunks


class SummaryAgentBaseline(Baseline):
    name = "summary_agent"

    def run(self, query: Query) -> RunResult:
        t0 = time.perf_counter()

        in_tok = out_tok = cr = cc = 0
        cost = 0.0
        num_calls = 0
        rounds: list[dict] = []

        question, context = _split_question(query.prompt)
        if not context:
            # Small prompt: treat as direct
            call = sonnet_call(user=query.prompt)
            in_tok, out_tok, cr, cc, cost = (
                call.input_tokens, call.output_tokens,
                call.cache_read_tokens, call.cache_creation_tokens, call.cost_usd,
            )
            return RunResult(
                benchmark=query.metadata.get("benchmark", "unknown"),
                method=self.name,
                query_id=query.id,
                prediction=call.text,
                duration_sec=time.perf_counter() - t0,
                input_tokens=in_tok, output_tokens=out_tok,
                cache_read_tokens=cr, cache_creation_tokens=cc,
                cost_usd=cost,
                num_iterations=1, num_subcalls=0,
                extras={"rounds": [], "fit_directly": True},
            )

        # Iterative chunk-and-summarize rounds
        current = context
        round_idx = 0
        while True:
            tok_count = len(_TOK.encode(current))
            if tok_count <= _FINAL_BUDGET:
                break
            if round_idx >= 3:
                # Safety bound — 3 rounds of summarization is plenty
                break
            chunks = _chunk_tokens(current, _CHUNK_TOKENS)
            summaries: list[str] = []
            for ch in chunks:
                call = sonnet_call(
                    user=_COMPACT_TEMPLATE.format(question=question, chunk=ch)
                )
                summaries.append(call.text)
                in_tok += call.input_tokens
                out_tok += call.output_tokens
                cr += call.cache_read_tokens
                cc += call.cache_creation_tokens
                cost += call.cost_usd
                num_calls += 1
            current = "\n\n".join(summaries)
            rounds.append(
                {"round": round_idx, "num_chunks": len(chunks), "out_tokens": len(_TOK.encode(current))}
            )
            round_idx += 1

        # Final answer call
        final = sonnet_call(user=_FINAL_TEMPLATE.format(question=question, evidence=current))
        in_tok += final.input_tokens
        out_tok += final.output_tokens
        cr += final.cache_read_tokens
        cc += final.cache_creation_tokens
        cost += final.cost_usd
        num_calls += 1

        return RunResult(
            benchmark=query.metadata.get("benchmark", "unknown"),
            method=self.name,
            query_id=query.id,
            prediction=final.text,
            duration_sec=time.perf_counter() - t0,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_tokens=cr,
            cache_creation_tokens=cc,
            cost_usd=cost,
            num_iterations=round_idx + 1,
            num_subcalls=num_calls - 1,
            extras={"rounds": rounds, "fit_directly": False},
        )
