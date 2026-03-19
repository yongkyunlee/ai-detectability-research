# (langchain_v1) ContextualCompressionRetriever not found

**Issue #33292** | State: closed | Created: 2025-10-06 | Updated: 2026-03-16
**Author:** amanchaudhary-95
**Labels:** external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

```python

from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_core.retrievers.contextual_compression import ContextualCompressionRetriever
```

### Error Message and Stack Trace (if applicable)

`ModuleNotFoundError: No module named 'langchain.retrievers'`

`ModuleNotFoundError: No module named 'langchain_core.retrievers.contextual_compression'; 'langchain_core.retrievers' is not a package`

### Description

As per the v1.0 alpha doc [Link](https://docs.langchain.com/oss/python/integrations/retrievers/cohere-reranker), I can't find the `ContextualCompressionRetriever` in `langchain` and `langchain_core`. 

### System Info

System Information
------------------
> OS:  Windows
> OS Version:  10.0.26100
> Python Version:  3.12.11 (main, Jun 12 2025, 12:44:17) [MSC v.1943 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 1.0.0a6
> langchain: 1.0.0a10
> langchain_community: 0.3.30
> langsmith: 0.4.32
> langchain_mongodb: 0.7.0
> langchain_ollama: 1.0.0a1
> langchain_openai: 1.0.0a3
> langchain_qdrant: 1.0.0a1
> langchain_text_splitters: 1.0.0a1
> langgraph_sdk: 0.2.9

## Comments

**eyurtsev:**
These will be available through langchain-classic

**NathanAP:**
Sorry to revive this topic. 

Just to ensure: using ContextualCompressionRetriever is "wrong"? I mean, should I use something else instead or it was moved to classic because it wont change any time soon?

**Narendra2811:**
correct import is --> from langchain_classic.retrievers import ContextualCompressionRetriever
