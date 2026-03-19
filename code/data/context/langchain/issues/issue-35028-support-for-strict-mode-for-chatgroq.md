# Support for strict mode for ChatGroq

**Issue #35028** | State: closed | Created: 2026-02-05 | Updated: 2026-03-05
**Author:** keenborder786
**Labels:** feature request, groq, external

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
- [x] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

I would like to have strict support for `ChatGroq` as I want to use `ChatGroq` structured_output in a production-grade environment. 

### Use Case

The doc suggests `https://console.groq.com/docs/structured-outputs`, that it is important to have `strict=True` for production case uses with `json_schema`. But currently, that is not supported in ChatGroq. In order to use `ChatGroq` in production grade setting, I would like to have `strict` support.

### Proposed Solution

I already have already created a relevant PR following the given docs ``https://console.groq.com/docs/structured-outputs` to support strict mode for the models supported.

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**keenborder786:**
+1 for this please, really need this feature, right now using a custom version for my production application but ideally want to stick to Langchain.
