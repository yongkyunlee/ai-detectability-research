# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-Augmented Generation has become the standard technique for grounding large language models in external knowledge. Rather than relying solely on a model's parametric memory, RAG fetches relevant documents at query time and feeds them as context alongside the user's question. The result is more factual, more current, and more controllable than a bare LLM call. LangChain provides a layered set of abstractions for building these pipelines, with vector stores and retrievers sitting at the center of the retrieval stage. Understanding how these components fit together, and where the sharp edges lie, is essential for anyone building a production RAG system.

## The Two Core Abstractions

LangChain separates retrieval into two distinct interfaces: the `VectorStore` and the `BaseRetriever`. They serve different purposes, and the distinction matters more than it might seem at first glance.

A **vector store** is a persistence layer. It accepts documents, computes or stores their embedding vectors, and exposes search methods: similarity search, search with scores, and maximal marginal relevance search. The `VectorStore` abstract class defines operations like `add_documents`, `similarity_search`, `similarity_search_with_relevance_scores`, and `max_marginal_relevance_search`. Every concrete implementation, whether backed by Chroma, Pinecone, FAISS, Qdrant, or even a simple in-memory dictionary, must implement at least `similarity_search` and the `from_texts` class method.

A **retriever**, on the other hand, is a query interface. It takes a string and returns a list of `Document` objects. That is the entire contract. The `BaseRetriever` class extends LangChain's `Runnable` protocol, meaning every retriever can be invoked with `.invoke()`, batched with `.batch()`, or composed with other runnables using the pipe operator. The critical method to implement is `_get_relevant_documents`, which receives a query string and returns the documents. An optional `_aget_relevant_documents` provides native async support; if you omit it, the framework wraps the synchronous version in an executor automatically.

The key insight is that a retriever is strictly more general than a vector store. A retriever does not need to store anything. It might query an API, run a SQL query, call a search engine, or consult a TF-IDF index built with scikit-learn. Vector stores happen to be the most common backend for retrievers, but they are not the only option.

## Bridging Stores and Retrievers

The connection between these two abstractions is the `as_retriever()` method on `VectorStore`. Calling it produces a `VectorStoreRetriever` that wraps the store and delegates search calls to it. This method accepts several configuration options that control how retrieval behaves.

The `search_type` parameter selects the search strategy. Three options are available: `"similarity"` performs a standard nearest-neighbor lookup and returns the top-k results. `"mmr"` uses maximal marginal relevance, which balances relevance to the query against diversity among the selected documents. `"similarity_score_threshold"` filters results below a specified cosine similarity score, returning only documents that meet a minimum relevance bar.

The `search_kwargs` dictionary provides fine-grained control. You can set `k` to control how many documents come back, `fetch_k` to control how many candidates the MMR algorithm considers before selecting its final set, `lambda_mult` to tune the relevance-diversity trade-off in MMR, `score_threshold` for threshold-based filtering, and `filter` for metadata-based constraints.

A typical setup might look like this:


retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 50, "lambda_mult": 0.25}
)
docs = retriever.invoke("How does authentication work?")


This fetches 50 candidate documents by similarity, then selects 6 that balance relevance with diversity. The low `lambda_mult` value pushes toward greater diversity, which is useful when your corpus contains many near-duplicate passages.

## Choosing a Search Strategy

The choice of search strategy has a direct impact on answer quality, and the right choice depends on your data and your failure modes.

**Pure similarity search** is the simplest and fastest option. It works well when your corpus has clear topical separation and your queries map cleanly to a single cluster of relevant documents. The downside is redundancy: if your top-5 results all say roughly the same thing, you are wasting context window tokens without adding information.

**Maximal marginal relevance** addresses this by penalizing candidates that are too similar to documents already selected. The algorithm first retrieves `fetch_k` candidates by similarity, then iteratively picks documents that maximize a weighted combination of query relevance and dissimilarity to the already-selected set. The `lambda_mult` parameter controls this balance. A value of 1.0 reduces to pure similarity; a value of 0.0 maximizes diversity at the expense of relevance. In practice, values between 0.25 and 0.5 tend to work well. MMR is particularly valuable when your documents were chunked from a small number of source files, because adjacent chunks often have high embedding similarity but contain complementary information.

**Score thresholding** takes a different approach entirely. Instead of returning a fixed number of results, it returns only those whose relevance score exceeds a cutoff. This prevents the retriever from stuffing irrelevant passages into the context when a query has no good matches in the corpus. The trade-off is that you must tune the threshold empirically. LangChain normalizes relevance scores to a 0-to-1 range, with the normalization depending on the distance metric used by the underlying store: cosine distance, Euclidean distance, and inner product each have their own conversion function.

## Building a Custom Retriever

