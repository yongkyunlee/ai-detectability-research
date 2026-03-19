# [BUG] Regression in CrewAI 1.9.3: custom BaseTool wrapper around BedrockKBRetrieverTool gets called without args (_run() missing query) and enters infinite tool-use loop

**Issue #4495** | State: open | Created: 2026-02-16 | Updated: 2026-03-09
**Author:** jonas-cohen-verbit
**Labels:** bug

### Description

After upgrading CrewAI from 1.6.1 → 1.9.3, a custom tool wrapper around BedrockKBRetrieverTool no longer receives its required query argument. The tool call fails with:
	•	ParsedBedrockKBRetrieverTool._run() missing 1 required positional argument: 'query'
…and the agent repeatedly attempts to use the tool, effectively entering an infinite tool-calling loop.
In crewai==1.6.1, the same code and workflow work as expected.

The logs also show an events mismatch warning during the loop:
[CrewAIEventsBus] Warning: Event pairing mismatch. 'tool_usage_finished' closed 
'flow_started' (expected 'tool_usage_started')
Tool kb_retrieve executed with result: Error executing tool: ParsedBedrockKBRetrieverTool._run() missing 1 required positional argument: 'query'

This looks like a regression in how tool arguments are passed from the agent → tool execution in newer CrewAI versions.

Environment
	•	crewai==1.9.3 (broken)
	•	crewai==1.6.1 (works)
	•	Tool involved: crewai_tools.aws.bedrock.knowledge_base.retriever_tool.BedrockKBRetrieverTool  ￼
	•	Custom tool extends crewai.tools.BaseTool (wrapper with post-processing)

### Steps to Reproduce

1.	Install and run with crewai==1.9.3
	2.	Create an agent (in a Crew) that has a tool list including a custom wrapper tool around BedrockKBRetrieverTool.
	3.	Ask the agent a question that triggers retrieval from the knowledge base.
	4.	Observe that the tool fails with a missing query arg, and the agent repeatedly retries tool usage.

### Expected behavior

Expected behavior
	•	The tool should be invoked with the query argument (as defined by the tool schema), execute once, and return retrieval results (JSON).

Actual behavior
	•	Tool execution fails because _run() is called without the required query parameter.
	•	The agent loops, repeatedly trying to use the tool.
	•	Event bus warning appears: “Event pairing mismatch … expected tool_usage_started”.

### Screenshots/Code snippets

from typing import Type
import json
from pydantic import BaseModel, Field, PrivateAttr
from crewai.tools import BaseTool
from crewai_tools.aws.bedrock.knowledge_base.retriever_tool import BedrockKBRetrieverTool

class KBQueryInput(BaseModel):
    """Input schema for KB retrieval tool."""
    query: str = Field(..., description="Natural language query for the knowledge base.")

class ParsedBedrockKBRetrieverTool(BaseTool):
    name: str = "kb.retrieve"
    description: str = "Retrieve from Bedrock KB and parse results into RetrievedRef-shaped objects."
    args_schema: Type[BaseModel] = KBQueryInput
    _inner: BedrockKBRetrieverTool = PrivateAttr()

    def __init__(self, inner: BedrockKBRetrieverTool):
        super().__init__()
        self._inner = inner

    def _run(self, query: str) -> str:
        raw = self._inner._run(query)

        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return json.dumps({"message": "Failed to parse BedrockKBRetrieverTool response as JSON."})

        if not isinstance(payload, dict):
            return json.dumps({"message": "Unexpected BedrockKBRetrieverTool response type."})

        results = payload.get("results")
        if results is None:
            return json.dumps({"message": payload.get("message", "No results found for the given query.")})

        # parsing logic omitted for brevity...
        return json.dumps({"results": results})

def build_kb_retrieval_tool(knowledge_base_id: str, n_results: int = 100) -> BaseTool:
    inner = BedrockKBRetrieverTool(
        knowledge_base_id=knowledge_base_id,
        number_of_results=n_results
    )
    return ParsedBedrockKBRetrieverTool(inner=inner)

### Operating System

Ubuntu 22.04

### Python Version

3.12

### crewAI Version

1.9.3

### crewAI Tools Version

1.9.3

### Virtual Environment

Poetry

### Evidence

