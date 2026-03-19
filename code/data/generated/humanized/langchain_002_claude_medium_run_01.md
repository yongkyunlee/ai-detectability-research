# Building RAG Pipelines with LangChain Retrievers and Vector Stores

Retrieval-augmented generation has pretty much become the default way to ground large language models in domain-specific knowledge. Instead of fine-tuning a model on your data, you fetch relevant documents at query time and pass them along as context. LangChain gives you a layered set of abstractions that make assembling this pipeline fairly painless, and (more to the point) that let you customize things when the defaults don't cut it.

## The Core Abstractions

Two interfaces sit at the foundation of any LangChain RAG pipeline: `VectorStore` and `BaseRetriever`.

`VectorStore` handles storing and looking up document embeddings. You load documents, embed them through something like OpenAI's `text-embedding-3-small` or a local sentence-transformer, and the vector store indexes those embeddings for similarity search. LangChain supports a bunch of backends here: Chroma for lightweight local use, FAISS for high-performance in-memory search, Pinecone and Qdrant for managed cloud deployments, pgvector if your team is already invested in PostgreSQL, and several others.

`BaseRetriever` is simpler. It takes a string query, returns a list of `Document` objects. Every retriever implements `_get_relevant_documents`, with an optional async counterpart. The key design decision worth understanding is that vector stores can be converted into retrievers through `.as_retriever()`, which wraps the store in a `VectorStoreRetriever` conforming to the standard interface. This separation matters. Not every retrieval strategy depends on vector similarity; keyword search, graph lookups, and API calls all fit the same `BaseRetriever` contract.

Both abstractions implement LangChain's `Runnable` interface, so they compose naturally using the expression language. A typical chain pipes a retriever's output into a prompt template, then into an LLM:

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

Plain similarity search is the default retrieval mode, but it's not always what you want. When your top results cluster around the same subtopic, you lose breadth. Maximal marginal relevance (MMR) addresses this by balancing similarity to the query against diversity among returned documents. Most vector store implementations support it as a search type parameter.

Then there's hybrid search. For domains where exact keyword matching matters alongside semantic understanding, you can combine BM25-style term matching with vector similarity. Pinecone's hybrid search retriever implements this pattern, though the async pathway for hybrid retrieval has been an open gap, something to keep in mind if your application serves concurrent requests.

## Beyond Basic Retrieval

Simple similarity search starts to break down when your chunking strategy creates tension between embedding quality and answer completeness. Small chunks embed well but lack surrounding context; large chunks preserve context but dilute the embedding signal. The `ParentDocumentRetriever` resolves this with two levels of granularity. It indexes small child chunks for accurate matching, then returns the larger parent document containing the match. You'll need both a vector store and a separate document store for this, plus two text splitters configured at different sizes.

Conversational applications hit a different problem. Queries often reference prior turns, so "what about the second option?" means nothing without history. A history-aware retriever uses an LLM to reformulate those queries into standalone search terms before hitting the vector store. Yes, this adds a round-trip to the language model. But it dramatically improves retrieval accuracy in multi-turn dialogues, and I think in most conversational use cases the latency tradeoff is worth it.

When a single retriever isn't enough, LangChain supports ensemble approaches through `MergerRetriever`, which combines results from multiple sources. You might pair a vector retriever with a keyword-based one, or merge results from different document collections.

## Practical Pitfalls

Chroma's in-memory mode can surprise you. Even with `persist_directory=None`, the in-process storage may retain state across iterations within the same Python session. If you're running experiments in a loop, explicitly resetting the client prevents stale data from contaminating your results. Honestly this bit us more than once before we figured out what was happening.

Metadata filtering is another area where implementations diverge. Some backends handle only string and list types in filter conditions, silently failing or throwing unexpected errors on integers or floats. Test your specific filter patterns against your chosen backend early. You don't want to discover this during a demo.

Import paths have shifted a lot across LangChain versions. The `create_retriever_tool` function (which wraps a retriever as an agent-usable tool) has migrated from `langchain.tools.retriever` to `langchain_community` and now lives in `langchain_core.tools`. Features like `ContextualCompressionRetriever` have moved to the `langchain_classic` package. The docs don't always make this obvious. Pin your dependency versions and check current documentation before starting a new project; it'll save you from following outdated tutorials down a dead end.

## Security in RAG Systems

Retrieved documents introduce an attack surface that pure LLM applications don't have. If an adversary can influence content in your document store, they can embed instructions the model may follow. This is called indirect prompt injection. A poisoned document might tell the model to ignore its system prompt or exfiltrate data from the conversation.

LangChain mitigates this partially by wrapping retrieved context in XML delimiters and prepending instructions to ignore embedded directives. But those instruction-level defenses aren't bulletproof. Production deployments should layer on additional protections: scanning retrieved documents for injection patterns, validating outputs for sensitive data leakage, and monitoring retrieval patterns for anomalies.

## Making the Right Trade-offs

Your choice of vector store shapes operational constraints pretty directly. In-memory options like FAISS are fast and simple but don't persist. Chroma with a directory works well for prototyping and moderate-scale applications. Cloud-hosted services like Pinecone scale horizontally but introduce vendor dependency and network latency. Self-managed deployments of Qdrant or Milvus give you control at the cost of operational overhead.

Each retriever wrapper you add (history-aware reformulation, parent document lookup, compression) introduces latency. For interactive applications, profile the full chain end-to-end and make sure async support works throughout the stack. Bottlenecks that only appear under load are the worst kind.

LangChain gives you the building blocks. The real engineering challenge is knowing which ones your use case actually needs, and resisting the urge to stack every available optimization before you've measured whether simpler retrieval already meets your quality bar.
