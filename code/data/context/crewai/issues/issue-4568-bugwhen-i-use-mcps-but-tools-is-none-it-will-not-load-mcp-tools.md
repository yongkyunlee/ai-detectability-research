# [BUG]When I use mcps but tools is None, it will not load mcp tools

**Issue #4568** | State: closed | Created: 2026-02-23 | Updated: 2026-03-03
**Author:** kid0317
**Labels:** bug

### Description

when I use mcp like this
```
sandbox_agent = Agent(
role="…",
goal="…",
backstory="…",
mcps=[
        MCPServerHTTP(
            url="http://localhost:8022/mcp",  
        )
    ],
)
```
mcp will not load. I check the source code at crewai/agent/core.py , 
```
if mcps and self.tools is not None:
        self.tools.extend(mcps)
```

### Steps to Reproduce

use mcps but tools is None

### Expected behavior

can just use mcps

### Screenshots/Code snippets

above

### Operating System

macOS Ventura

### Python Version

3.10

### crewAI Version

1.7.2

### crewAI Tools Version

1.7.2

### Virtual Environment

Venv

### Evidence

if mcps and self.tools is not None:
        self.tools.extend(mcps)

### Possible Solution

when tools is None, let it []

### Additional context

no more

## Comments

**xXMrNidaXx:**
Good catch! This is a logic bug in the condition.

## The Issue

```python
if mcps and self.tools is not None:
    self.tools.extend(mcps)
```

When you don't pass `tools`, it defaults to `None`. The condition `self.tools is not None` is `False`, so the MCP tools never get added — even though you explicitly passed them.

## Workaround (Until Fixed)

Just pass an empty list for `tools`:

```python
sandbox_agent = Agent(
    role="…",
    goal="…",
    backstory="…",
    tools=[],  # ← This makes self.tools not None
    mcps=[
        MCPServerHTTP(url="http://localhost:8022/mcp")
    ],
)
```

## The Fix

Your suggested fix is correct. The code should be:

```python
if mcps:
    if self.tools is None:
        self.tools = []
    self.tools.extend(mcps)
```

This ensures MCP tools are added regardless of whether `tools` was explicitly provided. Might be worth opening a PR — it's a one-liner fix.

---

*We've hit similar MCP integration issues at [RevolutionAI](https://revolutionai.io) — happy to help test a fix if one gets merged.*

**xXMrNidaXx:**
Good catch! The conditional logic is indeed the issue.

**Workaround until this is fixed:**
```python
sandbox_agent = Agent(
    role="...",
    goal="...",
    backstory="...",
    tools=[],  # Pass empty list instead of None
    mcps=[
        MCPServerHTTP(
            url="http://localhost:8022/mcp",  
        )
    ],
)
```

By passing `tools=[]` instead of leaving it as `None`, the MCP tools will be properly loaded and extended onto the tools list.

**The fix in source would be:**
```python
# Instead of:
if mcps and self.tools is not None:
    self.tools.extend(mcps)

# Should be:
if mcps:
    if self.tools is None:
        self.tools = []
    self.tools.extend(mcps)
```

This ensures MCPs work standalone without requiring pre-existing tools.