[CrewAIEventsBus] Warning: Event pairing mismatch. 'tool_usage_finished' closed 
'flow_started' (expected 'tool_usage_started')
Tool kb_retrieve executed with result: Error executing tool: ParsedBedrockKBRetrieverTool._run() missing 1 required positional argument: 'query'...

### Possible Solution

None
in early version its works

### Additional context

None

## Comments

**amabito:**
This feels like a deterministic failure being handled as a transient one.

When the same tool invocation fails with the same argument pattern (e.g., `_run()` missing `query`) and the retry loop treats it generically, it effectively becomes an execution amplifier. The system keeps re-invoking a call that cannot succeed without a state change.

We ran into a similar pattern where argument validation happened inside the retry boundary, so the same broken invocation was replayed repeatedly.

One lightweight mitigation that worked well for us was distinguishing:
- transient failures (network, rate limits, timeouts) → retry
- stable failures (identical input → identical exception) → short-circuit

Even a simple guard such as:
"if the same error signature occurs N times consecutively, halt"
prevented runaway loops without altering the core orchestration logic.

Is the current retry path in crewAI differentiating between transient and deterministic failures, or does everything flow through the same retry handler?

**jonas-cohen-verbit:**
> This feels like a deterministic failure being handled as a transient one.
> 
> When the same tool invocation fails with the same argument pattern (e.g., `_run()` missing `query`) and the retry loop treats it generically, it effectively becomes an execution amplifier. The system keeps re-invoking a call that cannot succeed without a state change.
> 
> We ran into a similar pattern where argument validation happened inside the retry boundary, so the same broken invocation was replayed repeatedly.
> 
> One lightweight mitigation that worked well for us was distinguishing:
> 
> * transient failures (network, rate limits, timeouts) → retry
> * stable failures (identical input → identical exception) → short-circuit
> 
> Even a simple guard such as: "if the same error signature occurs N times consecutively, halt" prevented runaway loops without altering the core orchestration logic.
> 
> Is the current retry path in crewAI differentiating between transient and deterministic failures, or does everything flow through the same retry handler?

Thank you for the response. I’m not sure what you meant.

What bothered me more is that the exact same code (without any code changes on my end) works properly in crewAI versions lower than 1.9.0 (not including 1.9.0).

**amabito:**
Totally fair — if the exact same code works on <1.9.0, then this points to a regression rather than just retry behavior.

What I was trying to describe earlier only applies after the failure starts looping — but the first thing to isolate here is what changed in 1.9.x around tool argument binding.

A couple of quick checks that might help narrow it down:

1) Can you share the minimal `_run` / `_arun` signature of your custom BaseTool and how it's registered with the agent?
2) In 1.9.3, does the tool receive any kwargs at all, or is `query` consistently missing?
3) Are you wrapping the tool or relying on signature introspection? If so, 1.9.x may have altered how arguments are constructed before dispatch.

If you can provide a minimal reproducible snippet (even stripped down), it should be possible to pinpoint which change in 1.9.x is breaking argument passing.

**amabito:**
To clarify: “deterministic vs transient” was just about the *retry loop behavior* — your case still looks like a 1.9.x regression in how tool args are built/passed, and that’s the main thing to isolate first.

