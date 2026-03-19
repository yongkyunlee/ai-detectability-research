# Memory and Context Management in CrewAI

CrewAI's memory system has gone through a significant redesign. The old approach fragmented memory into separate short-term, long-term, entity, and external stores. The current unified `Memory` class replaces all of that with a single API that uses an LLM to analyze content at save time, inferring scope, categories, and importance automatically. It's a bold design choice. And it introduces trade-offs worth understanding before you wire it into a production crew.

## The Unified Memory API

The surface area is small. You call `memory.remember()` to store something, `memory.recall()` to retrieve it, and `memory.forget()` to drop a scope. Behind the scenes, the system runs an LLM on every save to decide where in a hierarchical scope tree to place the record, how important it is, and what categories it belongs to.

```python
from crewai import Memory

memory = Memory()
memory.remember("We decided to use PostgreSQL for the user database.")
matches = memory.recall("What database did we choose?")
```

That's it for basic usage. But the defaults hide a lot of machinery. The default LLM is `gpt-4o-mini`. The default storage backend is LanceDB, writing to `./.crewai/memory`. The default embedding provider is OpenAI's `text-embedding-3-small`. Every one of these is configurable, and you'll probably need to change at least one of them.

## How Context Flows Between Tasks

Memory is only half the context story. The other half is how CrewAI passes output between sequential tasks. Each task receives context from prior tasks through `_get_context()`, which calls `aggregate_raw_outputs_from_task_outputs()` in the formatter module. This concatenates all prior task raw outputs verbatim. In a five-task crew, task five's prompt can easily exceed 8,000 tokens of unfiltered prior output. A feature request (issue #4661, filed March 2026) proposes an opt-in `context_strategy="summarized"` parameter that would compress each task's output into a two-to-three sentence summary via a lightweight LLM call before handing it downstream. That hasn't landed yet. So if you're running long sequential pipelines, be aware that context grows linearly with each task.

Separately, memory-enabled crews extract discrete facts from task output after each step and store them. Before the next task, the agent recalls relevant context from memory and injects it alongside the raw context. This dual path - explicit task output forwarding plus memory-backed retrieval - is how CrewAI tries to give agents enough context without blowing the context window.

## Scopes: The Filesystem Metaphor

Memories are organized into a hierarchical tree that works like a filesystem. Paths look like `/project/alpha/decisions` or `/agent/researcher/findings`. When you recall within a scope, the search is restricted to that subtree. This improves both precision and performance.

The interesting part is automatic scope inference. If you call `remember()` without specifying a scope, the LLM examines the content and the existing scope tree, then picks the best placement. It can even create new scopes on the fly. Over time the tree grows organically. You don't design a schema upfront.

I think this is a reasonable default for prototyping. But I wouldn't rely on it in production without monitoring what the tree actually looks like. Automatic inference can produce inconsistent placements if the LLM's judgment drifts across invocations. The docs recommend starting flat and keeping depth to two or three levels - solid advice. A path like `/project/alpha/architecture` is fine; `/project/alpha/architecture/decisions/databases/postgresql` is too deep and will fragment your data.

`MemoryScope` lets you create restricted views for specific agents. A researcher agent can get `memory.scope("/agent/researcher")`, and it'll only see and write within that subtree. `MemorySlice` extends this to multiple disjoint scopes - useful when an agent needs read access to its own branch plus shared company knowledge, but shouldn't write to the shared branch.

## Composite Scoring and Recall Depth

Recall results aren't ranked by raw vector similarity alone. CrewAI uses a weighted composite score:

```
composite = semantic_weight * similarity + recency_weight * decay + importance_weight * importance
```

The defaults are 0.5 for semantic, 0.3 for recency, and 0.2 for importance, with a recency half-life of 30 days. You can tune these per use case. A sprint retrospective might want `recency_weight=0.5` and `recency_half_life_days=7`. An architecture knowledge base might favor `importance_weight=0.4` and a half-life of 180 days. The scoring formula is transparent and each `MemoryMatch` includes a `match_reasons` list explaining why it ranked where it did.

Recall supports two depths. Shallow does a straight vector search with composite scoring - fast, roughly 200ms, no LLM calls. Deep (the default) runs a multi-step RecallFlow: query analysis, scope selection, parallel vector search, confidence-based routing, and optional recursive exploration. Queries shorter than 200 characters skip the LLM analysis even in deep mode, since short queries are already effective search phrases. This saves one to three seconds per recall for typical short queries.

The trade-off here is clear. Shallow is simpler and cheaper, but deep gives you better results for complex queries at the cost of latency and LLM token spend. For routine agent context during sequential task execution, shallow is probably the right call. Reserve deep for cases where an agent genuinely needs to synthesize across a broad knowledge base.

## The Context Bleed Problem

