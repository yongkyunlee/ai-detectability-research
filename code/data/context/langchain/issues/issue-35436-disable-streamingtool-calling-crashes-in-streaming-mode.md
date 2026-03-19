# `disable_streaming="tool_calling"` crashes in streaming mode

**Issue #35436** | State: open | Created: 2026-02-25 | Updated: 2026-03-17
**Author:** edwardmeng
**Labels:** bug, core, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
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

#34654

### Reproduction Steps / Example Code (Python)

```python
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Sunny in {city}"

llm = ChatOpenAI(
    model="qwen-max",  # or any OpenAI-compatible model
    openai_api_key="your-key",
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.3,
    streaming=True,
    disable_streaming="tool_calling",
)

agent = create_react_agent(model=llm, tools=[get_weather])

async def main():
    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]},
        version="v2",
    ):
        print(event["event"])

asyncio.run(main())
```

### Error Message and Stack Trace (if applicable)

```shell
AttributeError: 'AsyncStream' object has no attribute 'model_dump'

  File "langchain_core/language_models/chat_models.py", line 1361, in _agenerate_with_cache
    result = await self._agenerate(...)
  File "langchain_openai/chat_models/base.py", line 1744, in _agenerate
    return await run_in_executor(None, self._create_chat_result, response, generation_info)
  File "langchain_openai/chat_models/base.py", line 1540, in _create_chat_result
    response if isinstance(response, dict) else response.model_dump()
    # response is an AsyncStream, not a ChatCompletion
```

### Description

There are **two separate bugs** that make `disable_streaming="tool_calling"` unusable with `ChatOpenAI` when `streaming=True`:

Bug 1: `_agenerate` receives an **AsyncStream** instead of **ChatCompletion**
Root cause: `BaseChatOpenAI._default_params` hardcodes `"stream": self.streaming`.
```
@property
def _default_params(self) -> dict[str, Any]:
    return {
        "model": self.model_name,
        "stream": self.streaming,  # ← always True when streaming=True
        **{k: v for k, v in exclude_if_none.items() if v is not None},
        **self.model_kwargs,
    }
```
When `disable_streaming="tool_calling"` triggers, `BaseChatModel._agenerate_with_cache` calls `_agenerate()` instead of `_astream()`. But `_agenerate()` calls `_get_request_payload()` which includes `_default_params` → `stream=True` is in the payload → the OpenAI async client returns an `AsyncStream` → `_create_chat_result` calls `response.model_dump()` → crash.

Bug 2: `_should_stream` disables streaming for ALL turns, not just tool-call turns
Root cause: In `BaseChatModel._should_stream`
```
if self.disable_streaming == "tool_calling" and kwargs.get("tools"):
    return False
```
This checks whether tools are bound (`kwargs.get("tools")`), not whether the current response contains tool calls. When using `create_react_agent` (or any agent with `bind_tools`), tools are always in `kwargs` for every LLM invocation — including the final text-response turn. This means `_should_stream` returns `False` for all turns, completely disabling token-by-token streaming.

This is an inherent limitation: you can't know whether a response will contain tool calls before making the API call. However, the current behavior is misleading — `disable_streaming="tool_calling"` suggests it only affects tool-calling turns, but it actually disables streaming entirely when tools are bound.

**Context: Why this matters**
OpenAI-compatible providers (e.g., Dashscope/Qwen, vLLM) sometimes produce malformed tool call chunks during streaming — splitting a single tool call into a valid call with empty args and an invalid fragment containing the actual args. disable_streaming="tool_calling" would be the ideal fix (non-streaming for tool calls = no chunk splitting), but the two bugs above make it unusable.

### System Info

```
System Information
------------------
> OS:  Windows
> OS Version:  10.0.26200
> Python Version:  3.13.12 (tags/v3.13.12:1cbe481, Feb  3 2026, 18:22:25) [MSC v.1944 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 1.2.15
> langchain: 1.2.10
> langchain_community: 0.4.1
> langsmith: 0.7.6
> langchain_anthropic: 1.3.3
> langchain_classic: 1.0.1
> langchain_openai: 1.1.10
> langchain_text_splitters: 1.1.1
> langgraph_sdk: 0.3.8

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.3
> anthropic: 0.83.0
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.9
> numpy: 2.4.2
> openai: 2.22.0
> orjson: 3.11.7
> packaging: 24.2
> pydantic: 2.12.5
> pydantic-settings: 2.13.1
> PyYAML: 6.0.3
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> SQLAlchemy: 2.0.46
> sqlalchemy: 2.0.46
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> wrapt: 2.1.1
> xxhash: 3.6.0
> zstandard: 0.25.0
```
The same bugs exist in the latest master source code (verified Feb 25, 2026) — `_default_params` still includes `"stream": self.streaming` and `_should_stream` still checks `kwargs.get("tools")`.

