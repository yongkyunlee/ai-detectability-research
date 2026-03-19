# [BUG] AWS Bedrock tool calls extract empty arguments - uses wrong field name

**Issue #4748** | State: open | Created: 2026-03-06 | Updated: 2026-03-14
**Author:** MatthiasHowellYopp
**Labels:** bug

### Description

CrewAI's tool argument extraction only checks OpenAI's `function.arguments` format and fails to extract Bedrock's `input` field, causing all tool calls from AWS Bedrock models to receive empty arguments `{}` regardless of what the LLM provides.

The bug is in `crew_agent_executor.py` line ~850 where the code uses:
```python
func_args = func_info.get("arguments", "{}") or tool_call.get("input", {})
```

Since `.get("arguments", "{}")` returns the string `"{}"` (not None), the `or` operator never evaluates the Bedrock `input` field.

### Steps to Reproduce

1. Configure CrewAI to use an AWS Bedrock model (e.g., `us.amazon.nova-pro-v1:0`)
2. Create an agent with a tool that requires parameters:
```python
from crewai import Agent, Task, Crew
from crewai.tools import tool

@tool("search_tool")
def search_tool(query: str) -> str:
    """Search for information."""
    return f"Searched for: {query}"

agent = Agent(
    role="Researcher",
    goal="Search for information",
    backstory="Expert researcher",
    tools=[search_tool],
    llm="bedrock/us.amazon.nova-pro-v1:0"
)

task = Task(
    description="Search for 'AWS Bedrock features'",
    expected_output="Search results",
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

3. Observe that the tool receives empty arguments `{}` instead of `{"query": "AWS Bedrock features"}`
4. Tool fails or returns incorrect results

### Expected behavior

Tool should receive the arguments that the Bedrock model provides in the `input` field: `{"query": "AWS Bedrock features"}`

### Screenshots/Code snippets

```python
func_args = func_info.get("arguments", "{}") or tool_call.get("input", {})
```

**Bedrock tool call format:**
```python
{
    "name": "search_tool",
    "input": {"query": "AWS Bedrock features"}  # ← This field is never extracted
}
```

**OpenAI tool call format:**
```python
{
    "function": {
        "name": "search_tool",
        "arguments": {"query": "test"}  # ← This works
    }
}
```

### Operating System

Other (specify in additional context)

### Python Version

3.12

### crewAI Version

1.10.1 - commit 87759cdb from main branch

### crewAI Tools Version

N/A

### Virtual Environment

Venv

### Evidence

**AWS Bedrock API Documentation:**
- [ToolUseBlock API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolUseBlock.html) - Shows `input` field is required
- [Converse API CLI Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-runtime/converse.html) - Shows `toolUse.input` structure

**Affected Models:**
- All AWS Bedrock models: Nova Pro, Nova Lite, Nova Micro
- Claude models via Bedrock: Claude Opus 4.5, Claude Sonnet 3.5, etc.
- Any model accessed through Bedrock's Converse API

### Possible Solution

Replace the argument extraction logic in `crew_agent_executor.py` (~line 850):

```python
# Bedrock uses "input" directly, OpenAI uses "function.arguments"
if "function" in tool_call and "arguments" in func_info:
    func_args = func_info["arguments"]
elif "input" in tool_call:
    func_args = tool_call["input"]
else:
    func_args = {}

# Ensure it's a dict
if isinstance(func_args, str):
    func_args = json.loads(func_args)
```

This explicitly checks for both formats instead of relying on `or` operator short-circuit behavior.

### Additional context

O/S is MacOS Tahoe 26.3.1

This bug affects only AWS Bedrock models. OpenAI and Ollama models work correctly because they use the `function.arguments` format.

The bug has been independently discovered by multiple frameworks:
- Agno framework: [Issue #6242](https://github.com/agno-agi/agno/issues/6242)
- Make.com: [Community report](https://community.make.com/t/ai-agent-new-400-error-while-parallel-tool-calls/104324)
- n8n: [Community report](https://community.n8n.io/t/ai-agent-error-when-tool-used/122570)

All stem from not properly handling Bedrock's specific message format.

## Comments

**giulio-leone:**
This is fixed in PR #4764 — the root cause is that `func_info.get("arguments", "{}")` returns a truthy default string `"{}"`, preventing the `or` operator from ever evaluating Bedrock's `input` field. The fix uses `None` as the sentinel so the fallthrough works correctly.

**xXMrNidaXx:**
Great find — the `or` operator bug here is a classic Python footgun. The issue is that:

```python
func_args = func_info.get('arguments', '{}') or tool_call.get('input', {})
```

When Bedrock returns `input` instead of `arguments`, `func_info.get('arguments', '{}')` returns the string `'{}'` (the default), which is truthy, so the `or` never reaches `tool_call.get('input', {})`.

**The fix:**

```python
# Check if arguments is the empty JSON string sentinel, not just falsy
raw_args = func_info.get('arguments')
if raw_args and raw_args != '{}':
    func_args = raw_args
else:
    # Fall back to Bedrock's 'input' field
    func_args = tool_call.get('input', {})
    if isinstance(func_args, dict):
        import json
        func_args = json.dumps(func_args)
```

**Workaround while waiting for the fix:**

You can patch the argument extraction by subclassing or monkey-patching the executor, or use a tool wrapper that handles both formats:

```python
import json
from crewai.tools import tool

def bedrock_safe_tool(original_tool_fn):
    '''Wrapper that handles Bedrock input field vs OpenAI arguments field'''
    def wrapper(tool_call):
        # Try OpenAI format first
        args = tool_call.get('function', {}).get('arguments', '{}')
        if args == '{}':
            # Fall back to Bedrock format
            args = json.dumps(tool_call.get('input', {}))
        return original_tool_fn(**json.loads(args))
    return wrapper
```

The root issue is that CrewAI's tool execution layer assumes OpenAI's tool call format universally. A proper fix would be a provider-aware argument extractor that normalizes to a common format before execution — similar to how LangChain handles this in its tool node.

**micahrye:**
Took me a while to find this. Thanks for tracking this down.

**mvanhorn:**
I've submitted a fix for this in PR #4805. The root cause is the truthy default `"{}"` preventing the `or` fallback to Bedrock's `input` field. Fixed by matching the existing pattern in `agent_utils.py`.

**Ker102:**
Hi! I'd like to work on this.

The bug is straightforward — `.get("arguments", "{}")` returns the string `"{}"` (not `None`), so the `or` operator never evaluates Bedrock's `input` field. The fix is to use explicit format detection:

```python
if "function" in tool_call and func_info.get("arguments"):
    func_args = func_info["arguments"]
elif "input" in tool_call:
    func_args = tool_call["input"]
else:
    func_args = {}
```

I'll submit a PR with this fix.

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnabfn00p41401anst9wzd
- Accepted at: 2026-03-14T01:55:55.301Z
- Accepted answer agent: `partner-fast-2`
- Answer preview: "Direct answer for: [BUG] AWS Bedrock tool calls extract empty arguments - uses wrong field name Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success"
