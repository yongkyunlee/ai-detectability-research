# Support Anthropic Claude automatic caching in ChatOpenRouter

**Issue #35920** | State: open | Created: 2026-03-15 | Updated: 2026-03-15
**Author:** clemp6r
**Labels:** feature request, external, openrouter

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
- [x] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

We would need the ability to enable Anthropic Claude automatic caching (at request top-level) using the openrouter integration (`ChatOpenRouter`).

### Use Case

We need that for costs optimization when using Claude with OpenRouter. Automatic caching is recommended for long conversations.

### Proposed Solution

_No response_

### Alternatives Considered

I tried this:
```python
ChatOpenRouter(
    model="anthropic/claude-haiku-4.5",
    model_kwargs={"cache_control":{"type": "ephemeral"}}
)
```

But then got:
```
TypeError: Chat.send() got an unexpected keyword argument 'cache_control'
```

There might be a limitation in the underlying ˋopenrouterˋ library.

### Additional Context

https://openrouter.ai/docs/guides/best-practices/prompt-caching#anthropic-claude
> Automatic caching: Add a single cache_control field at the top level of your request. The system automatically applies the cache breakpoint to the last cacheable block and advances it forward as conversations grow. Best for multi-turn conversations.

## Comments

**TamarAzriel:**
Hi! I've been looking into this and I have a working implementation that allows cache_control to be passed correctly to OpenRouter. I've also verified it with unit tests to ensure it doesn't break existing model_kwargs logic. I'd love to submit a PR for review; could you please assign this to me?
