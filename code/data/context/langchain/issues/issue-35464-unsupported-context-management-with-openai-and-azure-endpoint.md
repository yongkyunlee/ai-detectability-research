# Unsupported context management with openai and azure endpoint

**Issue #35464** | State: open | Created: 2026-02-27 | Updated: 2026-03-18
**Author:** Djkmarco
**Labels:** bug, langchain, openai, external

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

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
from langchain_openai import ChatOpenAI

try:
    _llm = ChatOpenAI(
        model=config["model_name"],
        base_url=f"{config['azure_endpoint']}/openai/v1/",
        api_key=config["azure_api_key"],
        reasoning={
        "effort": "high",  # 'low', 'medium', or 'high'
        "summary": "auto",  # 'detailed', 'auto', or None
        },
        use_previous_response_id=True,
        use_responses_api=True,
        context_management=[{"type": "compaction", "compact_threshold": 100_000}],
    )

    response = _llm.invoke([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "tell me the best way to optimize a function in python?"}])

except Exception as e:
    print(f"Error: {e}")

```

### Error Message and Stack Trace (if applicable)

```shell
Error: Error code: 400 - {'error': {'message': 'compact_threshold is not enabled.', 'type': 'invalid_request_error', 'param': 'compact_threshold', 'code': 'unsupported_parameter'}}
```

### Description

Trying to use azure endpoint with context_management=[{"type": "compaction", "compact_threshold": 100_000}] returns a compact_threshold is not enabled error

### System Info

System Information
------------------
> OS:  Windows
> OS Version:  10.0.26200
> Python Version:  3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 1.2.16
> langchain: 1.2.10
> langsmith: 0.7.7
> langchain_openai: 1.1.10
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.9
> openai: 2.24.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pytest: 8.4.2
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> xxhash: 3.6.0

## Comments

**keenborder786:**
@Marco Franzoi (Djkmarco)
The error you're getting is because Azure OpenAI does not support the compact_threshold parameter in context_management. 

This is an OpenAI-native Responses API feature that Azure has not yet enabled.
If you look at the Azure OpenAI Responses [API](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses?tabs=python-key) documentation, there are two key things to note:

1.  No mention of context_management: The Azure docs do not document the context_management parameter at all. The automatic server-side compaction triggered by compact_threshold (as described in the OpenAI compaction guide) is not available on Azure.

2.  Explicit compaction has limited support: At the bottom of the Azure docs, under the "Not currently supported" section, it explicitly states.

**aayushbaluni:**
Hi, I'd like to work on this issue. Could I be assigned? I have a fix ready in PR #36022 that skips `context_management` when the base URL points to Azure.

**fairchildadrian9-create:**
Any update on this

On Tue, Mar 17, 2026, 11:28 AM Ayush Baluni ***@***.***>
wrote:

> *aayushbaluni* left a comment (langchain-ai/langchain#35464)
> 
>
> Hi, I'd like to work on this issue. Could I be assigned? I have a fix
> ready in PR #36022 
> that skips context_management when the base URL points to Azure.
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
