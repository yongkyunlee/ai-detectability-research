# [Feature Request] RAG troubleshooting checklist using the WFGY 16-problem map

**Issue #35360** | State: open | Created: 2026-02-20 | Updated: 2026-03-09
**Author:** onestardao
**Labels:** feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Feature Description

I would like LangChain to include an opinionated RAG troubleshooting checklist that uses the WFGY 16-problem map:

https://github.com/onestardao/WFGY/blob/main/ProblemMap/README.md

The idea is not to add a new dependency, but to document the typical failure modes in RAG systems in a way that is aligned with LangChain concepts and components.

### Use Case

I am building RAG systems with LangChain. When answers look wrong, it is often unclear whether the root cause is retrieval collapse, chunking, embedding mismatch, memory issues, or orchestration logic.

The WFGY 16-problem map is a compact taxonomy of RAG failure modes that many developers already use as a checklist. Mapping these problems to LangChain objects would make it easier for users to debug their own stacks and choose the right knobs to turn.

### Proposed Solution

A possible implementation could be:

1. A new docs page, for example "RAG failure modes and debugging", that lists the 16 WFGY problem types and shows which LangChain pieces are involved for each one. Example: No.1 hallucination and chunk drift points to retrievers, vector stores, and chunking strategy. No.5 semantic vs embedding mismatch points to embedding model choice and normalization, etc.

2. One or two short code examples that run a LangChain RAG pipeline on a small dataset and then walk through how to diagnose it with this checklist. This could reuse the existing evaluation utilities instead of adding new core APIs.

3. Optional: a light helper class or notebook in the examples folder that emits problem codes for a given run. This could stay out of the main library if you prefer to keep core small.

### Alternatives Considered

I currently rely on a mix of blog posts, my own notes, and external evaluation libraries to debug RAG systems. These are helpful, but they are not aligned with LangChain abstractions, so it is harder for new users to transfer that knowledge into concrete changes in their stack.

There are also scattered debugging tips in community content, yet there is no single, systematic taxonomy that covers the full failure space inside the official docs.

### Additional Context

The WFGY 16-problem map is MIT licensed and already used as a reference by:

- Harvard MIMS Lab ToolUniverse (LLM tools benchmark and registry)  
- University of Innsbruck Data Science Group (Rankify RAG toolkit)  
- QCRI LLM Lab Multimodal RAG Survey  

If this looks useful, I am happy to adapt the wording and contribute a PR that follows your documentation style and tone.

## Comments

**onestardao:**
Nice, that makes total sense.

Happy to take this on and turn it into a small “RAG troubleshooting checklist” page plus a tiny helper, like you sketched. I can start from your example and extend it to cover the full 16-problem map with a mapping table to the relevant LangChain components.

I’ll draft something along those lines and open a PR for review.
