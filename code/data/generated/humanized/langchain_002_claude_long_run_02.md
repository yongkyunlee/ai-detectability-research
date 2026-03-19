# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-Augmented Generation has become the go-to technique for grounding large language models in external knowledge. Instead of counting on a model's parametric memory alone, RAG fetches relevant documents at query time and passes them as context with the user's question. You get answers that are more factual, more current, and easier to control than a bare LLM call. LangChain gives you a layered set of abstractions for building these pipelines, with vector stores and retrievers at the center of the retrieval stage. Honestly, understanding how they fit together (and where the sharp edges are) matters more than most tutorials let on.

## The Two Core Abstractions

LangChain splits retrieval into two interfaces: the `VectorStore` and the `BaseRetriever`. They serve different purposes. The distinction matters more than it might seem at first.

A vector store is your persistence layer. It takes in documents, computes or stores their embedding vectors, and exposes search methods: similarity search, search with scores, and maximal marginal relevance search. The `VectorStore` abstract class defines operations like `add_documents`, `similarity_search`, `similarity_search_with_relevance_scores`, and `max_marginal_relevance_search`. Every concrete implementation, whether it's backed by Chroma, Pinecone, FAISS, Qdrant, or a simple in-memory dictionary, must implement at least `similarity_search` and the `from_texts` class method.

A retriever is different. It's a query interface: give it a string, get back a list of `Document` objects. That's the whole contract. The `BaseRetriever` class extends LangChain's `Runnable` protocol, so every retriever can be invoked with `.invoke()`, batched with `.batch()`, or composed with other runnables using the pipe operator. The method you need to implement is `_get_relevant_documents`, which receives a query string and returns documents. There's also an optional `_aget_relevant_documents` for native async support; skip it and the framework wraps your synchronous version in an executor automatically.

Here's what I think is the real takeaway: a retriever is strictly more general than a vector store. A retriever doesn't need to store anything. It might query an API, run a SQL query, call a search engine, or consult a TF-IDF index built with scikit-learn. Vector stores happen to be the most common backend, but they're far from the only option.

## Bridging Stores and Retrievers

The `as_retriever()` method on `VectorStore` connects these two abstractions. Call it and you get a `VectorStoreRetriever` that wraps the store and delegates search calls to it. The method takes several configuration options that control how retrieval behaves.

The `search_type` parameter picks the search strategy. `"similarity"` does a standard nearest-neighbor lookup and returns the top-k results. `"mmr"` uses maximal marginal relevance, balancing query relevance against diversity among the selected documents. `"similarity_score_threshold"` filters out results below a specified cosine similarity score, so only documents that clear a minimum relevance bar come back.

Then there's `search_kwargs`, a dictionary for fine-grained control. You can set `k` for how many documents to return, `fetch_k` for how many candidates the MMR algorithm considers before making its final selection, `lambda_mult` to tune the relevance-vs-diversity trade-off in MMR, `score_threshold` for threshold-based filtering, and `filter` for metadata constraints.

A typical setup:


retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 50, "lambda_mult": 0.25}
)
docs = retriever.invoke("How does authentication work?")


This fetches 50 candidate documents by similarity, then picks 6 that balance relevance with diversity. The low `lambda_mult` value pushes toward greater diversity, which helps when your corpus has a lot of near-duplicate passages.

## Choosing a Search Strategy

Which strategy you pick directly affects answer quality. The right choice depends on your data and what's going wrong.

Pure similarity search is the simplest and fastest. It works well when your corpus has clear topical separation and queries map cleanly to a single cluster of relevant documents. The downside? Redundancy. If your top-5 results all say roughly the same thing, you're burning context window tokens without adding information.

MMR fixes this by penalizing candidates that look too much like documents already selected. The algorithm first grabs `fetch_k` candidates by similarity, then iteratively picks documents that maximize a weighted combination of query relevance and dissimilarity to the already-selected set. The `lambda_mult` parameter controls the balance: 1.0 reduces to pure similarity, 0.0 maximizes diversity at the expense of relevance. From what I can tell, values between 0.25 and 0.5 tend to work best in practice. It's particularly valuable when your documents were chunked from a small number of source files, because adjacent chunks often have high embedding similarity but contain complementary information.

