# Building RAG Pipelines with LangChain Retrievers and Vector Stores

RAG isn't new anymore. But most teams still get it wrong the first time around, and LangChain's abstraction layers are part of the reason why. I've spent enough time reading through the framework's source, its GitHub issues, and the community's war stories to have opinions about how to wire up a retrieval-augmented generation pipeline that doesn't fall apart under real traffic. Here's what I think matters.

## What RAG Actually Solves

A language model on its own will confidently tell you things that aren't true. That's the core problem. RAG fixes it by fetching relevant documents from a knowledge base before asking the model to synthesize an answer. The model stops guessing. It starts citing.

The difference is measurable. Teams building legal document search have reported that a generic LLM gave generic advice, while a RAG-enabled system cited specific acts, referenced 5km no-fly zones, and linked directly to permit pages. Grounding matters. And the pipeline that handles the grounding - chunking, embedding, storing, retrieving, synthesizing - is what we're here to talk about.

## Chunking: The Decision That Haunts You Later

Before anything touches a vector store, your documents need to be split into chunks. LangChain's `langchain-text-splitters` package (version 0.3.0 as of this writing) provides a wide range of strategies: character-based, recursive, semantic, HTML-aware, Markdown-aware, and language-specific splitters for Python, JSX, and LaTeX, among others.

The one you'll reach for most often is `RecursiveCharacterTextSplitter`. It tries to split on natural boundaries - paragraphs, then sentences, then words - before falling back to raw character counts. Two parameters control everything: `chunk_size` and `chunk_overlap`. A typical production setup might look like 1000-character chunks with 100-character overlap, though I've seen teams processing 594 PDFs across 33,000 pages settle on 150 tokens per chunk with 50 tokens of overlap.

The overlap matters more than people think. Without it, a critical sentence that straddles two chunks gets lost on both sides. Too much overlap and you're burning embedding compute on redundant text. There's no universal right answer, but start with 10% overlap relative to chunk size and adjust based on your retrieval accuracy.

Don't sleep on the specialized splitters either. If you're processing Markdown documentation, the `MarkdownTextSplitter` preserves header hierarchy. For codebases, the Python-aware splitter respects function and class boundaries. Choosing the wrong splitter for your content type is one of the most common mistakes, and it silently degrades your entire pipeline because the embeddings look fine - they're just embeddings of incoherent fragments.

## Vector Stores: Picking Your Backend

LangChain supports a frankly absurd number of vector store backends. Chroma, FAISS, Pinecone, Qdrant, Weaviate, Azure CosmosDB - the list keeps growing. Each has trade-offs that matter at different scales and for different access patterns.

Chroma is the easiest to start with. It runs in-memory, requires no infrastructure, and the integration is straightforward. But there's a subtle behavior that's bitten multiple teams: in-memory Chroma instances persist data across iterations within a single Python process. If you're running evaluation loops or batch experiments, stale vectors from previous runs will contaminate your results. The workaround is to call `chromadb.reset()` or create a new collection for each iteration. This isn't a bug exactly - it's a design choice around shared in-memory storage - but it violates the principle of least surprise.

Chroma is simpler to run locally, but Pinecone gives you managed infrastructure with filtering and scaling out of the box. That's the core trade-off. If your team doesn't want to operate vector database infrastructure and your dataset fits Pinecone's pricing model, it's a reasonable choice. If you need full control over your data locality or you're running air-gapped, FAISS with a persistence layer is probably your answer.

Qdrant deserves a mention for its filtering capabilities, though watch out for import path issues in the documentation. Some older LangChain docs reference `from qdrant_client.http import models` when the correct import is `from qdrant_client import models`. This kind of documentation lag behind implementation changes is a recurring theme across the LangChain ecosystem.

Regardless of which store you choose, the pattern for loading documents into it looks roughly the same. You split your documents, choose an embedding model, and call `from_documents`:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)
texts = text_splitter.split_documents(retrieved_documents)

