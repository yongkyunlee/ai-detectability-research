# Multiple SQL schema support

**Issue #35947** | State: closed | Created: 2026-03-16 | Updated: 2026-03-16
**Author:** k290
**Labels:** langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
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

This is a re-open of https://github.com/langchain-ai/langchain/issues/3036
It was closed by the bot a long time ago as stale, but since then there has been high demand

Users would like to query via SQLDatabaseSequentialChain or SQLDatabaseChain involving multiple tables living in multiple different schemas. 

### Use Case

Some databases organize related tables across multiple schemas (e.g., `sales`, `crm`, `billing`) while queries frequently need to join data across them. When using `SQLDatabase.from_uri`, only a single schema can currently be reflected, which prevents the LLM from seeing or reasoning about tables in other schemas. This makes it difficult to use LangChain with real-world databases where multiple schemas are common. 

### Proposed Solution

Maintainers in https://github.com/langchain-ai/langchain/issues/3036 mentioned they have already looked at the code and it should be possible

### Alternatives Considered

A workaround exists by setting PostgreSQL’s `search_path` in the connection string, it effectively flattens multiple schemas into a single namespace.  [This hasn't been tested on other flavours of sql. ]

Nonetheless, this loses schema context and creates ambiguity when different schemas contain tables with the same name, since only the first match in the search path is reliably accessible. It also relies on database-specific behavior and prevents the LLM from generating fully qualified table references (e.g., `sales.orders`). Native support for multiple schemas in `from_uri` would allow the database wrapper to expose schema-qualified tables directly, enabling clearer prompts, avoiding naming collisions, and supporting more realistic database structures without relying on connection-level workarounds.

### Additional Context

_No response_

## Comments

**keenborder786:**
@k290 SQLDatabaseChain is now part of https://github.com/langchain-ai/langchain-experimental, so will recommend you close the issue here and reopen it in the above repo.

**k290:**
Got it. Will do
