# Building RAG Pipelines with LangChain Retrievers and Vector Stores

RAG is deceptively simple on a whiteboard. You chunk some documents, embed them, store the vectors, and retrieve the relevant ones at query time. Then you stuff that context into a prompt and let the LLM do its thing. But the gap between that whiteboard sketch and a production system that doesn't hallucinate, doesn't miss obvious context, and doesn't silently fail is enormous. We've been building retrieval-augmented generation pipelines with LangChain for a while now, and I want to walk through the architecture that actually matters: the retriever and vector store abstractions, the search strategies you should care about, and the advanced patterns that solve real problems.

## The Two Core Abstractions

LangChain's retrieval stack is split across two abstract classes that live in `langchain_core`. Understanding the boundary between them saves you hours of confusion.

`VectorStore` is the storage layer. It's defined in `langchain_core/vectorstores/base.py` and handles embedding, indexing, and searching your documents. Every vector store implementation - Chroma, Qdrant, Pinecone, PgVector, the built-in `InMemoryVectorStore` - inherits from this class. The contract is straightforward: you must implement `similarity_search` and `from_texts`. Everything else has default implementations or raises `NotImplementedError` for you to override.

`BaseRetriever` is the query interface. It lives in `langchain_core/retrievers.py` and implements LangChain's `Runnable` protocol, which means it plugs directly into LCEL chains via `invoke` and `ainvoke`. A retriever doesn't need to store anything. It just takes a string query and returns a list of `Document` objects. So a retriever can wrap a vector store, but it can also wrap an API call, a SQL query, or a TF-IDF index.

