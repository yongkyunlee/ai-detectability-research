# fix(core): ToolRuntime (@tool decorator) raises Pydantic ValidationError due to _DirectlyInjectedToolArg not filtered from inferred schema

**Issue #35931** | State: open | Created: 2026-03-15 | Updated: 2026-03-15
**Author:** shivamtiwari3
**Labels:** external

## Bug Description

When a tool function uses `runtime: ToolRuntime` (or any `_DirectlyInjectedToolArg` subclass) and the schema is **inferred** via the `@tool` decorator or `StructuredTool.from_function()` (i.e., no custom `args_schema` is passed), `ToolNode.invoke()` raises a `pydantic_core.ValidationError`:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for get_current_time
runtime
  Input should be a dictionary or an instance of ToolRuntime [type=dataclass_type,
  input_value=ToolRuntime(state={'messages': [...]}, context=None, ...), input_type=ToolRuntime]
```

This was originally reported in [langchain-ai/langgraph#6431](https://github.com/langchain-ai/langgraph/issues/6431).

## Root Cause

`_filter_schema_args` in `structured.py` only filters `FILTERED_ARGS` (callback manager args) and config params. It does **not** call `_is_directly_injected_arg_type`, so `runtime: ToolRuntime` appears as a **required** field in the auto-generated Pydantic schema (which uses `extra="forbid"` via `_SchemaConfig`).

When `ToolNode` injects the `ToolRuntime` instance and calls `tool.invoke(...)`, `_parse_input` → `model_validate` fails because Pydantic cannot validate the stdlib `@dataclass` instance against the field type.

## Minimal Reproduction

```python
from dataclasses import dataclass
from langchain_core.tools import tool
from langchain_core.tools.base import _DirectlyInjectedToolArg

@dataclass
class MyRuntime(_DirectlyInjectedToolArg):
    data: dict

@tool
def my_tool(query: str, runtime: MyRuntime) -> str:
    """A tool."""
    return query

# Raises ValidationError:
my_tool.invoke({"query": "hello", "runtime": MyRuntime(data={})})
```

## Fix

Two-part fix in `langchain_core`:

1. **`_filter_schema_args` (`structured.py`)**: filter params whose annotation satisfies `_is_directly_injected_arg_type` so they are excluded from the Pydantic schema.
2. **`_parse_input` (`base.py`)**: strip `_DirectlyInjectedToolArg` instances from `tool_input` before `model_validate` to avoid `extra="forbid"` rejection; the existing `_injected_args_keys` loop re-injects them afterwards.

A fix is ready in PR #35929.

## Related

- langchain-ai/langgraph#6431 (original report)
- #34770 (related: model_dump serializes injected args)
- #34246 (related: custom strict schema + injected args)

## Comments

**shivamtiwari3:**
I have a fix ready in PR #35929. Could a maintainer please assign me to this issue so the PR can be reopened?