**jonas-cohen-verbit:**
@amabito I shared a snippet of my code above. I will share again:
```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Optional, Type
from urllib.parse import urlparse

from pydantic import BaseModel, Field, PrivateAttr

from crewai.tools import BaseTool
from crewai_tools.aws.bedrock.knowledge_base.retriever_tool import BedrockKBRetrieverTool

class KBQueryInput(BaseModel):
    """Input schema for KB retrieval tool."""
    query: str = Field(..., description="Natural language query for the knowledge base.")

@dataclass(frozen=True)
class RetrievedRef:
    doc_name: str
    text: str
    score: float
    s3_uri: Optional[str]

def _serialize_retrieved_ref(ref: RetrievedRef) -> dict[str, Any]:
    return asdict(ref)

def _filename_from_uri(uri: Optional[str]) -> str:
    if not uri:
        return "unknown"

    if uri.startswith("s3://"):
        tail = uri.rstrip("/").split("/")[-1]
        return tail or "unknown"

    parsed = urlparse(uri)
    if parsed.path:
        tail = parsed.path.rstrip("/").split("/")[-1]
        return tail or "unknown"

    tail = uri.rstrip("/").split("/")[-1]
    return tail or "unknown"

def _normalize_content_type(result_item: dict[str, Any]) -> str:
    content_type = (
        result_item.get("content_type")
        or result_item.get("contentType")
        or result_item.get("contentType".lower())
        or ""
    )
    return str(content_type).upper()

class ParsedBedrockKBRetrieverTool(BaseTool):
    name: str = "kb.retrieve"
    description: str = "Retrieve from Bedrock KB and parse results into RetrievedRef-shaped objects."
    args_schema: Type[BaseModel] = KBQueryInput
    _inner: BedrockKBRetrieverTool = PrivateAttr()

    def __init__(self, inner: BedrockKBRetrieverTool):
        super().__init__()
        self._inner = inner

    def _run(self, query: str) -> str:
        raw = self._inner._run(query)

        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return json.dumps({"message": "Failed to parse BedrockKBRetrieverTool response as JSON."})

        if not isinstance(payload, dict):
            return json.dumps({"message": "Unexpected BedrockKBRetrieverTool response type."})

        results = payload.get("results")
        if results is None:
            return json.dumps({"message": payload.get("message", "No results found for the given query.")})

        parsed: list[RetrievedRef] = []
        for item in results or []:
            source_uri = item.get("source_uri") or item.get("sourceUri")
            score = float(item.get("score") or 0.0)
            doc_name = _filename_from_uri(source_uri)

            content_type = _normalize_content_type(item)

            if content_type == "TEXT":
                text = item.get("content", "") or ""
            elif content_type == "IMAGE":
                metadata = item.get("metadata") or {}
                text = metadata.get("x-amz-bedrock-kb-description", "") or ""
            else:
                text = item.get("content", "") or ""

            parsed.append(
                RetrievedRef(
                    doc_name=doc_name,
                    text=text,
                    score=score,
                    s3_uri=source_uri,
                )
            )

        return json.dumps({"results": [_serialize_retrieved_ref(ref) for ref in parsed]})

def build_kb_retrieval_tool(knowledge_base_id: str, n_results: int = 100) -> BaseTool:
    """Build a KB retrieval tool for the given knowledge base ID."""
    inner = BedrockKBRetrieverTool(
        knowledge_base_id=knowledge_base_id,
        number_of_results=n_results
    )
    return ParsedBedrockKBRetrieverTool(inner=inner)

```  

and this is the tool that I give to the agent:
`kb_tool = build_kb_retrieval_tool(knowledge_base_id=knowledge_base_id, n_results=100)`

**amabito:**
Thanks for sharing the snippet — this helps a lot.

Given that the exact same code works on =1.9.0 with `_run() missing query`, this strongly suggests a regression in how tool arguments are being constructed or bound in 1.9.x rather than a retry issue.

One thing that stands out is the custom `__init__` on a `BaseTool` subclass. Since `BaseTool` is pydantic-based, if initialization changes in 1.9.x affect schema or field registration, the dispatcher might be invoking the tool with empty kwargs — which would explain why `query` is missing.

Two quick experiments that could help isolate it:

1) Modify the constructor to forward model data:
   `def __init__(self, inner: BedrockKBRetrieverTool, **data):`
   `    super().__init__(**data)`
   `    self._inner = inner`

2) Temporarily change `_run` to:
   `def _run(self, query: str = None, **kwargs):`
   and log `kwargs` to see what the dispatcher is actually passing in 1.9.3.

If either restores argument passing, we've likely narrowed the regression to the tool initialization / introspection path introduced in 1.9.x.

**amabito:**
I've confirmed the root cause of #4495 in source.

## Root Cause (Confirmed)

In 1.9.x Native tool-calling path, crewAI bypasses `CrewStructuredTool.invoke()` and `_parse_args()` entirely and directly calls `BaseTool.run()` via `available_functions`.

### Evidence

**Tool mapping**

`agent_utils.py:94`
```python
available_functions[sanitized_name] = tool.run  # BaseTool.run bound method
```

So Native mode maps directly to `BaseTool.run`, not to `CrewStructuredTool.invoke`.

**Native execution**

`crew_agent_executor.py:856`
```python
tool_func = available_functions[func_name]
raw_result = tool_func(**args_dict)  # no validation
```

`base_tool.py:153`
```python
return self._run(**kwargs)
```

There is no Pydantic validation in this path.

In 1.8.x this path did not exist — tool execution always went through:

