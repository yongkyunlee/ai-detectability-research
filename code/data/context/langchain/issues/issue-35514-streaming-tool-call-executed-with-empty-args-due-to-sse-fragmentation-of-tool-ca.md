# Streaming tool call executed with empty args {} due to SSE fragmentation of tool call arguments

**Issue #35514** | State: open | Created: 2026-03-02 | Updated: 2026-03-11
**Author:** backer-and
**Labels:** bug, core, openai, external

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
- [x] langchain-openai
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

#32562, #30563, #32016, langchain-ai/langchainjs#8394

### Reproduction Steps / Example Code (Python)

```python
import os
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool

@tool
def my_tool(url: str) -> str:
    """Fetch data from the given URL."""
    return f"Fetched: {url}"

llm = ChatOpenAI(
    model="deepseek/deepseek-v3.2",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

agent = create_agent(
    model=llm,
    tools=[my_tool],
    system_prompt="You are a helpful assistant.",
)

import asyncio

async def main():
    async for stream_mode, data in agent.astream(
        {"messages": [{"role": "user", "content": 'Use my_tool with "http://mywebsite.com"'}]},
        stream_mode=["messages", "updates"],
    ):
        if stream_mode == "messages":
            token, metadata = data
            if hasattr(token, 'tool_call_chunks') and token.tool_call_chunks:
                for tc in token.tool_call_chunks:
                    print(f"[TOOL_CHUNK] name={tc.get('name')} args={tc.get('args')!r} id={tc.get('id')}")
            if hasattr(token, 'tool_calls') and token.tool_calls:
                for tc in token.tool_calls:
                    print(f"[TOOL_CALL_PARSED] name={tc.get('name')} args={tc.get('args')}")

asyncio.run(main())
```

### Error Message and Stack Trace (if applicable)

```shell
ToolException: Error executing tool my_tool: 1 validation error for my_toolArguments
url
  Field required [type=missing, input_value={}, input_type=dict]
    at langgraph/prebuilt/tool_node.py
    at langchain_core/tools/base.py
```

### Description

When streaming tool calls via OpenRouter (tested with `deepseek/deepseek-v3.2`), the agent executes tools with empty args `{}`, causing `Field required` validation errors. The root cause is that OpenRouter's upstream providers fragment tool call arguments across multiple SSE chunks, and langchain parses the first empty chunk as a valid tool call.

**Instrumented streaming output showing the problem:**

```
[TOOL_CHUNK] name=my_tool args='' id=call_34db6a0a9d314d71a8a74b3d
[TOOL_CALL_PARSED] name=my_tool args={}           ← parsed as valid, tool executed with empty args
[TOOL_CHUNK] name= args='{' id=
[TOOL_CHUNK] name= args='"url": "http://mywebsite.com"' id=
[TOOL_CHUNK] name= args='}' id=
```

The first chunk arrives with `name="my_tool"` and `args=""`. `parse_partial_json("")` returns `{}` — a valid but empty dict. The ToolNode executes the tool immediately with these empty args. The subsequent chunks containing the actual arguments arrive too late.

**This fragmentation is common across providers.** I tested all 8 upstream providers available for this model on OpenRouter. Most exhibit this pattern, with varying frequency. The failure rate in production depends on which provider OpenRouter routes to and timing conditions.

When the agent encounters the error, it often retries the tool call in a loop, generating the same fragmented pattern repeatedly until hitting the recursion limit.

**JS-side fix exists:** This is the same root cause reported and fixed on the JS side in langchain-ai/langchainjs#8394 (PR langchain-ai/langchainjs#8419). The fix concatenates all `tool_call_chunks` belonging to the same tool call before parsing. As far as I can tell, this hasn't been ported to the Python side.

**Workaround:** Setting `streaming=False` on `ChatOpenAI` reliably resolves the issue.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  Ubuntu 22.04
> Python Version:  3.12.3

Package Information
-------------------
> langchain_core: 1.2.14
> langchain: 1.2.10
> langchain_openai: 1.1.10
> langgraph: 1.0.9

Other Dependencies
------------------
> openai: 2.21.0
> pydantic: 2.12.5
> httpx: 0.28.1

## Comments

**backer-and:**
@A404coder CI is currently failing due to ruff F401: `merge_lists` is imported in `langchain_core/messages/ai.py` but not used (so it can be removed or used).

Also, it looks like a small edge case can happen: in `init_tool_calls()`, when `concatenated_args == ""` you set `args_ = {}` and still emit a `tool_call`. With providers that stream args in later SSE fragments, this might lead to early tool execution with `{}`. It may be worth delaying `tool_calls` emission/handling until the args are non-empty (or until the JSON is parseable / final).

**JiwaniZakir:**
I'd like to work on this issue. I'll submit a PR shortly.

**JiwaniZakir:**
I've submitted a PR to address this issue: https://github.com/langchain-ai/langchain/pull/35528

**aashmawy:**
Hi all, sharing something I put together in case it helps with triage for #35514:

https://github.com/aashmawy/trajectly-experiments/tree/main/langchain-issue-35514-harness

It models the same failure pattern described here: fragmented `tool_call_chunks` where the first chunk has `name` + empty `args`, which can lead to early tool execution with `{}` and a missing required field error.

What this repo is meant to help with:
- deterministic baseline vs regression checks for this failure class
- one-command local verification (`bash scripts/verify_demo.sh`)
- CI gate that catches this behavior consistently

This is not an upstream fix; it is just a small reproducible regression harness to make investigation and validation easier.  

Feedback is very welcome. Hope this could be useful to others.

**JiwaniZakir:**
Hey, I ran into this too and think I can put together a fix. Taking a crack at it. I'll include a test to prevent regression.

**JiwaniZakir:**
Here's my fix: https://github.com/langchain-ai/langchain/pull/35617 -- happy to iterate on feedback.

**alemarcosa:**
The empty-args execution path you described is exactly the kind of thing that makes tool calling feel unsafe even when the higher-level agent logic is sound. If a partial stream chunk can trigger a real tool run, then validation is happening too late. I’ve been looking at Daedalab because it focuses on that preflight layer: block invalid tool calls, prevent repeat failures, and make the execution path observable enough to debug quickly.

**giulio-leone:**
PR #35634 addresses this — it accumulates tool call argument deltas until the AIMessageChunk is complete before executing the tool, preventing empty `{}` args from SSE fragmentation.

**mvanhorn:**
Submitted a fix in #35743. The root cause is a truthiness check (`if chunk["args"]`) that treats empty string `""` as falsy and defaults to `{}`. Changed to `if chunk["args"] is not None` so empty strings from SSE fragmentation go through `parse_partial_json` instead of being treated as complete empty args.

**mvanhorn:**
I'd like to work on this issue. Could I be assigned?
