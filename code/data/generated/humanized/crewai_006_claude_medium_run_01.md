# Memory and Context Management in CrewAI

Multi-agent frameworks have a hard problem on their hands: agents need shared context to work together, but too much of it kills performance and runs up your bill. CrewAI's answer has changed a lot over time. What used to be a scattered set of short-term, long-term, entity, and external memory stores is now a single unified memory system.

## The Unified Memory Architecture

CrewAI's current design centers on one `Memory` class that wraps all memory operations behind a single API. Instead of making developers figure out which memory type fits a given piece of information, the system hands that decision to an LLM. When you call `remember()` without specifying organizational details, the LLM looks at the content and the existing memory structure, then picks the scope placement, category, and an importance score between zero and one.

There's a real cost to this LLM-in-the-loop design, though. Every save without explicit metadata triggers an inference call. More latency, more spend. The framework tries to soften this with lazy initialization (the LLM only spins up when actually needed) and graceful degradation: if the analysis call fails, the memory still gets stored under a default root scope with a neutral importance score. Nothing gets dropped. You can also run the whole thing locally using Ollama-served models, which I think matters a lot for teams dealing with compliance rules about data leaving their infrastructure.

## Hierarchical Scopes and Controlled Visibility

Memories live in a tree of scopes that looks a lot like a filesystem. A scope like `/project/alpha/architecture` creates a natural retrieval boundary. When an agent recalls within a scope, the search stays inside that subtree. Better precision, faster queries.

The scoping system opens up some useful access patterns. Give an agent a `MemoryScope` and its reads and writes stay confined to a private subtree, so one agent's intermediate findings don't pollute another's context. Need cross-cutting access? A `MemorySlice` gives a read-only view across multiple disjoint scopes. A writer agent could read from both its own scope and a shared knowledge base without being able to write to the shared data.

This directly addresses something the CrewAI community asked for repeatedly: sharing memory across separate crew instances. Earlier versions had no clean way to do it. Now the unified memory, backed by LanceDB on disk, can point at the same storage directory from multiple crews, and the scoping system keeps them from stepping on each other.

## Composite Scoring and Adaptive Recall

Retrieval isn't just vector similarity. Each recalled result gets a composite score from three weighted signals: semantic similarity from the embedding search, a recency factor that decays exponentially with a configurable half-life, and the importance score assigned at write time. Defaults are 0.5 for semantic relevance, 0.3 for recency, 0.2 for importance. All tunable. A sprint retro might crank recency weight with a seven-day half-life; an architecture knowledge base might favor importance with a half-life measured in months.

Two depths of recall exist here. Shallow recall does a direct vector search with composite scoring and returns in roughly 200 milliseconds. Deep recall (the default) is more involved: the LLM distills the query into targeted sub-queries, selects candidate scopes, searches them in parallel, then routes results through a confidence threshold. If confidence drops below a configurable floor, the system spends an exploration budget on extra LLM-driven rounds of context extraction. Short queries skip the distillation step entirely, since something like "What database did we choose?" is already a perfectly good search phrase.

## The Context Accumulation Problem

Memory is only half the story. The other half is how context flows between tasks during execution, and honestly, this is where things get messy.

When a crew runs tasks sequentially, prior task outputs get concatenated and injected as context for downstream tasks. In a five-task crew, the final task can receive thousands of tokens of unfiltered prior output. Community members have reported context window overflows and degraded quality from this, and there's a feature request out for opt-in context summarization that would compress inter-task context through a small LLM call after each task completes.

A separate (and sneakier) problem involves the agent executor's message history. When the same agent handles multiple tasks, the executor accumulates messages from all prior executions. System prompts duplicate, user messages stack up, and eventually the LLM gets a confused context that leads to empty or invalid responses. This bug shows up repeatedly in the issue tracker. The experimental agent executor handles it correctly by resetting state at the start of each invocation, but the production executor needed explicit patching.

Threading adds yet another wrinkle. Tasks with asynchronous execution spawn worker threads that don't inherit context variables from the calling thread. This silently breaks observability tools like OpenTelemetry and tracing SDKs that rely on context propagation. The unified memory system itself is more careful here, using `contextvars.copy_context()` in its background save pool and serializing writes through a single-threaded executor to prevent race conditions against LanceDB.

## Consolidation and Deduplication

Over time, agents will inevitably generate duplicate memories. The encoding pipeline deals with this at two levels. Within a single batch, items are compared using cosine similarity and near-exact duplicates are dropped before they ever reach storage. Across batches, newly written content is compared against existing records; when similarity exceeds a configurable threshold, the LLM decides whether to keep, update, merge, or delete the existing record.

This consolidation logic is part of a five-step encoding flow: batch embedding, intra-batch deduplication, parallel similarity search against storage, parallel LLM analysis for field resolution and consolidation decisions, then a bulk write. The parallelism is deliberate. Up to eight concurrent storage searches and ten concurrent LLM calls can run at once, keeping the pipeline fast even for large batches.

## Looking Ahead

The community keeps pushing on memory from multiple angles. Third-party projects like crewai-soul offer markdown-based alternatives for developers who want human-readable, git-versionable memory stores. External preference learning services try to capture structured behavioral preferences that raw memory logs miss. From what I can tell, the broader takeaway is that memory in multi-agent systems isn't solved. It's an active design space, and the right abstraction depends heavily on where and how you're deploying.
