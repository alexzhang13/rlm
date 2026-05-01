# AI Reflection

*1-page reflection on this project's use of Claude Code, per Juncheng's
proposal comment.*

This project was built almost entirely through Claude Code working in
the terminal, no VS Code, no Cursor. I drove it through a cron loop
with the goals defined clearly at the start, then let the agent execute
against them across many sessions. The agent took a fork of `alexzhang13/rlm`
through five benchmark adapters, three non-RLM baselines, five system-prompt
arms, an experiment runner with per-cell timeouts, two analysis scripts,
and ~340 query cells of pilot execution. What I want to record here are
the agent-collaboration lessons, not the implementation summary.

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
single bug.** A 395K-token BrowseComp+ prompt produced a bare `exit
code 1` with no stderr because of a stdout buffer cap I could not move
from the Python side. I dropped the benchmark. The Max-subscription
OAuth quota is token-weighted, not call-count-weighted, so small "hello"
probes kept passing even after big prompts had exhausted the window,
which made it hard to tell what state I was in. None of this is in the
SDK docs.

**3. The best engineering decision I made was a hard per-cell timeout
added mid-run.** A CodeQA × direct cell hung for 44 minutes with no
progress before I killed it. The fix, a threaded `_run_with_timeout`
that abandons and moves on, was 40 lines and let every subsequent pilot
complete. In hindsight, that timeout should have been in place on day
zero. For the next project, runners ship with per-cell deadlines.

**4. Token consumption substantially exceeded my forecast.** The pilot
plan and actual spend diverged by several multiples. The Agent SDK
injects a ~16K-token Claude Code preamble into every call. Max-subscription
quotas are token-weighted, so a single 100K-token CodeQA call drained
more quota than twenty short S-NIAH calls. The per-cell hang in lesson
3 cost a full overnight before I caught it. Next time, multiply naive
token estimates by harness overhead first, and budget for the long tail
of extension runs the design inevitably grows into.

**5. The agent extends well. It does not simplify well.** When I asked
for a new arm, a new benchmark, another analysis script, the agent did
the work cleanly. When I asked it to find the simpler version of a
tangled draft, or to reframe a messy result into a clean narrative, the
output was thinner. Coherent reframings still required me. Mechanical
implementation the agent did well. The thinking about *what to do*, and
the work of pulling a streamlined story out of a reasonably messy reality,
stayed with me. Most of the project hours went to that thinking and to
scaffolding, not to typing.
