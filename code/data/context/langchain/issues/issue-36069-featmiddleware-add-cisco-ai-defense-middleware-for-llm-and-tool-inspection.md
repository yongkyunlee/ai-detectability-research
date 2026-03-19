# feat(middleware): Add Cisco AI Defense middleware for LLM and tool inspection

**Issue #36069** | State: closed | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** shiva-guntoju-09
**Labels:** external

## Feature Request

### Description

Add two new middleware classes that integrate [Cisco AI Defense](https://developer.cisco.com/docs/ai-defense/overview/) security policies into LangChain agents:

- **`CiscoAIDefenseMiddleware`** — inspects LLM inputs and outputs via `before_model` / `after_model` hooks using the Cisco AI Defense Chat Inspection API.
- **`CiscoAIDefenseToolMiddleware`** — inspects tool call requests and responses via `wrap_tool_call` using the Cisco AI Defense MCP Inspection API.

### Motivation

Cisco AI Defense provides runtime security inspection for AI applications, detecting prompt injection, jailbreaks, PII leakage, toxic content, and unsafe tool usage. Integrating it as LangChain middleware lets users add security guardrails to any agent with a single line of configuration — no code changes to their tools or models.

### Proposed Design

Two composable middleware classes in a single file (`cisco_ai_defense.py`), following LangChain's existing patterns (similar to `PIIMiddleware`, `ModelCallLimitMiddleware`):

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    CiscoAIDefenseMiddleware,
    CiscoAIDefenseToolMiddleware,
)

# LLM inspection only
agent = create_agent(
    "openai:gpt-4.1",
    middleware=[CiscoAIDefenseMiddleware(api_key="...", region="us")],
)

# Tool inspection only
agent = create_agent(
    "openai:gpt-4.1",
    tools=[my_tool],
    middleware=[CiscoAIDefenseToolMiddleware(api_key="...", region="us")],
)

# Both LLM + tool inspection
agent = create_agent(
    "openai:gpt-4.1",
    tools=[my_tool],
    middleware=[
        CiscoAIDefenseMiddleware(api_key="...", region="us"),
        CiscoAIDefenseToolMiddleware(api_key="...", region="us"),
    ],
)
```

### Key features

- **Composable**: use either middleware independently or both together
- **Sync + async**: implements both sync and async hooks
- **Configurable exit behavior**: `"end"` (jump to end with violation message) or `"error"` (raise exception)
- **Fail-open / fail-closed**: configurable behavior when AI Defense API is unreachable
- **Lazy import**: `aidefense` SDK is imported inside methods, so it remains an optional dependency — no changes to `pyproject.toml` needed
- **Region aliases**: `"us"`, `"eu"`, `"apj"` normalized automatically

### Implementation

I have a working implementation ready with:
- Middleware source: `libs/langchain_v1/langchain/agents/middleware/cisco_ai_defense.py`
- Updated exports: `libs/langchain_v1/langchain/agents/middleware/__init__.py`
- 19 unit tests: `libs/langchain_v1/tests/unit_tests/agents/middleware/implementations/test_cisco_ai_defense.py`
- MDX documentation: `libs/langchain_v1/langchain/agents/middleware/docs/cisco_ai_defense.mdx`

PR: #36068 (auto-closed due to missing issue link — will relink once this issue is approved)

cc @sydney-runkle for review

## Comments

**shiva-guntoju-09:**
@sydney-runkle can you please take a look and let me know if I need to add more details.

**shiva-guntoju-09:**
Hi @sydney-runkle — I'd like to work on this issue. Could you please assign it to me?

I have a ready implementation with:
- Two composable middleware classes (`CiscoAIDefenseMiddleware` for LLM inspection, `CiscoAIDefenseToolMiddleware` for tool/MCP inspection)
- 19 unit tests with mocked `aidefense` client
- MDX documentation following the existing LangChain middleware docs format
- `aidefense` as an optional lazy-imported dependency (no `pyproject.toml` changes needed)

The PR is at #36068 — it was auto-closed pending issue assignment. Once assigned, I'll trigger the reopen. Thanks!

**eyurtsev:**
Hi @shiva-guntoju-09, 

If you want to add 3rd party middleware, you need to create your own pypi package for the middleware. For it to be featured in the integration docs, you need to be associated officially with the 3rd party.

Hope this helps!

Eugene
