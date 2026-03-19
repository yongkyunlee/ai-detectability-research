# `set_llm_cache` does not apply when using `create_react_agent` from LangGraph prebuilt agents

**Issue #31949** | State: closed | Created: 2025-07-10 | Updated: 2026-03-01
**Author:** valenvivaldi
**Labels:** investigate, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

``` python
from langchain.globals import set_llm_cache
from langgraph.prebuilt import create_react_agent
from langchain_community.cache import SQLiteCache
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.graph_transformers.llm import system_prompt
from langchain_openai import ChatOpenAI
import langchain
import time

SYSTEM_PROMPT_PLACEHOLDER = "{system_prompt}"

# Set up the cache
set_llm_cache(SQLiteCache(database_path="aaaaaacache.db"))

# Set up the LLM
llm = ChatOpenAI(model="gpt-4.1", temperature=0)

# Test with a simple prompt
prompt = "What is the capital of France?"
start_time = time.time()
response = llm.invoke(prompt)
print(f"First call: {response.content}")
print(f"Time: {time.time() - start_time} seconds")

start_time = time.time()
response = llm.invoke(prompt)
print(f"Second call: {response.content}")
print(f"Time: {time.time() - start_time} seconds")

# Tests with a ReAct agent
start_time = time.time()

agent = create_react_agent(llm, tools=[], prompt="You are a friendly agent")
response = agent.invoke({"messages": [{"role": "user", "content": "What is the capital of France?"}]})

print(f"Agent response: {response.get('messages')[1].content}")
print(f"Time: {time.time() - start_time} seconds")

start_time = time.time()
response = agent.invoke({"messages": [{"role": "user", "content": "What is the capital of France?"}]})
print(f"Agent response: {response.get('messages')[1].content}")
print(f"Time: {time.time() - start_time} seconds")

```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

Description:
LangChain provides a function called set_llm_cache, which enables response caching for LLM provider calls. This works correctly when using the model directly — for example, calling ChatOpenAI().invoke() on the same prompt multiple times results in a cache hit after the first call.

However, when using LangGraph, specifically with the prebuilt agent created via create_react_agent, the cache does not appear to be used. Identical prompts passed to the agent result in repeated full LLM calls, with no observable reuse of cached responses.

Upon inspecting the cache database (SQLite), I found that the structure of the messages array — passed to the LLM internally — includes dynamically generated unique IDs. These appear after the system_prompt in the serialized input. Because these IDs change on each run, the resulting serialized input differs each time, preventing cache hits.

See the attached screenshot comparing two nearly identical cached inputs — the only difference is a unique ID field.

To confirm this theory, I reviewed the internal code — specifically the _generate_with_cache method in the BaseModel class. I temporarily modified the input being passed to the cache lookup by copying it and removing the unique ID fields before the lookup. After doing this, caching started working correctly, and repeated calls to the agent returned instantly from cache.

I’ve attached a second screenshot highlighting (in red) the extra block of code I added to test this workaround.

The example execution after this change:

Thanks in advance for taking a look at this. I’m aware that my workaround (manually stripping dynamic IDs before caching) is likely not optimal, but I hope it can serve as a helpful starting point for someone more familiar with the internal architecture of LangChain and LangGraph to propose a proper fix.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.4.0: Fri Apr 11 18:33:47 PDT 2025; root:xnu-11417.101.15~117/RELEASE_ARM64_T6000
> Python Version:  3.12.0 (v3.12.0:0fb18b02c8, Oct  2 2023, 09:45:56) [Clang 13.0.0 (clang-1300.0.29.30)]

