# LangChain v1.1-1.12 create_agent with response_format hardcodes tool_choice="any" for structured output tool, breaking Anthropic thinking + structured output.

**Issue #35539** | State: closed | Created: 2026-03-03 | Updated: 2026-03-05
**Author:** stoyan-atanasov-beye
**Labels:** bug, langchain, anthropic, external

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
from langchain_anthropic import ChatAnthropic
from pydantic_v1 import BaseModel, Field
from langchain.agents import create_agent

class Result(BaseModel):
    answer: str = Field(description="Final answer")

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    thinking={"type": "enabled", "budget_tokens": 5000}
)

agent = create_agent(llm, tools=[], response_format=Result, system_prompt="Answer directly.")
agent.invoke({"messages": [{"role": "user", "content": "What is 2+2?"}]})
```

### Error Message and Stack Trace (if applicable)

```shell
Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Thinking may not be enabled when tool_choice forces tool use.'}, 'request_id': 'req_011CYggXHSpHGThY9So9qSzy'}
```

### Description

`create_agent(model, ..., response_format=Schema)` converts structured output to a tool call with `tool_choice="any"`. 

Anthropic rejects this with `"Thinking may not be enabled when tool_choice forces tool use"` when model has `thinking={"type": "enabled"}`.

**Expected:** Use provider native structured output (`with_structured_output(method="anthropic_json_mode")`) or `tool_choice="auto"`.

**Actual:** Forces tool-based structured output with `tool_choice="any"`.

### Reproduction
```python
from langchain_anthropic import ChatAnthropic
from pydantic_v1 import BaseModel, Field
from langchain.agents import create_agent

class Result(BaseModel):
    answer: str = Field(description="Final answer")

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    thinking={"type": "enabled", "budget_tokens": 5000}
)

agent = create_agent(llm, tools=[], response_format=Result, system_prompt="Answer directly.")
agent.invoke({"messages": [{"role": "user", "content": "What is 2+2?"}]})
```
**Error:** `400: 'Thinking may not be enabled when tool_choice forces tool use.'`

### Environment
- `langchain==1.1.x`
- `langchain-anthropic==0.x.x`

### Workaround
Manual LangGraph or `llm.with_structured_output(Result, method="anthropic_json_mode")`.

### Source
`create_agent` → structured output → tool binding → `tool_choice="any"`.

**Fix:** Add `provider_strategy="anthropic_json_mode"` or detect `thinking` param → skip tool-based structured output.

### System Info

ystem Information
------------------
> OS:  Linux
> OS Version:  #91-Ubuntu SMP PREEMPT_DYNAMIC Tue Nov 18 14:14:30 UTC 2025
> Python Version:  3.13.11 (main, Dec  9 2025, 02:03:30) [GCC 12.2.0]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langchain_community: 0.4
> langsmith: 0.4.37
> langchain_anthropic: 1.3.4
> langchain_classic: 1.0.0
> langchain_google_genai: 4.2.0
> langchain_google_vertexai: 3.2.1
> langchain_openai: 1.0.1
> langchain_postgres: 0.0.16
> langchain_text_splitters: 1.0.0
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.0
> anthropic: 0.84.0
> asyncpg: 0.31.0
> bottleneck: 1.6.0
> dataclasses-json: 0.6.7
> filetype: 1.2.0
> google-cloud-aiplatform: 1.134.0
> google-cloud-storage: 3.8.0
> google-genai: 1.60.0
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.10
> numexpr: 2.14.1
> numpy: 2.3.4
> openai: 2.14.0
> openai-agents: 0.4.1
> orjson: 3.11.5
> packaging: 25.0
> pgvector: 0.3.6
> psycopg: 3.2.11
> psycopg-pool: 3.3.0
> pyarrow: 22.0.0
> pydantic: 2.12.3
> pydantic-settings: 2.12.0
> pytest: 8.4.2
> PyYAML: 6.0.3
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.2.0
> SQLAlchemy: 2.0.44
> sqlalchemy: 2.0.44
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> validators: 0.35.0
> zstandard: 0.25.0

## Comments

**ccurme:**
Merged in a patch. However, Anthropic now supports native structured output, so I'd recommend using that via [ProviderStrategy](https://docs.langchain.com/oss/python/langchain/structured-output#provider-strategy):
```python
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy

class Result(BaseModel):
    answer: str = Field(description="Final answer")

llm = ChatAnthropic(
    model="claude-haiku-4-5",
    thinking={"type": "enabled", "budget_tokens": 5000},
    max_tokens=10_000,
)

agent = create_agent(
    llm,
    tools=[],
    response_format=ProviderStrategy(Result),
    system_prompt="Answer directly.",
)
agent.invoke({"messages": [{"role": "user", "content": "What is 2+2?"}]})
```
