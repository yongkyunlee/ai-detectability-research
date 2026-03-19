# ChatOpenAI/ChatAnthropic: request_timeout=None (default) disables SDK timeout, causing infinite hangs

**Issue #35597** | State: open | Created: 2026-03-06 | Updated: 2026-03-11
**Author:** christianboris
**Labels:** external

## Checked other resources

- [x] This is a bug, not a usage question
- [x] I added a clear and descriptive title that summarizes this issue
- [x] I used the GitHub search to find a similar question and didn't find it
- [x] I am sure that this is a bug in LangChain rather than my code
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package)
- [x] This is not related to the langchain-community package
- [x] I posted a self-contained, minimal, reproducible example

## Package

`langchain-openai`, `langchain-anthropic`

## Related Issues / PRs

- https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues/1617 (same root cause, independently discovered)
- https://github.com/langchain-ai/langchain/issues/13124 (related timeout config issues)

## Reproduction Steps / Example Code (Python)

```python
from openai._utils import is_given
from openai._types import NOT_GIVEN
import openai
import httpx

# Step 1: ChatOpenAI defaults request_timeout to None
from langchain_openai import ChatOpenAI
print(ChatOpenAI.model_fields["request_timeout"].default)  # None

# Step 2: LangChain passes timeout=None to openai.OpenAI()
# In ChatOpenAI.validate_environment() (line ~1005):
#   client_params = {"timeout": self.request_timeout, ...}
# When request_timeout=None -> openai.OpenAI(timeout=None)

# Step 3: OpenAI SDK treats None as "explicitly no timeout"
print(is_given(None))       # True  -> SDK treats this as an explicit value
print(is_given(NOT_GIVEN))  # False -> only NOT_GIVEN triggers SDK defaults

# Step 4: SDK default (600s) is bypassed
print(openai.DEFAULT_TIMEOUT)
# Timeout(connect=5.0, read=600, write=600, pool=600)
# This default is ONLY applied when timeout is NOT_GIVEN, not when it's None

# Step 5: httpx receives timeout=None -> no timeout at all
print(httpx.Timeout(None))
# Timeout(timeout=None) -> connect=None, read=None, write=None, pool=None

# Same issue exists for ChatAnthropic:
from langchain_anthropic import ChatAnthropic
print(ChatAnthropic.model_fields["default_request_timeout"].default)  # None
# Line ~291: if self.default_request_timeout is None or self.default_request_timeout > 0:
#                client_params["timeout"] = self.default_request_timeout
# -> anthropic.Anthropic(timeout=None) -> same infinite hang
```

## Error Message and Stack Trace (if applicable)

No error — the process hangs silently. When hitting a network issue or server-side delay, the HTTP request blocks indefinitely with no timeout. The only way to recover is to kill the process (`kill -9`). In `strace`, the process shows `futex_wait` — waiting forever for an HTTP response that will never arrive.

## Description

### Problem

When users create a `ChatOpenAI` or `ChatAnthropic` instance without explicitly setting `request_timeout`, the default value `None` is passed through to the underlying SDK (`openai.OpenAI(timeout=None)` / `anthropic.Anthropic(timeout=None)`).

Both the OpenAI and Anthropic SDKs distinguish between:
- **`NOT_GIVEN`** → "user didn't set this" → SDK default timeout applies (600s read)
- **`None`** → "user explicitly wants no timeout" → `httpx.Timeout(None)` → infinite

LangChain uses `None` to mean "not configured", but the SDKs interpret `None` as "explicitly disable all timeouts". This semantic mismatch causes **every default LangChain installation to run without any HTTP timeout**.

### Impact

| Provider | LangChain default | SDK default (bypassed) | Effective timeout |
|---|---|---|---|
| `ChatOpenAI` | `request_timeout=None` | 600s read | **infinite** |
| `ChatAnthropic` | `default_request_timeout=None` | 600s read | **infinite** |
| `ChatGoogleGenerativeAI` | `timeout=None` | unknown | **infinite** |

Any network glitch, load balancer timeout, or server-side hang causes the process to block forever. This is especially critical in autonomous/agentic loops where there is no human to notice and kill the process.

### Observed in production

During an autonomous agent loop using `ChatOpenAI` against a local llama-server (OpenAI-compatible API), the process hung after 38 successful LLM calls. Server-side monitoring confirmed the server had **finished generating** (EOS after 180 tokens), but the client never closed the connection. The httpx client waited indefinitely because `timeout=None`.