Score thresholding takes a completely different approach. Instead of returning a fixed number of results, it only returns those whose relevance score exceeds a cutoff. No good matches in the corpus? You get nothing back, which beats stuffing irrelevant passages into the context. The catch is that you have to tune the threshold empirically. LangChain normalizes relevance scores to a 0-to-1 range, and the normalization depends on which distance metric your underlying store uses; cosine distance, Euclidean distance, and inner product each have their own conversion function.

## Building a Custom Retriever

Sometimes the built-in strategies don't match what you need. LangChain makes it pretty straightforward to build your own by subclassing `BaseRetriever`. Since the interface only requires implementing `_get_relevant_documents`, you can wrap whatever retrieval logic you want.

Here's a retriever that uses scikit-learn's TF-IDF vectorizer:


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


Because it implements the `Runnable` interface, this plugs directly into any LangChain chain or agent expecting a retriever. You get callback support, LangSmith tracing, batching, and async execution for free.

## Common Pitfalls and How to Avoid Them

Community experience with LangChain's retrieval stack has surfaced several recurring issues. Worth knowing about before they bite you in production.

Ephemeral store behavior can surprise you. Some vector store backends (Chroma being the classic example) reuse in-memory storage across instances within the same Python process. If you create a new Chroma instance in a loop expecting a fresh store each time, documents from previous iterations may still be there. You can either explicitly reset the client between iterations or use unique collection names. LangChain's built-in `InMemoryVectorStore` doesn't have this problem because it just uses a plain Python dictionary.

Async support is uneven across integrations, and the docs don't make this obvious. The `BaseRetriever` class provides a default `_aget_relevant_documents` that wraps the synchronous method in a thread pool executor. So calling `ainvoke()` on any retriever will work, but you won't get true async I/O. For high-throughput applications, check whether your specific vector store integration provides native async methods. If it doesn't, you might end up bottlenecked on the thread pool.

Metadata filtering requires care. Different vector stores handle it differently. Some accept dictionary-style filters with field-level conditions; others expect callable filter functions. `InMemoryVectorStore` takes a Python function that receives a `Document` and returns a boolean. Chroma and Pinecone use their own filter syntax entirely. Complex metadata values (nested dictionaries, lists) often cause serialization errors. There's a `filter_complex_metadata` utility in `langchain_community.vectorstores.utils` that strips problematic fields before insertion, but be aware: you're losing that metadata when you use it.

Memory and retrieval chains together have historically been a source of bugs. When you use chains that return multiple outputs (source documents alongside the answer, for instance), the memory component may not know which output to store. Specifying `output_key` explicitly on your memory object fixes this.

## Security in RAG Pipelines

RAG introduces a security surface that pure LLM applications don't have: indirect prompt injection. When your system retrieves documents from external sources, an attacker can embed malicious instructions in those documents. If the retrieved text reaches the model's context window, the model may follow the attacker's instructions instead of your system prompt.

Defense-in-depth is the right approach. Wrapping retrieved context in delimiters helps the model distinguish instructions from data, but it isn't enough on its own. You should also consider scanning retrieved documents before including them in the prompt, validating user inputs for injection patterns, and applying output guardrails to catch data exfiltration attempts. The LangChain community has been actively discussing these defenses, and upstream improvements to default prompt templates have started incorporating explicit injection resistance.

## From Prototype to Production

The gap between a working RAG prototype and a production system is real. I've seen this come up constantly in community discussions. The prototype works great: chain a retriever to a prompt to an LLM, and you get reasonable answers. Then real traffic hits. Latency climbs as your corpus grows, embedding costs pile up, stale documents pollute results, and edge-case queries return irrelevant context that tanks answer quality.

A few principles help close that gap. First, invest in your chunking strategy before you start optimizing retrieval. Chunk quality sets an upper bound on retrieval quality; no amount of search tuning compensates for poorly split documents. Second, use relevance score thresholds or reranking to keep low-quality retrievals from reaching the LLM. Returning fewer but better documents consistently beats returning more but noisier ones. Third, trace your pipeline end-to-end. LangChain's integration with LangSmith gives you visibility into what each retriever returned, what scores those documents received, and how they contributed to the final answer.

The ecosystem around LangChain keeps evolving fast. Multi-stage retrieval pipelines combining sparse and dense search, reranking models that refine initial results, hybrid architectures blending vector similarity with structured metadata queries: these are all becoming standard practice. LangChain's layered architecture, with its clean separation between stores, retrievers, and chains, provides a solid foundation for building on top of. The trick is understanding the abstractions well enough to know when to use them as-is and when to reach past them.
