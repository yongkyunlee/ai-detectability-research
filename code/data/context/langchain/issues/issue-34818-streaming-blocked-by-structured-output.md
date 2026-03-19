# Streaming blocked by Structured Output

**Issue #34818** | State: open | Created: 2026-01-20 | Updated: 2026-03-16
**Author:** jmoreno11
**Labels:** core, langchain, openai, external

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
- [x] langchain-core
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

### Reproduction Steps / Example Code (Python)

```python
import asyncio
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field

class Result(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(description="Summary")
    answer: str = Field(description="Answer")

@tool
def get_info(topic: str) -> str:
    """Get information about a topic."""
    return f"Info about {topic}: very interesting!"

async def test(response_format, label: str) -> None:
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    agent = create_agent(
        name="Test",
        model=model,
        tools=[get_info],
        system_prompt="ALWAYS explain what you're doing BEFORE calling tools.",
        response_format=response_format,
    )

    text_before_tool = []
    seen_tool = False

    async for token, metadata in agent.astream(
        {"messages": [{"role": "user", "content": "Get info about Python"}]},
        stream_mode="messages",
    ):
        for block in getattr(token, "content_blocks", None) or []:
            if isinstance(block, dict):
                if block.get("type") == "tool_call_chunk" and block.get("name"):
                    seen_tool = True
                elif block.get("type") == "text" and not seen_tool:
                    text_before_tool.append(block.get("text", ""))

    text = "".join(text_before_tool)
    print(f"{label}: {len(text_before_tool)} chunks, content: {text[:60] or 'NONE'}...")

async def main():
    await test(None, "No response_format")
    await test(ToolStrategy(Result), "ToolStrategy")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

When using `create_agent` with a `response_format` (structured output), streaming no longer emits intermediate AI messages. Only the final structured output is visible.

Without `response_format`, streaming behaves as expected: the model emits natural language chunks before tool calls. As soon as a structured output or response format is provided, those intermediate AI messages disappear.

This breaks the “ChatGPT-like” streaming experience and makes it impossible to observe the agent’s reasoning or intent before tool execution.

I have a short video demonstrating this behavior side-by-side.

---

### Expected Behavior

When streaming an agent with tools, I expect intermediate AI messages to be streamed regardless of whether `response_format` is set.

Typical sequence:

```
"Let me look up that information..."
[tool call]
"Here is what I found..."
[final structured output]
```

The presence of a structured output should affect only the final response, not suppress intermediate messages.

---

### Actual Behavior

When `response_format` is provided:

* No natural language chunks are streamed before the tool call
* Only the final structured output appears

Observed configurations:

* No `response_format`: intermediate AI text is streamed correctly
* `ToolStrategy`: no AI text before tool call
* `ProviderStrategy`: only JSON output is streamed, no natural language

This was reproduced consistently on Azure OpenAI GPT-5.2.

---

### Minimal Reproduction

1. Create an agent with a single tool
2. Enable streaming
3. Compare:

   * Agent without `response_format`
   * Agent with structured output (`response_format`, `ToolStrategy`, or `ProviderStrategy`)
4. Observe streamed messages before the first tool call

Only the non-structured version emits intermediate AI messages.

---

### Impact

* Removes visibility into agent behavior during streaming
* Prevents user-facing explanations before tool usage
* Makes structured output incompatible with conversational or debuggable UIs

---

### Workaround

* Avoid `response_format`
* Prompt the model to emit JSON at the end
* Manually parse the final message

This works but bypasses LangChain’s structured output guarantees and validation.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.2.0: Tue Nov 18 21:07:05 PST 2025; root:xnu-12377.61.12~1/RELEASE_ARM64_T6020
> Python Version:  3.12.9 | packaged by Anaconda, Inc. | (main, Feb  6 2025, 12:55:12) [Clang 14.0.6 ]

Package Information
-------------------
> langchain_core: 1.0.0a8
> langchain: 1.0.0rc1
> langchain_community: 1.0.0a1
> langsmith: 0.4.34
> langchain_anthropic: 0.3.13
> langchain_astradb: 0.6.0
> langchain_aws: 0.2.7
> langchain_chroma: 0.1.4
> langchain_classic: 1.0.0a1
> langchain_cohere: 0.3.3
> langchain_elasticsearch: 0.3.0
> langchain_experimental: 0.3.4
> langchain_google_calendar_tools: 0.0.1
> langchain_google_community: 2.0.3
> langchain_google_genai: 2.0.6
> langchain_google_vertexai: 2.0.7
> langchain_graph_retriever: 0.6.1
> langchain_groq: 0.2.1
> langchain_ibm: 0.3.10
> langchain_mcp_adapters: 0.1.0
> langchain_milvus: 0.1.7
> langchain_mistralai: 0.2.3
> langchain_mongodb: 0.2.0
> langchain_nvidia: Installed. No version info available.
> langchain_nvidia_ai_endpoints: 0.3.8
> langchain_ollama: 0.2.1
> langchain_openai: 1.0.0a4
> langchain_pinecone: 0.2.2
> langchain_sambanova: 0.1.0
> langchain_tests: 0.3.19
> langchain_text_splitters: 1.0.0a1
> langchain_unstructured: 0.1.5
> langchainhub: 0.1.21
> langgraph_api: 0.4.39
> langgraph_cli: 0.4.3
> langgraph_license: Installed. No version info available.
> langgraph_runtime: Installed. No version info available.
> langgraph_runtime_inmem: 0.14.1
> langgraph_sdk: 0.2.9

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.11.18
> aiohttp=3.8.3: Installed. No version info available.
> anthropic=0.51.0: Installed. No version info available.
> anthropic[vertexai]: Installed. No version info available.
> astrapy: 2.0.1
> astrapy>=1.5.2;: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> backoff>=2.2.1: Installed. No version info available.
> beautifulsoup4: 4.12.3
> beautifulsoup4>=4.12.3;: Installed. No version info available.
> blockbuster=1.5.24: Installed. No version info available.
> boto3: 1.34.162
> cassio>=0.1.10;: Installed. No version info available.
> chromadb: 0.5.23
> chromadb>=0.5.23;: Installed. No version info available.
> click>=8.1.7: Installed. No version info available.
> cloudpickle>=3.0.0: Installed. No version info available.
> cohere: 5.15.0
> cryptography=42.0.0: Installed. No version info available.
> dataclasses-json=0.6.7: Installed. No version info available.
> db-dtypes: Installed. No version info available.
> elasticsearch[vectorstore-mmr]: Installed. No version info available.
> fastapi: 0.119.0
> filetype: 1.2.0
> gapic-google-longrunning: Installed. No version info available.
> gliner==0.2.13;: Installed. No version info available.
> google-api-core: 2.24.2
> google-api-python-client: 2.154.0
> google-api-python-client>=2.104.0: Installed. No version info available.
> google-auth-httplib2: 0.2.0
> google-auth-oauthlib: 1.2.2
> google-auth-oauthlib>=1.1.0: Installed. No version info available.
> google-cloud-aiplatform: 1.91.0
> google-cloud-bigquery: 3.31.0
> google-cloud-bigquery-storage: Installed. No version info available.
> google-cloud-contentwarehouse: Installed. No version info available.
> google-cloud-core: 2.4.3
> google-cloud-discoveryengine: Installed. No version info available.
> google-cloud-documentai: Installed. No version info available.
> google-cloud-documentai-toolbox: Installed. No version info available.
> google-cloud-speech: Installed. No version info available.
> google-cloud-storage: 2.19.0
> google-cloud-texttospeech: Installed. No version info available.
> google-cloud-translate: Installed. No version info available.
> google-cloud-vision: Installed. No version info available.
> google-generativeai: 0.8.5
> googlemaps: Installed. No version info available.
> graph-retriever: 0.6.1
> groq: 0.23.1
> grpcio: 1.76.0rc1
> grpcio-tools=1.75.0: Installed. No version info available.
> grpcio=1.75.0: Installed. No version info available.
> httpx: 0.27.2
> httpx-sse: 0.4.0
> httpx-sse=0.4.0: Installed. No version info available.
> httpx=0.23.0: Installed. No version info available.
> httpx=0.25.0: Installed. No version info available.
> httpx>=0.25.0: Installed. No version info available.
> httpx>=0.25.2: Installed. No version info available.
> httpx>=0.28.1;: Installed. No version info available.
> ibm-watsonx-ai: 1.3.13
> immutabledict>=4.2.1: Installed. No version info available.
> jsonpatch=1.33.0: Installed. No version info available.
> jsonschema-rs=0.20.0: Installed. No version info available.
> keybert>=0.8.5;: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-astradb>=0.5.3;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-chroma>=0.2.0;: Installed. No version info available.
> langchain-classic=1.0.0a1: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-community>=0.3.14;: Installed. No version info available.
> langchain-core=0.3.36: Installed. No version info available.
> langchain-core=0.3.53: Installed. No version info available.
> langchain-core=0.3.59: Installed. No version info available.
> langchain-core=1.0.0a6: Installed. No version info available.
> langchain-core=1.0.0a7: Installed. No version info available.
> langchain-core=1.0.0a8: Installed. No version info available.
> langchain-core>=0.3.29: Installed. No version info available.
> langchain-core>=0.3.64: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-perplexity;: Installed. No version info available.
> langchain-text-splitters=1.0.0a1: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langchain>=0.0.335: Installed. No version info available.
> langgraph-api=0.3;: Installed. No version info available.
> langgraph-checkpoint>=2.0.23: Installed. No version info available.
> langgraph-checkpoint>=2.0.25: Installed. No version info available.
> langgraph-runtime-inmem=0.14.0: Installed. No version info available.
> langgraph-runtime-inmem>=0.7;: Installed. No version info available.
> langgraph-sdk>=0.1.0;: Installed. No version info available.
> langgraph-sdk>=0.2.0: Installed. No version info available.
> langgraph=1.0.0a4: Installed. No version info available.
> langgraph>=0.2: Installed. No version info available.
> langgraph>=0.4.0: Installed. No version info available.
> langsmith-pyo3>=0.1.0rc2;: Installed. No version info available.
> langsmith=0.1.125: Installed. No version info available.
> langsmith=0.1.17: Installed. No version info available.
> langsmith=0.3.45: Installed. No version info available.
> langsmith>=0.3.45: Installed. No version info available.
> mcp>=1.7: Installed. No version info available.
> networkx>=3.4.2: Installed. No version info available.
> numpy: 1.26.4
> numpy>=1.26.2;: Installed. No version info available.
> numpy>=2.1.0;: Installed. No version info available.
> ollama: 0.4.8
> openai-agents>=0.0.3;: Installed. No version info available.
> openai=1.109.1: Installed. No version info available.
> opensearch-py>=2.8.0;: Installed. No version info available.
> opentelemetry-api>=1.30.0;: Installed. No version info available.
> opentelemetry-api>=1.37.0: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http>=1.30.0;: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http>=1.37.0: Installed. No version info available.
> opentelemetry-sdk>=1.30.0;: Installed. No version info available.
> opentelemetry-sdk>=1.37.0: Installed. No version info available.
> orjson>=3.10.1: Installed. No version info available.
> orjson>=3.9.14;: Installed. No version info available.
> orjson>=3.9.7: Installed. No version info available.
> packaging: 24.2
> packaging=23.2.0: Installed. No version info available.
> packaging>=23.2: Installed. No version info available.
> pandas: 2.2.3
> pinecone: 5.4.2
> protobuf=6.32.1: Installed. No version info available.
> protobuf>=4.25.0: Installed. No version info available.
> pyarrow: 19.0.0
> pydantic: 2.12.5
> pydantic-settings=2.10.1: Installed. No version info available.
> pydantic=1: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pydantic>=2.10.4: Installed. No version info available.
> pyjwt>=2.9.0: Installed. No version info available.
> pymilvus: 2.4.9
> pymongo: 4.10.1
> pytest-asyncio=0.20: Installed. No version info available.
> pytest-socket=0.6.0: Installed. No version info available.
> pytest=7: Installed. No version info available.
> pytest>=7.0.0;: Installed. No version info available.
> python-dotenv>=0.8.0;: Installed. No version info available.
> pytz>=2023.3.post1: Installed. No version info available.
> pyyaml=5.3.0: Installed. No version info available.
> PyYAML=5.3.0: Installed. No version info available.
> requests: 2.32.5
> requests-toolbelt>=1.0.0: Installed. No version info available.
> requests=2.0.0: Installed. No version info available.
> requests=2.32.5: Installed. No version info available.
> requests>=2.0.0: Installed. No version info available.
> rich>=13.9.4;: Installed. No version info available.
> spacy>=3.8.4;: Installed. No version info available.
> sqlalchemy=1.4.0: Installed. No version info available.
> SQLAlchemy=1.4.0: Installed. No version info available.
> sse-starlette=2.1.0: Installed. No version info available.
> sse-starlette>=2: Installed. No version info available.
> sseclient-py: 1.8.0
> starlette>=0.37: Installed. No version info available.
> starlette>=0.38.6: Installed. No version info available.
> structlog=24.1.0: Installed. No version info available.
> structlog>23: Installed. No version info available.
> syrupy=4: Installed. No version info available.
> tabulate: 0.9.0
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity>=8.0.0: Installed. No version info available.
> tiktoken=0.7.0: Installed. No version info available.
> tokenizers: 0.20.3
> truststore>=0.1: Installed. No version info available.
> types-requests: 2.32.0.20250328
> typing-extensions=4.7.0: Installed. No version info available.
> typing-extensions>=4.12.2: Installed. No version info available.
> unstructured-client: 0.25.9
> unstructured[all-docs]: Installed. No version info available.
> uvicorn>=0.26.0: Installed. No version info available.
> vcrpy>=7.0.0;: Installed. No version info available.
> watchfiles>=0.13: Installed. No version info available.
> zstandard>=0.23.0: Installed. No version info available.

## Comments

**keenborder786:**
@jmoreno11
You can stream, and when tool call happens, you can translate that through another AI chain call to something more human-readable.

**eyurtsev:**
@jmoreno11 could you explain in a few sentences what the proposed solution is logically?

The [PR](
https://github.com/langchain-ai/langchain/pull/34830) description explains what is being modified, not what the logical flow is that adds this:

```
"Based on what I found..."                     ← Natural text
```

---

We should first figure out what (if anything) can be done to *correctly* modify the LLMs behavior to provide this explanation in a way that plays nicely with chat history. And only then consider how to implement this. The solution is unlikely to involve adding more parameters to `create_agent`

**eyurtsev:**
Removed bug label since this doesn't seem like a bug, but as intended behavior right now and the issue is a feature that's requesting an extra summary out of the LLM before the structured output.

**eyurtsev:**
@jmoreno11 an alternative way to achieve what you want is to add an "explanation" field to the structured output schema to ask for an explanation / thinking etc

**jmoreno11:**
Hi @eyurtsev, thanks for response and apologies for the poor issue description. After coming back to it, I see that it's not clear. I updated it to better reflect the problem I'm having, but also here's a video where it's clear: if we pass `response_format`, we lose the intermediate messages.

In the example I show it's clear how this is a problem: I give two tasks (poem in binary and extract info), and only one is returned.

https://github.com/user-attachments/assets/417b5598-50ec-4e56-b3f3-6bfd02c441ba

**jmoreno11:**
Follow up comment for a real **bug** I encountered: 

When setting the `use_responses_api=True`, the `response_format` breaks the agent when using a pydantic model or `ProviderStrategy`. It only works with `ToolStrategy`.

I'll create a new bug issue, but wanted to give you the heads up here.

https://github.com/user-attachments/assets/806ea8b6-68fd-4e9c-902c-be30ef7f8a78

**keenborder786:**
@jmoreno11 
- Firstly, no matter if you are using response_api or not, given that you are not specifying a strategy for response format, for `gpt-4.1` it will use ProviderStrategy, which will use `json_schema` from OpenAI: https://platform.openai.com/docs/guides/structured-outputs
- Problem is that no matter whether you are using the response API or not, I have been able to get parsing error due to AI response drift, which is due toan unclear user message (your task is very funny and what you are trying to achieve, which is two completely different things, causing LLM to produce wrong output).
- I slightly updated your instructions as follows:
```python

