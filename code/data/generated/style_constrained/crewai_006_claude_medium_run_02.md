# Memory and Context Management in CrewAI

Stateless agents are easy to build. Stateful agents are useful. That gap is where most multi-agent frameworks quietly fall apart, and it's where CrewAI's unified memory system tries to do something genuinely interesting.

## The Problem With Forgetting

If you've run a multi-step crew and noticed the third agent re-asking a question the first agent already answered, you've felt this problem directly. Context evaporates between tasks. Agents repeat work. Token bills climb because the system re-summarizes the same five paragraphs ten times over. Community threads on Reddit are full of engineers who've spent entire weekends watching agents loop on stale context — one user described burning through $15 before producing a single usable output file, mostly because agents kept rehashing information they should have retained.

The core issue isn't prompting. It's plumbing. Without persistent, structured memory, each agent in a crew operates with the recall capacity of a goldfish that has access to an expensive API.

## How CrewAI's Unified Memory Works

CrewAI v1.11.0 ships a single `Memory` class that replaced the earlier patchwork of short-term, long-term, entity, and external memory types. The API is small: `remember()`, `recall()`, `forget()`, and `extract_memories()`. Under the hood, an LLM analyzes content at save time to infer scope, categories, and importance. Retrieval uses a composite scoring formula that blends semantic similarity, recency decay, and importance weighting.

The scoring formula is explicit:

```
composite = semantic_weight * similarity + recency_weight * decay + importance_weight * importance
```

Defaults are 0.5 / 0.3 / 0.2 for semantic, recency, and importance respectively, with a 30-day recency half-life. These are tunable. A sprint retrospective might want `recency_weight=0.5` and `recency_half_life_days=7` so yesterday's decisions outrank last month's. An architecture knowledge base might flip to `importance_weight=0.4` and a 180-day half-life so foundational decisions don't fade.

That tuning flexibility matters. Most frameworks give you vector similarity and nothing else. CrewAI's three-signal approach is simpler than building your own ranking pipeline, but it still gives you meaningful knobs.

## Scopes: A Filesystem for Memory

Memories are organized into hierarchical paths — `/project/alpha`, `/agent/researcher`, `/company/engineering` — that work like a filesystem. You can let the LLM infer scope automatically, or pin it yourself with an explicit `scope=` parameter. A `MemoryScope` object restricts all operations to a subtree, so an agent scoped to `/agent/researcher` can't accidentally read or pollute the writer's context.

This matters for multi-agent isolation. The documentation recommends giving each agent a private scope while keeping shared knowledge in a common branch. An agent can also get a `MemorySlice` — a read-only view across multiple disjoint scopes — so a writer can pull from both its own private notes and shared company knowledge without being able to write to the shared branch.

The scope design is pragmatic. Start flat, let the LLM self-organize, and only impose structure where you need hard boundaries. That said, the docs wisely advise keeping depth shallow at two to three levels. Deeply nested scopes get sparse fast, and sparse scopes degrade search precision.

## Consolidation and Deduplication

One subtle but important feature: memory consolidation. On every save, the encoding pipeline checks existing records for semantic similarity above a configurable threshold (default 0.85). When it finds a near-match, the LLM decides whether to keep, update, merge, or delete the existing record. This prevents the kind of memory bloat where "we use PostgreSQL" gets stored forty times across a long-running crew.

Batch operations get their own deduplication layer. `remember_many()` compares items within the same batch using pure cosine similarity at a 0.98 threshold — no LLM call needed. Near-exact duplicates are silently dropped before they ever hit storage.

## The Storage Layer

LanceDB is the default backend, storing data under `.crewai/memory/` (or wherever `$CREWAI_STORAGE_DIR` points). The implementation handles concurrency with a shared lock and automatic retry on commit conflicts — up to 5 retries with exponential backoff. Background compaction runs periodically to merge fragment files. These are the kinds of operational details that separate a production storage layer from a demo.

The storage backend is also pluggable. CrewAI defines a `StorageBackend` protocol with methods like `save()`, `search()`, `delete()`, and `get_scope_info()`. You can swap in your own implementation if LanceDB doesn't fit your deployment model. This is a meaningful escape hatch. Some teams in the community have already explored alternatives — markdown-based storage for git-versionable memory, serverless backends on DynamoDB and pgvector for sub-10ms reads.

## Recall Depth: Shallow vs. Deep

Recall supports two modes. Shallow recall is a direct vector search with composite scoring — fast, around 200ms, no LLM calls. Deep recall (the default) runs a multi-step flow: query analysis, scope selection, parallel vector search, and confidence-based routing that can trigger additional exploration rounds when initial results aren't confident enough.

There's a smart optimization here. Queries shorter than 200 characters skip LLM analysis entirely, even in deep mode. Short questions like "What database did we choose?" are already good embedding targets — running them through an LLM for distillation adds latency without improving results. Only longer queries benefit from decomposition into sub-queries.

The trade-off is real: shallow recall is simpler and cheaper, but deep recall gives you better results on complex, multi-faceted queries. For routine agent context injection between tasks, shallow is probably sufficient. Reserve deep recall for the cases where an agent needs to synthesize information scattered across multiple scopes.

## Failure Modes and Practical Concerns

CrewAI's memory degrades gracefully when the LLM fails. If save analysis breaks, the memory still gets stored with defaults — root scope, no categories, importance 0.5. If query analysis fails, recall falls back to plain vector search. No exceptions are raised for analysis failures; only storage or embedder problems will actually throw.

And that default LLM? It's `gpt-4o-mini`. Every `remember()` call that doesn't specify explicit scope and categories makes an LLM call. For a crew that processes dozens of task outputs, those calls add up. You can point the memory LLM at a local model via Ollama (`llm="ollama/llama3.2"`) if you need to keep costs down or data private.

Saves are non-blocking by design. `remember_many()` submits work to a background thread and returns immediately. Every `recall()` call drains pending writes before searching, so you don't get stale results. When a crew finishes, `kickoff()` drains all pending saves in its `finally` block. These are the details that prevent subtle data-loss bugs in production.

## Where This Sits

CrewAI's memory system is opinionated in a useful way. It assumes you want LLM-assisted organization, hierarchical scoping, and automatic deduplication. That's a significant step up from raw vector stores or context-window stuffing. But it does put an LLM in your write path, which adds latency and cost that some teams find unacceptable at scale.

For crews that run a handful of tasks with moderate context, the built-in memory is solid and requires almost no configuration. For high-throughput production deployments, you'll want to tune the scoring weights, consider a local LLM for analysis, and possibly swap in a custom storage backend. The framework gives you room for both.
