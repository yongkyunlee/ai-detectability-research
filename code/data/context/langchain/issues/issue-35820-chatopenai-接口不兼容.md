# ChatOpenAI 接口不兼容

**Issue #35820** | State: open | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** 294978174
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

使用ChatOpenAI接口调用Qwen3.5-2B，没有结果返回

### Reproduction Steps / Example Code (Python)

```python
vllm serve Qwen/Qwen3.5-2B --port 40051 --tensor-parallel-size 1 --max-model-len 8192 --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser
 qwen3_coder

以下我会展示两段代码。

使用openai接口调用有结果：
from openai import OpenAI
client = OpenAI()
messages = [
    {"role": "user", "content": "介绍下自己"},
]
chat_response = client.chat.completions.create(
    model="Qwen/Qwen3.5-2B",
    messages=messages,
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    presence_penalty=2.0,
    extra_body={
        "top_k": 20,
    }, 
)
print("Chat response:", chat_response)

下面使用ChatOpenAI调用返回的是空结果。
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 初始化
llm = ChatOpenAI(
    base_url="http://localhost:40051/v1",
    model="Qwen/Qwen3.5-2B",
    temperature=0.1,
    api_key="EMPTY"
)

conversation = [HumanMessage(content="你好！请介绍一下自己")]

response = llm.generate([[msg for msg in conversation]])  # 注意外层列表
print(response.generations[0][0].text)
```

### Error Message and Stack Trace (if applicable)

```shell
空的结果
```

### Description

使用ChatOpenAI接口调用Qwen3.5-2B，没有结果返回

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #149~20.04.1-Ubuntu SMP Wed Apr 16 08:29:56 UTC 2025
> Python Version:  3.12.12 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 20:16:04) [GCC 11.2.0]

Package Information
-------------------
> langchain_core: 1.2.18
> langchain: 1.2.12
> langchain_community: 0.4.1
> langsmith: 0.7.17
> langchain_anthropic: 1.3.4
> langchain_aws: 1.4.0
> langchain_classic: 1.0.2
> langchain_deepseek: 1.0.1
> langchain_graph_retriever: 0.8.0
> langchain_huggingface: 1.2.1
> langchain_litellm: 0.6.1
> langchain_mongodb: 0.11.0
> langchain_ollama: 1.0.1
> langchain_openai: 1.1.11
> langchain_openrouter: 0.1.0
> langchain_text_splitters: 1.1.1
> langgraph_sdk: 0.3.11

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.3
> anthropic: 0.84.0
> backoff: 2.2.1
> boto3: 1.42.67
> cryptography: 46.0.5
> dataclasses-json: 0.6.7
> graph-retriever: 0.8.0
> httpx: 0.28.1
> httpx-sse: 0.4.3
> huggingface-hub: 1.6.0
> immutabledict: 4.3.1
> jsonpatch: 1.33
> langgraph: 1.1.2
> lark: 1.2.2
> litellm: 1.82.1
> networkx: 3.6.1
> numpy: 2.2.6
> ollama: 0.6.1
> openai: 2.26.0
> openrouter: 0.7.11
> opentelemetry-api: 1.40.0
> opentelemetry-exporter-otlp-proto-http: 1.40.0
> opentelemetry-sdk: 1.40.0
> orjson: 3.11.7
> packaging: 25.0
> pydantic: 2.12.5
> pydantic-settings: 2.13.1
> pymongo: 4.16.0
> pymongo-search-utils: 0.3.0
> pytest: 9.0.2
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> SQLAlchemy: 2.0.48
> sqlalchemy: 2.0.48
> tenacity: 9.1.4
> tiktoken: 0.12.0
> tokenizers: 0.22.2
> transformers: 5.3.0.dev0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> websockets: 16.0
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**rawathemant246:**
When you launch vLLM with --reasoning-parser qwen3, it splits the model's output into two fields: reasoning_content  
  (the thinking/reasoning tokens) and content (the final answer). The content field can end up empty if the model puts 
  its response into the reasoning portion.                                                                             
                                                                                                                     
  ChatOpenAI only supports the standard OpenAI API specification. Non-standard fields like reasoning_content added by  
  third-party providers (vLLM in this case) are intentionally not extracted. This is documented at the top of the    
  module:                                                                                                              
                                                                                                                     
  Non-standard response fields added by third-party providers (e.g., reasoning_content, reasoning_details) are not     
  extracted or preserved. Use the corresponding provider-specific LangChain package instead.                         
                                                                                                                       
  Workarounds:                                                                                                       
                                                                                                                     
  1. Remove the reasoning parser flag — launch vLLM without --reasoning-parser qwen3 so the full response stays in the
  content field:                                                                                                       
  vllm serve Qwen/Qwen3.5-2B --port 40051 --tensor-parallel-size 1 --max-model-len 8192
  2. Use the OpenAI client directly if you need reasoning separation:                                                  
  from openai import OpenAI                                                                                            
  client = OpenAI(base_url="http://localhost:40051/v1", api_key="EMPTY")                                               
  response = client.chat.completions.create(                                                                           
      model="Qwen/Qwen3.5-2B",                                                                                       
      messages=[{"role": "user", "content": "你好！请介绍一下自己"}],                                                  
  )                                                                                                                    
  print(response.choices[0].message.content)                                                                           
                                                                                                                       
  Hope that helps!

**294978174:**
Okay, I'll give it a try

**passionworkeer:**
Hi! I'd like to help fix this. Could you please assign it to me?
