# Building RAG Pipelines with LangChain Retrievers and Vector Stores

RAG isn't one thing. It's a composition of at least three distinct subsystems - document ingestion, vector retrieval, and prompt assembly - each with its own failure modes. LangChain gives you abstractions for all three, but the ones that matter most sit at the boundary between your vector store and your LLM: the retriever and the vector store interface. I want to walk through how these pieces actually connect, what the code looks like under the hood, and where you'll run into sharp edges.

## The Two Core Abstractions

LangChain splits retrieval into two layers. `VectorStore` is the abstract base class for anything that stores embeddings and runs similarity search. `BaseRetriever` is a more general interface - it takes a string query and returns a list of `Document` objects. A retriever doesn't have to be backed by a vector store at all. It could wrap a SQL query, a keyword index, or an external API. The relationship between the two is that every vector store can produce a retriever via `as_retriever()`, but not every retriever needs a vector store behind it.

This distinction is easy to miss and worth understanding. The `BaseRetriever` class, defined in `langchain_core/retrievers.py`, extends `RunnableSerializable`, which means every retriever is a first-class Runnable. You call it with `invoke()` or `ainvoke()`. You chain it with pipes. You can batch across queries. That composability is the real value - not the retrieval itself.

## How Vector Store Search Actually Works

The `VectorStore` base class in `langchain_core/vectorstores/base.py` supports three search types: `similarity`, `mmr`, and `similarity_score_threshold`. These aren't just string labels. They correspond to fundamentally different retrieval strategies.

Plain similarity search returns the `k` nearest documents by cosine distance. This is your default (and `k` defaults to 4). The `similarity_score_threshold` variant adds a float threshold between 0 and 1 - documents below the threshold get dropped. And `mmr` (maximal marginal relevance) optimizes for both relevance to the query and diversity among results, controlled by a `lambda_mult` parameter that ranges from 0 (maximum diversity) to 1 (minimum diversity), defaulting to 0.5.

The MMR path is the interesting one. It first fetches `fetch_k` candidates (default 20), then re-ranks them to select the final `k` results. So you're trading a larger initial retrieval set for less redundancy in the final output. This matters when your corpus has many near-duplicate chunks - which, if you've ever run a recursive text splitter over real documents, you know happens constantly.

The tradeoff here is clear: plain similarity search is simpler and faster, but MMR gives you better coverage when your chunks overlap. For most production RAG systems where documents share a lot of semantic content, I'd lean toward MMR with `fetch_k` set to at least 3x your final `k`.

## Wiring a Retriever to a Vector Store

The bridge between these two layers is `VectorStoreRetriever`, and the typical way to get one is through the `as_retriever()` method on any vector store instance. Here's what actually happens when you call it:

```python
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 50, "lambda_mult": 0.25}
)
docs = retriever.invoke("How do I configure authentication?")
```

That `invoke()` call runs through LangChain's callback machinery - setting up tracing, tagging, and metadata - before dispatching to `_get_relevant_documents`, which delegates to the appropriate search method on the underlying vector store. The retriever also reports LangSmith tracing parameters automatically, including the vector store provider name and embedding provider, so your observability pipeline can track which backend handled each query.

We should talk about filtering. The `search_kwargs` dictionary accepts a `filter` parameter, but the filter format is entirely dependent on the vector store backend. For the built-in `InMemoryVectorStore`, filters are Python callables that take a `Document` and return a boolean. For Qdrant, they're `models.Filter` objects with field conditions. For Chroma, they're dictionaries. There's no universal filter syntax, and the documentation for each integration sometimes uses the wrong imports - an issue that's bitten enough people to generate multiple bug reports in the LangChain tracker.

## The In-Memory Store: Good for Prototypes, Nothing Else

LangChain ships `InMemoryVectorStore` in `langchain-core` itself. It stores embeddings in a plain Python dictionary, computes cosine similarity using numpy, and implements MMR with a greedy selection loop. For prototyping or testing, it's perfect. You can instantiate it with any `Embeddings` object, add documents, and search - no external services required.

But don't ship it. It has no persistence beyond `dump()` and `load()` methods that serialize to JSON. It holds everything in process memory. And its cosine similarity implementation, while correct, is O(n) per query against the full document set. The optional `simsimd` library can speed up the math, but the algorithm is still a brute-force scan.

## Async: Not as Smooth as You'd Think

Every method on `VectorStore` and `BaseRetriever` has an async counterpart - `ainvoke`, `asimilarity_search`, `aadd_documents`, and so on. But here's the catch: the default async implementations in the base class just wrap the synchronous methods with `run_in_executor`. That means you're not getting true async IO unless the specific vector store integration overrides the async methods with native implementations.

This has real consequences. The Pinecone hybrid search retriever, for example, had an open issue (#29170) where `ainvoke` didn't work properly because `_aget_relevant_documents` wasn't implemented. The base class's fallback ran the sync method in a thread pool, which technically worked but defeated the purpose of going async in the first place. If you're building an async RAG pipeline, check whether your specific vector store integration actually implements native async or is just wrapping sync calls.

## Watch Out for Stale State

One particularly nasty gotcha involves Chroma's in-memory behavior. If you create multiple `Chroma` instances within the same Python process without specifying different collection names, they silently share the same underlying storage. Issue #28774 documented this: iterating over different document sets and creating fresh `Chroma.from_documents()` calls in each loop resulted in document counts of 6, 12, 18, 24 - the previous iterations' documents were still there. The workaround is to either reset the Chroma client explicitly or use unique collection names per batch.

This isn't a LangChain bug per se - it's Chroma's in-process storage reuse - but it's the kind of thing that silently corrupts your retrieval results and is very hard to debug without knowing to look for it.

## Choosing Your Stack

The LangChain ecosystem currently provides integration packages for most major vector databases: Pinecone, Qdrant, Chroma, Milvus, and others, each published as separate packages like `langchain-chroma` or `langchain-qdrant`. As of `langchain-core` 1.2.20, the core retriever and vector store interfaces are stable, but the integration quality varies. Some integrations have native async. Some don't. Some have well-tested metadata filtering. Others have documented import bugs.

My recommendation: pick a vector store based on your operational requirements (managed vs. self-hosted, scale, cost), then verify that the LangChain integration for it actually supports the features you need - especially async methods and metadata filtering. Don't assume the integration is complete just because the package exists. Read the source, run the tests, and check the GitHub issues for your specific backend before committing to it in production.

RAG pipelines are deceptively simple to prototype and genuinely hard to run well. LangChain's abstractions give you a solid compositional skeleton, but the details - search strategy selection, filter semantics, async correctness, and state isolation - are where real systems succeed or fail.