embeddings = OpenAIEmbeddings(max_retries=1000)
docsearch = Chroma.from_documents(texts, embeddings)
```

That `max_retries=1000` on the embeddings isn't paranoia - it's practical. Embedding API rate limits will bite you on large ingestion jobs, and you'd rather retry than lose your place in a multi-hour pipeline.

## Retrievers: Where the Real Engineering Happens

A vector store holds your data. A retriever decides what comes back when someone asks a question. LangChain cleanly separates these concerns, and the retriever layer is where most of the interesting engineering decisions live.

The simplest retriever is `.as_retriever()` called on any vector store. It returns the top-k most similar documents by embedding distance. You control k through `search_kwargs`:

```python
doc_retriever = docsearch.as_retriever(search_kwargs={"k": 5})
```

This works fine for straightforward queries. But real user questions are messy. They're ambiguous, compound, and sometimes contradict themselves. That's where multi-query retrieval comes in. The idea is to break a user's question into multiple sub-queries - essentially generating keyword variants - and retrieving against each one separately before merging the results. Coverage improves dramatically because you're no longer dependent on a single embedding similarity score.

Hybrid search combines keyword matching with vector similarity. Some backends like Pinecone support this natively through their `PineconeHybridSearchRetriever`. But be warned: the async story isn't complete. The hybrid search retriever is missing its `_aget_relevant_documents` implementation, which means you can't use `ainvoke` on it. If your application is async-first - and most modern Python web services are - this is a real limitation. You'll need to wrap the synchronous call or use a different retriever.

Contextual compression is another retriever strategy worth knowing about. It runs a secondary model over retrieved documents to extract only the passages relevant to the query. This reduces noise in the context window and can meaningfully improve answer quality, though it adds latency and cost from the extra model call.

And if you're building an agent that needs retrieval as one of several tools, `create_retriever_tool` from `langchain_core.tools` wraps a retriever into something an agent can call:

```python
from langchain_core.tools import create_retriever_tool

retriever_tool = create_retriever_tool(
    retriever,
    name="sql_get_similar_examples",
    description=tool_description
)
```

This bridges the gap between RAG and agentic workflows, letting the model decide when to retrieve rather than always retrieving.

## Memory and Conversational RAG

Adding conversation history to a RAG pipeline introduces real complexity. LangChain's `ConversationBufferMemory` is the most common choice, and integrating it with a retrieval chain requires careful configuration:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key='chat_history',
    return_messages=True,
    output_key='answer'
)
```

That `output_key='answer'` is critical. If you're using `ConversationalRetrievalChain` with `return_source_documents=True`, the chain produces multiple output keys. Without specifying which one the memory should track, you'll get an error. This particular incompatibility has tripped up enough developers to generate multiple GitHub issues.

Persistent memory across sessions is even harder. Teams building customer support agents have explored confidence decay - downweighting old preferences over time - and hierarchical memory structures where user-level preferences override team-level defaults. We're past LangChain's built-in abstractions at that point, but the retriever pattern still applies: store memories as documents, retrieve relevant ones based on the current conversation context.

## The Migration Reality

LangChain's API surface has been changing rapidly. The `initialize_agent` function is deprecated in favor of `langgraph.prebuilt.create_react_agent`. Classic chain patterns are giving way to LangGraph's graph-based orchestration. If you're starting a new project today, build on LangGraph from the start. Migrating later isn't fun.

The package structure itself has fragmented. Core abstractions live in `langchain-core` (0.3.15). The main `langchain` package (0.3.3) is increasingly a thin wrapper. Partner integrations like `langchain-openai` (0.2.2) and `langchain-pinecone` (0.2.0) ship on their own release cycles. This fragmentation means version pinning matters. A lot.

So run `uv sync --all-groups` if you're using the `uv` package manager (which the LangChain team themselves use for development), and pin your versions explicitly. Don't let a minor bump in `langchain-core` break your retriever because a method signature changed.

## What I'd Actually Recommend

Start with `RecursiveCharacterTextSplitter`, Chroma for local development, and a basic `.as_retriever()` call. Get your pipeline working end to end. Measure retrieval quality - are the right chunks coming back for your test queries? Then upgrade the pieces that matter.

Swap Chroma for Pinecone or Qdrant when you need persistence and scale. Add multi-query retrieval when single-query recall isn't good enough. Layer in contextual compression when your context window is filling up with irrelevant passages. And don't add conversational memory until you actually need conversation - it's a complexity multiplier.

The learning curve is steep. Embeddings, chunking strategies, retriever types, LCEL syntax, vector database operations - there's a lot to absorb. But the retriever abstraction is genuinely good engineering. It separates what you're searching from how you're searching, and that separation lets you iterate on each piece independently. Build the simple version first. Make it correct. Then make it fast.
