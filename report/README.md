# CS2640 Report + AI Reflection

Two deliverables for May 6:

1. **3-page technical report** (`report.md` or `report.tex`) — NeurIPS or ACM
   template. Covers motivation → RLM background → cache theory → methods →
   results → discussion → limitations.
2. **1-page AI reflection** (`ai_reflection.md`) — which Claude Code
   sessions, what worked, what didn't, agent-assisted engineering choices.
   Juncheng requested this in his Apr 3 proposal comment.

## Outline

### Report (3 pages)

**1. Motivation (¼ page)**
Context windows are the bottleneck for modern LMs; the caching literature
has spent 50 years on eviction policies. Recent RLM paper (Zhang+Kraska+
Khattab 2026, arXiv:2512.24601) has a root LM manipulating prompt state in
a Python REPL via recursive sub-calls. Open question: if you teach the
root LM cache-eviction theory as prompt suggestions, does it manage its
REPL memory better?

**2. RLM background (½ page)**
REPL scaffold, `llm_query` / `rlm_query`, iteration loop, sub-call
depth. Reference to upstream fork commit.

**3. Cache theory (½ page)**
LRU, S3-FIFO, SIEVE, admission control. Frame as analogous to REPL
variable management.

**4. Methods (¾ page)**
8 methods × 2 benchmarks table:
  - direct, summary_agent, codeact_bm25
  - rlm_a0 vanilla
  - rlm_a1 LRU, rlm_a3 S3-FIFO, rlm_a4 SIEVE, rlm_a6 theory primer

Anthropic Sonnet 4.6 via Claude Agent SDK (OAuth). Benchmarks: S-NIAH
(synthetic haystack, 2K-8K tiers), LongBench-v2 CodeQA
(`domain="Code Repository Understanding"`). BrowseComp+ was infeasible
due to Agent SDK CLI stdin-length cap (documented in Limitations).

**5. Results (¾ page)**
Table 1: methods × benchmarks, cell = score ± cost.
Key finding: directive cache policies (A3, A4) hurt S-NIAH; gentler
theory primer (A6) matches vanilla. A1 (LRU) partial degradation.

**6. Discussion (½ page)**
Hypothesis: "drop freshly-created vars" guidance encourages the model to
evict the very context variable it needs. The theory primer's
"retention vs reconstruction cost" framing lets the model apply judgment
instead of following a rule.

**7. Limitations (¼ page)**
- n=3 per cell (paper used 50), CIs span [-1, 0]
- BrowseComp+ infeasible due to SDK CLI limit
- Behavioral cluster separation was 0.94 (<1.5 threshold) → no
  observably different strategies in final predictions; richer per-
  iteration traces would help

### AI reflection (1 page)

Structure: (a) which agents did what, (b) surprising failure modes,
(c) what I'd do differently.

Notes to incorporate:
- Agent SDK vs raw Anthropic decision (chose Agent SDK for OAuth billing;
  hit 1MB stdin cap + 5-hour quota windows)
- Research agent's factual errors (LongBench domain name wrong; Zyphra/
  oolong doesn't exist; these cost ~30 min to catch in smoke tests)
- Threaded cell timeout patch — in hindsight, the runner should have
  been built with per-cell timeouts from day 0
- The "prompt that causes the LM to hallucinate JavaScript hoisting"
  bug — worth a paragraph on LM reliability/coupling to prompt format