We need to talk about a real bug pattern that has bitten people in production. When the same agent is reused across multiple sequential tasks, the `CrewAgentExecutor` doesn't always reset its internal message history between executions. Issue #4319 documented this clearly: after task one, the executor has 4 messages. After task two, it has 8. After task three, 12. System messages duplicate. The LLM sees three system prompts for the same task. Eventually this causes confused responses or outright crashes with `ValueError: Invalid response from LLM call - None or empty`.

Issue #4389, filed against version 1.9.3, confirmed the same root cause. The `invoke()` and `ainvoke()` methods on `CrewAgentExecutor` weren't resetting `self.messages` and `self.iterations` at the start of each execution. The experimental `AgentExecutor` at `crewai/experimental/agent_executor.py` already handled this correctly. The fix is two lines of code - `self.messages = []` and `self.iterations = 0` at the top of each invocation - but until it ships in the executor you're using, the workaround is to create new agent instances for each task, which defeats agent reuse.

This is the kind of context management failure that's invisible in demos and devastating in production. One community post nailed it: "memory injects bad context into later steps" was listed alongside tool failures and delegation drift as the real debugging challenges, not the ones you'd find by tweaking prompts.

## Memory Consolidation and Dedup

CrewAI has built-in deduplication at two levels. At save time, the encoding pipeline checks for similar existing records. If cosine similarity exceeds the `consolidation_threshold` (default 0.85), the LLM decides whether to keep, update, or delete the existing record and whether to insert the new one. This prevents the same fact from accumulating as duplicate entries across crew runs.

For batch operations, `remember_many()` performs intra-batch dedup purely with vector math - no LLM call. If two items within the same batch have cosine similarity at or above `batch_dedup_threshold` (default 0.98), the later one is silently dropped. So calling `remember_many()` with three items where the first and third are near-identical results in only two stored records.

`remember_many()` is also non-blocking. It submits the encoding pipeline to a background thread and returns immediately. The agent can continue to the next task while memories are being saved. Every `recall()` call runs `drain_writes()` first as a read barrier, so queries always see the latest persisted records. When a crew finishes, `kickoff()` drains all pending saves in its `finally` block.

## Knowledge vs. Memory

CrewAI separates two related-but-distinct concepts. Memory is what agents accumulate during execution - facts extracted from task outputs, decisions made along the way, intermediate findings. Knowledge is external reference material loaded before execution - PDFs, CSVs, text files, string content, even API data. Knowledge uses ChromaDB for vector storage (separate from memory's LanceDB backend), supports sources like `StringKnowledgeSource`, `PDFKnowledgeSource`, and custom sources, and can be scoped at either the crew or agent level.

The storage is independent. Agent knowledge goes into a collection named after the agent's role. Crew knowledge goes into a collection named `crew`. Both live under `~/.local/share/CrewAI/{project}/knowledge/` on Linux or the platform-appropriate equivalent.

One practical gotcha: knowledge sources are re-embedded every time `kickoff()` is triggered unless you directly initialize the `knowledge` parameter instead of `knowledge_sources`. For large sources, this adds significant latency on every run.

## Third-Party Alternatives and Community Sentiment

The community isn't unanimously sold on CrewAI's built-in memory. One developer built `crewai-soul`, a markdown-based memory alternative that stores agent identity and memories in readable `.md` files, version-controllable with git, no database required. The pitch was transparency: "you can read what your agent remembers." Another project, Mnemora, takes the opposite approach from CrewAI by keeping LLMs out of the CRUD path entirely - state reads hit DynamoDB at sub-10ms, and the LLM only runs at write time to generate embeddings.

And then there's pref0, which targets a specific gap: structured user preferences that persist across sessions. Its creator observed that "the average preference gets re-corrected 4+ times before people just give up." Neither raw conversation logs nor document retrieval solves this. CrewAI's memory system stores facts but doesn't model preference confidence or decay the way a purpose-built preference layer does.

## Practical Recommendations

If you're enabling memory on a crew, pass a configured `Memory` instance rather than just `memory=True`. Control the LLM, embedder, and scoring weights explicitly. Don't let defaults surprise you when the bill arrives or when recall quality degrades.

Watch for the context bleed bug if you're reusing agents across tasks. Check your CrewAI version and verify that message history resets between task executions. If it doesn't, create fresh agent instances per task as a workaround.

For long sequential pipelines, keep an eye on total context size. Raw task outputs accumulate in the prompt. Until context summarization ships as a first-class feature, you may need to manage this yourself - either through careful task design that produces concise outputs, or by explicitly using memory recall instead of relying on raw context forwarding.

And if privacy matters - and it should - remember that memory content is sent to the configured LLM for scope and importance analysis on every save. Use `ollama/llama3.2` for both the LLM and embedder if you need fully offline operation.

The unified memory system is a genuine step forward from the fragmented approach. But context management in multi-agent systems remains hard. The framework gives you the primitives. Making them work reliably is still your job.
