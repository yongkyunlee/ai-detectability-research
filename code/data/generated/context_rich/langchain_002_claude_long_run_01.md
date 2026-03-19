# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-Augmented Generation has settled into a comfortable spot at the center of most production LLM applications. The premise is simple: instead of relying solely on the parametric knowledge baked into a language model during training, you fetch relevant documents at query time and hand them to the model alongside the user's question. LangChain's retriever and vector store abstractions give you a structured way to build these pipelines, but the gap between a working prototype and a reliable system is wider than many tutorials let on. This post walks through the architecture of LangChain's retrieval layer, the design decisions embedded in its source code, and the practical pitfalls that surface once you move past toy examples.

## The Two-Layer Architecture

LangChain draws a deliberate boundary between two concepts that newcomers often conflate: the vector store and the retriever.

A **vector store** is responsible for persisting embedded representations of your documents and performing similarity search against them. It speaks the language of floating-point vectors and distance metrics. LangChain's `VectorStore` abstract base class defines the core contract: you can add documents, delete them by ID, and search using plain similarity, score-thresholded similarity, or maximal marginal relevance (MMR). Every concrete implementation — whether backed by Chroma, Pinecone, FAISS, Qdrant, or the built-in `InMemoryVectorStore` — must implement at least `similarity_search` and the `from_texts` class method.

A **retriever**, on the other hand, is a broader abstraction. In the framework's own words, "a retriever does not need to be able to store documents, only to return (or retrieve) them." The `BaseRetriever` class extends `RunnableSerializable`, which means every retriever is a first-class Runnable that slots directly into LangChain Expression Language (LCEL) chains. It takes a string query and produces a list of `Document` objects. Vector stores can serve as the engine behind a retriever, but so can keyword search indices, SQL databases, graph traversals, or custom API calls.

The bridge between these two layers is the `as_retriever()` method on `VectorStore`. Calling it returns a `VectorStoreRetriever` that wraps your store and delegates search calls to it. You configure the retriever's behavior entirely through two parameters: `search_type` and `search_kwargs`.

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 50, "lambda_mult": 0.25}
)
```

This pattern lets you swap the underlying store without touching any downstream chain logic. Your LCEL pipeline sees a Runnable that accepts a string and returns documents — nothing more.

## Search Strategies and When They Matter

The `VectorStoreRetriever` supports three search modes, and choosing the right one has real consequences for answer quality.

**Plain similarity** (`search_type="similarity"`) is the default. It embeds your query, finds the `k` nearest vectors, and returns the corresponding documents. Fast and intuitive, but it has a failure mode: when your corpus contains many near-duplicate passages — repeated boilerplate, overlapping chunks from similar source files — the top-k results can be redundant, wasting your context window on paraphrases of the same information.

**Maximal Marginal Relevance** (`search_type="mmr"`) addresses this directly. It first retrieves a larger candidate set (`fetch_k` documents, defaulting to 20), then iteratively selects `k` results that balance relevance to the query against diversity among the chosen set. The `lambda_mult` parameter controls this trade-off: 1.0 gives you pure relevance (identical to similarity search), while 0.0 maximizes diversity. The default of 0.5 is a reasonable starting point. Under the hood, this is implemented in a utility function that computes pairwise cosine similarities between candidates and greedily selects each next document to maximize a weighted combination of query similarity and dissimilarity to already-selected documents.

MMR is particularly valuable when your documents share structural patterns — technical documentation where every page has a similar header, legal contracts with boilerplate clauses, or codebases where many files import the same modules.

**Similarity with score threshold** (`search_type="similarity_score_threshold"`) adds a relevance floor. You must provide a `score_threshold` float between 0 and 1 in `search_kwargs`, and the retriever discards any results below it. This is useful when you want to avoid stuffing irrelevant context into your prompt — better to return nothing and let the model say "I don't know" than to hand it misleading passages. One subtlety: the threshold operates on normalized relevance scores, and normalization depends on the distance metric your store uses. Cosine distance, Euclidean distance, and inner product all map to the 0-1 range differently, so a threshold of 0.8 means different things in different stores.

## Beyond the Built-in: Custom Retrievers

The framework makes it straightforward to build custom retrievers for cases where vector similarity alone is insufficient. You subclass `BaseRetriever` and implement `_get_relevant_documents`:

```python
class HybridRetriever(BaseRetriever):
    vector_store: VectorStore
    keyword_index: Any
    k: int = 5

    def _get_relevant_documents(self, query: str, *, run_manager) -> list[Document]:
        vector_results = self.vector_store.similarity_search(query, k=self.k)
        keyword_results = self.keyword_index.search(query, limit=self.k)
        return self._merge_and_deduplicate(vector_results, keyword_results)