The bridge between them is `VectorStoreRetriever`, and you create one by calling `as_retriever()` on any vector store instance. This is the pattern you'll use 90% of the time:

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 50}
)
docs = retriever.invoke("How does authentication work?")
```

That single method call gives you a fully compliant `Runnable` that you can compose into chains. And the `search_type` parameter is where things get interesting.

## Three Search Strategies That Matter

The `VectorStoreRetriever` accepts three values for `search_type`, and picking the right one is half the battle.

The default is `"similarity"` - plain cosine or euclidean nearest-neighbor search. It returns `k` documents (defaulting to 4) ranked by embedding distance. Simple, fast, predictable. But if your document corpus has clusters of near-duplicates, you'll get back five chunks that all say the same thing.

That's where `"mmr"` comes in. Maximal marginal relevance optimizes for both similarity to the query and diversity among results. It works in two phases: first it fetches `fetch_k` candidates (default 20), then it re-ranks them using a `lambda_mult` parameter that trades off relevance against diversity. A `lambda_mult` of 1.0 gives you pure similarity; 0.0 gives you maximum diversity. The default sits at 0.5. We've found that setting `fetch_k` to at least 4x your final `k` value produces noticeably better results, because the MMR algorithm needs a wide enough candidate pool to actually find diverse documents.

The third option is `"similarity_score_threshold"`, which filters results by a minimum relevance score between 0 and 1. This is useful when you'd rather return nothing than return garbage. If no documents meet the threshold, LangChain logs a warning: "No relevant docs were retrieved using the relevance score threshold." You must pass the threshold as a float in `search_kwargs`, or the validator will reject your configuration outright.

MMR is simpler to reason about than threshold-based filtering, but threshold gives you a hard quality floor. We default to MMR for general Q&A pipelines and switch to threshold-based search when the downstream task can't tolerate irrelevant context - like code generation or structured data extraction.

## The Parent-Child Retrieval Pattern

Here's a tension that shows up in every RAG system: small chunks embed more precisely, but large chunks carry more context. A 400-character chunk about a specific API method will match a targeted query beautifully, but when you hand that snippet to the LLM, it won't have enough surrounding context to generate a useful answer.

LangChain's `ParentDocumentRetriever` solves this directly. It uses two text splitters - a child splitter that produces small chunks for embedding (the example in the source uses `chunk_size=400`) and a parent splitter that produces larger chunks for retrieval (the example uses `chunk_size=2000`). During ingestion, child chunks get embedded and stored in the vector store, with each child tagged with the ID of its parent. At query time, the retriever searches over child chunks, collects the unique parent IDs from their metadata, and returns the full parent documents from a separate docstore.

This is built on top of `MultiVectorRetriever`, which handles the core mechanics: searching the vector store, extracting parent IDs from the `doc_id` metadata key, and calling `docstore.mget(ids)` to fetch the originals. The parent-child variant just adds the two-splitter ingestion logic on top.

The approach works well. But it requires maintaining two storage backends - a vector store for the child embeddings and a `BaseStore` (like `InMemoryStore`) for the parent documents. That's more operational surface. If your use case doesn't need fine-grained embedding precision, a simpler setup with `RecursiveCharacterTextSplitter` at a moderate chunk size and plain similarity search will get you surprisingly far with less infrastructure.

## Time-Weighted Retrieval for Memory Systems

Not all retrieval is about finding the most semantically similar document. Sometimes recency matters. The `TimeWeightedVectorStoreRetriever` combines embedding similarity with an exponential decay function. Its scoring formula is `(1.0 - decay_rate) ** hours_passed + vector_relevance`, where `decay_rate` defaults to 0.01. A document accessed an hour ago gets a strong recency boost; one from last week gets almost none.

This pattern emerged from agentic memory research. It tracks a `memory_stream` of documents, stamps each with `last_accessed_at` and `created_at` metadata, and updates the access time on every retrieval. You can also plug in additional scoring factors through the `other_score_keys` parameter - for example, an `importance` score that the agent assigns when creating the memory.

I wouldn't use this for a standard document Q&A pipeline. But for conversational agents that need to recall recent interactions over older ones, it's a solid fit. The retriever defaults to fetching `k=100` candidates from the vector store before applying the combined scoring, which ensures the recency reranking has enough material to work with.

## The Production Gotchas Nobody Warns You About

Reading the LangChain issue tracker reveals patterns that documentation doesn't cover.

Silent indexing failures are a real problem. A reported issue with WeaviateVectorStore (issue #35572, filed March 2026) shows that `add_documents` logs errors when chunks fail to index but still returns a valid list of chunk IDs. If your application doesn't attach a handler to LangChain's logger, you won't know that half your documents never made it into the store. The proposed fix is to return both successful and failed object lists, but until that lands, you need to verify document counts after ingestion.

Chroma's in-memory mode has a subtle state leak. Issue #28774 documents that creating multiple `Chroma` instances with `persist_directory=None` in the same Python process causes document accumulation across iterations - counts go from 6 to 12 to 18 to 24 instead of staying at 6. The underlying Chroma client reuses storage within a single process. The workaround is explicit: call `client.reset()` between iterations, or create new collection names.

And then there's security. Issue #34780 proposes a defense-in-depth guide for RAG applications, covering indirect prompt injection through retrieved documents. The threat model is real: if an attacker can control any document in your corpus, they can inject instructions that the LLM follows. The proposed mitigations include content filtering on retrieved documents before they reach the prompt, output validation, and rate limiting. A separate proposal (issue #35953) goes further, suggesting cryptographic signing of chunks at ingestion time and signature verification before injection into the LLM prompt - essentially a zero-trust model for retrieval. That proposal was closed in favor of community packages, but the underlying concern isn't going away.

## Choosing Your Vector Store

LangChain's partner ecosystem covers a wide range of vector databases: Chroma, Qdrant, Pinecone, Milvus, PgVector, Elasticsearch, Neo4j, DuckDB, and many others. Each gets its own package under `libs/partners/` in the monorepo. For prototyping, `InMemoryVectorStore` from `langchain_core` works fine - it uses numpy for cosine similarity and requires no external dependencies beyond that. For production, the choice depends on your scale, your existing infrastructure, and whether you need features like metadata filtering or hybrid keyword-plus-vector search.

The community discussion around this is active and opinionated. A February 2026 thread on r/AgentsOfAI captures a sentiment I see often: developers who started with LangChain are stripping down to raw Python loops for more control over prompt flow. And they're not wrong that frameworks add weight. But the value of `BaseRetriever` as an interface isn't the framework magic - it's the composability. A retriever that implements `Runnable` can be batched, streamed, traced with LangSmith, and swapped out without rewriting the chain around it. That's plumbing, not magic, and plumbing is what you need when the system grows past one person's ability to hold it in their head.

## Where This Is All Heading

The feature requests tell a story about where RAG pipelines are going. Issue #36090 asks for one-to-many batch similarity search - the ability to score a single query embedding against a custom list of entity embeddings rather than the entire database. This enables multi-step ranking with different embedding strategies for retrieval versus reranking, a pattern that tools like ShapedQL (discussed on Hacker News in January 2026) formalize into a SQL dialect with native RETRIEVE, FILTER, SCORE, and REORDER stages. And the WFGY 16-problem framework (issue #35360) is trying to map common RAG failure modes - hallucination, chunk drift, embedding mismatch, retrieval collapse - to specific LangChain components so teams can diagnose issues systematically rather than guessing.

The retriever abstraction is solid. The vector store interface is comprehensive. But the hard part of RAG was never the storage or the search. It's knowing whether your pipeline is actually retrieving the right documents, failing gracefully when it isn't, and defending against the adversarial cases that production inevitably surfaces. That's where the real engineering work lives, and no framework can do it for you.
