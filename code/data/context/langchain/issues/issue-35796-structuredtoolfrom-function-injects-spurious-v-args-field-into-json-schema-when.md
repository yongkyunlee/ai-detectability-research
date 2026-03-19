# StructuredTool.from_function injects spurious v__args field into JSON schema when function parameter is named args

**Issue #35796** | State: open | Created: 2026-03-12 | Updated: 2026-03-13
**Author:** schuay
**Labels:** bug, core, langchain, external

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

Related issues that show the runtime symptom of the same underlying cause (but were closed as user workarounds without a
framework fix): #26849, #30910. This issue focuses on the schema generation side — the v__args ghost field polluting the
tool description sent to LLMs, causing silent parameter loss and API-level schema validation failures.

### Reproduction Steps / Example Code (Python)

```python
Reproducer

from langchain_core.tools import StructuredTool

def run_command(working_dir: str, args: list[str], timeout: int = 60) -> str:
"""Run a command."""
...

st = StructuredTool.from_function(run_command)
schema = st.args_schema.model_json_schema()
print(list(schema["properties"].keys()))
# → ['working_dir', 'timeout', 'v__args']  ← spurious field; 'args' is missing!
print(schema["properties"]["v__args"])
# → {'default': None, 'items': {}, 'title': 'V  Args', 'type': 'array'}

Observed: schema has v__args: {type: array, items: {}} injected, while the legitimate args parameter is absent.

Expected: schema has only working_dir, args, timeout. No v__args.
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

Description

When a Python function with a parameter named args is wrapped via StructuredTool.from_function, the generated JSON schema
contains a spurious extra field v__args of type array with an empty items: {}. This breaks tool use with the Gemini API,
which requires all array schema fields to have a non-empty items.

Root cause

StructuredTool.from_function internally uses pydantic.deprecated.decorator.ValidatedFunction (Pydantic v1 compatibility
layer) to build the args schema. That wrapper always injects a sentinel field named args to validate that no unexpected
positional arguments are passed. When the wrapped function already has a parameter named args, it renames the sentinel to
v__args (see pydantic/deprecated/decorator.py lines 128–137) — but still injects it into the schema as list[Any] with
default: null. Pydantic renders list[Any] as {"type": "array", "items": {}}.

  Impact

  - Gemini API rejects tool schemas containing {type: array, items: {}} with INVALID_ARGUMENT: missing field items.
  - The legitimate args parameter is silently dropped from the schema, so the model never learns the parameter exists.

  Affected versions

  - langchain-core (tested: 0.3.x with Pydantic 2.x)

  Workaround

  Either rename the parameter to avoid args, or supply an explicit args_schema Pydantic model to bypass ValidatedFunction:

  from pydantic import BaseModel

  class RunCommandInput(BaseModel):
      working_dir: str
      args: list[str]
      timeout: int = 60

  st = StructuredTool.from_function(run_command, args_schema=RunCommandInput)

### System Info

$ uv run python -m langchain_core.sys_info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP PREEMPT_DYNAMIC Wed, 04 Mar 2026 18:25:08 +0000
> Python Version:  3.12.12 (main, Feb 12 2026, 00:42:14) [Clang 21.1.4 ]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langsmith: 0.7.12
> deepagents: 0.4.5
> langchain_anthropic: 1.3.4
> langchain_chroma: 1.1.0
> langchain_deepseek: 1.0.1
> langchain_google_genai: 4.2.1
> langchain_mcp_adapters: 0.2.1
> langchain_openai: 1.1.10
> langchain_qdrant: 1.1.0
> langgraph_api: 0.7.63
> langgraph_cli: 0.4.14
> langgraph_runtime_inmem: 0.26.0
> langgraph_sdk: 0.3.9

## Comments

**MaybeSam05:**
Hi! I'd like to work on this issue and be assigned to it.

I've already implemented a fix locally that:
- Filters out Pydantic’s internal `v__args` sentinel from the generated args schema.
- Preserves a genuine `args` parameter on the wrapped function.
- Adds a regression test to cover the `run_command(working_dir: str, args: list[str], timeout: int = 60)` case.

Tests:

```bash
source .venv/bin/activate
pytest libs/core/tests/unit_tests/test_tools.py -k "structured_tool_from_function_with_args_param"

**giulio-leone:**
Hi! Could I be assigned to this issue? I have a fix ready in PR #35808 that addresses the root cause — Pydantic's `ValidatedFunction` renames parameters named `args` to `v__args`, and the current `create_schema_from_function` doesn't detect this rename.

**Ker102:**
I'd like to work on this as well. The `v__args` ghost field from Pydantic's `ValidatedFunction` breaking Gemini API schemas is a clear bug. I'll submit a PR to filter out the Pydantic sentinel fields from the generated JSON schema in `StructuredTool`.