from langchain.agents.factory import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    """Contact information for a person."""

    name: str = Field(description="The name of the person")
    email: str = Field(description="The email address of the person")
    phone: str = Field(description="The phone number of the person")
    poem: str = Field(description="The poem generated by the user") # I added this as well

llm = ChatOpenAI(
    model="gpt-4.1",
    use_responses_api=True
)

agent = create_agent(model=llm, response_format=ContactInfo)

for token in agent.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "Please first write a poem and then convert it to binary and then extract contact info from name: John Doe, email: john@example.com, phone: (555) 1. For name, email and phone, use small letter in keys."
            }
        ]
    },
    stream_mode="messages",
):
    for block in token[0].content_blocks:
        if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
            print(block.get("text"), end="")

```
and then faced no error, even after running it 50 times.
- Safe to say, this is not a bug in Langchain Parsing for ProviderStrategy, you are just giving very strange instructions.....

**jmoreno11:**
@keenborder786 thanks for the response, but my goal is not to get the _poem_ at the end, is to be able to still see streaming while the agent is working. This is an oversimplified example, but my agent is investigating internal company processes for minutes and needs to produce a structured output at the end. In the UI, I want to show the streaming of the intermediate steps and tool calls, but the issue I found is what I pointed out: when you set `response_format`, the streaming breaks.

**keenborder786:**
The root cause of streaming getting broken is due to your instructions and not due to an internal bug, no need of any changes to Langchain code or PR.

**toctavus:**
Great writeup on this issue! The breakdown of expected vs actual behavior is really helpful.

This is indeed a tricky UX problem—users want the responsive feel of streaming while also getting structured, type-safe outputs for downstream processing.

We ran into this same challenge building [Octavus](https://github.com/octavus-ai) and ended up treating streaming + structured output as orthogonal concerns in our protocol. The stream emits text deltas during generation, and when `responseType` is specified, the final structured object is parsed and emitted as a separate `UIObjectPart`:

```yaml
handlers:
  user-message:
    Respond:
      block: next-message
      responseType: ChatResponse  # Type schema defined in protocol
      output: RESPONSE  # Stores parsed object
```

The client receives both streaming text events AND the final typed object, so you get the conversational UX while still having type-safe data to work with.

Curious if the `force_tool_choice` approach in the linked PR fully solves the intermediate text streaming or if it's more about ensuring tools are called? The "Let me look that up..." intermediate messages seem like the key UX win here.
