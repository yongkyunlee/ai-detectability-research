# feat(anthropic): support custom httpx client for mTLS and certificate-based authentication

**Issue #35843** | State: open | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** YNNEKUW
**Labels:** feature request, anthropic, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [x] langchain-anthropic
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

I would like to add `http_client` and `http_async_client` optional fields to the `ChatAnthropic` class. These fields will allow users to provide their own pre-configured `httpx.Client` or `httpx.AsyncClient` instances, which will be passed directly to the underlying Anthropic SDK.

### Use Case

I'm trying to build an application that requires **mTLS (mutual TLS)** or **certificate-based authentication** to connect to an Anthropic API proxy in a highly secure enterprise environment.

Currently, I have to work around this by manually monkey-patching or wrapping the internal client creation, which is fragile.

This feature would help users to easily configure security-related transport settings that are only accessible through a custom `httpx` client.

### Proposed Solution

I think this could be implemented by adding two optional fields to `ChatAnthropic`:

```python
http_client: Any = Field(default=None, exclude=True)
http_async_client: Any = Field(default=None, exclude=True)
```

In the client initialization logic, if these fields are provided, they should be passed to the `anthropic.Anthropic` and `anthropic.AsyncAnthropic` constructors instead of letting the SDK create default clients.

### Alternatives Considered

_No response_

### Additional Context

- **Related issues**: N/A

- **Similar features in other libraries**: Many other LangChain partner packages (like `langchain-openai`) already support custom HTTP clients for similar reasons.

- **Additional context**: I have already implemented this feature with unit tests and am ready to submit a PR as soon as this issue is assigned or acknowledged.

*This request was developed with the assistance of Claude Code (Anthropic).*

## Comments

**YNNEKUW:**
Hello maintainers,

I have already implemented this feature and have a PR ready. Could you please assign this issue to me so the PR can be reopened? Thanks!

**bitloi:**
@ccurme @mdrxy Can you assign me the issue? I am very interested in this issue.
