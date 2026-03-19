# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-Augmented Generation has become one of the most widely adopted patterns for grounding large language model outputs in factual, domain-specific data. Rather than relying solely on a model's parametric knowledge, a RAG system fetches relevant documents at query time and feeds them into the prompt as context. LangChain provides a layered abstraction for building these pipelines, centered on two core primitives: vector stores and retrievers. Understanding how these pieces fit together — and where the seams show — is essential for anyone building production RAG systems today.

## The Two-Layer Architecture

LangChain draws a deliberate line between storage and retrieval. A `VectorStore` handles the mechanics of embedding, indexing, and searching documents. A `BaseRetriever` is a more general interface: given a text query, return a list of relevant documents. The retriever does not need to know anything about embeddings or vectors. It might wrap a vector store, but it could just as easily query a SQL database, a search API, or a static list.

This separation matters in practice. The `VectorStore` abstract class defines methods like `similarity_search`, `similarity_search_with_relevance_scores`, and `max_marginal_relevance_search`. Each of these operates directly on embeddings and returns `Document` objects. The `BaseRetriever`, by contrast, conforms to LangChain's `Runnable` protocol. You call `invoke` with a string and get back a list of documents. This means retrievers compose naturally with other runnables — prompt templates, language models, output parsers — using the same chaining syntax.

The bridge between these two layers is `as_retriever()`. Any vector store can produce a `VectorStoreRetriever` by calling this method, which wraps the store's search functionality behind the retriever interface. You configure the search strategy at this boundary: similarity, maximal marginal relevance, or similarity with a score threshold.

## Search Strategies and Their Trade-offs

The default search type is plain cosine similarity, which returns the `k` nearest neighbors to the query embedding. This works well when your corpus is diverse enough that the top results are naturally varied. But when your dataset contains many near-duplicate passages — common with technical documentation, legal filings, or scraped web content — straight similarity search can return redundant results that waste your context window.

Maximal marginal relevance (MMR) addresses this by balancing relevance against diversity. It first fetches a larger candidate set (`fetch_k` documents), then iteratively selects results that are similar to the query but dissimilar to each other. The `lambda_mult` parameter controls this trade-off: values near 1.0 favor relevance, while values near 0.0 maximize diversity. In practice, starting with `lambda_mult=0.5` and `fetch_k` of three to five times your target `k` gives a reasonable baseline.

The third option, similarity with a score threshold, is useful when you want to avoid returning irrelevant results entirely. Rather than always returning `k` documents, it filters out anything below a specified relevance score. This is particularly valuable in production systems where injecting low-quality context can degrade the model's output more than having no context at all.

## Metadata Filtering and Document Management

Vector stores in LangChain support metadata alongside the embedded text. Each document carries a dictionary of arbitrary key-value pairs — source file names, timestamps, categories, access levels — that can be used for filtering at query time. The filtering mechanism varies by backend, but the pattern is consistent: you pass a `filter` parameter through `search_kwargs` when configuring the retriever.

This filtering capability is critical for multi-tenant applications and access-controlled corpora. If your vector store contains documents from multiple departments, you can scope retrieval to a specific department without maintaining separate indices. The `InMemoryVectorStore` included in LangChain's core library accepts filter functions directly, making it straightforward to prototype filtering logic before migrating to a hosted backend.

Document lifecycle management — adding, updating, and deleting entries — flows through the `add_documents` and `delete` methods on the vector store. These operations use stable document IDs, which means you can implement incremental indexing pipelines that only re-embed changed content rather than rebuilding the entire index.

## Common Pitfalls in Practice

Several recurring issues surface in real-world RAG deployments built on these abstractions. One that catches many developers involves in-memory state persistence. Some vector store backends, notably Chroma when used without explicit collection management, silently reuse shared memory across what appear to be independent instances within a single Python process. If you are creating ephemeral vector stores in a loop — say, for per-query document retrieval — the second iteration may contain documents from the first. The fix is to either explicitly reset the backing store between iterations or use unique collection names.

Async support is another area that requires care. While `BaseRetriever` provides both `invoke` and `ainvoke` entry points, the async path falls back to running the synchronous implementation in a thread executor unless the concrete retriever overrides `_aget_relevant_documents`. For high-throughput applications, check whether your chosen vector store integration provides native async methods, and prefer those when available.

The relevance score normalization across different backends also deserves attention. LangChain normalizes scores to a 0-to-1 range through backend-specific functions — cosine distance, Euclidean distance, and inner product each have different mappings. If you switch vector store backends, your score thresholds may need recalibration. The framework will warn you if scores fall outside the expected range, but it cannot automatically correct for different embedding scales or distance metrics.

## Beyond Simple Retrieval

The retriever abstraction supports composition patterns that go well beyond basic vector search. Contextual compression retrievers wrap an inner retriever and use a secondary model to extract or summarize only the portions of each document that are relevant to the query, reducing noise in the context window. Multi-query retrievers generate several reformulations of the original question and merge their results, improving recall for ambiguous queries.

For production systems, security considerations are becoming increasingly important. Retrieved documents can contain adversarial content designed to manipulate the language model — a class of attacks known as indirect prompt injection. Defensive measures include scanning retrieved chunks before they enter the prompt, using XML delimiters to separate context from instructions, and validating outputs for signs of injection compliance. These concerns are independent of LangChain itself, but the retriever boundary is the natural place to insert such filtering.

## Choosing the Right Configuration

For a first RAG prototype, start with the simplest possible configuration: a single vector store, default similarity search, and a fixed `k` of four or five. Measure retrieval quality by inspecting which documents are returned for representative queries before tuning anything else. Once the retrieval baseline is solid, experiment with MMR for diversity, score thresholds for precision, and metadata filters for scoping.

The gap between a working demo and a reliable production system often comes down to these details: understanding which search strategy fits your data distribution, managing document freshness and deduplication, handling the async execution model correctly, and validating what enters the model's context window. LangChain's retriever and vector store abstractions provide clean interfaces for each of these concerns, but the engineering judgment about how to configure and compose them remains firmly with the developer.
