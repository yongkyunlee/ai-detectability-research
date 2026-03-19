# Memory and Context Management in CrewAI

Multi-agent orchestration frameworks face a fundamental challenge: how do you give autonomous agents the ability to remember what matters without drowning them in irrelevant history? CrewAI's answer has evolved significantly. The framework recently overhauled its memory system, moving from a fragmented collection of specialized stores to a single unified `Memory` class that leans on LLM inference to handle the organizational burden. This shift has real implications for how developers build and tune their agent crews.

## From Four Memory Types to One

Earlier versions of CrewAI separated memory into distinct buckets—short-term, long-term, entity, and user memory—each with its own storage mechanism and retrieval logic. In practice, developers had to reason about which memory type held what information and manually route data between them. The current architecture collapses all of these into a single `Memory` class built around the concept of a `MemoryRecord`.

Each record carries a text payload, an embedding vector, an importance score, categorical tags, a hierarchical scope path, timestamps, and optional source attribution. Rather than forcing developers to decide where information belongs at write time, the system can use an LLM to infer scope placement, assign categories, and estimate importance automatically. You can still set these values explicitly when you know exactly where something should live—but the framework no longer punishes you for not knowing.

This design choice trades away the conceptual clarity of named memory types for a more flexible, schema-free approach. Whether that trade-off works for a given project depends on how much structure the developer wants to impose upfront versus how much they trust the LLM's organizational judgment.

## Hierarchical Scopes: Organizing Without Over-Engineering

The scope system gives memory a tree-like structure. A scope path like `/project/alpha/decisions` lets agents write memories to specific branches and query across subtrees. When an agent stores a finding under `/agent/researcher`, other agents searching the root scope can still discover it, but an agent with a scoped view restricted to `/agent/writer` won't see it unless explicitly granted access.

This becomes particularly useful in multi-crew or multi-user scenarios. Customer support agents can write to per-customer scopes like `/customer/acme-corp`, ensuring that one customer's preferences don't leak into another's context. Project-specific decisions stay isolated from unrelated work. The framework also supports memory slices—views that span multiple disjoint scopes with configurable read/write permissions—allowing an agent to read from shared knowledge bases while writing only to its own namespace.

The documentation recommends starting flat and letting the LLM organize memories into scopes organically, adding explicit structure only when retrieval quality demands it. Keeping scope depth to two or three levels avoids sparsity problems where too many narrowly defined branches each contain too few records for meaningful semantic search.

## The Recall Pipeline: Balancing Speed and Intelligence

Memory retrieval operates in two modes. Shallow recall performs a direct vector similarity search against the stored embeddings, applies composite scoring, and returns results—typically completing in a couple hundred milliseconds with no LLM involvement. Deep recall adds an intelligence layer: the LLM analyzes the query, decomposes it into targeted sub-queries, selects which scopes to search, and can iteratively explore additional branches if initial results fall below a confidence threshold.

The composite scoring formula blends three signals: semantic similarity from the vector search, a recency decay function, and the record's importance score. Each signal carries a configurable weight, and the recency component uses an exponential half-life model. A memory with a 30-day half-life retains half its recency score after a month and a quarter after two months. This means that for a sprint retrospective agent, you might crank recency weight to 0.5 with a 7-day half-life, while an architecture knowledge base would favor importance at 0.4 with a 180-day half-life.

An interesting optimization sits at the boundary between shallow and deep recall: queries shorter than 200 characters skip LLM analysis entirely, even when deep recall is requested. The reasoning is that short queries are already effective search phrases, and the latency cost of an LLM roundtrip (one to three seconds) outweighs the marginal improvement in retrieval quality. This threshold is configurable, but the default reflects a practical observation about when query decomposition actually helps.

## Deduplication and Consolidation

Any system where agents continuously write memories will accumulate redundant information over time. CrewAI addresses this with two deduplication mechanisms. On individual saves, the system performs a vector search for similar existing records. If any match exceeds a configurable similarity threshold (defaulting to 0.85), an LLM evaluates whether to keep the existing record, update it with new information, replace it entirely, or insert the new record alongside it.

For batch operations using `remember_many()`, a faster approach applies: a cosine similarity matrix identifies near-duplicates above a 0.98 threshold and silently drops them without involving the LLM. This keeps batch ingestion fast while preventing obvious redundancies.

