---
source_url: https://blog.langchain.com/retrieval/
author: "LangChain team"
platform: blog.langchain.com
scope_notes: "Trimmed from the original 'Retrieval' blog post. Focused on the RAG concept, retriever abstraction, and vector store integration. Removed Q&A section and some introductory material to stay within 300-500 words."
---

Since ChatGPT came out, one of the most popular things that people have done is create a "ChatGPT for my data." The core limitation of ChatGPT is that it doesn't know about YOUR specific data. The primary solution to this is "Retrieval Augmented Generation." Rather than just passing a question to the language model, you first "retrieve" relevant documents and pass those alongside the question for a generation step.

Most people accomplish this with semantic search. A numerical vector (an embedding) is calculated for all documents, and those vectors are then stored in a vector database optimized for fast vector queries. Incoming queries are also embedded, and the documents closest in embedding space are retrieved.

We identified two problems with how we originally exposed these abstractions. First, there are lots of different variations on this type of retrieval. There are two different methods to query: one that optimizes for similarity and one that optimizes for maximal marginal relevance. Users want to apply metadata filters before doing semantic search. And people want to use alternative indexes, like graphs. Second, people are building retrievers outside the LangChain ecosystem — for example, OpenAI's ChatGPT Retrieval Plugin — and those should plug in easily. By making our abstractions centered around VectorDBQA we were limiting use of our chains.

### Solution

In recent Python and TypeScript releases we introduced three changes:

1. **Introduced the `Retriever` concept.** This only has one required method: `get_relevant_documents(self, query: str) -> List[Document]`. This is purposefully permissive — we don't want to limit the ways in which a retriever can be constructed.

2. **Renamed VectorDB chains to use Retrievers.** `VectorDBQA` became `RetrievalQA`. `ChatVectorDBChain` became `ConversationalRetrievalChain`. The naming convention is that `Conversational` prefix indicates the use of memory while `Chat` prefix indicates a chat model is used.

3. **Integrated non-LangChain retrievers,** starting with the ChatGPT Retrieval Plugin, demonstrating the new flexibility.

The retriever interface is deliberately minimal. Only `query: str` is required as an argument. Other parameters, including metadata filtering, should be stored on the retriever itself to permit nested usage in chains. If you were using a VectorStore before in `VectorDBQA` chain, you can create a `VectorStoreRetriever` by calling `vectorstore.as_retriever()`.

This design makes it easier for alternative retrievers to be used in chains and agents, and encourages innovation in alternative retrieval methods beyond basic semantic search.
