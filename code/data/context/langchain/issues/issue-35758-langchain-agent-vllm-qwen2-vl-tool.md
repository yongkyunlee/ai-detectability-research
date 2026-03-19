# LangChain Agent + vLLM Qwen2-VL + @tool

**Issue #35758** | State: open | Created: 2026-03-11 | Updated: 2026-03-12
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

_No response_

### Reproduction Steps / Example Code (Python)

```python
# from dataclasses import dataclass

# from langchain.agents import create_agent
# from langchain.chat_models import init_chat_model
# from langchain.tools import tool, ToolRuntime
# from langgraph.checkpoint.memory import InMemorySaver
# from langchain.agents.structured_output import ToolStrategy
# from langchain_openai import ChatOpenAI

# # Define system prompt
# SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

# You have access to two tools:

# - get_weather_for_location: use this to get the weather for a specific location
# - get_user_location: use this to get the user's location

# If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""

# # Define context schema
# @dataclass
# class Context:
#     """Custom runtime context schema."""
#     user_id: str

# # Define tools
# @tool
# def get_weather_for_location(city: str) -> str:
#     """Get weather for a given city."""
#     return f"It's always sunny in {city}!"

# @tool
# def get_user_location(runtime: ToolRuntime[Context]) -> str:
#     """Retrieve user information based on user ID."""
#     user_id = runtime.context.user_id
#     return "Florida" if user_id == "1" else "SF"

# # Configure model
# model = ChatOpenAI(
#     base_url="http://localhost:40050/v1",
#     model="Qwen/Qwen2-VL-7B-Instruct",
#     temperature=0.1,
#     api_key="EMPTY"
# )

# # Define response format
# @dataclass
# class ResponseFormat:
#     """Response schema for the agent."""
#     # A punny response (always required)
#     punny_response: str
#     # Any interesting information about the weather if available
#     weather_conditions: str | None = None

# # Set up memory
# checkpointer = InMemorySaver()

# # Create agent
# agent = create_agent(
#     model=model,
#     system_prompt=SYSTEM_PROMPT,
#     tools=[get_user_location, get_weather_for_location],
#     context_schema=Context,
#     response_format=ToolStrategy(ResponseFormat),
#     checkpointer=checkpointer
# )

# # Run agent
# # `thread_id` is a unique identifier for a given conversation.
# config = {"configurable": {"thread_id": "1"}}

# response = agent.invoke(
#     {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
#     config=config,
#     context=Context(user_id="1")
# )

# print(response['structured_response'])
# # ResponseFormat(
# #     punny_response="Florida is still having a 'sun-derful' day! The sunshine is playing 'ray-dio' hits all day long! I'd say it's the perfect weather for some 'solar-bration'! If you were hoping for rain, I'm afraid that idea is all 'washed up' - the forecast remains 'clear-ly' brilliant!",
# #     weather_conditions="It's always sunny in Florida!"
# # )

# # Note that we can continue the conversation using the same `thread_id`.
# response = agent.invoke(
#     {"messages": [{"role": "user", "content": "thank you!"}]},
#     config=config,
#     context=Context(user_id="1")
# )

# print(response['structured_response'])
# # ResponseFormat(
# #     punny_response="You're 'thund-erfully' welcome! It's always a 'breeze' to help you stay 'current' with the weather. I'm just 'cloud'-ing around waiting to 'shower' you with more forecasts whenever you need them. Have a 'sun-sational' day in the Florida sunshine!",
# #     weather_conditions=None
# # )

# from dataclasses import dataclass
# from langchain_openai import ChatOpenAI
# from langgraph.checkpoint.memory import InMemorySaver
# from langchain.agents.structured_output import ToolStrategy
# from langchain.agents import create_agent
# import time

# # 系统提示
# SYSTEM_PROMPT = """
# You are a weather forecaster who speaks in puns.
# Answer in a concise, structured way.
# """

# # 上下文
# @dataclass
# class Context:
#     user_id: str

# # 模型
# model = ChatOpenAI(
#     base_url="http://localhost:40050/v1",
#     model="Qwen/Qwen2-VL-7B-Instruct",
#     temperature=0.1,
#     api_key="EMPTY"
# )

# # 输出格式
# @dataclass
# class ResponseFormat:
#     punny_response: str
#     weather_conditions: str | None = None

# # 内存
# checkpointer = InMemorySaver()

# # 创建 Agent
# agent = create_agent(
#     model=model,
#     system_prompt=SYSTEM_PROMPT,
#     tools=[],  # 暂时不使用工具
#     context_schema=Context,
#     response_format=ToolStrategy(ResponseFormat),
#     checkpointer=checkpointer
# )

# # 线程配置
# config = {"configurable": {"thread_id": "1"}}

# # ------------------------
# # 辅助函数：将结构化输出包装为 OpenAI 风格
# # ------------------------
# def wrap_openai_format(structured_response: ResponseFormat):
#     return {
#         "id": f"chatcmpl-{int(time.time())}",
#         "object": "chat.completion",
#         "created": int(time.time()),
#         "model": "Qwen/Qwen2-VL-7B-Instruct",
#         "choices": [
#             {
#                 "index": 0,
#                 "message": {
#                     "role": "assistant",
#                     "content": structured_response.punny_response
#                 },
#                 "finish_reason": "stop"
#             }
#         ]
#     }

# # ------------------------
# # 调用 Agent
# # ------------------------
# resp1 = agent.invoke(
#     {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
#     config=config,
#     context=Context(user_id="1")
# )

# resp2 = agent.invoke(
#     {"messages": [{"role": "user", "content": "thank you!"}]},
#     config=config,
#     context=Context(user_id="1")
# )

# # ------------------------
# # 打印 OpenAI 风格输出
# # ------------------------
# print(wrap_openai_format(resp1['structured_response']))
# print(wrap_openai_format(resp2['structured_response']))

from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
import time

# ------------------------
# 系统提示（中文）
# ------------------------
SYSTEM_PROMPT = """
你是一位天气预报专家，说话风格幽默带双关。
你可以使用两个工具：
- get_weather_for_location(city)：查询指定城市的天气
- get_user_location()：获取用户所在城市
请回答时严格遵守 ResponseFormat 结构。
"""

# ------------------------
# 上下文
# ------------------------
@dataclass
class Context:
    user_id: str  # 用户 ID

# ------------------------
# 输出格式
# ------------------------
@dataclass
class ResponseFormat:
    punny_response: str           # 带双关语的回答
    weather_conditions: str | None = None  # 天气信息（可选）

# ------------------------
# 内存
# ------------------------
checkpointer = InMemorySaver()

# ------------------------
# 模型
# ------------------------
model = ChatOpenAI(
    base_url="http://localhost:40050/v1",
    model="Qwen/Qwen2-VL-7B-Instruct",
    temperature=0.1,
    api_key="EMPTY"
)

# ------------------------
# 工具函数
# ------------------------
@tool
def get_weather_for_location(city: str) -> str:
    """查询指定城市的天气"""
    return f"{city} 的天气总是晴朗！"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 获取所在城市"""
    return "佛罗里达" if runtime.context.user_id == "1" else "旧金山"

# ------------------------
# 创建 Agent
# ------------------------
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ToolStrategy(ResponseFormat),
    checkpointer=checkpointer
)

# ------------------------
# 配置线程
# ------------------------
config = {"configurable": {"thread_id": "1"}}

# ------------------------
# 辅助函数：包装成 OpenAI 风格 JSON
# ------------------------
def wrap_openai_format(structured_response: ResponseFormat):
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": structured_response.punny_response
                },
                "finish_reason": "stop"
            }
        ]
    }

# ------------------------
# 多轮调用示例
# ------------------------
resp1 = agent.invoke(
    {"messages": [{"role": "user", "content": "现在外面天气怎么样？"}]},
    config=config,
    context=Context(user_id="1")
)
print(wrap_openai_format(resp1['structured_response']))

resp2 = agent.invoke(
    {"messages": [{"role": "user", "content": "谢谢你！"}]},
    config=config,
    context=Context(user_id="1")
)
print(wrap_openai_format(resp2['structured_response']))
```