The 0.85 consolidation threshold represents a deliberate balance. Setting it lower would aggressively merge records that might actually represent distinct but related concepts. Setting it higher would let duplicates accumulate, eventually degrading retrieval quality as the same information occupies multiple slots in search results. In practice, tuning this value requires understanding the semantic granularity of the domain—technical documentation with many similar-but-distinct concepts may need a higher threshold than a general knowledge base.

## Background Saves and the Read Barrier

Save operations can run asynchronously in a background thread, allowing agents to continue working without waiting for embedding computation and storage writes to complete. This is particularly valuable during batch ingestion or when agents are producing findings at a high rate.

The system implements a read barrier: any recall operation automatically drains pending writes before executing the search. This ensures that agents never miss information they've recently stored, even if the background save hasn't finished. The crew's `kickoff()` method also drains writes in its cleanup phase, preventing data loss if the process shuts down while saves are still queued.

This architecture accepts a trade-off: save failures are communicated through events rather than exceptions, since the calling code has already moved on by the time a background save might fail. Developers who need guaranteed persistence should monitor memory events or use synchronous `remember()` calls for critical information.

## Embedder Flexibility and Local-First Options

The memory system supports a wide range of embedding providers—OpenAI, Ollama, Cohere, Google, Voyage AI, Hugging Face sentence-transformers, and others—as well as fully custom embedding functions. This matters for teams with data sovereignty requirements or cost constraints. A fully local configuration using Ollama for both the LLM and embeddings can operate without any external API calls, keeping all memory data on-premises.

One technical constraint worth noting: LanceDB, the default vector store, fixes the embedding dimension per table based on the first record saved. Switching embedding models after data has been stored requires resetting the memory and re-encoding all records. This isn't unique to CrewAI—it's inherent to how columnar vector databases handle schema—but it's easy to overlook during development when experimenting with different providers.

## Context Window Challenges

Beyond memory, CrewAI faces the broader challenge of managing context windows across multi-task crews. Currently, all prior task outputs are concatenated verbatim into subsequent tasks' context. For crews with five or more sequential tasks, this can push against model context limits, particularly when early tasks produce lengthy outputs that later tasks don't need in full.

A proposed improvement would add an opt-in summarization strategy: after each task completes, a lightweight LLM call compresses its output into a concise summary. Downstream tasks would receive these summaries instead of raw outputs, dramatically reducing context consumption. This feature remains in discussion, and its absence means that developers working with long chains of tasks need to be intentional about output length or implement their own context management.

The framework's context limit detection also has known gaps. While it recognizes common OpenAI error patterns, some providers' error formats—notably certain Anthropic messages—aren't matched, potentially causing confusing failures instead of graceful handling.

## Transparency and Community Alternatives

A recurring theme in community discussions is the desire for more transparency in how memory operates. The default vector database storage can feel opaque compared to approaches where memory is stored as human-readable files. Community projects like crewai-soul take a different approach entirely, storing memories as markdown files that can be version-controlled with git and inspected without specialized tooling. These alternatives sacrifice some of the automated intelligence—LLM-inferred scoping, composite scoring, background consolidation—in favor of debuggability and developer control.

Another community-driven concern involves preference persistence. Users report that agents sometimes need to be corrected multiple times across sessions before a preference sticks. Tools like pref0 address this by extracting structured preferences from corrections and maintaining confidence scores that decay over time, creating a more robust preference learning loop than raw memory storage alone.

## Practical Guidance

For teams adopting CrewAI's memory system, a few patterns emerge from the documentation and community experience. Start with default settings and tune the scoring weights only after observing retrieval quality in your specific domain. Use explicit scopes for clear organizational boundaries (per-customer, per-project) but let the LLM handle finer-grained categorization. Monitor memory events to catch silent failures in background saves. And if your crew chains more than a handful of tasks, watch for context window pressure—consider breaking long pipelines into shorter crews that communicate through memory rather than direct context passing.

The unified memory system represents a genuine step forward in making agent memory practical rather than theoretical. Its main limitation is the same one facing all LLM-dependent systems: the quality of automatic organization depends on the quality of the underlying model, and that quality isn't always predictable. Teams that need deterministic behavior should use explicit scopes and categories; teams comfortable with some inference-driven uncertainty will benefit from the reduced boilerplate.
