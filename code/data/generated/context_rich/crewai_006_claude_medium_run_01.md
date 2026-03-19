# Memory and Context Management in CrewAI

Multi-agent orchestration frameworks face a fundamental tension: agents need enough shared context to collaborate effectively, but too much context degrades performance and inflates costs. CrewAI's approach to this problem has evolved significantly, culminating in a unified memory system that replaces what was once a fragmented collection of short-term, long-term, entity, and external memory stores.

## The Unified Memory Architecture

At the core of CrewAI's current design sits a single `Memory` class that consolidates all memory operations behind one API. Rather than forcing developers to reason about which type of memory to use for a given piece of information, the system relies on an LLM to analyze content at write time and determine where it belongs. When you call `remember()` without specifying organizational details, the LLM examines the content and the existing memory structure, then decides on scope placement, category assignment, and an importance score between zero and one.

This LLM-in-the-loop design carries a real cost. Every save without explicit metadata triggers an inference call, adding latency and spend. The framework mitigates this through lazy initialization, so the LLM is only instantiated when actually needed, and through graceful degradation: if the analysis call fails, the memory still gets stored under a default root scope with a neutral importance score. Nothing is dropped. The system also supports fully local operation using models served through Ollama, which matters for teams with compliance constraints around data leaving their infrastructure.

## Hierarchical Scopes and Controlled Visibility

Memories are organized into a tree of scopes resembling a filesystem. A scope like `/project/alpha/architecture` provides a natural boundary for retrieval. When an agent recalls within a scope, the search is restricted to that subtree, which improves both precision and query speed over searching the entire memory store.

The scoping system enables several useful access patterns. Individual agents can receive a `MemoryScope` that confines their reads and writes to a private subtree, preventing one agent's intermediate findings from polluting another's context. For cases where an agent needs cross-cutting access, a `MemorySlice` provides a read-only view across multiple disjoint scopes. A writer agent, for example, might read from both its own scope and a shared knowledge base without having write access to the shared data.

This design directly addresses a longstanding request from the CrewAI community: sharing memory across separate crew instances. Earlier versions had no clean mechanism for this. The current unified memory, backed by LanceDB on disk, can be pointed at the same storage directory by multiple crews, and the scoping system provides the isolation boundaries that prevent unintended interference.

## Composite Scoring and Adaptive Recall

Retrieval goes beyond simple vector similarity. Each recalled result receives a composite score blending three weighted signals: semantic similarity from the embedding search, a recency factor that decays exponentially with a configurable half-life, and the importance score assigned at write time. The default weights favor semantic relevance at 0.5, with recency at 0.3 and importance at 0.2, but these are tunable per use case. A sprint retrospective might crank up recency weight with a seven-day half-life, while an architecture knowledge base might favor importance with a half-life measured in months.

The recall system operates at two depths. Shallow recall performs a direct vector search with composite scoring and returns in roughly 200 milliseconds. Deep recall, the default, runs a multi-step flow: the LLM distills the query into targeted sub-queries, selects candidate scopes, searches in parallel across those scopes, and routes results through a confidence threshold. If confidence falls below a configurable floor, the system spends an exploration budget on additional LLM-driven rounds of context extraction. Short queries skip the LLM distillation step entirely, since a question like "What database did we choose?" is already a good search phrase.

## The Context Accumulation Problem

Memory is only half of the context management story. The other half involves how context flows between tasks during execution. This is where CrewAI has faced its most persistent practical challenges.

When a crew executes tasks sequentially, prior task outputs are concatenated and injected as context for downstream tasks. In a five-task crew, the final task can receive thousands of tokens of unfiltered prior output. Community members have reported context window overflows and degraded output quality from this approach, and a feature request for opt-in context summarization has been proposed to compress inter-task context through a small LLM call after each task completes.

A separate and more insidious problem involves the agent executor's message history. When the same agent is reused across multiple tasks, the executor accumulates messages from all prior executions. System prompts duplicate, user messages stack up, and the LLM eventually receives a confused context that leads to empty or invalid responses. This bug has been documented repeatedly in the issue tracker. The experimental agent executor handles this correctly by resetting state at the start of each invocation, but the production executor required explicit patching.

Threading introduces another dimension of complexity. Tasks with asynchronous execution spawn worker threads that do not inherit context variables from the calling thread. This silently breaks observability tools like OpenTelemetry and tracing SDKs that rely on context propagation. The unified memory system itself handles threading more carefully, using `contextvars.copy_context()` in its background save pool and serializing writes through a single-threaded executor to prevent race conditions against LanceDB.

## Consolidation and Deduplication

As agents generate memories over time, duplication becomes inevitable. The encoding pipeline addresses this at two levels. Within a single batch, items are compared against each other using cosine similarity, and near-exact duplicates are dropped before they ever reach storage. Across batches, newly written content is compared against existing records, and when similarity exceeds a configurable threshold, the LLM decides whether to keep, update, merge, or delete the existing record.

This consolidation logic runs as part of a five-step encoding flow: batch embedding, intra-batch deduplication, parallel similarity search against storage, parallel LLM analysis for field resolution and consolidation decisions, and finally a bulk write. The parallelism is deliberate. Up to eight concurrent storage searches and ten concurrent LLM calls can run simultaneously, keeping the pipeline fast even for large batches.

## Looking Ahead

The community around CrewAI continues to push on memory from multiple directions. Third-party projects like crewai-soul offer markdown-based alternatives for developers who want human-readable, git-versionable memory stores. External preference learning services aim to capture the structured behavioral preferences that raw memory logs miss. These efforts reflect a broader recognition that memory in multi-agent systems is not a solved problem but an active design space where the right abstraction depends heavily on the deployment context.