### Root cause in code

**`langchain-openai`** (`ChatOpenAI.validate_environment`, line ~1005):

```python
client_params: dict = {
    "timeout": self.request_timeout,  # None by default -> passed as-is
    ...
}
```

**`langchain-anthropic`** (`ChatAnthropic.validate_environment`, line ~291):

```python
if self.default_request_timeout is None or self.default_request_timeout > 0:
    client_params["timeout"] = self.default_request_timeout  # None -> passed as-is
```

### Suggested fix

When `request_timeout` is `None` (not explicitly set by the user), **omit the `timeout` key from `client_params`** so the SDK defaults apply:

For `langchain-openai`:

```python
client_params: dict = {
    "organization": self.openai_organization,
    "base_url": self.openai_api_base,
    "default_headers": self.default_headers,
    "default_query": self.default_query,
}
if self.request_timeout is not None:
    client_params["timeout"] = self.request_timeout
```

For `langchain-anthropic`:

```python
if self.default_request_timeout is not None and self.default_request_timeout > 0:
    client_params["timeout"] = self.default_request_timeout
```

This is a one-line change per provider that restores the SDK's built-in 600s timeout for all users who haven't explicitly configured a timeout.

## System Info

```
System Information
------------------
> OS:  Linux
> Python Version:  3.12.3

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langchain_anthropic: 1.3.4
> langchain_openai: 1.1.10
> langchain_google_genai: 4.2.1
> langchain_ollama: 1.0.1

Other Dependencies
------------------
> anthropic: 0.84.0
> httpx: 0.28.1
> openai: 2.24.0
> pydantic: 2.12.5
```

## Comments

**christianboris:**
Update: langchain-google-genai is actually not affected. ChatGoogleGenerativeAI correctly guards against None (line ~2765):

```
if timeout is not None:
    timeout = int(timeout * 1000)
elif self.timeout is not None:
    timeout = int(self.timeout * 1000)
```

**keenborder786:**
@Christian Boris (christianboris), instead of bypassing the value, why not just update the default timeout values to match the SDK values that are currently being bypassed? This would result in an even more minimal change.

**christianboris:**
It's an option, but it would mean LangChain will set defaults that could change upstream. In that case, LangChain would silently diverge without the user knowing. Omitting the key is how it is already done in langchain-google-genai. The above fix would align the OpenAI and Anthropic integrations with that.

**keenborder786:**
@christianboris you are right. I double-checked langchain-google-genai, and it is implemented the same way there, so let’s sync it.

**xXMrNidaXx:**
This is an important behavior to document clearly. When `request_timeout=None` is passed explicitly, it disables the SDK's default timeout and passes `None` through to the underlying HTTP client (httpx), which treats `None` as no timeout — meaning requests can hang indefinitely.

The counter-intuitive part: most users who write `request_timeout=None` intend to mean 'use the default' rather than 'disable all timeouts.'

**Workaround while this is being addressed:**

Instead of passing `None`, either:

1. Omit `request_timeout` entirely to use the SDK default:
```python
llm = ChatOpenAI(model='gpt-4o')  # uses default timeout
```

2. Or set an explicit timeout value appropriate for your use case:
```python
llm = ChatOpenAI(model='gpt-4o', request_timeout=120)  # 2 minutes
```

3. For streaming with long outputs where you genuinely need no timeout, be explicit about it:
```python
# If you intentionally want no timeout (e.g., very long streaming responses):
import httpx
llm = ChatOpenAI(
    model='gpt-4o', 
    http_client=httpx.Client(timeout=None)  # explicit intent
)
```

**Suggested fix:** In the LangChain wrapper, treat `request_timeout=None` as 'use SDK default' and only pass it through if the user explicitly opts in to no-timeout behavior via a sentinel or a dedicated parameter like `disable_timeout=True`.

**mvanhorn:**
I'd like to work on this issue. Could I be assigned?

**mvanhorn:**
Submitted a fix in #35745. The root cause is that `request_timeout` defaults to `None`, which passes `timeout=None` to the OpenAI SDK and disables its built-in 600s default. The fix uses a sentinel so that when no timeout is specified, the `timeout` parameter is omitted entirely from client construction, letting the SDK use its own default.
