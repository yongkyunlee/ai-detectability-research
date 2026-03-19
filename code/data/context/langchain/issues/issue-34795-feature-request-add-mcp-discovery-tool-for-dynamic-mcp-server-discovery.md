# [Feature Request] Add MCP Discovery tool for dynamic MCP server discovery

**Issue #34795** | State: open | Created: 2026-01-17 | Updated: 2026-03-18
**Author:** yksanjo
**Labels:** external

## Feature Request

Add a LangChain tool wrapper for MCP Discovery API, enabling agents to dynamically discover MCP servers.

## Motivation

LangChain agents are limited to pre-configured tools. With MCP Discovery, agents could:
- Discover new MCP servers based on task requirements
- Get performance metrics before choosing a tool
- Adapt their toolset dynamically

## Proposed Solution

```python
from langchain.tools import MCPDiscoveryTool

discovery = MCPDiscoveryTool(api_url="https://mcp-discovery-production.up.railway.app")

# Agent can now discover MCP servers
result = discovery.run("I need to send emails")
# Returns: Gmail MCP server + install command + metrics
```

## What MCP Discovery provides

- **Semantic search** - 24+ MCP servers indexed
- **Performance metrics** - Latency, uptime data
- **Server comparison** - Side-by-side analysis
- **Free tier** - 100 queries/month

## Links

- GitHub: https://github.com/yksanjo/mcp-discovery
- npm: https://www.npmjs.com/package/mcp-discovery-api
- API: https://mcp-discovery-production.up.railway.app

Happy to submit a PR if there's interest!

## Comments

**dhansuhkumar:**
Great proposal. I have experience building tool wrappers like this and can pick this up immediately.

I'll implement the MCPDiscoveryTool with full error handling for the API response and include a notebook example for the docs showing how an agent utilizes the discovery metrics.

Please assign this to me if it's available

**connerlambden:**
As an example of a domain-specific MCP server that would benefit from discovery: [BGPT MCP](https://github.com/connerlambden/bgpt-mcp) is a hosted MCP server for searching full-text scientific papers, returning structured experimental data (methods, results, quality scores, 25+ fields). Connect to `https://bgpt.pro/mcp/sse` or run `npx bgpt-mcp`. A discovery layer would make tools like this much easier for agents to find and use.

**m13v:**
dynamic MCP discovery is something we need too. right now our agent's MCP tools are all statically configured in settings.json and adding a new server requires restarting the session. one thing to consider for the discovery tool: caching. the discovery API response should be cached with a reasonable TTL so you're not hitting it on every tool selection. in our setup we cache the tool list for the duration of the session and only refresh on explicit request

**m13v:**
For reference, our MCP server that demonstrates the tool discovery pattern (macOS desktop automation tools): https://github.com/mediar-ai/mcp-server-macos-use/blob/main/Sources/MCPServer/main.swift

Each tool is registered with a schema, description, and input validation. The discovery response includes everything a client needs to decide whether to use the tool without making a test call.

**yksanjo:**
Thanks for the engagement here — really appreciate it.

**To @dhansuhkumar** — we'd love your help. A few notes to make the implementation smooth:
- The `MCPDiscoveryTool` already exists at [`langchain/mcp_discovery_tool.py`](https://github.com/yksanjo/mcp-discovery/blob/main/langchain/mcp_discovery_tool.py) in our repo and just shipped a major update (true async via `aiohttp`, `force_refresh`, verified badge display). Feel free to base your LangChain PR on that.
- For the notebook: a minimal agent example showing `force_refresh=True` to skip the cache would be the most useful demo.

**To @m13v** — great point on caching. We shipped exactly this:
- Server-side: LRU cache with per-type TTLs (5 min for search, 1 hr for embeddings, 10 min for server data)
- New `force_refresh` parameter on `POST /api/v1/discover` — pass `"force_refresh": true` to bypass the cache and get a live result on demand, without restarting the session.

**To @connerlambden** — BGPT MCP is a great example. Once you're indexed, semantic search will surface it naturally for queries like "scientific papers" or "experimental data". You can submit via the API or open an issue in our repo.

Changelog: https://github.com/yksanjo/mcp-discovery
