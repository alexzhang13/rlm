I'm too lazy to write up a stricter set of rules for PRs, but generally I just ask that you avoid touching `core/` files unless necessary. I'd like to keep the repo as minimal as possible for as long as possible so it's still easy for users to read the entire repo in a short sitting.

Generally though, I'll outline the things we 1) need to implement; 2) want to implement; 3) can dream about implementing. The state of this repo is that it should be fully functional for most use cases, but it isn't super fast or anything.

There are likely more things we'll want to do, but here are some things I've been meaning to tackle. 

## Urgent TODOs
- [ ] **Additional Sandboxes**. Any more interesting, commonly used sandboxes (e.g. Prime Sandboxes are WIP atm).
- [ ] **Persistent REPL across the client.** Currently, the REPL is only persistent across an RLM completion call, but for multi-turn settings we may want a `flag` to handle persistence. There's some trickiness here though, which is that after every turn, the input context will change / be added onto. I haven't decided yet (open to suggestions), but we could add `context_{x}` and tell the model that it has a new context or something in the next completion step.
- [ ] **Finding interesting benchmarks / examples we can provide to get started**.
- [ ] **Improve documentation**. See `docs/`.

Low-hanging fruit of the urgent TODOs:
- [ ] **Add better unit tests.** I have a Mock LM class inspired by `verifiers`, but we need more comprehensive unit tests. Generally these should be made with most PRs.
- [ ] **Do more comprehensive bug finding**: Just find bugs and report them, we'll try to squash them all

## Would-be-nice TODOs
- [ ] **Multi-modal / arbitrary input support.** As it stands, we just support `str` / standard LM dict messages, but we should generally support any type of picklable-inputs. We might want to think of clever ways to do this lazily as well.
- [ ] **File-system based environments**. Beyond REPLs, we can also think about supporting filesystem + bash as a new type of environment. There seems to be a lot of interest in this.
- [ ] **Improved UI for visualization**.
- [ ] **Improvements to what data gets stored, useful for training and statistics about RLMs**/

## "If you can tackle these, thanks LOL" TODOs
- [ ] **Pipelining / asynchrony of LM calls**. This could be a paper of its own IMO, but how we deal with LM calls and how we actually implement these recursive calls can have big implications. I suspect this might happen when the repo has a massive overhaul, but something to think about.
- [ ] **Efficient prefix caching**. Another "would be nice" thing, but requires restructuring a lot of the core logic. Could also be a paper / entire research project of its own.
- [ ] **Training models to work as RLMs**. See the `verifiers` [rlm_env](https://github.com/PrimeIntellect-ai/verifiers/blob/main/verifiers/envs/experimental/rlm_env.py) as a starting point.