# Temperature dropped from responses api payload with gpt-5.2 default reasoning effort

**Issue #35423** | State: open | Created: 2026-02-24 | Updated: 2026-03-09
**Author:** artdent
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

_No response_

### Reproduction Steps / Example Code (Python)

```python
model = ChatOpenAI(
    model="gpt-5.2",
    use_responses_api=True,
    temperature=0.5,
)
model.invoke([{"role": "user", "content": "Hello, world"}])
```

### Error Message and Stack Trace (if applicable)

```shell
DEBUG:openai._base_client:Request options: {'method': 'post', 'url': '/responses', 'headers': {'X-Stainless-Raw-Response': 'true'}, 'files': None, 'idempotency_key': 'stainless-python-retry-9a86afe9-a319-4db8-b386-d974747f84fe', 'content': None, 'json_data': {'input': [{'content': 'Hello, world', 'role': 'user'}], 'model': 'gpt-5.2', 'stream': False}}
```

### Description

Temperature is supported in newer (5.x) openai models as long as reasoning is disabled. With gpt-5.2, the default reasoning effort is `none`, so the temperature parameter should be included when reasoning_effort is not supplied. Instead, `validate_temperature` removes the temperature parameter in that scenario, as does `_construct_responses_api_payload`:
https://github.com/langchain-ai/langchain/blob/5c6f8fe0a63442e594c7ea0c996e37c3de6def65/libs/partners/openai/langchain_openai/chat_models/base.py#L939-L944
https://github.com/langchain-ai/langchain/blob/5c6f8fe0a63442e594c7ea0c996e37c3de6def65/libs/partners/openai/langchain_openai/chat_models/base.py#L3952-L3958

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.6.0: Wed Nov  5 21:32:34 PST 2025; root:xnu-11417.140.69.705.2~1/RELEASE_ARM64_T6020
> Python Version:  3.11.11 (main, Feb 12 2025, 15:06:01) [Clang 19.1.6 ]

Package Information
-------------------
> langchain_core: 1.2.15
> langsmith: 0.7.6
> langchain_openai: 1.1.10

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> openai: 2.23.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**xXMrNidaXx:**
Good catch. The issue is that `validate_temperature` and `_construct_responses_api_payload` both check if the model **supports** reasoning (via `_is_reasoning_model()`), but don't consider whether reasoning is **actually enabled** for this request.

**The bug:**
```python
# In validate_temperature()
if _is_reasoning_model(values.get("model")):  # True for gpt-5.2
    values["temperature"] = None  # ❌ Drops temperature even if reasoning_effort=none
```

**The fix should check reasoning state:**
```python
def validate_temperature(values: dict) -> dict:
    model = values.get("model", "")
    reasoning_effort = values.get("reasoning_effort")
    
    # Only drop temperature if reasoning IS enabled
    if _is_reasoning_model(model) and reasoning_effort is not None:
        values["temperature"] = None
    
    return values
```

Same pattern applies to `_construct_responses_api_payload`:
```python
# Current (wrong):
if _is_reasoning_model(model):
    payload.pop("temperature", None)

# Fixed:
if _is_reasoning_model(model) and reasoning_effort is not None:
    payload.pop("temperature", None)
```

**Edge case to consider:** What about models where `reasoning_effort` defaults to something other than `none`? The logic should probably be:
- If `reasoning_effort` is explicitly set (any value), drop temperature
- If `reasoning_effort` is `None` (not set), check model defaults

At RevolutionAI (https://revolutionai.io) we've been working around this by using the direct OpenAI client for gpt-5.x models with temperature. Happy to test a PR if one gets opened.

**Gravqc:**
After reviewing #35424 more closely and checking the model defaults, the model-specific default handling is more accurate. Closing this PR in favor of that approach. Thanks!

**xXMrNidaXx:**
Good catch! This is a subtle edge case in the reasoning model detection logic.

**Root cause analysis:**

The code assumes reasoning models always have reasoning_effort enabled, but gpt-5.2's default of `reasoning_effort=none` breaks this assumption. The validation functions check for the presence of reasoning capabilities rather than whether reasoning is actually active:

```python
# Current logic (simplified):
if model in REASONING_MODELS:
    drop_temperature()  # Wrong for gpt-5.2 with reasoning_effort=none
    
# Should be:
if model in REASONING_MODELS and reasoning_effort not in (None, 'none'):
    drop_temperature()
```

**Workaround until fixed:**

```python
from langchain_openai import ChatOpenAI

# Force temperature through model_kwargs to bypass validation
model = ChatOpenAI(
    model="gpt-5.2",
    use_responses_api=True,
    model_kwargs={"temperature": 0.5}
)
```

Or patch the validation:

```python
# Monkey-patch for urgent production fix
import langchain_openai.chat_models.base as base_module

original_validate = base_module.validate_temperature

def patched_validate(cls, data):
    model = data.get('model', '')
    reasoning_effort = data.get('reasoning_effort')
    # Allow temperature for 5.x models with no/none reasoning
    if 'gpt-5' in model and reasoning_effort in (None, 'none'):
        return data
    return original_validate(cls, data)

base_module.validate_temperature = classmethod(patched_validate)
```

**Suggested fix direction:**

The model profile system should probably track whether a model *supports* reasoning vs whether reasoning is *enabled*. A model that supports reasoning but has it disabled should behave like a standard chat model for temperature purposes.

**artdent:**
@xXMrNidaXx your bot seems to be glitching. Please stop.
