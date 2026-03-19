# core: `_configure_hooks` variable accumulates with each call to `get_usage_metadata_callback`

**Issue #32300** | State: open | Created: 2025-07-29 | Updated: 2026-03-18
**Author:** optionals
**Labels:** bug, investigate, core, external

### Checked other resources

- [x] This is a bug, not a usage question. For questions, please use the LangChain Forum (https://forum.langchain.com/).
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

```python

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import get_usage_metadata_callback

llm_1 = init_chat_model(model="openai:gpt-4o-mini")
llm_2 = init_chat_model(model="anthropic:claude-3-5-haiku-latest")

with get_usage_metadata_callback() as cb:
    llm_1.invoke("Hello")
    llm_2.invoke("Hello")
    print(cb.usage_metadata)
```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

The `get_usage_metadata_callback` context manager, introduced in `langchain_core.callbacks`, appears to have a design flaw that leads to the continuous growth of the `_configure_hooks` global variable.

Specifically, inside `get_usage_metadata_callback`, the line `register_configure_hook(usage_metadata_callback_var, inheritable=True)` is executed every time the context manager is entered. The `register_configure_hook` function, in turn, appends a tuple containing the `usage_metadata_callback_var` to the global `_configure_hooks` list.

This means that each subsequent call to `get_usage_metadata_callback()` adds another entry to `_configure_hooks`. Over the lifetime of an application that frequently uses this context manager, `_configure_hooks` will grow indefinitely, potentially leading to:

- **Memory Leakage:** The global list will consume more and more memory.
- **Performance Degradation:** iterate over or process `_configure_hooks` in langchain_core.callbacks.manager._configure become slower as the list grows larger .
- **Unexpected Behavior:** While `register_configure_hook` seems to only add to the list, having duplicate or redundant entries for the same context variable might lead to unforeseen side effects in how callbacks are managed or configured.

### Potential Solutions

1. **Restrict Usage to Evaluation Scenarios:** Add a **warning log** within `get_usage_metadata_callback` to indicate that it is intended for use primarily in **evaluation scenarios** (e.g., one-off runs, testing scripts) and not for long-running production applications. This would clarify its intended scope and alert users to the potential for `_configure_hooks` accumulation if used inappropriately.
2. **Make `usage_metadata_callback_var` Global and Register Once:**
   - Remove the `name` parameter from `get_usage_metadata_callback`, as custom naming contributes to multiple `ContextVar` instances being registered.
   - Declare `usage_metadata_callback_var` as a **global variable**.
   - Move the `register_configure_hook` call for `usage_metadata_callback_var` to the **top level** (e.g., module initialization). This ensures it's registered only once when the module is loaded, preventing redundant appends to `_configure_hooks`

3. ...

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.5.0: Tue Apr 22 19:53:26 PDT 2025; root:xnu-11417.121.6~2/RELEASE_X86_64
> Python Version:  3.12.11 (main, Jun  3 2025, 15:41:47) [Clang 17.0.0 (clang-1700.0.13.3)]

Package Information
-------------------
> langchain_core: 0.3.72
> langchain: 0.3.27
> langchain_community: 0.3.27
> langsmith: 0.4.8
> langchain_mcp_adapters: 0.1.9
> langchain_openai: 0.3.28
> langchain_postgres: 0.0.15
> langchain_qdrant: 0.2.0
> langchain_tavily: 0.2.11
> langchain_text_splitters: 0.3.9
> langgraph_api: 0.2.109
> langgraph_cli: 0.3.6
> langgraph_license: Installed. No version info available.
> langgraph_runtime: Installed. No version info available.
> langgraph_runtime_inmem: 0.6.4
> langgraph_sdk: 0.2.0

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.12.14
> aiohttp=3.8.3: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> asyncpg>=0.30.0: Installed. No version info available.
> blockbuster=1.5.24: Installed. No version info available.
> click>=8.1.7: Installed. No version info available.
> cloudpickle>=3.0.0: Installed. No version info available.
> cryptography=42.0.0: Installed. No version info available.
> dataclasses-json=0.5.7: Installed. No version info available.
> fastembed: Installed. No version info available.
> httpx: 0.28.1
> httpx-sse=0.4.0: Installed. No version info available.
> httpx>=0.25.0: Installed. No version info available.
> httpx>=0.25.2: Installed. No version info available.
> jsonpatch=1.33: Installed. No version info available.
> jsonschema-rs=0.20.0: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.36: Installed. No version info available.
> langchain-core=0.2.13: Installed. No version info available.
> langchain-core=0.3.66: Installed. No version info available.
> langchain-core=0.3.68: Installed. No version info available.
> langchain-core=0.3.72: Installed. No version info available.
> langchain-core>=0.3.64: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-perplexity;: Installed. No version info available.
> langchain-text-splitters=0.3.9: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langchain=0.3.26: Installed. No version info available.
> langgraph-api=0.2.67;: Installed. No version info available.
> langgraph-checkpoint>=2.0.23: Installed. No version info available.
> langgraph-checkpoint>=2.0.25: Installed. No version info available.
> langgraph-runtime-inmem=0.6.0: Installed. No version info available.
> langgraph-runtime-inmem>=0.6.0;: Installed. No version info available.
> langgraph-sdk>=0.1.0;: Installed. No version info available.
> langgraph-sdk>=0.2.0: Installed. No version info available.
> langgraph>=0.2: Installed. No version info available.
> langgraph>=0.4.0: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith>=0.1.125: Installed. No version info available.
> langsmith>=0.1.17: Installed. No version info available.
> langsmith>=0.3.45: Installed. No version info available.
> mcp>=1.9.2: Installed. No version info available.
> numpy=1.21: Installed. No version info available.
> numpy>=1.26.2;: Installed. No version info available.
> numpy>=2.1.0;: Installed. No version info available.
> openai-agents: Installed. No version info available.
> openai=1.86.0: Installed. No version info available.
> opentelemetry-api: 1.35.0
> opentelemetry-exporter-otlp-proto-http: 1.35.0
> opentelemetry-sdk: 1.35.0
> orjson: 3.11.1
> orjson>=3.10.1: Installed. No version info available.
> orjson>=3.9.7: Installed. No version info available.
> packaging: 24.2
> packaging>=23.2: Installed. No version info available.
> pgvector=0.2.5: Installed. No version info available.
> psycopg-pool=3.2.1: Installed. No version info available.
> psycopg=3: Installed. No version info available.
> pydantic: 2.11.7
> pydantic-settings=2.4.0: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pydantic>=2.7.4: Installed. No version info available.
> pyjwt>=2.9.0: Installed. No version info available.
> pytest: 8.4.1
> python-dotenv>=0.8.0;: Installed. No version info available.
> PyYAML>=5.3: Installed. No version info available.
> qdrant-client: 1.15.0
> requests: 2.32.4
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> rich: 14.1.0
> SQLAlchemy=1.4: Installed. No version info available.
> sqlalchemy=2: Installed. No version info available.
> sse-starlette=2.1.0: Installed. No version info available.
> sse-starlette>=2: Installed. No version info available.
> starlette>=0.37: Installed. No version info available.
> starlette>=0.38.6: Installed. No version info available.
> structlog=24.1.0: Installed. No version info available.
> structlog>23: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity>=8.0.0: Installed. No version info available.
> tiktoken=0.7: Installed. No version info available.
> truststore>=0.1: Installed. No version info available.
> typing-extensions>=4.14.0: Installed. No version info available.
> typing-extensions>=4.7: Installed. No version info available.
> uvicorn>=0.26.0: Installed. No version info available.
> watchfiles>=0.13: Installed. No version info available.
> zstandard: 0.23.0

## Comments

**Miguel-Andrade-Cruz:**
@eyurtsev I was looking for making a PR on this issue, but I'm not sure on what is the best approach. It will be my second contribution ever. Do you have any advice?

**Alexxigang:**
I reproduced this locally on the current codebase. Re-entering `get_usage_metadata_callback()` repeatedly grows `langchain_core.tracers.context._configure_hooks` monotonically (e.g. starting at 1 and reaching 6 after 5 empty context-manager uses), so this is a real accumulation issue rather than just a theoretical concern. I'm working on a fix that registers the usage-metadata configure hook only once per callback context variable and will add regression coverage for repeated calls, custom names, and callback isolation.

**Ker102:**
I'd like to work on this. The root cause is clear — `register_configure_hook()` appends to a global list on every `get_usage_metadata_callback()` context manager entry, causing unbounded growth. I can fix this by deduplicating hooks or registering once at module level. Could I be assigned?

**gitbalaji:**
Hi, I have an open PR (#35330) that fixes this issue. Could you please assign this to me? Happy to address any review feedback.
