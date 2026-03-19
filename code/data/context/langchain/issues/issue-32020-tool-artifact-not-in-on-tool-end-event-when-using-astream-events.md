# Tool artifact not in `on_tool_end` event when using `astream_events`

**Issue #32020** | State: closed | Created: 2025-07-14 | Updated: 2026-03-12
**Author:** Maxew42
**Labels:** help wanted, investigate, core, external

### Checked other resources

- [x] This is a bug, not a usage question. For questions, please use GitHub Discussions.
- [x] I added a clear and detailed title that summarizes the issue.
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I included a self-contained, minimal example that demonstrates the issue INCLUDING all the relevant imports. The code run AS IS to reproduce the issue.

### Example Code

```python
from langchain_core.prompts import ChatPromptTemplate
import asyncio
from typing import Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

async def get_agent( tools = []):
        user_input_template = ("human", "{input}")
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a superb assistant."),
                user_input_template,
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        agent= create_tool_calling_agent(ChatOpenAI(temperature=0), tools, prompt_template)
        agent_executor = AgentExecutor(agent=agent, tools=tools)
        return agent_executor

@tool(response_format="content_and_artifact")
async def dummy_tool(query: str) -> tuple[str, Any]:
    """Tool for testing"""
    query_metadata = {"length": len(query), "num_vowels": sum(1 for char in query if char.lower() in "aeiou")}
    return query[::-1], {"artifact": query_metadata}

async def main():
    agent_executor = await get_agent(tools=[dummy_tool])
    response = ""
    async for event in agent_executor.astream_events({"input": "Use the dummy tool with the string 'Hello World'"}, version="v2"):
        if event["event"] == "on_chat_model_stream":
            response += event["data"]["chunk"].content
        elif event["event"] == "on_tool_end":
            print(f"Tool end: {event} \n")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Message and Stack Trace (if applicable)

```shell
Tool end: {'event': 'on_tool_end', 'data': {'output': 'dlroW olleH', 'input': {'query': 'Hello World'}}, 'run_id': 'a937c952-9ac8-478b-a8f6-19cc5fc614d1', 'name': 'dummy_tool', 'tags': [], 'metadata': {}, 'parent_ids': ['1add89ed-6eb2-4e04-abc8-d8bae2bbdb8e']}
```

### Description

When using the `astream_events` API, it is unclear how to obtain the artifact returned by a tool. I would except it to be returned in the `on_tool_end` event, or maybe another event. But it is not in any event. 

A solution I have found is to emit a custom event directly from the tool, using `adispatch_custom_event()`. While this solution work fine, I still imagine not being able to use artifact for that is not intended.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 23.5.0: Wed May  1 20:19:05 PDT 2024; root:xnu-10063.121.3~5/RELEASE_ARM64_T8112
> Python Version:  3.10.13 (main, Nov 13 2024, 09:42:16) [Clang 15.0.0 (clang-1500.3.9.4)]

Package Information
-------------------
> langchain_core: 0.3.60
> langchain: 0.3.23
> langchain_community: 0.3.21
> langsmith: 0.3.33
> langchain_aws: 0.2.23
> langchain_docling: 0.2.0
> langchain_mcp_adapters: 0.1.8
> langchain_openai: 0.3.14
> langchain_postgres: 0.0.14
> langchain_text_splitters: 0.3.8

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp=3.8.3: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> asyncpg: 0.30.0
> boto3: 1.37.38
> dataclasses-json=0.5.7: Installed. No version info available.
> docling: 2.41.0
> httpx: 0.27.2
> httpx-sse=0.4.0: Installed. No version info available.
> jsonpatch=1.33: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.36: Installed. No version info available.
> langchain-core=0.3.51: Installed. No version info available.
> langchain-core=0.3.53: Installed. No version info available.
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
> langchain-text-splitters=0.3.8: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langchain=0.3.23: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith=0.1.125: Installed. No version info available.
> langsmith=0.1.126: Installed. No version info available.
> langsmith=0.1.17: Installed. No version info available.
> mcp>=1.9.2: Installed. No version info available.
> numpy: 1.26.4
> numpy=1.26.2: Installed. No version info available.
> openai-agents: Installed. No version info available.
> openai=1.68.2: Installed. No version info available.
> opentelemetry-api: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http: Installed. No version info available.
> opentelemetry-sdk: Installed. No version info available.
> orjson: 3.10.14
> packaging: 24.1
> packaging=23.2: Installed. No version info available.
> pgvector: 0.3.6
> psycopg: 3.2.2
> psycopg-pool: 3.2.6
> pydantic: 2.11.4
> pydantic-settings=2.4.0: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pydantic>=2.7.4: Installed. No version info available.
> pytest: 7.4.4
> PyYAML>=5.3: Installed. No version info available.
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> rich: 13.8.1
> sqlalchemy: 2.0.35
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tiktoken=0.7: Installed. No version info available.
> typing-extensions>=4.14.0: Installed. No version info available.
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: 0.23.0

## Comments

**Allyyi:**
Hi, it looks like no solution has been merged yet. I can help investigate. Could you please assign this to me?

**ccurme:**
See the streaming docs [here](https://docs.langchain.com/oss/python/langchain/streaming/overview#common-patterns), artifacts appear to be emitted in chunks from the tool node.

**laniakea001:**
## 技术建议

这个问题涉及到  API 中 tool artifact 的传递，是一个很实际的 Agent 监控/调试场景。

### 根因分析

查看源码， 事件目前只返回 （工具返回内容），而 （额外返回的数据）没有在事件payload中传递。这是因为事件系统设计上将  作为独立的数据流处理。

### 解决方案建议

**方案1：在事件中添加 artifact 字段（推荐）**

修改  中的事件发射逻辑，在  事件的  中添加  字段：

这样用户就可以通过  访问工具的额外返回值。

**方案2：使用自定义事件（当前 workaround 的改进）**

用户已经发现的 workaround 是使用 ，但可以封装成更通用的模式：

### 相关源码位置

-  - 流式事件处理
-  -  装饰器的 artifact 处理逻辑

### 测试用例建议

这个问题对于构建 Agent 监控面板、调试工具非常重要，期待修复！

**laniakea001:**
## 技术建议

这个问题涉及到 `astream_events` API 中 tool artifact 的传递，是一个很实际的 Agent 监控/调试场景。

### 根因分析

查看源码，`on_tool_end` 事件目前只返回 `output`（工具返回内容），而 `artifact`（额外返回的数据）没有在事件payload中传递。这是因为事件系统设计上将 `artifact` 作为独立的数据流处理。

### 解决方案建议

**方案1：在事件中添加 artifact 字段（推荐）**

修改 `langchain-core/langchain_core/tracers/` 中的事件发射逻辑，在 `on_tool_end` 事件的 `data` 中添加 `artifact` 字段：

```python
# 在 tool_end 事件发射处添加
if response_format == "content_and_artifact":
    event_data = {
        "output": content,
        "artifact": artifact,  # 新增
        "input": inputs,
        # ...
    }
```

这样用户就可以通过 `event["data"]["artifact"]` 访问工具的额外返回值。

**方案2：使用自定义事件（当前 workaround 的改进）**

用户已经发现的 workaround 是使用 `adispatch_custom_event`，但可以封装成更通用的模式：

```python
from langchain_core.callbacks import AsyncCustomEventHandler

class ToolArtifactHandler:
    async def on_tool_artifact(self, name: str, artifact: Any):
        print(f"Tool {name} artifact: {artifact}")
```

### 相关源码位置

- `langchain-core/langchain_core/tracers/_streaming.py` - 流式事件处理
- `langchain-core/langchain_core/tools.py` - `tool` 装饰器的 artifact 处理逻辑

### 测试用例建议

```python
async def test_tool_artifact_in_event():
    @tool(response_format="content_and_artifact")
    def test_tool(query: str) -> tuple[str, dict]:
        return query, {"meta": "data"}
    
    # 验证 on_tool_end 包含 artifact
    async for event in agent.astream_events(...):
        if event["event"] == "on_tool_end":
            assert "artifact" in event["data"]  # 应该通过
```

这个问题对于构建 Agent 监控面板、调试工具非常重要，期待修复！
