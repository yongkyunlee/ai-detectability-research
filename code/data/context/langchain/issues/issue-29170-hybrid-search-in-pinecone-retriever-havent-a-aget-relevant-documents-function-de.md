# Hybrid search in pinecone retriever haven't a _aget_relevant_documents function defined, which is mandatory in async setup (upon 'ainvoke' calls on retrievers)

**Issue #29170** | State: closed | Created: 2025-01-13 | Updated: 2026-03-06
**Author:** festnoze
**Labels:** bug, investigate, external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code
```python
from langchain_community.retrievers import PineconeHybridSearchRetriever

retriever = PineconeHybridSearchRetriever(...)
await retriever.ainvoke(query)
```
### Error Message and Stack Trace (if applicable)

not applicable

### Description

**"_aget_relevant_documents"** function is missing from the hybrid search for pinecone retriever (class name: **'PineconeHybridSearchRetriever'** in 'langchain_community.retrievers'). 
**This method is mandatory in an async setup** because as seen it the parent class **BaseRetriever**, a call to _ainvoke_ actually calls the  retriever __aget_relevant_documents_ method.
Fix is simple though :  simply add a "_aget_relevant_documents" method to PineconeHybridSearchRetriever class with the same code that the one into _get_relevant_documents, or even better adapt the code to use the "await" keyword to free the system while processing retrieval.

### System Info

System Information
------------------
> OS:  Windows
> OS Version:  10.0.19045
> Python Version:  3.12.1 (tags/v3.12.1:2305ca5, Dec  7 2023, 22:03:25) [MSC v.1937 64 bit (AMD64)]
> VS code 

Package Information
-------------------
> langchain_core: 0.3.15
> langchain: 0.3.3
> langchain_community: 0.3.2
> langsmith: 0.1.136
> langchain_anthropic: 0.2.4
> langchain_chroma: 0.1.4
> langchain_cli: 0.0.35
> langchain_experimental: 0.3.2
> langchain_groq: 0.2.0
> langchain_ollama: 0.2.0
> langchain_openai: 0.2.2
> langchain_pinecone: 0.2.0
> langchain_qdrant: 0.2.0
> langchain_text_splitters: 0.3.0
> langgraph: 0.2.38
> langserve: 0.3.0

## Comments

**dosubot[bot]:**
Hi, @festnoze. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- You reported a missing "_aget_relevant_documents" function in the PineconeHybridSearchRetriever class.
- This function is crucial for supporting asynchronous operations.
- You suggested adding this method or modifying "_get_relevant_documents" to support async with "await".
- No comments or developments from other users or maintainers have been made.

**Next Steps**
- Please let me know if this issue is still relevant to the latest version of the LangChain repository by commenting here.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