## Comments

**xXMrNidaXx:**
Ran into a similar issue! The `disable_streaming="tool_calling"` option seems to have a logic bug when used with `astream_events`.

**Root Cause Analysis:**

Looking at the langchain-core code, when `disable_streaming="tool_calling"` is set, the model is supposed to:
1. Detect when a tool call is being made
2. Fall back to non-streaming for just that inference
3. Resume streaming for regular responses

The issue appears to be in how `astream_events` handles the mode switch. When the model decides to use a tool, the streaming context isn't properly suspended, leading to the crash.

**Workaround until fixed:**

```python
from langchain_core.callbacks import AsyncCallbackHandler

class ToolCallStreamingHandler(AsyncCallbackHandler):
    """Manually handle streaming suspension during tool calls."""
    
    async def on_llm_start(self, *args, **kwargs):
        # Check if this is a tool-calling turn
        pass
    
    async def on_tool_start(self, *args, **kwargs):
        # Suspend streaming events here
        pass

# Alternative: disable streaming entirely for tool-using agents
llm = ChatOpenAI(
    model="qwen-max",
    streaming=False,  # Disable streaming when tools are primary use case
    # ... other params
)
```

**Suggested Fix Direction:**

The `_generate_with_tools` method in langchain-core should check the streaming context before attempting to yield events. Something like:

```python
if self.disable_streaming == "tool_calling" and is_tool_call_response:
    # Use invoke instead of stream for this turn
    return await self._ainvoke_non_streaming(...)
```

Would be happy to look at a PR for this if maintainers can point to the right file to modify!

**xXMrNidaXx:**
## Analysis and Workaround

The issue stems from `disable_streaming="tool_calling"` not properly handling the async stream context when the model response requires tool calls. When tool calling is detected, the code attempts to call `model_dump()` on an `AsyncStream` object instead of first collecting the streamed chunks.

### Root Cause

In `langchain_core/language_models/chat_models.py`, the `_agenerate_with_cache` method branches based on `disable_streaming` but the tool-calling path doesn't properly await and collect the stream before accessing result attributes.

### Workarounds

**Option 1: Disable streaming entirely for tool-calling agents**

```python
llm = ChatOpenAI(
    model="qwen-max",
    openai_api_key="your-key",
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.3,
    streaming=False,  # Disable all streaming
)
```

**Option 2: Custom stream handling wrapper**

```python
from langchain_core.callbacks import BaseCallbackHandler

class ToolCallStreamFixer(BaseCallbackHandler):
    """Intercept and fix tool call streaming issues"""
    
    async def on_llm_start(self, *args, **kwargs):
        # Force non-streaming for tool detection
        pass

# Use with callbacks
agent = create_react_agent(
    model=llm, 
    tools=[get_weather],
    # Use non-streaming invoke for initial tool detection
)
```

**Option 3: Use `astream` instead of `astream_events`**

```python
async for chunk in agent.astream(
    {"messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]}
):
    print(chunk)
```

### Suggested Fix

The SDK should check if the response is an `AsyncStream` and collect it before calling `model_dump()`:

```python
# In _agenerate_with_cache
if hasattr(result, "__aiter__"):
    # Collect stream chunks first
    chunks = [chunk async for chunk in result]
    result = self._combine_chunks(chunks)
```

Would be happy to submit a PR if maintainers confirm this approach.

---
*Encountered this while building AI agents for retail automation. Happy to provide more details if helpful.*

**AlonNaor22:**
I've submitted a fix for Bug 1 (the crash) in #35573 — `_generate` and `_agenerate` now explicitly set `stream=False` in the payload, preventing the OpenAI client from returning a `Stream`/`AsyncStream` when the non-streaming path is taken.

Regarding **Bug 2** (`_should_stream` disabling streaming for all turns when tools are bound): this is a design-level issue since you can't know whether a response will contain tool calls before making the API call. The current check `kwargs.get("tools")` effectively makes `disable_streaming="tool_calling"` equivalent to `disable_streaming=True` whenever tools are bound.

A few potential approaches I see:

1. **Accept as-is** and document the current behavior (streaming is disabled for all turns when `disable_streaming="tool_calling"` and tools are bound)
2. **Stream-first, fallback approach** — always stream, but if tool calls are detected in the response, re-issue as non-streaming (doubles API cost on tool-call turns, but preserves streaming for text-response turns)
3. **Smarter heuristic** — e.g., only disable streaming when the message history suggests a tool call is likely (no prior tool results in context)

