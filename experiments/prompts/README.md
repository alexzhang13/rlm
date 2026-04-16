# Prompt arms

Five system-prompt variants for the RLM root model. Each file contains the
**suffix** that gets appended after `\n\n---\n\n` to the upstream
`RLM_SYSTEM_PROMPT` (from `rlm/utils/prompts.py`). The runner composes:

    full = RLM_SYSTEM_PROMPT + "\n\n---\n\n" + open(arm).read()

| Arm | File              | Flavor                                          |
|-----|-------------------|-------------------------------------------------|
| A0  | `A0_vanilla.txt`  | Empty suffix — control                          |
| A1  | `A1_lru.txt`      | LRU recency hint                                |
| A3  | `A3_s3fifo.txt`   | S3-FIFO probation/main/ghost hint               |
| A4  | `A4_sieve.txt`    | SIEVE lazy promotion hint                       |
| A6  | `A6_theory.txt`   | Cache-theory primer w/ citations                |

Tone convention: suggestive, not directive. "Consider", "you might", "one
option is". No hard imperatives. The hint is offered as a tool, not a rule.

Trace-grep targets (Phase 6 gate check):
- A1: `LRU`, `last_used`, `recently`
- A3: `probation`, `ghost`, `promote`, `one-hit`
- A4: `SIEVE`, `lazy`, `re-referenced`
- A6: `reconstruction`, `admission`, `retention_cost`, `S3-FIFO`, `SIEVE`

If hit rate < 20% per arm in pilot, iterate the prompt.
