# feat(anthropic): add http_client and http_async_client fields to ChatAnthropic (parity with ChatOpenAI)

**Issue #36056** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** keenborder786
**Labels:** feature request, anthropic

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

ChatOpenAI already supports passing a custom httpx.Client and httpx.AsyncClient directly via http_client and http_async_client fields (lines 763–775 in chat_models/base.py). This is used in practice for SSL customization, custom proxies, and corporate network environments.

ChatAnthropic has no equivalent. It always builds its own httpx client internally via _get_default_httpx_client(), and there is no way to inject a pre-configured one. The Anthropic SDK itself does support http_client as a constructor argument — ChatAnthropic just never exposes it.

### Use Case

- Disable SSL verification in dev/test environments: httpx.Client(verify=False)
- Use a corporate CA bundle: httpx.Client(verify="/etc/ssl/certs/corporate-ca.crt")
- Custom transport layers, timeouts per-request, or mTLS certificates
- Environments where global SSL settings cannot be changed

### Proposed Solution

```python

import httpx
from langchain_anthropic import ChatAnthropic

# Custom SSL CA bundle
llm = ChatAnthropic(
    model="claude-opus-4-5",
    http_client=httpx.Client(verify="/etc/ssl/certs/my-ca.crt"),
    http_async_client=httpx.AsyncClient(verify="/etc/ssl/certs/my-ca.crt"),
)

# Disable SSL verification
llm = ChatAnthropic(
    model="claude-opus-4-5",
    http_client=httpx.Client(verify=False),
    http_async_client=httpx.AsyncClient(verify=False),
)

```

What needs to change in the code:

Add two new fields to ChatAnthropic in chat_models.py (same pattern as ChatOpenAI):

```python
http_client: Any | None = Field(default=None, exclude=True)
"""Optional `httpx.Client` for sync invocations."""
http_async_client: Any | None = Field(default=None, exclude=True)
"""Optional `httpx.AsyncClient` for async invocations."""
In the _client cached property, use the user-supplied client if provided, otherwise fall back to the existing _get_default_httpx_client():
@cached_property
def _client(self) -> anthropic.Anthropic:
    http_client = self.http_client or _get_default_httpx_client(**http_client_params)
    return anthropic.Anthropic(**client_params, http_client=http_client)
```
Same for _async_client with http_async_client.

### Alternatives Considered

Users have to subclass ChatAnthropic and override the _client and _async_client cached properties, which is fragile and not documented anywhere.

### Additional Context

Related: #35977 

Please assign this so I can implement the above plan.
