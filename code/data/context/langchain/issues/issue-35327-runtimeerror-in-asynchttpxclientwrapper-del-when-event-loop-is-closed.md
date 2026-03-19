# RuntimeError in _AsyncHttpxClientWrapper.__del__ when event loop is closed

**Issue #35327** | State: open | Created: 2026-02-19 | Updated: 2026-03-14
**Author:** Shivangisharma4
**Labels:** bug, langchain, anthropic, openai, external, trusted-contributor

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [x] langchain
- [x] langchain-openai
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

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
import asyncio
import gc
from langchain_openai.chat_models._client_utils import _AsyncHttpxClientWrapper

async def main():
    client = _AsyncHttpxClientWrapper(base_url="http://test", timeout=10)
    # used...
    pass

if __name__ == "__main__":
    asyncio.run(main()) 
    # Logic: loop is closed here
    gc.collect() # Trigger __del__ -> RuntimeError: no running event loop
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

Description:

I found a resource cleanup issue in langchain-openai and langchain-anthropic. 
The `_AsyncHttpxClientWrapper.__del__` method attempts to schedule an async cleanup task using `asyncio.get_running_loop()`.

However, if the object is garbage collected during interpreter shutdown or in a context where the event loop is already closed, `get_running_loop()` raises a RuntimeError. 

The current code catches this in a broad `except Exception:` block and suppresses it, meaning `self.aclose()` is never called, potentially leading to unclosed resource warnings from `httpx`

Proposed Fix: Safely check for the running loop using try/except RuntimeError and loop.is_running() before attempting to schedule the cleanup task.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.2.0: Tue Nov 18 21:08:48 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T8132
> Python Version:  3.13.0rc3 (v3.13.0rc3:fae84c70fbd, Oct  1 2024, 00:10:10) [Clang 15.0.0 (clang-1500.3.9.4)]

Package Information
-------------------
> langchain_core: 1.2.13
> langsmith: 0.7.4
> langgraph_sdk: 0.3.6

Other Dependencies
------------------
> httpx: 0.28.1

## Comments

**Shivangisharma4:**
I'm working on this issue and have some proposed changes in progress

**desiorac:**
The async event loop issue is a good reminder of a broader concern: robustness of critical paths in AI systems.

Regulated AI systems (under EU AI Act, GDPR, etc.) need guaranteed cleanup and audit logging—even under unusual shutdown scenarios. When event loops close unexpectedly, you lose the audit trail.

A few patterns that help:
1. Graceful shutdown handlers that flush audit logs first
2. Non-blocking audit writes (to avoid blocking the main event loop)
3. Persistent event stores (not in-memory)

If building production AI systems, consider adding compliance-aware shutdown handlers that ensure no audit events are lost. We have open-source tooling for this: https://arkforge.fr/mcp

**desiorac:**
Runtime stability is critical for compliance systems. Proper cleanup is essential for audit trails. Have you considered making cleanup more observable for compliance logging?

**alvinttang:**
Hi, I'd like to be assigned to this issue. I have a fix ready in PR #35878 that adds `loop.is_closed()` checks and narrows the exception handling in `__del__`. Happy to address any feedback.
