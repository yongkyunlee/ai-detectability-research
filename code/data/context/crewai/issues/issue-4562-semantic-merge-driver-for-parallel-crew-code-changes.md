# Semantic merge driver for parallel crew code changes

**Issue #4562** | State: open | Created: 2026-02-22 | Updated: 2026-03-03
**Author:** rs545837

When crews run coding agents in parallel, merging their changes back is the hard part. git's line-level merge conflicts on any file touched by two agents, even if they edited completely different functions.

[weave](https://github.com/ataraxy-labs/weave) is a semantic merge driver that merges at the function/class level using tree-sitter. Registers via `.gitattributes` so `git merge` uses it automatically. 31/31 benchmark scenarios resolved cleanly vs git's 15/31.

Also ships as an MCP server with 14 tools for agent coordination:
- `weave_claim_entity` / `weave_release_entity` for advisory locks on specific functions/classes
- `weave_potential_conflicts` for predictive conflict detection across branches
- `weave_who_is_editing` to check what other agents are touching
- `weave_preview_merge` for simulating merge outcomes before attempting them

This lets parallel crews coordinate at entity granularity (functions, classes) rather than file level.

`brew install ataraxy-labs/tap/weave`

## Comments

**rs545837:**
Update: since CrewAI already has MCPServerAdapter, weave's 14 MCP tools work out of the box without any code changes to CrewAI. Here's a minimal example:

```python
from crewai import Agent, Crew
from crewai_tools import MCPServerAdapter

weave_tools = MCPServerAdapter(
    server_params={"command": "weave-mcp", "args": ["--stdio"]}
)

coding_agent = Agent(
    role="Backend Developer",
    tools=weave_tools.tools,
    # agent can now claim entities, check conflicts, preview merges
)
```

Happy to put together a docs PR under `docs/en/tools/integration/` showing the full multi-agent coordination setup if that would be useful.
