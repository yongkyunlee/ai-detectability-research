# core: create_schema_from_function ignores include_injected=False when filter_args is provided

**Issue #35831** | State: open | Created: 2026-03-13 | Updated: 2026-03-18
**Author:** indexedakki
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

_No response_

### Reproduction Steps / Example Code (Python)

```python
from typing import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.utils.function_calling import create_schema_from_function

def my_tool(
    query: str,
    secret: Annotated[str, InjectedToolArg],
):
    pass

schema = create_schema_from_function(
    "MyTool",
    my_tool,
    filter_args=["query"],
    include_injected=False,
)

print(schema.schema()["properties"])
# Expected: {}
# Actual:   {"secret": ...}  ← injected arg leaked
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

## Bug Description

`create_schema_from_function` silently ignores `include_injected=False` when 
`filter_args` is also provided, causing injected arguments to leak into the schema.

## Root Cause

The injected arg filtering logic was nested inside the `else` branch of the 
`filter_args` check, so it never ran when `filter_args` was provided:
```python
if filter_args:
    filter_args_ = filter_args      # injected filtering never happens here
else:
    ...
    for existing_param in existing_params:
        if not include_injected and _is_injected_arg_type(...):  # only runs in else
            filter_args_.append(existing_param)
```
## Impact

`InjectedToolArg` is designed to hide sensitive arguments (API keys, sessions, 
internal context) from the LLM. When they leak into the schema, the LLM sees 
them and may attempt to fill them in — defeating the purpose of `InjectedToolArg`.

## Fix

Move the injected arg filtering outside the `if/else` block so it always runs,
and copy `filter_args` to avoid mutating the caller's list:
```python
if filter_args:
    filter_args_ = list(filter_args)  # copy to avoid mutation
else:
    existing_params: list[str] = list(sig.parameters.keys())
    if existing_params and existing_params[0] in {"self", "cls"} and in_class:
        filter_args_ = [existing_params[0], *list(FILTERED_ARGS)]
    else:
        filter_args_ = list(FILTERED_ARGS)

# Now runs regardless of whether filter_args was provided
for existing_param in list(sig.parameters.keys()):
    if not include_injected and _is_injected_arg_type(
        sig.parameters[existing_param].annotation
    ):
        if existing_param not in filter_args_:
            filter_args_.append(existing_param)
```

## Additional Notes

- The same `if filter_args` branch also directly assigned the caller's sequence 
  (`filter_args_ = filter_args`) without copying it, which could mutate the 
  caller's original list. Fixed with `list(filter_args)`.
- A regression test has been added to `tests/unit_tests/test_tools.py`.

### System Info

System Information
------------------
> OS:  Windows
> OS Version:  10.0.26200
> Python Version:  3.12.11 (main, Jul 11 2025, 22:40:18) [MSC v.1944 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 1.2.18
> langsmith: 0.7.13
> langchain_tests: 1.1.5
> langchain_text_splitters: 1.1.1

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> numpy: 2.3.5
> orjson: 3.11.5
> packaging: 26.0
> pydantic: 2.12.5
> pytest: 9.0.2
> pytest-asyncio: 1.3.0
> pytest-benchmark: 5.2.3
> pytest-codspeed: 4.3.0
> pytest-recording: 0.13.4
> pytest-socket: 0.7.0
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.2.0
> syrupy: 5.1.0
> tenacity: 9.1.4
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> vcrpy: 8.1.1
> wrapt: 2.0.1
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**jackjin1997:**
Hi, I'd like to work on this. 

The fix is in `create_schema_from_function` in `libs/core/langchain_core/tools/base.py`. When `filter_args` is provided, the code short-circuits before the `include_injected` check, so injected args are never filtered. The fix is to also apply the injected-arg filtering when `filter_args` is explicitly passed.

Could a maintainer please assign me to this issue? Thanks!

**biefan:**
I have a fix ready in #35890 and the PR was auto-closed because I am not yet assigned to this issue. Could a maintainer assign #35831 to me so I can reopen the PR?

**indexedakki:**
Hi maintainers, can anyone look into this @ccurme @mdrxy @eyurtsev

**xr843:**
Hi, I'd like to work on this issue. Could you please assign it to me? I've already opened PR #36064 with a fix. Thanks\!

**xr843:**
Hi, I'd like to work on this issue. Could I be assigned? I have a fix ready that moves the InjectedToolArg filtering outside the if/else block so it always runs. I previously submitted PR #36064 which was auto-closed before assignment.
