# Allow to pass to .invoke method {messages: list[AnyMessage}

**Issue #35429** | State: open | Created: 2026-02-24 | Updated: 2026-03-09
**Author:** dantetemplar
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
from langchain.agents import create_agent
from langgraph.graph.message import MessagesState

# Create full agent
agent = create_agent(model="openai:gpt-4o-mini", system_prompt="You are a personalized assistant. Just say hi.")

agent.invoke(MessagesState(messages=[HumanMessage(content="What's your name?")]))
```

### Error Message and Stack Trace (if applicable)

```shell
Argument of type "MessagesState" cannot be assigned to parameter "input" of type "_InputAgentState | Command[Unknown] | None" in function "invoke"
  Type "MessagesState" is not assignable to type "_InputAgentState | Command[Unknown] | None"
    "messages" is an incompatible type
      "list[AnyMessage]" is not assignable to "list[AnyMessage | dict[str, Any]]"
    "MessagesState" is not assignable to "Command[Unknown]"
    "MessagesState" is not assignable to "None"basedpyrightreportArgumentType
Ctrl+click to open in new tab
```

### Description

Currently we cannot pass `list[AnyMessage]` as input to invoke method if we create agent with high-level `create_agent` util.

`create_agent` sets `_InputAgentState` as input schema, and `_InputAgentState` has bad typing on `list[AnyMessage | dict[...]`, so list from user code actually should accept both `AnyMessage` and `dict` .
https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py#L358-L361

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP PREEMPT_DYNAMIC Mon Nov 24 18:41:15 UTC 2025
> Python Version:  3.12.12 (main, Oct 10 2025, 00:00:00) [GCC 15.2.1 20250924 (Red Hat 15.2.1-2)]

Package Information
-------------------
> langchain_core: 1.2.10
> langchain: 1.2.10
> langsmith: 0.4.53
> langchain_openai: 1.1.8
> langgraph_sdk: 0.3.8

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.9
> openai: 1.109.1
> opentelemetry-api: 1.39.1
> opentelemetry-exporter-otlp-proto-http: 1.39.1
> opentelemetry-sdk: 1.39.1
> orjson: 3.11.7
> packaging: 25.0
> pydantic: 2.12.5
> pytest: 8.4.1
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.12.0
> zstandard: 0.25.0

## Comments

**dantetemplar:**
Actually, can't find solution to it. Very strange covariance issue on Discriminator.

**xXMrNidaXx:**
This is a **type covariance issue** with Python's `list` — valid runtime code, but the type checker complains.

**Why it happens:**

`list` is *invariant* in Python's type system (for good reason — lists are mutable). This means:
- `list[Animal]` is NOT a subtype of `list[Animal | Plant]`
- Even though every `Animal` is a valid `Animal | Plant`

`_InputAgentState.messages` is typed as:
```python
messages: list[AnyMessage | dict[str, Any]]
```

But `MessagesState.messages` is:
```python
messages: list[AnyMessage]
```

Type checkers correctly reject the assignment because someone could theoretically append a `dict` to the `list[AnyMessage | dict]` after the assignment, violating the `list[AnyMessage]` contract.

**Workarounds:**

1. **Cast at call site** (quick fix):
```python
from typing import cast
agent.invoke(cast(dict, state))
```

2. **Use Sequence instead of list** (proper fix):
```python
# Sequence is covariant, so this works:
messages: Sequence[AnyMessage | dict[str, Any]]
```

3. **Widen your input type** (manual):
```python
input_state = {"messages": list(state.messages)}  # fresh list
agent.invoke(input_state)
```

**Suggested fix for LangChain:**

Change `_InputAgentState.messages` to use `Sequence` or `Iterable`:
```python
class _InputAgentState(TypedDict, total=False):
    messages: Sequence[AnyMessage | dict[str, Any]]  # Covariant!
```

This would make the type signature accept both `list[AnyMessage]` and `list[AnyMessage | dict]` without runtime behavior changes.

---
*[RevolutionAI](https://revolutionai.io) — We hit these covariance gotchas regularly when building typed agent pipelines. Happy to test a PR.*

**xXMrNidaXx:**
Good feature request! Passing messages directly would simplify a lot of code.

**Current workaround:**
```python
from langchain_core.messages import HumanMessage, AIMessage

messages = [HumanMessage(content="Hello"), AIMessage(content="Hi!")]

# Instead of invoke, use the chat model directly
response = chat_model.invoke(messages)
```

**For RunnableSequence:**
```python
from langchain_core.runnables import RunnablePassthrough

chain = RunnablePassthrough() | chat_model
result = chain.invoke({"messages": messages})
```

Would love to see `invoke(messages=[...])` as a first-class pattern!

---

Building with LangChain? We are hiring: https://www.revolutionai.io/find-work
