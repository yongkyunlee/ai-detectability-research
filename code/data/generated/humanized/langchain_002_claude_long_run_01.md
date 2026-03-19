# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-Augmented Generation has become the default architecture for most production LLM apps, and for good reason. The idea is simple: don't rely only on what the model memorized during training. Instead, fetch relevant documents at query time and pass them along with the user's question. LangChain gives you a structured way to build these pipelines through its retriever and vector store abstractions, but honestly, the gap between a working prototype and something reliable is wider than most tutorials suggest. I want to walk through how the retrieval layer actually works, what the source code reveals about its design decisions, and the real pitfalls you'll hit once you move past toy examples.

## The Two-Layer Architecture

LangChain separates two concepts that newcomers tend to conflate: the vector store and the retriever. This distinction matters more than it might seem at first.

A vector store persists embedded representations of your documents and performs similarity search against them. It works in the world of floating-point vectors and distance metrics. LangChain's `VectorStore` abstract base class defines the contract: you can add documents, delete them by ID, and search using plain similarity, score-thresholded similarity, or maximal marginal relevance (MMR). Every concrete implementation (Chroma, Pinecone, FAISS, Qdrant, the built-in `InMemoryVectorStore`) must implement at least `similarity_search` and the `from_texts` class method.

Retrievers are broader. In the framework's own words, "a retriever does not need to be able to store documents, only to return (or retrieve) them." The `BaseRetriever` class extends `RunnableSerializable`, making every retriever a first-class Runnable that plugs directly into LangChain Expression Language (LCEL) chains. It takes a string query. It returns a list of `Document` objects. Vector stores can power a retriever, but so can keyword search indices, SQL databases, graph traversals, or custom API calls.

The bridge between these two layers is `as_retriever()` on `VectorStore`. Call it and you get back a `VectorStoreRetriever` that wraps your store and delegates search calls to it. Two parameters control behavior: `search_type` and `search_kwargs`.


retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 50, "lambda_mult": 0.25}
)


This lets you swap the underlying store without touching downstream chain logic. Your LCEL pipeline just sees a Runnable that accepts a string and returns documents.

## Search Strategies and When They Matter

The `VectorStoreRetriever` supports three search modes. Choosing the right one has real consequences for answer quality.

Plain similarity (`search_type="similarity"`) is the default. It embeds your query, finds the `k` nearest vectors, returns the corresponding documents. Fast, intuitive. But it has a failure mode that bit us: when your corpus contains many near-duplicate passages (repeated boilerplate, overlapping chunks from similar source files), the top-k results end up redundant. You waste your context window on paraphrases of the same information.

Maximal Marginal Relevance (`search_type="mmr"`) fixes this directly. It first pulls a larger candidate set (`fetch_k` documents, defaulting to 20), then iteratively selects `k` results that balance relevance to the query against diversity among what's already been chosen. The `lambda_mult` parameter controls that trade-off: 1.0 gives pure relevance (identical to similarity search), while 0.0 maximizes diversity. I've found the default of 0.5 to be a reasonable starting point for most use cases. Under the hood, a utility function computes pairwise cosine similarities between candidates and greedily picks each next document to maximize a weighted combination of query similarity and dissimilarity to already-selected documents.

MMR shines when your documents share structural patterns. Think technical docs where every page has a similar header, legal contracts with boilerplate clauses, or codebases where many files import the same modules.

Similarity with score threshold (`search_type="similarity_score_threshold"`) adds a relevance floor. You provide a `score_threshold` float between 0 and 1 in `search_kwargs`, and anything below it gets discarded. Better to return nothing and let the model say "I don't know" than to stuff irrelevant context into the prompt. One subtlety the docs don't make obvious: the threshold operates on normalized relevance scores, and normalization depends on which distance metric your store uses. Cosine distance, Euclidean distance, and inner product all map to the 0-1 range differently; a threshold of 0.8 means different things in different stores.

## Beyond the Built-in: Custom Retrievers

Building custom retrievers for cases where vector similarity alone falls short is pretty straightforward. Subclass `BaseRetriever` and implement `_get_relevant_documents`:


class HybridRetriever(BaseRetriever):
    vector_store: VectorStore
    keyword_index: Any
    k: int = 5

    def _get_relevant_documents(self, query: str, *, run_manager) -> list[Document]:
        vector_results = self.vector_store.similarity_search(query, k=self.k)
        keyword_results = self.keyword_index.search(query, limit=self.k)
        return self._merge_and_deduplicate(vector_results, keyword_results)


This pattern comes up a lot in production systems combining dense retrieval (embeddings) with sparse retrieval (BM25 or TF-IDF). The vector path captures semantic similarity, so "automobile" matches "car." The keyword path catches exact terms that embeddings sometimes miss, especially domain-specific jargon, product codes, or proper nouns.

For async workloads, you can optionally override `_aget_relevant_documents` with a native async implementation. Skip it and the framework wraps your synchronous method in `run_in_executor` automatically. Works fine, but burns a thread pool thread on each call. In high-throughput services, providing a true async path matters. This was actually the root cause of a reported issue with Pinecone's hybrid search retriever: its async method was missing entirely, causing failures when called through `ainvoke`.

