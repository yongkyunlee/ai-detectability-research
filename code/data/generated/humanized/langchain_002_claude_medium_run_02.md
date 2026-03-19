# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-Augmented Generation has become one of the most popular patterns for grounding LLM outputs in real, domain-specific data. Instead of trusting the model's built-in knowledge alone, a RAG system pulls relevant documents at query time and stuffs them into the prompt as context. LangChain gives you a layered set of abstractions for building these pipelines, organized around two main primitives: vector stores and retrievers. Getting a handle on how they connect (and where things get messy) matters if you're building anything beyond a toy demo.

## The Two-Layer Architecture

LangChain makes a deliberate split between storage and retrieval. A `VectorStore` handles embedding, indexing, and searching documents. A `BaseRetriever` is more general: you give it a text query, it gives you back relevant documents. It doesn't need to know about embeddings at all. It might wrap a vector store, or it could just as easily query a SQL database, a search API, or a static list.

Why does this matter? The `VectorStore` abstract class defines methods like `similarity_search`, `similarity_search_with_relevance_scores`, and `max_marginal_relevance_search`. These all operate directly on embeddings and return `Document` objects. The `BaseRetriever`, by contrast, follows LangChain's `Runnable` protocol. You call `invoke` with a string; you get back a list of documents. Because of this, retrievers compose naturally with other runnables (prompt templates, language models, output parsers) using the same chaining syntax.

The bridge between the two layers is `as_retriever()`. Any vector store can produce a `VectorStoreRetriever` by calling this method, which wraps the store's search logic behind the retriever interface. You configure the search strategy at this boundary: similarity, maximal marginal relevance, or similarity with a score threshold.

## Search Strategies and Their Trade-offs

Plain cosine similarity is the default. It returns the `k` nearest neighbors to the query embedding. Works great when your corpus is varied enough that the top results don't overlap too much. But if your dataset has lots of near-duplicate passages (common in technical docs, legal filings, or scraped web content), straight similarity search will hand you back redundant results that eat up your context window for no good reason.

Maximal marginal relevance (MMR) tackles this by balancing relevance against diversity. It first grabs a larger candidate set (`fetch_k` documents), then iteratively picks results that are close to the query but far from each other. The `lambda_mult` parameter controls the trade-off: values near 1.0 favor relevance, values near 0.0 push for diversity. I've found that starting with `lambda_mult=0.5` and `fetch_k` set to three to five times your target `k` gives a reasonable baseline.

Then there's similarity with a score threshold. Instead of always returning `k` documents, it drops anything below a specified relevance score. This is especially useful in production, where injecting low-quality context can actually make the model's output worse than having no context at all. Honestly, this tripped me up early on; I assumed more context was always better.

## Metadata Filtering and Document Management

Vector stores in LangChain support metadata alongside the embedded text. Each document carries a dictionary of arbitrary key-value pairs (source file names, timestamps, categories, access levels) that you can use for filtering at query time. The exact filtering mechanism depends on the backend, but the pattern stays the same: pass a `filter` parameter through `search_kwargs` when configuring the retriever.

This matters a lot for multi-tenant apps and access-controlled corpora. If your vector store holds documents from multiple departments, you can scope retrieval to just one department without maintaining separate indices. The `InMemoryVectorStore` in LangChain's core library accepts filter functions directly, so it's easy to prototype filtering logic before moving to a hosted backend.

Document lifecycle (adding, updating, deleting entries) goes through `add_documents` and `delete` on the vector store. These use stable document IDs, so you can build incremental indexing pipelines that only re-embed changed content instead of rebuilding everything from scratch.

## Common Pitfalls in Practice

A few issues come up again and again in real-world RAG deployments built on these abstractions.

One that catches a lot of people: in-memory state persistence. Some vector store backends, Chroma being a notable example when used without explicit collection management, silently reuse shared memory across what look like independent instances within a single Python process. If you're creating ephemeral vector stores in a loop (say, for per-query document retrieval), the second iteration may contain documents from the first. Not great. The fix is either explicitly resetting the backing store between iterations or using unique collection names.

Async support needs some attention too. `BaseRetriever` gives you both `invoke` and `ainvoke`, but the async path just runs the synchronous implementation in a thread executor unless the concrete retriever overrides `_aget_relevant_documents`. For high-throughput apps, check whether your vector store integration provides native async methods and prefer those.

Relevance score normalization across backends is another thing the docs don't make obvious. LangChain normalizes scores to a 0-to-1 range through backend-specific functions; cosine distance, Euclidean distance, and inner product each map differently. Switch backends, and your score thresholds may need recalibration. The framework warns you if scores fall outside the expected range, but it can't automatically correct for different embedding scales or distance metrics.

## Beyond Simple Retrieval

The retriever abstraction supports composition patterns that go well past basic vector search. Contextual compression retrievers wrap an inner retriever and use a secondary model to extract or summarize only the relevant portions of each document, cutting noise in the context window. Multi-query retrievers generate several reformulations of the original question and merge their results, which helps with recall on ambiguous queries.

On the security side, retrieved documents can contain adversarial content designed to manipulate the language model (a class of attacks called indirect prompt injection). Defensive measures include scanning retrieved chunks before they enter the prompt, using XML delimiters to separate context from instructions, and validating outputs for signs of injection compliance. These concerns aren't specific to LangChain, but the retriever boundary is the natural place to insert that kind of filtering.

## Choosing the Right Configuration

For a first prototype, keep it simple. One vector store, default similarity search, a fixed `k` of four or five. Inspect which documents come back for representative queries before you touch any knobs. Once your retrieval baseline looks solid, try MMR for diversity, score thresholds for precision, and metadata filters for scoping.

The gap between a working demo and something you'd actually trust in production usually comes down to these details: picking the right search strategy for your data distribution, managing document freshness and deduplication, handling async execution correctly, and validating what enters the model's context window. LangChain's retriever and vector store abstractions give you clean interfaces for each of these concerns. The engineering judgment about how to configure and compose them, though, is still on you.
