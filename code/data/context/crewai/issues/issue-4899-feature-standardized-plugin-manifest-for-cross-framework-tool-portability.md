# Feature: standardized plugin manifest for cross-framework tool portability

**Issue #4899** | State: open | Created: 2026-03-15 | Updated: 2026-03-15
**Author:** augmentedmike

## Feature Request

A standardized plugin manifest format that would let tool packages work across CrewAI, LangChain, pydantic-ai, and MCP with minimal adapter code.

## Use Case

When building agent systems with many tools (20+), the wiring code to register each tool with the framework becomes a significant maintenance burden. Each framework has its own tool interface:

- CrewAI: `BaseTool` subclass with `_run()` method
- LangChain: `BaseTool` with `_run()` / `_arun()`
- pydantic-ai: `@agent.tool` decorator
- MCP: JSON-RPC tool registration

A standardized manifest would let a single package declare its tools once and have thin framework adapters handle the registration.

## Proposed Solution

A plugin manifest format like:

```json
{
  "id": "my-tool-package",
  "version": "1.0.0",
  "tools": [
    {
      "name": "search_knowledge_base",
      "description": "Search the local knowledge base with semantic + keyword matching",
      "parameters": {
        "type": "object",
        "required": ["query"],
        "properties": {
          "query": { "type": "string", "description": "Search query" },
          "limit": { "type": "number", "description": "Max results", "default": 10 }
        }
      },
      "entrypoint": "tools.kb:search"
    }
  ]
}
```

CrewAI could then auto-discover and register these tools:

```python
from crewai.plugins import load_manifest
tools = load_manifest("./plugin-manifest.json")
agent = Agent(role="Researcher", tools=tools)
```

## Context

I'm building [MiniClaw](https://github.com/augmentedmike/miniclaw-os), a modular agent runtime with 25+ plugins. We use a similar manifest pattern internally and it's worked well for managing tool composition at scale. Happy to contribute an implementation if there's interest.

## Alternatives Considered

- **MCP as the universal standard**: MCP is great for client-server tool access but adds network overhead for local tools and doesn't cover lifecycle hooks.
- **Manual adapter per framework**: Works but doesn't scale — maintaining N adapters for M tools is O(N*M) work.
