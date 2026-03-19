# [langchain-openai] with_structured_output() silently drops previously bound tools and lacks support for OpenAI native tool bindings

**Issue #35320** | State: open | Created: 2026-02-19 | Updated: 2026-03-09
**Author:** ardakdemir
**Labels:** bug, openai, external

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

[Related issue: #28848](https://github.com/langchain-ai/langchain/issues/28848)

This is related to #28848 (`bind_tools` not callable after `with_structured_output`), which describes the reverse ordering problem. This issue covers a different but connected scenario: when `.bind(tools=...)` is called **before** `.with_structured_output()`, the tools are **silently dropped** from the API request with no error or warning. Together, these issues show that `with_structured_output()` and tool bindings are fundamentally incompatible in **both** directions — and neither direction gives the user a clear signal.

### Reproduction Steps / Example Code (Python)

```python
from langchain_openai import ChatOpenAI
from langchain_core.utils.function_calling import convert_to_openai_function
from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    temperature: float = Field(description="The temperature in fahrenheit")
    condition: str = Field(description="The weather condition")

llm = ChatOpenAI(model="gpt-5-mini")

# ----------------------------------------------------------------
# BUG: .with_structured_output() silently drops tools from .bind()
# ----------------------------------------------------------------

# Step 1 — Bind an OpenAI native tool (e.g. web_search)
llm_with_tools = llm.bind(tools=[{"type": "web_search"}])

# Step 2 — Apply structured output on top
chain = llm_with_tools.with_structured_output(WeatherResponse)

# Step 3 — Invoke
result = chain.invoke("What is the weather in San Francisco right now?")
print(result)
# => temperature=57.0
#    condition='Estimated typical current weather: cool and often foggy.
#    I can't access live weather data — ...'
#
# The model HALLUCINATED the weather because web_search was silently dropped.
# No error, no warning — it just disappears.

# ----------------------------------------------------------------
# WORKAROUND: bypass with_structured_output(), use a single .bind()
# ----------------------------------------------------------------

# Users must manually replicate LangChain's internal schema conversion
# to build the response_format dict — no Pydantic convenience here.
function = convert_to_openai_function(WeatherResponse, strict=True)
function["schema"] = function.pop("parameters")
response_format = {"type": "json_schema", "json_schema": function}

llm_fixed = llm.bind(
    tools=[{"type": "web_search"}],
    tool_choice="auto",
    response_format=response_format,
)

result = llm_fixed.invoke("What is the weather in San Francisco right now?")
print(result)
# => content=[..., {'type': 'web_search_call', 'status': 'completed', ...},
#    ..., {'type': 'text', 'text': '{"temperature":52,"condition":"Mostly cloudy ..."}'}]
#
# The model correctly performed a web search and returned real data.
```

### Error Message and Stack Trace (if applicable)

```shell
**There is no error.** That is the core problem — this fails **completely silently**.

No exception is raised, no warning is logged, no deprecation notice is emitted. The `tools` parameter is simply absent from the HTTP request payload sent to OpenAI. This was confirmed by inspecting raw HTTP requests via `httpx` event hooks.

The model returns a plausible-looking response (hallucinated data), making it very difficult to notice that tools were dropped.
```

### Description

#### Part 1: Bug — Silent dropping of all tool bindings

Calling `.bind(tools=[...])` followed by `.with_structured_output(schema)` on a `ChatOpenAI` instance causes the tool bindings to be **silently discarded**.

**Root cause:** `with_structured_output()` internally creates a new `RunnableSequence` that configures its own model bindings to enforce the output schema (via `response_format` or `tool_choice`). These new bindings **do not merge** with the previously bound kwargs from `.bind()`. The `tools` kwarg is effectively overwritten.

This silent drop affects **all tool types** — both OpenAI native tools (`{"type": "web_search"}`) and custom LangChain tools (callables passed via `bind_tools()`). Any kwargs set via `.bind()` before calling `.with_structured_output()` are lost.

I verified this by injecting `httpx` event hooks to log the raw HTTP request body. The logs confirmed:

| Scenario | `tools` in payload | `response_format` in payload |
|---|---|---|
| `.bind(tools=...)` then `.with_structured_output(...)` | **Missing** | Present |
| `.bind(tools=..., response_format=...)` (workaround) | **Present** | Present |

#### Part 2: Feature gap — No Pydantic-friendly path for native tools + structured output

The OpenAI API fully supports sending **both** `tools` and `response_format` in the same request — these are independent, composable features. This is especially important for OpenAI's native tools (`web_search`, `code_interpreter`, `file_search`), which are designed to work alongside structured output: the model uses the tool internally and returns results in the structured format.

However, there is currently **no way** to combine a Pydantic class (via `with_structured_output()`) with native tools. The only workaround is to:

1. Manually convert the Pydantic class to an OpenAI-compatible JSON schema dict (replicating LangChain's internal `_convert_to_openai_response_format` logic)
2. Pass both `tools` and `response_format` in a single `.bind()` call

This defeats the purpose of the `with_structured_output()` abstraction and forces users to work at a lower level of the API.

### Why This Is a Problem

1. **Silent failures are dangerous.** The code appears to work — it returns structured JSON — but the model is hallucinating instead of using the tool. In a production system this produces incorrect results with no signal that something is wrong. Libraries should fail fast and loud, not silently swallow configuration.

2. **No Pydantic path for a common use case.** Combining native tools with structured output is a mainstream OpenAI pattern (e.g., "search the web and return results as this Pydantic schema"). Today, users cannot use `with_structured_output(MyPydanticModel)` for this — they must manually build the `response_format` dict, which is error-prone and bypasses LangChain's schema validation and strict-mode handling.

3. **The workaround is non-trivial.** Users must replicate LangChain's internal `_convert_to_openai_response_format` logic (using `convert_to_openai_function`, renaming `parameters` → `schema`, wrapping in the `json_schema` envelope). This is fragile and may break across LangChain versions.

### Suggested Fix

**Option A — Preserve existing bindings (minimal fix for the bug):**

`with_structured_output()` should read the current `self.kwargs` before creating new bindings and merge them, so previously bound tools are not lost:

```python
# Inside with_structured_output(), before creating the new chain:
existing_kwargs = getattr(self, 'kwargs', {})
# Merge tools, tool_choice, etc. from existing_kwargs into the new binding
```

**Option B — Accept a `tools` parameter directly (fixes both bug and feature gap):**

Allow `with_structured_output()` to accept tools alongside the Pydantic schema, so users can combine them in a single call:

```python
# Allow users to specify tools and structured output together:
llm.with_structured_output(
    WeatherResponse,
    tools=[{"type": "web_search"}],
    tool_choice="auto",
)
```

This would provide the Pydantic convenience that users expect, while correctly sending both `tools` and `response_format` to the OpenAI API.

**Option C — At minimum, warn or raise (fixes the silent failure):**

If supporting both is not feasible, detect when previously bound kwargs would be lost and raise an explicit error:

```python
if self.kwargs.get("tools"):
    raise ValueError(
        "with_structured_output() does not preserve previously bound tools. "
        "Use llm.bind(tools=..., response_format=...) instead to combine "
        "tools with structured output."
    )
```

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.2.0: Tue Nov 18 21:09:41 PST 2025; ---
> Python Version:  3.13.11 (main, Dec  5 2025, 16:06:33)---

Package Information
-------------------
> langchain_core: 1.2.8
> langsmith: 0.4.60
> langchain_openai: 1.1.7
> langgraph_sdk: 0.3.3

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> openai: 2.16.0
> opentelemetry-api: 1.39.1
> opentelemetry-sdk: 1.39.1
> orjson: 3.11.7
> packaging: 25.0
> pydantic: 2.12.5
> pytest: 8.4.2
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.2
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> zstandard: 0.25.0

## Comments

**keenborder786:**
@ardakdemir If you want to bind tools while using `with_structured_output`, you can just pass tools as a parameter, and it will be binded as a parameter which will send to final request payload to OpenAI:
```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    temperature: float = Field(description="The temperature in fahrenheit")
    condition: str = Field(description="The weather condition")

llm = ChatOpenAI(model="gpt-5-mini")
chain = llm.with_structured_output(WeatherResponse, tools=[{"type": "web_search"}])
result = chain.invoke("What is the weather in San Francisco right now?")
print(result)

```

This is the payload that is send to OpenAI API (for above code), therefore avoiding the drop of tools:
```python
{'model': 'gpt-5-mini', 'stream': False, 'input': [{'content': 'What is the weather in San Francisco right now?', 'role': 'user'}], 'tools': [{'type': 'web_search'}], 'text_format': }

```

**ardakdemir:**
### Update: `with_structured_output()` actually accepts `tools=` as a kwarg

(shared by [rolsonjr](https://github.com/rolsonjr))

After further testing, I discovered that `with_structured_output()` **does** pass through `**kwargs` to the internal `.bind()` call. This means the following works correctly:

```python
# ✅ Works — tools passed directly as kwarg to with_structured_output()
chain = llm.with_structured_output(
    WeatherResponse,
    include_raw=True,
    strict=True,
    tools=[{"type": "web_search"}],
)
result = chain.invoke("What is the weather in San Francisco right now?")
# => parsed: temperature=51.0 condition='Mostly cloudy'
# => raw: [..., {'type': 'web_search_call', 'status': 'completed'}, ...]
# Web search ran, real data returned, structured output parsed correctly.
```

While the sequential pattern silently drops them:

```python
# ❌ Silent failure — tools are dropped
chain = llm.bind(tools=[{"type": "web_search"}]).with_structured_output(WeatherResponse)
# => temperature=57.0 condition='Estimated typical current weather: cool and often foggy...'
# No web search, hallucinated data.
```

**This reinforces that the bug is specifically about `with_structured_output()` not merging with previously bound kwargs.** The method *can* handle tools — it just creates a fresh `.bind()` internally instead of merging with existing ones.

This also provides a **simpler workaround** than manually constructing `response_format`: just pass `tools=` directly to `with_structured_output()`.

However, the core issues remain:
1. The silent drop of previously bound kwargs is still a bug — it should at minimum warn
2. The `tools=` kwarg on `with_structured_output()` is undocumented — users have no way to discover it

**keenborder786:**
@ardakdemir I think so, it might be a usecase where the user might call a method sequentially after binding parameters, which will be ignored in the underlying method. 
The root fix will be in `RunnableBinding.__getattr__` as right now, only configs are being passed, and **kwargs are ignore.
However, specifically for `with_structured_output `, I will still recommend you use the tools passing the way suggested.

**ardakdemir:**
Thanks @keenborder786  for the quick response and for identifying the root cause in RunnableBinding.__getattr__! That's really helpful.
We'll use the recommended approach of passing `tools=` directly to `with_structured_output() `for our use case.

That said, I think the sequential pattern (.bind().with_structured_output()) silently dropping kwargs is still worth addressing, since it's a subtle footgun: no error, no warning, just hallucinated output in the case of dropping the web search tool. Even if the fix in RunnableBinding.__getattr__ is non-trivial, a warning when kwargs are silently dropped would save others from debugging the same issue.
Updated documentation showing the correct pattern for combining native tools with structured output would also be very valuable.

Happy to contribute a PR for either the warning or the docs update if that would be helpful, just let me know!

**keenborder786:**
I have already created a PR @ardakdemir

**ardakdemir:**
thank you @keenborder786 !!

**desiorac:**
Transparency matters for compliance. Silent behavior changes break audit trails. Have you considered adding deprecation warnings to maintain observability?