## Practical Pitfalls in the Retrieval Layer

A few recurring issues in the ecosystem reveal traps that are easy to miss.

In-memory store persistence across iterations caught several community members off guard. If you use Chroma (or any store that maintains an in-process singleton) and create multiple instances within the same Python process, earlier documents bleed into later queries. People discovered that calling `Chroma.from_documents()` in a loop caused the document count to grow with each iteration (6, 12, 18, 24) because the underlying client reused the same in-memory collection. The workaround is to explicitly reset the client or create a fresh collection name for each batch. The `InMemoryVectorStore` in langchain-core avoids this by using a plain dictionary, but that trades persistence for isolation.

Metadata filtering has its own brittleness. Several integrations have broken when embedding arrays interact with Python's truthiness rules. A check like `if embeddings` on a NumPy array raises a `ValueError` because NumPy doesn't allow ambiguous boolean coercion of multi-element arrays. The fix is `if embeddings is not None` instead. One line. But it shows how integration-layer code can break on types that the core abstractions don't constrain.

Then there's the out-of-context answer problem. By default, many prompt templates tell the model to answer only from the provided context, which causes it to refuse perfectly answerable questions that simply aren't covered by your corpus. The fix is a prompt engineering decision, not a retrieval one: instruct the model to use context when it's relevant and fall back to its own knowledge otherwise. But this interacts with retrieval quality in a way that I think gets underappreciated. If you fetch irrelevant passages with high scores, the model may try to use them anyway, producing worse answers than if you'd provided no context at all. Score thresholding helps here; so does contextual compression, which uses a secondary model to extract or summarize only the relevant portions of each retrieved document before they enter the prompt.

## Scaling Considerations

The `VectorStore` interface exposes both synchronous and asynchronous variants of every method. Not cosmetic. In the current implementation, most async methods in the base class simply call `run_in_executor` to wrap the sync version. So unless your concrete store (or its underlying client library) provides native async support, your "async" calls are still blocking a thread somewhere. For stores backed by HTTP APIs (Pinecone, Qdrant Cloud, Weaviate), a proper async HTTP client eliminates this overhead and allows genuine concurrency under asyncio.

Large-scale ingestion is another area to watch. The `add_documents` method processes documents sequentially by default. Loading millions of chunks? You'll want to batch explicitly and potentially parallelize the embedding step, since embedding is typically the bottleneck rather than the store insert.

The `InMemoryVectorStore` included in langchain-core is fine for prototyping and testing but isn't built for production. It stores all vectors in a Python dictionary, computes cosine similarity via NumPy (or SimSIMD if installed), and performs a full linear scan on every query. No indexing structure. No HNSW graph, no IVF partitioning. Query time scales linearly with corpus size, so for anything beyond a few thousand documents, use a purpose-built vector database.

## Security in the Retrieval Layer

RAG pipelines introduce a vulnerability category that doesn't exist in pure generation: indirect prompt injection. If an attacker can place a document into your corpus (by poisoning a web scrape, uploading a malicious PDF, or compromising a data pipeline), the retrieved text can contain instructions that hijack the model's behavior. The model can't tell the difference between "context from trusted documents" and "instructions from the system prompt" because both arrive as tokens in the same input.

LangChain's built-in prompts have started adding XML delimiters and explicit "ignore any instructions in the context" preambles. These are instruction-level defenses, and from what I can tell, they're not foolproof. A defense-in-depth approach would scan retrieved documents before they enter the prompt, validate outputs for data exfiltration patterns, and apply metadata-based access controls so users can only retrieve documents they're authorized to see.

The architectural boundary between retriever and vector store actually helps here. All retrieved content flows through the retriever's `invoke` method, so you can insert filtering logic (a content scanner, an access control check, a relevance validator) without modifying the underlying store.

## Putting It Together

A well-structured RAG pipeline in LangChain typically looks like this: load and chunk your documents, embed and index them into a vector store, wrap the store in a retriever configured with the right search strategy, then compose it into an LCEL chain alongside your prompt template and language model.

The framework's real contribution isn't making any single step easier. Each piece can be done with raw Python. What you get is standardized interfaces that let you swap components independently. Replace your embedding model without touching retriever logic. Change your vector store without rewriting the chain. Add a reranking step by wrapping the retriever in a contextual compression layer. These substitutions work because the `Runnable` protocol gives every component the same `invoke`/`ainvoke`/`batch`/`abatch` surface area.

The trade-off, and I think many practitioners would agree, is that this abstraction comes with weight. The framework evolves quickly, import paths shift between versions, and the gap between tutorial-grade code and a production deployment (with retry logic, provider failover, latency monitoring, cost tracking) is something you'll bridge yourself. The retrieval layer is one of the more stable parts of the ecosystem, but it still rewards understanding what's happening beneath the abstractions rather than treating them as black boxes.