```

This pattern shows up frequently in production systems that combine dense retrieval (embeddings) with sparse retrieval (BM25 or TF-IDF). The vector path captures semantic similarity — "automobile" matches "car" — while the keyword path catches exact terms that embeddings sometimes miss, especially for domain-specific jargon, product codes, or proper nouns.

For async workloads, you can optionally override `_aget_relevant_documents` with a native async implementation. If you do not, the framework automatically wraps your synchronous method in `run_in_executor`, which works but burns a thread pool thread on each call. In high-throughput services, providing a true async path matters. This was the root of a reported issue with Pinecone's hybrid search retriever: its `_aget_relevant_documents` method was missing entirely, causing failures when called through `ainvoke` in async setups.

## Practical Pitfalls in the Retrieval Layer

Several recurring issues in the LangChain ecosystem reveal traps that documentation does not always make obvious.

**In-memory store persistence across iterations.** If you use Chroma (or any vector store that maintains an in-process singleton) and create multiple store instances within the same Python process, earlier documents can bleed into later queries. Community members discovered that calling `Chroma.from_documents()` in a loop caused the document count to grow with each iteration — 6, 12, 18, 24 — because the underlying client reused the same in-memory collection. The workaround is to explicitly reset the client or create a fresh collection name for each batch. The `InMemoryVectorStore` in langchain-core avoids this by using a plain dictionary, but that trades persistence for isolation.

**Metadata filtering brittleness.** Several vector store integrations have had trouble with metadata filtering when embedding arrays interact with Python's truthiness rules. A check like `if embeddings` on a NumPy array raises a `ValueError` because NumPy does not allow ambiguous boolean coercion of multi-element arrays. The fix — using `if embeddings is not None` instead — is a single-line change, but it illustrates how integration-layer code can break on types that the core abstractions do not constrain.

**Out-of-context answers.** A perennial challenge with RAG is what happens when the retrieved documents are not relevant to the query. By default, many prompt templates tell the model to answer only from the provided context, which causes it to refuse perfectly answerable questions that simply are not covered by your corpus. The solution is a prompt engineering decision, not a retrieval one: instruct the model to use the context when it is relevant and fall back to its own knowledge otherwise. But this interacts with retrieval quality — if you fetch irrelevant passages with high scores, the model may try to use them anyway, producing worse answers than if you had provided no context at all. Score thresholding helps here, as does contextual compression, which uses a secondary model to extract or summarize only the relevant portions of each retrieved document before they enter the prompt.

## Scaling Considerations

The `VectorStore` interface exposes both synchronous and asynchronous variants of every method. This dual API is not cosmetic — it reflects a real architectural concern. In the current implementation, most async methods in the base class simply call `run_in_executor` to wrap the sync version. This means that unless the concrete vector store (or its underlying client library) provides native async support, your "async" calls are still blocking a thread somewhere. For stores backed by HTTP APIs — Pinecone, Qdrant Cloud, Weaviate — a proper async HTTP client eliminates this overhead and allows genuine concurrency under asyncio.

For large-scale ingestion, the `add_documents` method processes documents sequentially by default. If you are loading millions of chunks, you will want to batch them explicitly and potentially parallelize the embedding step, since embedding is typically the bottleneck rather than the vector store insert.

The `InMemoryVectorStore` included in langchain-core is useful for prototyping and testing but is not designed for production workloads. It stores all vectors in a Python dictionary, computes cosine similarity via NumPy (or SimSIMD if installed), and performs a full linear scan on every query. There is no indexing structure — no HNSW graph, no IVF partitioning — so query time scales linearly with corpus size. For anything beyond a few thousand documents, use a purpose-built vector database.

## Security in the Retrieval Layer

RAG pipelines introduce a category of vulnerability that does not exist in pure generation: indirect prompt injection. If an attacker can place a document into your corpus — by poisoning a web scrape, uploading a malicious PDF, or compromising a data pipeline — the retrieved text can contain instructions that hijack the model's behavior. The model cannot distinguish between "context from trusted documents" and "instructions from the system prompt" because both arrive as tokens in the same input.

LangChain's built-in prompts have begun adding XML delimiters and explicit "ignore any instructions in the context" preambles, but these are instruction-level defenses and are not foolproof. A defense-in-depth approach scans retrieved documents before they enter the prompt, validates outputs for data exfiltration patterns, and applies metadata-based access controls so that users can only retrieve documents they are authorized to see.

The architectural boundary between retriever and vector store actually helps here. Because all retrieved content flows through the retriever's `invoke` method, you can insert filtering logic — a content scanner, an access control check, a relevance validator — without modifying the underlying store.

## Putting It Together

A well-structured RAG pipeline in LangChain typically follows this shape: load and chunk your documents, embed and index them into a vector store, wrap the store in a retriever configured with the appropriate search strategy, and compose the retriever into an LCEL chain alongside your prompt template and language model.

The framework's contribution is not in making any single step easier — each piece can be done with raw Python — but in providing standardized interfaces that allow you to swap components independently. You can replace your embedding model without touching your retriever logic. You can change your vector store without rewriting your chain. You can add a reranking step by wrapping your retriever in a contextual compression layer. These substitutions work because the `Runnable` protocol gives every component the same `invoke`/`ainvoke`/`batch`/`abatch` surface area.

The trade-off, as many practitioners have noted, is that this abstraction comes with weight. The framework evolves quickly, import paths shift between versions, and the gap between the tutorial-grade chain and a production deployment — with retry logic, provider failover, latency monitoring, and cost tracking — is something you have to bridge yourself. The retrieval layer is one of the more stable and well-designed parts of the ecosystem, but it still benefits from understanding what is happening beneath the abstractions rather than treating them as black boxes.