### Error Message and Stack Trace (if applicable)

```shell
openai.BadRequestError: Error code: 400 - {'error': {'message': "1 validation error for list[function-wrap[__log_extra_fields__()]]\n  Invalid JSON: EOF while parsing a list at line 2673 column 0 [type=json_invalid, input_value='[  \\n     \\n     \\n    \\...  \\n    \\n     \\n    \\n', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.12/v/json_invalid", 'type': 'BadRequestError', 'param': None, 'code': 400}}
```

### Description

创建了本地的容器
sudo docker run --gpus all -p 40050:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HUGGING_FACE_HUB_TOKEN=hf_xxx" \
  --env "HF_ENDPOINT=https://hf-mirror.com" \
  --env "HF_HUB_ENABLE_HF_TRANSFER=1" \
  vllm/vllm-openai:latest \
  Qwen/Qwen2-VL-7B-Instruct \
  --trust-remote-code \
  --max-model-len 4096 \
  --dtype bfloat16 \
  --enable-auto-tool-choice \
  --tool-call-parser "openai"

在使用LangChain Agent + vLLM Qwen2-VL + @tool 过程中出现了不符的情况，请问是否有解决办法。

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #149~20.04.1-Ubuntu SMP Wed Apr 16 08:29:56 UTC 2025
> Python Version:  3.10.19 (main, Oct 21 2025, 16:43:05) [GCC 11.2.0]

