# Add ability to steer an agent in the create_agent flow

**Issue #35842** | State: open | Created: 2026-03-13 | Updated: 2026-03-13
**Author:** jackirvine97
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

The ability to steer an agent mid multi-turn execution is becoming prevalent in leading multi-turn tools (claude code, GH copilot)

Could this be something that is considered in the `create_aegnt` wrapper?

### Use Case

Suited to all longer time horizon use cases

### Proposed Solution

- perhaps some form of method "push steer" that queues steer requests, and injects them as "user" messages into the context state graph in between turns?
- I appreciate this might be complex and need async / thread management!

### Alternatives Considered

_No response_

### Additional Context

_No response_
