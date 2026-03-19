# Runtime not exported from langchain.agents.middleware

**Issue #35972** | State: closed | Created: 2026-03-16 | Updated: 2026-03-17
**Author:** november-pain
**Labels:** bug, langchain, external

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

### Related Issues / PRs

#33453 - same class of missing export, fixed in #33454

### Reproduction Steps / Example Code (Python)

```python
from langchain.agents.middleware import after_model, AgentState, Runtime
# ImportError: cannot import name 'Runtime' from 'langchain.agents.middleware'
```

### Error Message and Stack Trace (if applicable)

```shell
Traceback (most recent call last):
  File "", line 1, in 
ImportError: cannot import name 'Runtime' from 'langchain.agents.middleware'
```

### Description

`Runtime` (from `langgraph.runtime`) is used in `after_model` callback signatures (`state: AgentState, runtime: Runtime`) but is not exported from `langchain.agents.middleware`. Users implementing `@after_model` hooks need `Runtime` for the type annotation but must know to import it from `langgraph.runtime` directly.

This is the same class of issue as #33453 (`ModelResponse` missing from exports), fixed in #33454.

`Runtime` is already imported at runtime in multiple middleware modules (`human_in_the_loop.py`, `summarization.py`), so there is no circular import concern. It is simply missing from the import list and `__all__` in `langchain/agents/middleware/__init__.py`.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.6.0: Mon Jan 19 22:00:10 PST 2026; root:xnu-11417.140.69.708.3~1/RELEASE_X86_64
> Python Version:  3.12.9 (v3.12.9:fdb81425a9a, Feb  4 2025, 12:21:36) [Clang 13.0.0 (clang-1300.0.29.30)]

Package Information
-------------------
> langchain_core: 1.2.18
> langchain: 1.2.12
> langsmith: 0.6.6
> deepagents: 0.4.11
> langchain_anthropic: 1.3.4
> langchain_aws: 1.4.0
> langchain_google_genai: 4.2.0
> langchain_mcp_adapters: 0.2.1
> langchain_tavily: 0.2.17
> langgraph_api: 0.7.73
> langgraph_checkpoint_aws: 1.0.6
> langgraph_cli: 0.4.18
> langgraph_runtime_inmem: 0.26.0
> langgraph_sdk: 0.3.11

Optional packages not installed
-------------------------------
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.3
> anthropic: 0.84.0
> bedrock-agentcore: 1.2.0
> blockbuster: 1.5.26
> boto3: 1.42.67
> click: 8.3.1
> cloudpickle: 3.1.2
> croniter: 6.2.2
> cryptography: 46.0.4
> filetype: 1.2.0
> google-genai: 1.60.0
> grpcio: 1.78.0
> grpcio-health-checking: 1.78.0
> grpcio-tools: 1.78.0
> httpx: 0.28.1
> jsonpatch: 1.33
> jsonschema-rs: 0.44.1
> langgraph: 1.1.2
> langgraph-checkpoint: 4.0.1
> mcp: 1.26.0
> numpy: 2.4.1
> opentelemetry-api: 1.40.0
> opentelemetry-exporter-otlp-proto-http: 1.40.0
> opentelemetry-sdk: 1.40.0
> orjson: 3.11.5
> packaging: 25.0
> protobuf: 6.33.5
> pydantic: 2.12.5
> pyjwt: 2.10.1
> pytest: 9.0.2
> python-dotenv: 1.2.1
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> sse-starlette: 3.2.0
> starlette: 0.52.1
> structlog: 25.5.0
> tenacity: 9.1.2
> truststore: 0.10.4
> typing-extensions: 4.15.0
> typing_extensions: 4.15.0
> uuid-utils: 0.14.0
> uvicorn: 0.40.0
> watchfiles: 1.1.1
> wcmatch: 10.1
> zstandard: 0.25.0

## Comments

**november-pain:**
I have a fix ready on my fork: [`november-pain:fix/export-runtime-from-middleware`](https://github.com/november-pain/langchain/tree/fix/export-runtime-from-middleware). Linter (`make lint_package`) passes.

Could a maintainer please assign this to me so I can open a PR?
