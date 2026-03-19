# langchain_anthropic does not support set verify=False and cert filepath

**Issue #35977** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** liaowen9527
**Labels:** feature request, anthropic, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain-anthropic

### Feature Description

Here, it does not read the verify attribute from the input parameters.

### Use Case

Some environments may require a custom certificate file. I don't want to change the global certificate path, so I want the option to either disable verification or specify a custom certificate path.

## Comments

**keenborder786:**
@liaowen9527 
Can't you pass the custom certificate or disable verification by passing the http client directly:
```python
import httpx
from langchain_anthropic import ChatAnthropic
# Disable SSL verification
http_client = httpx.Client(verify=False)
llm = ChatAnthropic(
    model="claude-opus-4-5",
    http_client=http_client,
)

# Or use a custom CA certificate
http_client = httpx.Client(verify="/path/to/your/ca-bundle.crt")
llm = ChatAnthropic(
    model="claude-opus-4-5",
    http_client=http_client,
)

```

**liaowen9527:**
@keenborder786  I want to use this method, but ChatAnthropic does not support setting an HTTP client.

**keenborder786:**
@liaowen9527 Oh yes, my bad. Did not realise ChatAnthropic, unlike ChatOpenAI does not support custom HTTP client.  @liaowen9527 that will be an interesting feature to have and support, so users can pass a custom HTTP client rather than relying only on the internal one.

But until then, you can make use of the following (I have double checked and it works!!!):

```python

import httpx
import anthropic
from functools import cached_property
from langchain_anthropic import ChatAnthropic

class ChatAnthropicSSL(ChatAnthropic):
    """ChatAnthropic with custom SSL verification support."""

    ssl_verify: bool | str = True
    """Pass False to disable SSL verification, or a path string to a CA bundle."""

    model_config = {"arbitrary_types_allowed": True}

    @cached_property
    def _client(self) -> anthropic.Anthropic:
        return anthropic.Anthropic(
            **self._client_params,
            http_client=httpx.Client(verify=self.ssl_verify),
        )

    @cached_property
    def _async_client(self) -> anthropic.AsyncAnthropic:
        return anthropic.AsyncAnthropic(
            **self._client_params,
            http_client=httpx.AsyncClient(verify=self.ssl_verify),
        )

# Disable SSL verification entirely
llm = ChatAnthropicSSL(model="claude-opus-4-5", ssl_verify=False)

# Or point to a custom CA bundle
llm = ChatAnthropicSSL(model="claude-opus-4-5", ssl_verify="/etc/ssl/certs/my-ca.crt")

# Use normally
response = llm.invoke("Hello!")

```
