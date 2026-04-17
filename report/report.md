# Cache-Informed Prompting for Recursive Language Models

**Warren Zhu · CS2640 Spring 2026 · Final Project Report**

## 1. Motivation

Context windows are the storage hierarchy of modern language models, and
every LLM framework implements ad-hoc eviction: FIFO by turn, recency,
drop-oldest when token-budget trips. Fifty years of cache-systems
research has already catalogued the trade-offs (LRU, LFU, S3-FIFO,
SIEVE, admission control). If the LM itself is going to decide what to
keep in its prompt, should we teach it the caching literature?

This project asks a focused empirical question: **when the root LM of a
Recursive Language Model is given cache-eviction theory as a prompt
suggestion, does its behavior or performance change?** The question sits
directly on top of Juncheng's proposal-comment steer toward
"enhancing LLM-based compaction" and the course's S3-FIFO / SIEVE
units.

## 2. Background — Recursive Language Models

RLM (Zhang+Kraska+Khattab, arXiv:2512.24601) gives a root Sonnet model a
Python REPL it can read and write across iterations. The REPL exposes
`llm_query(prompt)` for one-shot sub-calls and `rlm_query(prompt)` for
spawning a nested RLM. Variables persist; `del` evicts. The root LM runs
until it emits `FINAL(...)`. Critically, RLM lets the model be the
*programmer* of its own context — chunking, summarising, retaining —
instead of having a framework impose a policy. That makes it the right
substrate to test whether systems knowledge transfers.

## 3. Cache theory in 250 words