Sometimes none of the built-in search strategies match your needs. LangChain makes it straightforward to build a custom retriever by subclassing `BaseRetriever`. Because the retriever interface only requires implementing `_get_relevant_documents`, you can wrap any retrieval logic you want.

For example, a retriever that uses a TF-IDF vectorizer from scikit-learn looks like this:


from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from sklearn.metrics.pairwise import cosine_similarity

class TFIDFRetriever(BaseRetriever):
    vectorizer: Any
    docs: list[Document]
    tfidf_array: Any
    k: int = 4

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str) -> list[Document]:
        query_vec = self.vectorizer.transform([query])
        results = cosine_similarity(self.tfidf_array, query_vec).reshape((-1,))
        return [self.docs[i] for i in results.argsort()[-self.k:][::-1]]


Because this retriever implements the `Runnable` interface, it plugs directly into any LangChain chain or agent that expects a retriever. You get callback support, tracing via LangSmith, batching, and async execution for free.

## Common Pitfalls and How to Avoid Them

Community experience with LangChain's retrieval stack has surfaced several recurring issues that are worth knowing about before you hit them in production.

**Ephemeral store behavior can surprise you.** Some vector store backends, notably Chroma, reuse in-memory storage across instances within the same Python process. If you create a new Chroma instance in a loop expecting a fresh store each time, documents from previous iterations may persist. The workaround is either to explicitly reset the client between iterations or to use unique collection names. LangChain's built-in `InMemoryVectorStore` avoids this problem because it uses a plain Python dictionary as its backing store.

**Async support is uneven across integrations.** The `BaseRetriever` class provides a default `_aget_relevant_documents` implementation that wraps the synchronous method in a thread pool executor. This means calling `ainvoke()` on any retriever will work, but it will not give you true async I/O. For high-throughput applications, check whether your specific vector store integration provides native async methods. If it does not, you may find yourself bottlenecked on the thread pool.

**Metadata filtering requires care.** Vector stores handle metadata differently. Some accept dictionary-style filters with field-level conditions, while others expect callable filter functions. LangChain's `InMemoryVectorStore`, for instance, takes a Python function that receives a `Document` and returns a boolean. Chroma and Pinecone use their own filter syntax. Complex metadata values, such as nested dictionaries or lists, often cause serialization errors. The `filter_complex_metadata` utility in `langchain_community.vectorstores.utils` strips problematic fields before insertion, but you should be aware that this means losing that metadata.

**Memory and retrieval chains have friction points.** Combining conversational memory with retrieval chains has historically been a source of bugs. When using chains that return multiple outputs, like source documents alongside the answer, the memory component may not know which output to store. Specifying the `output_key` explicitly on your memory object resolves this.

## Security in RAG Pipelines

RAG introduces a security surface that pure LLM applications do not have: indirect prompt injection. When your system retrieves documents from external sources, an attacker can embed malicious instructions in those documents. If the retrieved text reaches the model's context window, the model may follow the attacker's instructions rather than your system prompt.

Defense-in-depth is the right approach here. Wrapping retrieved context in delimiters to help the model distinguish instructions from data is a start, but it is not sufficient on its own. Consider scanning retrieved documents before including them in the prompt, validating user inputs for injection patterns, and applying output guardrails to catch data exfiltration attempts. The LangChain community has been actively discussing these defenses, and upstream improvements to default prompt templates have begun incorporating explicit injection resistance.

## From Prototype to Production

The gap between a working RAG prototype and a production system is real, and the community has been vocal about it. The prototype often works well: chain a retriever to a prompt to an LLM, and you get reasonable answers. The problems surface under real traffic. Latency climbs as your corpus grows, embedding costs accumulate, stale documents pollute results, and edge-case queries return irrelevant context that degrades answer quality.

A few principles help close this gap. First, invest in your chunking strategy before optimizing retrieval. The quality of your chunks sets an upper bound on retrieval quality; no amount of search tuning can compensate for poorly split documents. Second, use relevance score thresholds or reranking to prevent low-quality retrievals from reaching the LLM. Returning fewer but better documents consistently outperforms returning more but noisier ones. Third, trace your retrieval pipeline end-to-end. LangChain's integration with LangSmith provides visibility into what each retriever returned, what scores those documents received, and how they contributed to the final answer.

The ecosystem around LangChain continues to evolve rapidly. Multi-stage retrieval pipelines that combine sparse and dense search, reranking models that refine initial retrieval results, and hybrid architectures that blend vector similarity with structured metadata queries are all becoming standard practice. LangChain's layered architecture, with its clean separation between stores, retrievers, and chains, provides a solid foundation for building these increasingly sophisticated systems. The key is understanding the abstractions well enough to know when to use them as-is and when to reach past them.
