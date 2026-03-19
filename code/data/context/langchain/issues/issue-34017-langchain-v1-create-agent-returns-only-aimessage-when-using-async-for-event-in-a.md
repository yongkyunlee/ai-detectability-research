# LangChain v1: create_agent returns only AIMessage when using` async for event in agent.astream`, no AIMessageChunk

**Issue #34017** | State: closed | Created: 2025-11-19 | Updated: 2026-03-12
**Author:** wally-qin
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
- [ ] langchain-cli
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Example Code (Python)

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# If streaming is enabled in LLM, astream will report an error 'AsyncStream' object has no attribute 'model_dump'
model = ChatOpenAI(model="gpt-4o")
# 1. create agent
agent = create_agent(
    model=model,
    system_prompt="You are a helpful assistant."
)

# ❌This method cannot obtain AIMessageChunk, nor can it be obtained by using the stream method. 
async for event in agent.astream(
    {"messages": messages},
    stream_mode="messages"
):
    message, metadata = event
    print(type(message))  # AIMessage, not AIMessageChunk
```

### Error Message and Stack Trace (if applicable)

```shell
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# If streaming is enabled in LLM, astream will report an error 'AsyncStream' object has no attribute 'model_dump'
model = ChatOpenAI(model="gpt-4o")
# 1. create agent
agent = create_agent(
    model=model,
    system_prompt="You are a helpful assistant."
)

# ❌This method cannot obtain AIMessageChunk, nor can it be obtained by using the stream method. 
async for event in agent.astream(
    {"messages": messages},
    stream_mode="messages"
):
    message, metadata = event
    print(type(message))  # AIMessage, not AIMessageChunk
```

### Description

I’m migrating from LangGraph’s create_react_agent to LangChain v1’s create_agent.
In my previous setup, the agent streamed AIMessageChunk correctly.
After switching to create_agent, both stream and astream only return AIMessage, with no chunked messages.

Could you please advise how to enable chunk-level streaming in create_agent?
Any guidance would be greatly appreciated.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.0.0: Mon Aug 25 21:17:54 PDT 2025; root:xnu-12377.1.9~3/RELEASE_ARM64_T6041
> Python Version:  3.11.11 (main, Mar 17 2025, 21:51:13) [Clang 20.1.0 ]

Package Information
-------------------
> langchain_core: 1.0.5
> langchain: 1.0.7
> langchain_community: 0.3.31
> langsmith: 0.4.43
> langchain_anthropic: 1.1.0
> langchain_mcp_adapters: 0.1.13
> langchain_openai: 1.0.3
> langgraph_sdk: 0.2.9

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.13.2
> anthropic: 0.74.0
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.3
> mcp: 1.21.2
> numpy: 2.3.5
> openai: 2.8.1
> orjson: 3.11.4
> packaging: 25.0
> pydantic: 2.11.5
> pydantic-settings: 2.12.0
> pytest: 9.0.1
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.2.0
> SQLAlchemy: 2.0.44
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> zstandard: 0.25.0

## Comments

**josheppinette:**
How did you resolve this?

**wuyingtong:**
This problem already exists langchain==1.2.2

**nathaniafern:**
How was this resolved?

**nathaniafern:**
> How was this resolved?

For me this was a python version issue. I was working on python 3.10. When I switched to 3.12 it streamed the chunks.
