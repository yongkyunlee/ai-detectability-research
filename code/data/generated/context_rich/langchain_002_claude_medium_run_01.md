# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-augmented generation has become the standard approach for grounding large language models in domain-specific knowledge. Rather than fine-tuning a model on your data, you fetch relevant documents at query time and pass them as context. LangChain provides a layered set of abstractions that make this pipeline straightforward to assemble — and, importantly, to customize when the defaults fall short.

## The Core Abstractions

At the foundation of any LangChain RAG pipeline sit two key interfaces: `VectorStore` and `BaseRetriever`.

A `VectorStore` handles the storage and lookup of document embeddings. You load documents, embed them through a model like OpenAI's `text-embedding-3-small` or a local sentence-transformer, and the vector store indexes those embeddings for similarity search. LangChain supports a wide range of backends here — Chroma for lightweight local use, FAISS for high-performance in-memory search, Pinecone and Qdrant for managed cloud deployments, pgvector for teams already invested in PostgreSQL, and several others.

A `BaseRetriever` is a simpler abstraction. It takes a string query and returns a list of `Document` objects. Every retriever implements `_get_relevant_documents`, and optionally an async counterpart. The critical design decision is that vector stores can be converted into retrievers through the `.as_retriever()` method, which wraps the store in a `VectorStoreRetriever` that conforms to the standard retriever interface. This separation matters because not every retrieval strategy depends on vector similarity — keyword search, graph lookups, and API calls all fit the same `BaseRetriever` contract.

Because both abstractions implement LangChain's `Runnable` interface, they compose naturally using the expression language. A typical chain pipes a retriever's output into a prompt template, then into an LLM:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

prompt = ChatPromptTemplate.from_template(
    "Answer the question based on the context:\n{context}\n\nQuestion: {question}"
)
chain = {"context": retriever, "question": lambda x: x} | prompt | ChatOpenAI()
```

## Choosing a Search Strategy

The default retrieval mode is plain similarity search, but this isn't always ideal. When your top results cluster around the same subtopic, you lose breadth. Maximal marginal relevance addresses this by balancing similarity to the query against diversity among the returned documents. Most vector store implementations support MMR as a search type parameter.

For domains where exact keyword matching matters alongside semantic understanding, hybrid search combines BM25-style term matching with vector similarity. Pinecone's hybrid search retriever implements this pattern, though it's worth noting that the async pathway for hybrid retrieval has been an open gap — something to account for if your application serves concurrent requests.

## Beyond Basic Retrieval

Simple similarity search breaks down when your chunking strategy creates tension between embedding quality and answer completeness. Small chunks embed well but lack surrounding context. Large chunks preserve context but dilute the embedding signal. The `ParentDocumentRetriever` resolves this by maintaining two levels of granularity: it indexes small child chunks for accurate matching, then returns the larger parent document that contains the match. This requires both a vector store and a separate document store, along with two text splitters configured at different sizes.

For conversational applications, queries often reference prior turns — "what about the second option?" means nothing without history. A history-aware retriever uses an LLM to reformulate such queries into standalone search terms before hitting the vector store. This adds a round-trip to the language model but dramatically improves retrieval accuracy in multi-turn dialogues.

When a single retriever isn't sufficient, LangChain supports ensemble approaches through `MergerRetriever`, which combines results from multiple sources. You might pair a vector retriever with a keyword-based one, or merge results from different document collections.

## Practical Pitfalls

Several recurring issues surface when deploying these pipelines. Chroma's in-memory mode can surprise you — even with `persist_directory=None`, the in-process storage may retain state across iterations within the same Python session. If you're running experiments in a loop, explicitly resetting the client prevents stale data from contaminating results.

Metadata filtering is another area where implementations diverge. Some backends handle only string and list types in filter conditions, silently failing or throwing unexpected errors on integers or floats. Testing your specific filter patterns against your chosen backend early saves debugging time later.

Import paths have shifted significantly across LangChain versions. The `create_retriever_tool` function, which wraps a retriever as an agent-usable tool, has migrated from `langchain.tools.retriever` to `langchain_community` and now lives in `langchain_core.tools`. Features like `ContextualCompressionRetriever` have moved to the `langchain_classic` package. Pinning your dependency versions and checking current documentation before starting a new project avoids the frustration of following outdated tutorials.

## Security in RAG Systems

Retrieved documents introduce an attack surface that pure LLM applications don't have. If an adversary can influence the content in your document store, they can embed instructions that the model may follow — a technique known as indirect prompt injection. A poisoned document might instruct the model to ignore its system prompt or exfiltrate data from the conversation.

LangChain mitigates this partially by wrapping retrieved context in XML delimiters and prepending instructions to ignore embedded directives. But instruction-level defenses are not bulletproof. Production deployments should layer additional protections: scanning retrieved documents for injection patterns, validating outputs for sensitive data leakage, and monitoring retrieval patterns for anomalies.

## Making the Right Trade-offs

The vector store you choose shapes your operational constraints. In-memory options like FAISS are fast and simple but don't persist. Local persistent stores like Chroma with a directory work well for prototyping and moderate-scale applications. Cloud-hosted services like Pinecone scale horizontally but introduce vendor dependency and network latency. Self-managed deployments of Qdrant or Milvus offer control at the cost of operational overhead.

Each retriever wrapper you add — history-aware reformulation, parent document lookup, compression — introduces latency. For interactive applications, profiling the full chain end-to-end and ensuring async support throughout the stack prevents bottlenecks that only appear under load.

The LangChain ecosystem gives you the building blocks. The engineering challenge is knowing which ones your specific use case actually needs, and resisting the temptation to stack every available optimization before measuring whether simpler retrieval already meets your quality bar.
