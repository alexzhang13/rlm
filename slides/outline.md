# CS2640 Final Presentation Outline

8-minute slot, Apr 27–May 4. Instructor (Juncheng Yang) + class.

## Target audience

Classmates who know S3-FIFO / SIEVE from lectures but haven't read the
RLM paper. Contextualize RLM in the first 2 minutes.

## Slide flow (8 slides @ ~1 min each)

1. **Title + one-sentence thesis** (0:00–0:30)
   *"Teaching an LLM cache-eviction theory as prompt hints: does it
   change how it manages its own REPL memory?"*

2. **The cache we all forgot — the LM prompt** (0:30–1:30)
   Modern LMs have a 200K-token cache called "context." When it fills,
   we evict. Every framework does ad hoc eviction (FIFO, recency, drop-
   oldest). That's 50-year-old cache theory. What if we just told the
   LM to use the right policy?

3. **Recursive Language Models in 90 seconds** (1:30–2:30)
   RLM paper (Zhang+Kraska+Khattab 2026). Root LM has a Python REPL
   and can issue recursive sub-calls. Variables persist across turns.
   Diagram: root LM ↔ REPL ↔ sub-LMs.

4. **Our experiment: 5 arms** (2:30–3:30)
   A0 vanilla, A1 LRU, A3 S3-FIFO, A4 SIEVE, A6 cache-theory primer
   (L. LFU admission etc.). Each arm appends a hint block to the RLM
   system prompt.

5. **Setup** (3:30–4:30)
   Anthropic Sonnet 4.6 via Agent SDK (Max plan billing). Benchmarks:
   S-NIAH (haystack), LongBench-v2 CodeQA. [Note BrowseComp+ dropped —
   SDK CLI 1MB stdin cap killed multi-doc retrieval.]

6. **Results** (4:30–6:00)
   Table: arm × benchmark, score ± cost. Headline:
   - Directive policies (A3, A4) HURT on S-NIAH vs vanilla.
   - Gentler theory primer (A6) matches vanilla.
   Hypothesis: imperative "drop vars unless re-referenced" tells the
   model to evict the context variable itself.

7. **Engineering lessons** (6:00–7:00)
   - Agent SDK has a hidden 1MB stdin cap that silently kills the CLI
     with no stderr. Cost me 2 hours.
   - Max plan quotas are token-weighted, not call-count-weighted; one
     100K-token call can exhaust a multi-query budget.
   - Prompt format matters: "===== TEXT =====" banners triggered off-
     task responses (hallucinated JavaScript hoisting docs).

8. **Takeaways + future work** (7:00–8:00)
   - Prompting LMs with systems knowledge is NOT a free lunch —
     directive advice can mis-trigger eviction behaviors.
   - Behavioral feature space didn't separate arms (ratio 0.94 < 1.5).
     Richer per-iteration trace features would help.
   - Want: a cache-aware RLM scaffold that tracks variable access
     counts internally, not relying on LM self-discipline.

## Visuals to prepare

- Diagram: RLM scaffold (slide 3)
- Table 1 (slide 6) — render from `results/table1.md` → PNG
- One before/after trace excerpt showing A3 vs A0 on a tier-8K query
  (slide 7 or appendix)