Would appreciate maintainer guidance on which direction (if any) is preferred for Bug 2 before working on a follow-up PR.

**NIK-TIGER-BILL:**
I would like to work on this issue.

I have identified both bugs:
1. In `_create_chat_result()` (`langchain_openai/chat_models/base.py`): when `disable_streaming="tool_calling"` is set and the model is streaming-capable, the async path calls the non-streaming API but still receives an `AsyncStream` object in some code paths. `_create_chat_result()` then calls `response.model_dump()` which fails since `AsyncStream` has no such method.
2. The sync path likely has a mirrored issue.

Could a maintainer please assign this issue to me? I will open a PR once assigned. Thank you!

**Ker102:**
I'd like to work on this. The crash when `disable_streaming="tool_calling"` is used with streaming looks like the streaming code path doesn't check the `disable_streaming` flag before trying to process tool call chunks. Could I be assigned?

**nevanwang:**
Hi, I've done a thorough analysis of this issue and identified the root causes. I'd like to propose a fix and would be happy to submit a PR.

## Root Cause Analysis

### Bug 1: `_agenerate` receives `AsyncStream` instead of `ChatCompletion` when `streaming=True`

**Location:** `libs/partners/openai/langchain_openai/chat_models/base.py` — `BaseChatOpenAI._agenerate()` and `BaseChatOpenAI._generate()`

**The flow:**
1. When `disable_streaming="tool_calling"` and `tools` are provided, `_should_stream()` in `langchain-core` correctly returns `False`.
2. `_agenerate_with_cache()` then falls through to call `self._agenerate()` (the non-streaming path).
3. However, `_agenerate()` builds the payload via `self._get_request_payload(messages, stop=stop, **kwargs)`, which merges `_default_params` into the payload.
4. `_default_params` includes `"stream": self.streaming`. When users instantiate with `ChatOpenAI(streaming=True)` (or OpenAI-compatible providers like Dashscope/vLLM set it), the payload gets `stream=True`.
5. When `stream=True` is in the payload, `self.async_client.with_raw_response.create(**payload)` returns an `AsyncStream` object, not a `ChatCompletion`.
6. Calling `raw_response.parse()` on this yields an `AsyncStream`, which then fails downstream when `_create_chat_result()` tries to access it as a `ChatCompletion`.

**The sync `_generate()` has the same bug** — it shares identical logic.

**Fix:** In `_agenerate()` (and `_generate()`), explicitly ensure `stream=False` in the payload **before** calling the API. These methods are specifically for non-streaming completion calls, so they should always use `stream=False`:

```python
async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
    payload = self._get_request_payload(messages, stop=stop, **kwargs)
    payload["stream"] = False  # Force non-streaming for _agenerate
    ...
```

And the same for sync `_generate()`.

### Bug 2: `_should_stream()` disables streaming for ALL turns, not just tool-calling turns

**Location:** `libs/core/langchain_core/language_models/chat_models.py` — `_should_stream()`

**Current code:**
```python
if self.disable_streaming == "tool_calling" and kwargs.get("tools"):
    return False
```

**The problem:** The `tools` kwarg is typically passed via `bind_tools()`, which means it's present in **every** invocation of the model — including turns that don't actually make tool calls (e.g., the model's final text response after a tool result is returned). The intent of `disable_streaming="tool_calling"` is to disable streaming only when the model is **expected to produce tool calls**, but the current implementation disables it whenever `tools` is in the kwargs, which is always true for tool-bound models.

This is actually by design per the docstring: *"will bypass streaming case only when the model is called with a `tools` keyword argument"*. However, users reasonably expect `disable_streaming="tool_calling"` to mean "disable streaming only on the specific turns where tool calls are generated, not on text-response turns".

**Proposed approach:** This second bug is more nuanced. I'd recommend keeping the current behavior for now and clarifying the documentation, since predicting whether the model will produce tool calls vs text at invocation time is not reliably possible.

## Proposed Changes

1. **`libs/partners/openai/langchain_openai/chat_models/base.py`**: Force `stream=False` in both `_generate()` and `_agenerate()` payload, since these methods are only invoked on the non-streaming code path.
2. **Add regression tests**: Test `disable_streaming="tool_calling"` with `streaming=True` to verify the non-streaming fallback works correctly.
3. (Optional) Update docstring for `disable_streaming` to clarify the `"tool_calling"` behavior scope.

I'd love to take this on and submit a PR. Could you assign this issue to me?
