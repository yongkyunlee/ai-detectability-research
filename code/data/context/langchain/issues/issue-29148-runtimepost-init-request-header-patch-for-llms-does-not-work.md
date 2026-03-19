# Runtime/post init request header patch for LLMs does not work

**Issue #29148** | State: closed | Created: 2025-01-11 | Updated: 2026-03-06
**Author:** Peilun-Li
**Labels:** bug, external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

Say for example, we have user-defined `model`, and we want the same `model` object to be runnable in different environments, some environments require an additional request header for apikey auth

User-defined `model`
```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model_name="gpt-4o-mini")
```

Now imagine we receive this model object, and for it to be run in a dedicated environment, it needs additional request header
- First attempt to add `default_headers` - this doesn't work as the openai clients are already initialized at `model` object init time ([code](https://github.com/langchain-ai/langchain/blob/62074bac6049225c1547e1e9aca5621622ed8f55/libs/partners/openai/langchain_openai/llms/base.py#L166-L197)), thus any change on `default_headers` would not be reflected in openai clients used.
    ```python
    model.default_headers={"apikey": "xxx"}
    ```
- Second attempt to bind model - this doesn't work upon `model.invoke`: `TypeError: parse() got an unexpected keyword argument 'default_headers'`
    ```python
    model.bind(default_headers={"apikey:": "xxx"})
    ```

There are probably hacky ways by updating the internal openai clients directly at `model.client._client.default_headers` etc. but I don't feel that's a robust pattern as `_client` being a private object could evolve without notice. Any idea on how to better support such use case in a robust way?

### Error Message and Stack Trace (if applicable)

_No response_

### Description

I'm trying to patch additional header to a LLM model after its initialization, but couldn't find an easy and robust way. See example code for details.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP Wed Jul 17 15:10:20 UTC 2024
> Python Version:  3.9.13 (main, Aug 23 2022, 09:14:58) 
[GCC 10.2.1 20210110]

Package Information
-------------------
> langchain_core: 0.3.29
> langchain: 0.3.14
> langchain_community: 0.3.14
> langsmith: 0.2.10
> langchain_openai: 0.3.0
> langchain_text_splitters: 0.3.5

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.8.4
> async-timeout: 4.0.2
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.0
> jsonpatch: 1.33
> langsmith-pyo3: Installed. No version info available.
> numpy: 1.23.5
> openai: 1.59.6
> orjson: 3.10.14
> packaging: 24.2
> pydantic: 2.10.5
> pydantic-settings: 2.7.1
> PyYAML: 5.4.1
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.37
> tenacity: 8.2.2
> tiktoken: 0.8.0
> typing-extensions: 4.12.2

## Comments

**dosubot[bot]:**
Hi, @Peilun-Li. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- You are facing difficulties adding request headers to a user-defined LLM model in LangChain after initialization.
- Attempts to modify `default_headers` or use the `bind` method have not been successful.
- The issue remains unresolved, with no comments or developments from others.

**Next Steps:**
- Please let me know if this issue is still relevant to the latest version of the LangChain repository by commenting here.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