```
CrewStructuredTool.invoke()
→ _parse_args()
→ args_schema.model_validate()
```

So missing required arguments were caught as `ValidationError`.

In 1.9.x Native mode:
If `args_dict == {}` (e.g. provider parsing mismatch or empty arguments returned),
Python raises:

```
TypeError: missing required positional argument 'query'
```

This is then fed back to the LLM as a generic failure,
causing deterministic retry loops.

### Minimal Fix Proposal

Add `args_schema` validation inside `_handle_native_tool_calls()` before executing `tool.run`.

Example (conceptual):
```python
original_tool = self._find_original_tool(func_name)
if original_tool and original_tool.args_schema:
    try:
        validated = original_tool.args_schema.model_validate(args_dict)
        args_dict = validated.model_dump()
    except ValidationError as e:
        # Deterministic failure — do not execute tool
        raw_result = f"Argument validation failed: {e}"
        # return or continue without calling tool_func
```

This makes Native behavior consistent with the ReAct path
and prevents deterministic failure loops driven by `TypeError`.

If helpful, I can open a focused PR with:
- minimal validation patch
- regression test for Native tool call with missing required argument

**amabito:**
I've confirmed the root cause of #4495 in source.

## Root Cause (Confirmed)

In 1.9.x Native tool-calling path, crewAI bypasses `CrewStructuredTool.invoke()` and `_parse_args()` entirely and directly calls `BaseTool.run()` via `available_functions`.

### Evidence

**Tool mapping** — `agent_utils.py:196`

```python
available_functions[sanitized_name] = tool.run  # BaseTool.run bound method
```

So Native mode maps directly to `BaseTool.run`, not to `CrewStructuredTool.invoke`.

**Native execution** — `crew_agent_executor.py:858`

```python
tool_func = available_functions[func_name]
raw_result = tool_func(**args_dict)  # no validation
```

**`base_tool.py:153-158`**

```python
result = self._run(*args, **kwargs)
```

There is no Pydantic validation in this path.

In 1.8.x this path did not exist — tool execution always went through:

```
CrewStructuredTool.invoke() → _parse_args()
```

So missing required arguments were caught as `ValidationError`.

In 1.9.x Native mode, if `args_dict == {}` (e.g. provider parsing mismatch or empty arguments returned):

```
TypeError: missing required positional argument 'query'
```

This is then fed back to the LLM as a generic failure, causing deterministic retry loops.

## Minimal Fix Proposal

Add `args_schema` validation inside `_handle_native_tool_calls()` before executing `tool.run`.

Example (conceptual):

```python
if original_tool and getattr(original_tool, "args_schema", None):
    validated = original_tool.args_schema.model_validate(args_dict)
    args_dict = validated.model_dump()
```

This makes Native behavior consistent with the ReAct path and prevents deterministic failure loops driven by `TypeError`.

If helpful, I can open a focused PR with:
- minimal validation patch
- regression test for Native tool call with missing required argument

**jonas-cohen-verbit:**
@amabito Thank you again for the response and the help.
I’d be happy to understand, in summary (as simply as possible), what the actual root cause of the problem?
And do you think it’s possible to improve this in the next version (open a PR accordingly, etc.)?

**amabito:**
Sorry for the delayed reply — I was offline overnight.

Thanks — happy to summarize.

### Root cause (simple)
In **native tool calling mode (1.9.x)**, tool execution can bypass the structured tool validation path and end up calling **`BaseTool.run()` directly** with whatever `args_dict` was parsed from the provider tool-call response.

If the tool-call arguments are **missing / empty** (e.g. `{}` due to a provider response shape edge case or parsing mismatch), there is **no args_schema validation** before calling the tool, so Python raises a raw **`TypeError`** (e.g. missing required `query`). That error is then surfaced back to the model, which can repeat the same call → deterministic retry loop.

### Can we improve it in the next version?
Yes, very likely.

The minimal, low-risk fix is to **validate `args_dict` against the tool’s `args_schema` in the native path** (before executing `tool.run()`), so missing required fields produce a clear **Pydantic `ValidationError`** instead of a raw `TypeError`. That makes native behavior consistent with the structured/ReAct path.

If you’re aligned with that approach, I can open a focused PR with:
- the minimal validation change in the native execution path
- a regression test covering “missing required args” + “valid args still work”