Package Information
-------------------
> langchain_core: 0.3.68
> langchain: 0.3.26
> langchain_community: 0.3.27
> langsmith: 0.3.45
> langchain_anthropic: 0.3.17
> langchain_chroma: 0.2.3
> langchain_deepseek: 0.1.3
> langchain_experimental: 0.3.4
> langchain_google_genai: 2.1.7
> langchain_ollama: 0.3.4
> langchain_openai: 0.3.27
> langchain_sandbox: 0.0.4
> langchain_text_splitters: 0.3.8
> langgraph_codeact: 0.1.3
> langgraph_sdk: 0.1.72
> langgraph_supervisor: 0.0.21

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp=3.8.3: Installed. No version info available.
> anthropic=0.57.0: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> chromadb!=0.5.10,!=0.5.11,!=0.5.12,!=0.5.4,!=0.5.5,!=0.5.7,!=0.5.9,=0.4.0: Installed. No version info available.
> dataclasses-json=0.5.7: Installed. No version info available.
> filetype: 1.2.0
> google-ai-generativelanguage: 0.6.18
> httpx: 0.27.2
> httpx-sse=0.4.0: Installed. No version info available.
> httpx>=0.25.2: Installed. No version info available.
> jsonpatch=1.33: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.40: Installed. No version info available.
> langchain-core=0.3.56: Installed. No version info available.
> langchain-core=0.3.47: Installed. No version info available.
> langchain-core=0.3.51: Installed. No version info available.
> langchain-core=0.3.66: Installed. No version info available.
> langchain-core=0.3.68: Installed. No version info available.
> langchain-core>=0.3.52: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-openai=0.3.9: Installed. No version info available.
> langchain-perplexity;: Installed. No version info available.
> langchain-text-splitters=0.3.8: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langchain=0.3.26: Installed. No version info available.
> langgraph-prebuilt=0.1.7: Installed. No version info available.
> langgraph=0.3.5: Installed. No version info available.
> langgraph>=0.3.5: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith>=0.1.125: Installed. No version info available.
> langsmith>=0.1.17: Installed. No version info available.
> langsmith>=0.3.45: Installed. No version info available.
> numpy>=1.26.0;: Installed. No version info available.
> numpy>=1.26.2;: Installed. No version info available.
> numpy>=2.1.0;: Installed. No version info available.
> ollama=0.5.1: Installed. No version info available.
> openai-agents: Installed. No version info available.
> openai=1.86.0: Installed. No version info available.
> opentelemetry-api: 1.34.1
> opentelemetry-exporter-otlp-proto-http: Installed. No version info available.
> opentelemetry-sdk: 1.34.1
> orjson: 3.10.18
> orjson>=3.10.1: Installed. No version info available.
> packaging: 24.2
> packaging=23.2: Installed. No version info available.
> pydantic: 2.11.7
> pydantic-settings=2.4.0: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pydantic>=2.7.4: Installed. No version info available.
> pytest: 7.4.4
> PyYAML>=5.3: Installed. No version info available.
> requests: 2.32.4
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> rich: 14.0.0
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tiktoken=0.7: Installed. No version info available.
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: 0.23.0

## Comments

**louisoutin:**
+1

**zhiyuan-zhang0206:**
Same issue here, and I used this code as a workaround:
```  
from langchain_core.language_models.chat_models import BaseChatModel
    
_original_agenerate_with_cache = BaseChatModel._agenerate_with_cache
_original_generate_with_cache = BaseChatModel._generate_with_cache
  
async def _agenerate_with_cache_with_tool_workaround(self, messages, *args, **kwargs):
    messages = [message.copy(update={"id": None}) for message in messages]
    return await _original_agenerate_with_cache(self, messages, *args, **kwargs)
  
def _generate_with_cache_with_tool_workaround(self, messages, *args, **kwargs):
    messages = [message.copy(update={"id": None}) for message in messages]
    return _original_generate_with_cache(self, messages, *args, **kwargs)
  
BaseChatModel._agenerate_with_cache = _agenerate_with_cache_with_tool_workaround
BaseChatModel._generate_with_cache = _generate_with_cache_with_tool_workaround
```

I think they should merge this in, as I don't see the reason why we need to use message ids while looking up caches.

**mdrxy:**
This will be addressed in v1

**hellohawaii:**
The same problem still exist in v1.0.
````
langchain                   1.0.5
langchain-core              1.0.4
langchain-ollama            0.2.1
langchain-openai            1.0.2
langchain-text-splitters    0.3.8
langgraph                   1.0.3
langgraph-checkpoint        2.1.1
langgraph-checkpoint-sqlite 2.0.11
langgraph-prebuilt          1.0.4
langgraph-sdk               0.2.8
langsmith                   0.4.29
```

**mdrxy:**
Thanks for the contribution!

This PR/issue has been inactive for a while, so we're going to close it for now to keep things tidy.

If this is still relevant, feel free to reopen it or start a new discussion with updated context. We're happy to take another look.

Thanks again! 🙏

**ashminpolymath:**
Why is this closed without being fixed?
