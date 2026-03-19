# Building RAG Pipelines with LangChain Retrievers and Vector Stores

RAG is the single most useful pattern to come out of the LLM application wave. You ground a language model's responses in real data, and suddenly it stops making things up. But the retrieval layer — the part that actually finds relevant documents — is where most teams get stuck. LangChain's retriever and vector store abstractions give you a reasonable starting point, and they've matured enough to be worth understanding properly.

I want to walk through how these pieces fit together, where the design gets opinionated, and what trade-offs you're signing up for.

## The Two-Layer Architecture

LangChain separates retrieval into two distinct concepts. A `VectorStore` handles storage and similarity search. A `BaseRetriever` is a broader abstraction — it takes a string query and returns a list of `Document` objects. The retriever doesn't need to know anything about embeddings or vectors. It just returns documents.

This separation matters. A vector store is always a valid backbone for a retriever, but a retriever isn't always backed by a vector store. You might build one on top of a SQL database, an API, or even a simple TF-IDF index. The `BaseRetriever` class in `langchain-core` (currently at version 1.2.20) implements the standard `Runnable` interface, so you call it with `invoke` or `ainvoke` just like any other component in a chain.

The bridge between the two layers is `VectorStore.as_retriever()`. This method returns a `VectorStoreRetriever` that wraps the underlying store and delegates search calls. It accepts a `search_type` parameter and a `search_kwargs` dict, and that's where you configure the retrieval behavior.

## Three Search Strategies

The `VectorStoreRetriever` supports three search types: `similarity`, `mmr`, and `similarity_score_threshold`. Each one maps to a different method on the vector store.

Plain similarity search is the default. It embeds your query, finds the `k` nearest vectors (default is 4), and returns the corresponding documents. Simple and fast.

MMR — maximal marginal relevance — is more interesting. It fetches a larger candidate set (`fetch_k`, defaulting to 20), then iteratively selects documents that balance relevance against diversity. The `lambda_mult` parameter controls the trade-off: a value of 1.0 gives you pure relevance, 0.0 gives maximum diversity, and 0.5 splits the difference. We've found this useful for corpora with lots of near-duplicate content. If your dataset has many similar documents from the same source, plain similarity search tends to return five nearly identical passages. MMR fixes that.

Score thresholding takes a different approach. Instead of returning a fixed number of results, it filters by a minimum relevance score between 0 and 1. You set it via `search_kwargs={"score_threshold": 0.8}`. This is genuinely handy when you'd rather return nothing than return garbage — say, in a customer-facing Q&A system where a wrong answer is worse than no answer.

So here's the trade-off: MMR is simpler to reason about because you always get `k` results, but score thresholding gives you quality guarantees at the cost of sometimes returning zero documents. Pick based on whether your downstream chain can handle an empty retrieval gracefully.

## Vector Store Internals

The `VectorStore` base class defines the interface that every integration must implement. At minimum, a store needs `similarity_search` and `from_texts`. Everything else — `delete`, `get_by_ids`, MMR search, relevance scoring — has default implementations that subclasses can override.

The relevance scoring system deserves attention. Raw distance metrics vary across backends: some use cosine distance, others use Euclidean or inner product. The `_select_relevance_score_fn` method on `VectorStore` is supposed to normalize these into a 0-to-1 range. But here's the catch — each integration must implement this correctly, and not all of them do. I've seen warnings about scores outside the [0, 1] range pop up with certain backends. If your retriever suddenly stops returning results with `similarity_score_threshold`, check whether the underlying store's relevance function is actually calibrated properly.

For prototyping, `langchain-core` ships an `InMemoryVectorStore`. It stores embeddings in a Python dict and uses cosine similarity via numpy. You can also optionally install `simsimd` for faster similarity computation. The in-memory store supports all three search types, metadata filtering via callable functions, and even persistence through `dump`/`load` methods. It won't scale to millions of documents, but it's perfect for tests and demos.

## The Async Gap

One issue that surfaces regularly: async support across vector store integrations is inconsistent. The base `VectorStore` class provides async versions of every method, but most fall back to `run_in_executor` — they just wrap the synchronous implementation in a thread pool. That's fine for prototyping but it won't give you true async I/O benefits. And some community retrievers don't even implement `_aget_relevant_documents` at all. If you're building an async application with `ainvoke`, test your specific integration carefully.

## Metadata Filtering

Every vector store supports metadata on documents, but the filtering interface isn't standardized across backends. The `InMemoryVectorStore` accepts a Python callable as a `filter` parameter — you pass a function that receives a `Document` and returns a boolean. Other stores like Qdrant or Chroma use their own filter syntax, which you pass through `search_kwargs`.

This is a real pain point. Switching from one vector store to another means rewriting your filter logic. There's no abstraction layer for metadata filters in `langchain-core` itself. If you know you'll need to swap backends, keep your filter logic isolated and easy to replace.

## Practical Recommendations

Start with the `InMemoryVectorStore` and plain similarity search. Don't introduce Pinecone or Chroma until you've validated that your chunking strategy and embedding model actually produce good results on a small test set. Too many teams debug retrieval quality issues in production when they should've caught them with 50 documents locally.

Once you move to a real backend, use `as_retriever()` with explicit `search_kwargs` rather than calling the vector store's search methods directly. The retriever interface integrates cleanly into LCEL chains and gives you automatic tracing through LangSmith — the `VectorStoreRetriever` automatically populates `ls_vector_store_provider` and `ls_embedding_provider` in its tracing metadata.

And think about security early. There's active discussion in the LangChain community about prompt injection risks in RAG pipelines. Retrieved documents are untrusted content — a poisoned document in your index can manipulate the LLM's behavior. Scanning retrieved chunks before they enter the prompt is a basic defense-in-depth measure that too many pipelines skip entirely.

The retriever abstraction isn't glamorous. It doesn't need to be. It's the boring plumbing that determines whether your RAG system returns useful answers or confidently generated nonsense. Get the retrieval right first, then worry about the fancy parts.
