# Add Cala verified knowledge retriever to integrations docs

**Issue #36071** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** lancelot2
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
- [ ] Other / not sure / general

### Feature Description

## Feature request

### Motivation

Cala (https://cala.ai) is a verified knowledge graph API for AI agents. 
It returns structured, source-cited, traceable facts — not raw web scrapes — 
making it well-suited for production RAG pipelines that require auditable, 
hallucination-resistant retrieval.

A third-party LangChain integration package (`langchain-cala`) is already 
published on PyPI, implementing `CalaRetriever` as a native `BaseRetriever`.

### Proposed change

Add a provider documentation page:
`docs/docs/integrations/providers/cala.mdx`

The file follows the existing provider page format and includes:
- A short description of Cala
- Installation instructions (`pip install langchain-cala`)
- Usage examples for search, structured query, and RAG chain modes

### Links

- PyPI: https://pypi.org/project/langchain-cala/
- GitHub: https://github.com/lancelot2/langchain-cala
- PR ready: #35958

### Use Case

Developers building RAG pipelines with LangChain currently rely on web-search 
retrievers (Tavily, Exa) that return unverified, unstructured content. This 
forces them to add extra validation layers or accept hallucination risk in 
production.

Cala solves this directly: it returns verified, source-cited, entity-structured 
facts via a simple API, with full traceability compatible with EU AI Act 
Article 13 requirements.

A native CalaRetriever in the LangChain integrations hub means any developer 
building a knowledge-grounded agent can do `pip install langchain-cala` and 
drop it into their existing chain — no scraping, no validation overhead, no 
hallucination risk from stale web content.

### Proposed Solution

_No response_

### Alternatives Considered

_No response_

### Additional Context

_No response_
