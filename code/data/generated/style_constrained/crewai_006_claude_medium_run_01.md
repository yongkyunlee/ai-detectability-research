# Memory and Context Management in CrewAI

Agent frameworks have a dirty secret: they're terrible at remembering things. You build a five-task crew, and by the time Task 5 runs, it's either drowning in 8,000 tokens of unfiltered prior output or it's forgotten what Task 1 decided. CrewAI's unified memory system is an ambitious attempt to fix this, and it gets a surprising amount right -- but you need to understand how the pieces connect before you can trust it in production.

## The Old Model vs. The Unified Memory

CrewAI used to split memory into four separate stores: short-term, long-term, entity, and external. That's gone. The current system collapses everything into a single `Memory` class backed by LanceDB, stored by default under `./.crewai/memory`. You call `remember()` to save, `recall()` to retrieve, and the LLM handles the rest -- inferring scope, categories, and importance at save time, then ranking results with a composite score that blends semantic similarity, recency decay, and importance.

The API is deliberately simple. `memory = Memory()` gives you a working instance with `gpt-4o-mini` as the analysis LLM and OpenAI's `text-embedding-3-small` as the default embedder. Both are lazily initialized, so construction never fails even if your API keys aren't configured yet. Errors surface only when you actually try to save or recall.

## Composite Scoring: The Core Idea

Recall isn't just vector search. Every result is scored by a weighted formula:

```
composite = semantic_weight * similarity + recency_weight * decay + importance_weight * importance
```

The defaults are 0.5/0.3/0.2 for semantic/recency/importance, with a 30-day recency half-life. This means a memory from yesterday scores noticeably higher on recency than one from three weeks ago, even if the embeddings match equally well. You can tune these weights for your use case. A sprint retrospective crew might want `recency_weight=0.5` and `recency_half_life_days=7`, while an architecture knowledge base would favor `importance_weight=0.4` and a 180-day half-life.

That trade-off matters. Heavy recency weighting is simpler to reason about -- recent stuff always wins -- but it means older critical decisions can silently drop out of recall results as time passes. Bumping importance weight gives you more durable recall of key facts, but it depends on the LLM correctly judging importance at save time. There's no free lunch.

## Scopes and Slices: Partitioning What Agents See

The scope system is where things get interesting. Memories are organized into a hierarchical tree that looks like a filesystem -- `/project/alpha`, `/agent/researcher`, `/company/engineering`. When you recall within a scope, you only search that subtree. This improves both precision and performance.

You can let the LLM auto-organize incoming memories into scopes, or you can be explicit. The docs recommend starting flat and letting structure emerge, which sounds nice but can get unpredictable if your agents are producing noisy output. For anything where isolation matters, I'd pass scope explicitly.

`MemoryScope` restricts an agent's view to a single subtree. `MemorySlice` lets you combine multiple branches -- for instance, giving a writer agent read access to both its own scope and a shared `/company/knowledge` branch. Slices default to read-only, which is the right call. You don't want a random agent polluting your shared knowledge base. If you need write access through a slice, you have to set `read_only=False` and specify which scope to write to.

## The Context Bleed Problem

Memory architecture is only half the story. The other half is how context flows between tasks in a crew. And this is where CrewAI has had real trouble.

The `_get_context()` method concatenates all prior task raw outputs verbatim. In a five-task sequential crew, later tasks can receive thousands of tokens of irrelevant prior output. Issue #4661 proposes an opt-in `context_strategy="summarized"` mode that would compress each task's output into a few sentences before passing it downstream. It's not merged yet, but the problem it describes is real and will bite anyone running crews with more than three or four sequential tasks.

Worse, the agent executor itself had a bug (issues #4319 and #4389, the latter filed against version 1.9.3) where reusing an agent across sequential tasks accumulated the message history instead of clearing it. Task 1 ends with 4 messages; Task 2 starts with 8; Task 3 starts with 12. Eventually you get `ValueError: Invalid response from LLM call - None or empty` because the LLM context is completely polluted with duplicate system prompts. The experimental `AgentExecutor` handles this correctly by resetting state at the start of each invocation -- the production executor didn't. A fix was proposed and reviewed, but the issue was auto-closed by a stale bot before being fully resolved.

There's also a subtler context loss bug with `async_execution=True` (issue #4822). Tasks running on background threads via `threading.Thread()` don't inherit `contextvars.Context` from the spawning thread, which means OpenTelemetry trace context, Langfuse session state, and any other `ContextVar`-based state silently resets to defaults. The fix is a one-line change -- `ctx = contextvars.copy_context()` before spawning the thread -- but the failure mode is completely silent, which makes it brutal to debug. Interestingly, CrewAI's own `remember_many()` implementation gets this right: it uses `contextvars.copy_context()` when submitting to its background save pool.

## Consolidation and Dedup

One thing the unified memory does well is avoiding duplicate records. The encoding pipeline checks incoming content against existing records, and if cosine similarity exceeds the `consolidation_threshold` (default 0.85), the LLM decides whether to keep, update, delete, or insert separately. For batch saves via `remember_many()`, there's an additional intra-batch dedup step that drops near-exact duplicates at a 0.98 cosine threshold without any LLM call -- pure vector math. So if your crew extracts three slightly different phrasings of the same fact from a task output, only one gets stored.

Background saves are non-blocking. `remember_many()` submits to a single-threaded pool and returns immediately. But every `recall()` call hits a read barrier -- `drain_writes()` -- ensuring you never query stale data. And when a crew finishes, `kickoff()` drains pending saves in a `finally` block so nothing is lost.

## Practical Advice

If you're adopting CrewAI's memory, keep a few things in mind. Use `depth="shallow"` for routine agent context retrieval. The deep recall mode runs a multi-step `RecallFlow` with LLM query analysis, parallel multi-scope search, and confidence-based iterative deepening -- powerful, but slow. Queries under 200 characters skip LLM analysis automatically, even in deep mode, which is a sensible optimization.

Watch your context window budget. The memory system itself is well-designed, but the inter-task context concatenation can overwhelm it. Until a summarization strategy lands in the framework, consider breaking long pipelines into smaller crews or manually managing what context each task receives.

And test your scope design early. The LLM-inferred scope placement is convenient but can produce inconsistent hierarchies if your content varies a lot. Explicit scopes are more work up front but give you predictable isolation between agents and crews. The community has noticed this gap too -- projects like `crewai-soul` store memories in human-readable markdown files precisely because the default memory store feels like a black box when you need to debug what an agent actually remembers.

The unified memory architecture is a genuine improvement over the old four-way split. But memory is only as useful as the context management around it, and that's where CrewAI still has sharp edges to sand down.