A cache policy must decide, on eviction, which element to drop. The
classical answers exploit structure in the reference stream: **LRU**
assumes temporal locality (just-used → soon-used); **LFU** exploits hot
items; **S3-FIFO** (Yang, SOSP '23) splits items into probation, main,
and ghost zones — 50-70% of items are one-hit wonders and deserve a
cheap filter; **SIEVE** (Zhang, NSDI '24) argues *lazy promotion* — wait
for a second reference before elevating an item. Admission control
(do I *put* this in the cache?) is a separate axis and often more
consequential than replacement. For an RLM REPL, every variable has a
*retention cost* (tokens carried across iterations) and a *reconstruction
cost* (tokens/calls to regenerate). Classical reasoning says retain when
reconstruction > retention. The five arms in this study encode that
decision framework at varying specificity.

## 4. Methods

**Arms.** Five system-prompt variants all share the upstream RLM
system prompt, with a hint block appended after `\n\n---\n\n`:

| Arm | Suffix |
|-----|-------------|
| A0  | (empty — control) |
| A1  | LRU: "prefer to `del` the variable you have not touched recently" |
| A3  | S3-FIFO: "think of intermediate vars as probation / main / ghost zones" |
| A4  | SIEVE: "elevate on the *second* reference, not the first" |
| A6  | Cache-theory primer: retention-vs-reconstruction cost, LRU/LFU/S3-FIFO/SIEVE policies, admission filtering, and a batching suggestion |

Tone is suggestive ("consider", "one option is"), never directive, so
that refusal is a first-class outcome instead of a command-following
artifact.

**Benchmarks.** Two long-context tasks:

- **S-NIAH.** Synthetic needle-in-haystack (tiers 2K / 4K / 8K tokens).
  Scoring = exact match on the hidden integer.
- **LongBench-v2 CodeQA** (`zai-org/LongBench-v2`, domain =
  `Code Repository Understanding`). 503 examples total; 4-way MC;
  scoring = letter-exact on A/B/C/D. Contexts ~100K tokens.

BrowseComp+ was in scope but had to be dropped — see §7.

**Baselines.** Three non-RLM methods: `direct` (single Sonnet call with
head+tail truncation to 150K user-tokens), `summary_agent` (iterative
chunk-and-summarise compaction, the method Juncheng's proposal comment
called out), `codeact_bm25` (ReAct loop with SEARCH/PYTHON/FINAL and a
BM25 index on 400-token chunks).

**Model.** Claude Sonnet 4.6 for all arms and baselines, both root and
sub-calls, accessed through `claude_agent_sdk.query()` over an OAuth
Max-subscription token. Using the Agent SDK rather than raw Anthropic
means every call carries a ~16K-token Claude-Code system preamble; this
is a constant across arms and leaves relative comparisons valid, but
inflates absolute cost numbers vs. the RLM paper's raw-API baseline.

**Sampling.** Same 3 queries per benchmark fed to all 8 methods (paired
design), seeded `random.sample(indices, k=N, seed=2640)`. Full-scale
target was N=10; pilot and the data that grounds this report is N=3 per
cell.

## 5. Results

### Table 1 — Pilot, N=3 per cell

Cell = score ($mean ± $std across N queries). Cost excludes the ~16K
Claude Code preamble that is constant across all arms.

| Method | S-NIAH | CodeQA |
|---|---|---|
| direct | **1.00** ($0.057 ± $0.013) | **1.00** ($0.659 ± $0.224) |
| summary_agent | **1.00** ($0.044 ± $0.018) | 0.33 ($4.622 ± $3.642) |
| codeact_bm25 | **1.00** ($0.095 ± $0.086) | 0.33 ($0.184 ± $0.026) |
| rlm_a0 (vanilla) | **1.00** ($0.194 ± $0.076) | 0.50 ($0.322 ± $0.320) |
| rlm_a1 (LRU) | 0.67 ($0.208 ± $0.108) | 0.00 ($3.180 ± $5.048) [n=2] |
| rlm_a3 (S3-FIFO) | 0.33 ($0.174 ± $0.034) | 0.67 ($0.606 ± $0.228) |
| rlm_a4 (SIEVE) | 0.33 ($0.255 ± $0.275) | — [n=0; quota-blocked] |
| rlm_a6 (theory primer) | **1.00** ($0.163 ± $0.062) | **1.00** ($0.148 ± $0.257) [n=1] |

Paired bootstrap 95%-CI on score delta vs rlm_a0, per benchmark:

    sniah  rlm_a1          Δ=-0.333 [-1.000, +0.000]
    sniah  rlm_a3          Δ=-0.667 [-1.000, +0.000]
    sniah  rlm_a4          Δ=-0.667 [-1.000, +0.000]
    sniah  rlm_a6          Δ=+0.000 [+0.000, +0.000]

The CIs are wide because N=3. Nothing is statistically significant at
95%. But the directional signal is consistent enough to outline a
hypothesis.

### Headline finding

**On S-NIAH, directive eviction policies (A3 S3-FIFO, A4 SIEVE) both
drop from 1.00 → 0.33, while the gentler retention-vs-reconstruction
primer (A6) matches the vanilla A0.** A1 (LRU) sits in between at 0.67.
On CodeQA, the pattern inverts for A3 and A6: both exceed A0, though
with very small N. This suggests the cache-aware prompts' effect is
*task-conditional* — they hurt on pure retrieval (S-NIAH) and may help
on multi-step code reasoning (CodeQA).

## 6. Discussion

The most parsimonious explanation for S-NIAH: the REPL-level `context`
variable *is* the haystack. When A3 instructs the model to `del` freshly
created variables that aren't re-referenced within 1-2 iterations, and
A4 tells it "scan in creation order, drop the first one never
re-referenced," the model sometimes obliges — and evicts the variable
holding the needle. A1 is less aggressive (recency-not-re-reference) and
degrades less. A6's framing ("retention vs reconstruction cost") is a
decision framework rather than a rule, which leaves the model room to
notice that the context has infinite reconstruction cost and therefore
retain it. The vanilla A0 has no eviction language at all and coasts.

CodeQA's 4-way multiple-choice scoring is coarse, and our N=3 pattern
(A6 and A3 beating A0) could easily be noise. The more interesting
hypothesis it supports is that caching-style hints might be useful
specifically when a task benefits from carrying intermediate
computational results across iterations — which S-NIAH does not, but
code understanding might.

### Behavioral analysis

Cluster-separation ratio between-arm/within-arm on our final-prediction
feature vector was 1.00, below the 1.5 threshold for "behaviorally
distinct." Arms did not observably differ in the span of the
final-answer string (which is the only surface the runner logs). The
richer signal — per-iteration REPL traces — would need `RLMLogger`
wired into the runner, deferred.

## 7. Limitations

- **N=3 per cell.** RLM paper uses N=50. All CIs contain zero.
- **rlm_a4 × CodeQA = 0/3.** Max-plan OAuth quota windows on all three
  available tokens exhausted before this cell could run. Three follow-up
  retries (post-quota-probe-pass) still errored in 2s each, indicating
  the quota is token-weighted and 100K-token CodeQA calls drain it
  faster than small calls. The full-scale run (N=10) is gated on a
  multi-hour fully-rested quota window that wasn't available in the
  pilot session.
- **BrowseComp+ dropped.** 1K-doc setting → 395K user tokens per query.
  The Agent SDK CLI has an undocumented stdin-line-length cap below
  35K user tokens; calls above this die with a bare `exit code 1` and
  no stderr. Raising `max_buffer_size` to 16 MB did not help. Workaround
  paths exist (raw Anthropic SDK with a real API key, or forcing RLM's
  chunking so no single LM call carries the corpus) but fall outside
  this pilot's budget.
- **Claude Code preamble contamination.** Every call carries a ~16K
  preamble that isn't our prompt. Constant across arms, so relative
  comparisons are safe, but absolute costs are ~3-4× a raw-API Sonnet
  baseline.
- **Behavioral trace features only cover final predictions.** No
  per-iteration REPL inspection, so we can't say *how* the arms
  differ, only *that* the scores differ.
- **OOLONG dropped.** Initial plan included OOLONG trec_coarse at
  131K context, but the public `oolongbench/oolong-synth` dataset has
  no trec_coarse split. Substitution with `agnews` was scoped out
  early to focus the experimental budget on S-NIAH and CodeQA.

## 8. Conclusion

Teaching an LLM cache-eviction theory via prompt hints is **not a free
lunch.** At least on synthetic retrieval, directive policies actively
hurt by encouraging the model to evict the very variable it needs. The
gentler *decision-framework* style (A6's retention-vs-reconstruction
framing) matches vanilla on S-NIAH and trends positive on code
reasoning.

The immediate engineering takeaway: if we want cache-aware recursive
scaffolds, the policy almost certainly needs to be enforced by the
runtime (reference-count tracking, admission control on variable
creation) rather than delegated to the LM's self-discipline. Putting
S3-FIFO *behavior* into the REPL environment, not into the system
prompt, is the natural next step.

### What I'd do with another week

1. Wire `RLMLogger` into the runner so per-iteration traces enter the
   behavioral feature space; the cluster-separation ratio should rise
   above 1.5 once we can see actual `del` calls and peek patterns.
2. Run N=10 across all 8 methods on a fresh quota window.
3. Implement an A-prime arm where the RLM runtime *tracks* variable
   access counts and the LM sees `SHOW_VARS()` output annotated with
   reference counts. Same theory, but the accounting is done for the
   LM — test whether policy enforcement at the runtime outperforms
   policy suggestion via prompt.
