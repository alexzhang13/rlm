# AI Reflection

*1-page reflection on this project's use of Claude Code, per Juncheng's
proposal comment.*

This project was built almost entirely through Claude Code working in
the terminal — no VS Code, no Cursor. Over roughly six hours of active
session time, the coding agent drove a fork of `alexzhang13/rlm` through
five benchmark adapters, three non-RLM baselines, five system-prompt
arms, an experiment runner with per-cell timeouts, two analysis
scripts, and ~340 query cells of pilot execution. What I want to
record here is less the "what" than the agent-collaboration lessons —
three in particular.

**1. Delegating research to a subagent cost me 30+ minutes of
firefighting.** I spawned a `general-purpose` agent to verify HuggingFace
dataset schemas in parallel with building the base types. It returned a
detailed report, which I used to write the adapters. Three of its four
facts about public datasets were wrong: the LongBench-v2 domain name
("Code", actually "Code Repository Understanding"), the OOLONG dataset
path ("Zyphra/oolong", which doesn't exist), and the BrowseComp+ XOR
recipe (counter-suffixed SHA256 instead of repeated-digest). The
adapters looked plausible, passed unit scaffolding, and then failed
silently when I ran the pilot. Each miss needed an interactive
investigation to catch. Lesson: subagents save wall time only when the
work they produce is *falsifiable in one commit*. Research reports
about external systems are inherently hard to falsify from the
subagent's output alone.

**2. The Agent SDK's opaque failure modes cost me more than any
single bug.** Two specific ones. First, `max_buffer_size` defaults to
1 MB for the CLI's stdout line buffer; cross that with a 395K-token
BrowseComp+ prompt and the subprocess exits with bare `exit code 1`
and no stderr. I raised the buffer to 16 MB. Still failed. Dropped
BrowseComp+. Second, the Max subscription OAuth tokens are
*token-weighted*, not *call-count-weighted*: one 100K-token CodeQA
direct call spends more quota than twenty tier-2K S-NIAH queries. Small
"hello" probes keep passing even after big prompts have exhausted the
window. I lost the ability to read live progress through a grep pipe
because grep block-buffers stdout by default — had to re-fire with
`stdbuf -oL` on both sides. None of these are in the SDK docs.

**3. The best engineering decision I made was a hard per-cell timeout
added mid-run.** A CodeQA × direct cell hung for 44 minutes with no
progress — the Agent SDK never emitted a timeout — before I killed
it. The fix (a threaded `_run_with_timeout` in the runner that abandons
and moves on) was 40 lines and let every subsequent pilot complete.
In hindsight, that timeout should have been in place on day zero;
writing it *into* the runner rather than retrofitting it turned a
failed pilot night into a usable one. For the next project, runners
ship with per-cell deadlines.

I spent more of my agent-assisted time than expected on environment
scaffolding (OAuth token discovery, Agent SDK vs raw Anthropic
trade-offs, stdin-cap diagnosis) rather than on the core experimental
contribution. That's not a failure of agent assistance — it's a
feature of the actual work that needed doing. The part where Claude
Code accelerated me the most was the mechanical breadth: writing five
thin benchmark adapters with a shared `Query` type and paired-sampling
helper, then three analysis scripts that aggregate + bootstrap + print
a Markdown table, was a half-day task I didn't have to own keystroke
by keystroke. The part where human oversight mattered most was
catching the research agent's factual errors in smoke tests before
they contaminated the actual experiment matrix. The project shipped
with one failed smoke-test fix per subagent hand-off, which is about
the right calibration.
