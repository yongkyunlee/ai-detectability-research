# InjectedState with a NotRequired state field raises KeyError when the field is absent from state

**Issue #35585** | State: open | Created: 2026-03-06 | Updated: 2026-03-09
**Author:** linda-ai-receptionist
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

_No response_

### Reproduction Steps / Example Code (Python)

```python
from typing import Annotated

from langchain_core.tools import tool
from langchain.agents import create_agent
from typing_extensions import NotRequired
from langgraph.prebuilt import InjectedState
from langchain.agents import AgentState

class CustomAgentState(AgentState):
    city: NotRequired[str]

@tool
def get_weather(city: Annotated[str, InjectedState("city")]) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def build_graph():
    """Build and compile the agent graph."""
    return create_agent(
        model="claude-sonnet-4-6",
        tools=[get_weather],
        system_prompt="You are a helpful assistant",
        state_schema=CustomAgentState,
    )
```

### Error Message and Stack Trace (if applicable)

```shell
File ".../langgraph/prebuilt/tool_node.py", line 1358, in _inject_tool_args
    state[state_field] if state_field else state
    ~~~~~^^^^^^^^^^^^^
KeyError: 'city'
```

### Description

**Description**

When using `InjectedState()` on a tool parameter, and the referenced field is declared as NotRequired in the custom state schema, the ToolNode crashes with an unhandled KeyError if that field was never populated in the state.

We noticed this behaviour after upgrading to langchain >= 1.0.0. The same behaviour could not be reproduced with earlier versions.

### System Info

```
System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 23.5.0: Wed May  1 20:12:58 PDT 2024; root:xnu-10063.121.3~5/RELEASE_ARM64_T6000
> Python Version:  3.13.2 (main, Feb  4 2025, 14:51:09) [Clang 16.0.0 (clang-1600.0.26.6)]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langsmith: 0.7.13
> langchain_anthropic: 1.3.4
> langchain_openai: 1.1.10
> langgraph_sdk: 0.3.9
```

## Comments

**linda-ai-receptionist:**
Conversely, a similer code does produce a valid tool output with older versions.

```
from typing import Annotated
from typing import Optional, Annotated
from langchain_core.messages import AnyMessage
from langgraph.prebuilt import InjectedState
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

class CustomAgentState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int = Field(default=10)
    city: Optional[str] = Field(default=None)

def get_weather(city: Annotated[Optional[str], InjectedState("city")]) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def build_graph():
    """Build and compile the agent graph."""
    return create_react_agent(
        model="claude-sonnet-4-6",
        tools=[get_weather],
        prompt="You are a helpful assistant",
        state_schema=CustomAgentState,
    )
```

produces a valid tool output

```
[{'id': 'toolu_01SK9NoiRaRk7LK5MnreMiYH', 'caller': {'type': 'direct'}, 'input': {}, 'name': 'get_weather', 'type': 'tool_use'}]
Tool Calls:
  get_weather (toolu_01SK9NoiRaRk7LK5MnreMiYH)
 Call ID: toolu_01SK9NoiRaRk7LK5MnreMiYH
  Args:
================================= Tool Message =================================
Name: get_weather

It's always sunny in None!
```

with the following old dependencies

```
Package Information
-------------------
> langchain_core: 0.3.83
> langchain: 0.3.27
> langsmith: 0.7.13
> langchain_anthropic: 0.3.22
> langchain_openai: 0.3.35
> langchain_text_splitters: 0.3.11
> langgraph_sdk: 0.3.9
```

**ashmaac:**
Hi, I'd like to work on this! Could you assign it to me? I'm a Python developer looking to contribute.

**ashmaac:**
I've submitted a fix for this in PR [#7039](https://github.com/langchain-ai/langgraph/pull/7039)

**JiwaniZakir:**
Picked this up -- working on a fix now. I'll include a test to prevent regression.

**JiwaniZakir:**
PR is up: https://github.com/langchain-ai/langchain/pull/35638

**xXMrNidaXx:**
The issue is that `InjectedState` in LangGraph's tool node does a direct key lookup (`state[state_field]`) without checking whether the field is `NotRequired` and might be absent from the state dict.

When you use `NotRequired[str]` in your state schema, the field may legitimately not be present in the state. The tool node should handle this gracefully.

**Workaround:**

Provide a default value for the `NotRequired` field in your state initialization:

```python
from typing import Annotated
from langchain_core.tools import tool
from typing_extensions import NotRequired
from langgraph.prebuilt import InjectedState
from langchain.agents import AgentState, create_agent

class CustomAgentState(AgentState):
    city: NotRequired[str]

@tool
def get_weather(city: Annotated[str, InjectedState("city")]) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# When invoking, always include the field (even if empty)
graph = build_graph()
result = graph.invoke({
    "messages": [...],
    "city": ""  # provide empty default to avoid KeyError
})
```

Or make the tool handle the missing case by using `Optional`:

```python
@tool  
def get_weather(city: Annotated[str | None, InjectedState("city")] = None) -> str:
    """Get weather for a given city."""
    if not city:
        return "No city specified."
    return f"It's always sunny in {city}!"
```

**Fix direction:** The `_inject_tool_args` method in `tool_node.py:1358` should use `state.get(state_field)` instead of `state[state_field]`, or check whether the field is marked as `NotRequired` in the schema and skip injection when the field is absent.