Package Information
-------------------
> langchain_core: 1.2.18
> langchain: 1.2.11
> langsmith: 0.7.16
> langchain_anthropic: 1.3.4
> langchain_classic: 1.0.2
> langchain_huggingface: 1.2.1
> langchain_mongodb: 0.11.0
> langchain_openai: 1.1.11
> langchain_openrouter: 0.1.0
> langchain_qwq: 0.3.4
> langchain_text_splitters: 1.1.1
> langgraph_sdk: 0.3.11

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> anthropic: 0.84.0
> async-timeout: 4.0.3
> httpx: 0.28.1
> huggingface-hub: 1.6.0
> json-repair: 0.53.1
> jsonpatch: 1.33
> langgraph: 1.1.0
> lark: 1.3.1
> numpy: 2.2.6
> openai: 2.26.0
> openrouter: 0.7.11
> orjson: 3.11.7
> packaging: 25.0
> pydantic: 2.12.5
> pymongo: 4.16.0
> pymongo-search-utils: 0.3.0
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> sqlalchemy: 2.0.48
> tenacity: 9.1.4
> tiktoken: 0.12.0
> tokenizers: 0.22.2
> typing-extensions: 4.15.0
> urllib3: 2.6.3
> uuid-utils: 0.14.1
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**laniakea001:**
## 可能的解决方案

这个错误通常出现在 vLLM 的 tool-call-parser 与 LangChain 的结构化输出不兼容时。

### 方案1: 检查 vLLM 版本
```bash
pip install -U vllm>=0.4.0
```

### 方案2: 调整 tool-call-parser
尝试使用 `hermes` 替代 `openai`:
```bash
--tool-call-parser "hermes"
```

### 方案3: 使用 ChatCompletions 替代 Agent
```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(base_url="http://localhost:40050/v1", model="Qwen/Qwen2-VL-7B-Instruct")
functions = [convert_to_openai_function(get_weather)]
response = model.bind(functions=functions).invoke("天气如何?")
```

### 方案4: 增加 max-model-len
尝试 `--max-model-len 8192`.

希望这些方案能帮你解决问题！

**294978174:**
感谢，我尝试下

**laniakea001:**
## Potential Solution

This issue is related to multimodal model integration with LangChain agents. Here are some debugging steps:

1. Check vLLM version: Ensure you are using vLLM >= 0.4.0 which has better multimodal support
2. Tool call parser: Try different tool_parser configurations
3. Alternative models: Consider using Google Gemini or Anthropic Claude
4. max_model_len: Increase context window in vLLM to 8192

Hope this helps!

**294978174:**
仍然不行。
