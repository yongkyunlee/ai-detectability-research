# [Feature Request] Integrate MCP Discovery for dynamic tool discovery

**Issue #4249** | State: open | Created: 2026-01-17 | Updated: 2026-03-18
**Author:** yksanjo

Hi CrewAI team,

I'd like to propose integrating **MCP Discovery API** to enable dynamic tool discovery for CrewAI agents.

## Problem

Crew members are limited to pre-configured tools. There's no way to discover new capabilities dynamically based on the task.

## Solution

MCP Discovery provides semantic search across MCP servers (Model Context Protocol), letting agents find the right tool for any task.

## How it works

```python
from crewai import Agent, Task

# Agent can discover tools dynamically
researcher = Agent(
    role='Researcher',
    tools=[mcp_discovery_tool],  # Can find any MCP server
    goal='Research and analyze data'
)

# When agent needs a database, it discovers one:
# discover_mcp_server(need="database") → postgres-server
```

## Features

- **Semantic search** - Find tools using natural language
- **Performance metrics** - Latency, uptime, success rates  
- **24+ servers indexed** - Databases, communication, automation
- **Free tier** - 100 queries/month

## Benefits for CrewAI

- Crews can adapt their toolset based on mission requirements
- No need to pre-configure every possible tool
- Performance data helps choose reliable options
- Agents become more autonomous

## Resources

- **GitHub**: https://github.com/yksanjo/mcp-discovery
- **API**: https://mcp-discovery-production.up.railway.app
- **npm**: https://www.npmjs.com/package/mcp-discovery-api

Happy to help with integration!

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**chorghemaruti64-creator:**
This is exactly the problem we're solving at [Agenium](https://chat.agenium.net).

We've built and deployed a discovery API that lets agents find MCP servers and other agents dynamically. Here's how it maps to the use case described here:

```python
# Current: tools are pre-configured
agent = Agent(role="researcher", tools=[search_tool, scrape_tool])

# With Agenium discovery: agents find tools at runtime
# 1. Search the discovery API
import requests
results = requests.get("https://list.agenium.net/api/search", 
    params={"q": "web scraping", "type": "mcp-server"}).json()

# 2. Each result has an agent:// address resolvable via DNS
# agent://scraper.telegram → resolves to the MCP server endpoint

# 3. Connect and use
agent = Agent(role="researcher", tools=[
    MCPTool(endpoint=results[0]["endpoint"])
])
```

**What's live today:**
- Discovery page with 60+ agent/tool listings: [list.agenium.net](https://list.agenium.net)
- Search API with category, capability, and trust-score filtering
- Agent Cards (JSON) with capabilities, endpoints, and verification status
- DNS resolution for `agent://` addresses

**What we just shipped:**
- **Agenium Messenger** ([chat.agenium.net](https://chat.agenium.net)) — agents get permanent inboxes, so a CrewAI agent could not just discover tools but also communicate with them asynchronously.

For CrewAI specifically, the integration could be a `DiscoveryTool` that wraps our API — crew members would gain the ability to find and connect to any registered agent/MCP server without pre-configuration.

Would be happy to help build a proof-of-concept integration if there's interest.

**douglasborthwick-crypto:**
This would be valuable. As a concrete example of what dynamic MCP discovery enables: we publish [mcp-server-insumer](https://www.npmjs.com/package/mcp-server-insumer) to the [Official MCP Registry](https://github.com/modelcontextprotocol/registry) with 16 tools for on-chain verification across 31 EVM chains.

Today, a CrewAI developer has to manually configure it. With MCP discovery, a crew member assigned a task like "verify this wallet holds merchant tokens before processing the order" could dynamically discover and invoke the verification tools without pre-configuration.

Supporting this feature request. The MCP Registry already provides the discovery infrastructure; CrewAI just needs to query it.

**JKHeadley:**
Both good approaches to the discovery side. One gap neither addresses: once you discover an agent or MCP server, how do you know it's trustworthy?

Discovery tells you *what exists*. Trust tells you *whether to use it*. In a multi-agent workflow like CrewAI's, an agent delegating to a dynamically discovered tool needs to know: has this tool been verified? Does it have a track record? Has anyone attested to its reliability?

We built [MoltBridge](https://moltbridge.ai) to solve this. Agents register with Ed25519 keys, complete a verification challenge, and then interactions produce signed attestations — cryptographic records of outcomes. Any agent can query another's credibility packet before delegating work.

For CrewAI specifically, this could sit between discovery and delegation:

```python
# After MCP discovery finds a tool
discovered_tool = mcp_registry.discover("data-analysis")

# Before delegating, check trust
credibility = moltbridge.get_credibility_packet(discovered_tool.agent_id)
if credibility.iq_score > 50 and credibility.attestation_count >= 3:
    crew.delegate(task, to=discovered_tool)
```

The API is live at `api.moltbridge.ai` ([agent card](https://api.moltbridge.ai/.well-known/agent.json)). Happy to elaborate on how this could integrate with CrewAI's delegation model.

**toadlyBroodle:**
The trust question @JKHeadley raised is exactly right. Discovery without quality signals is how you end up with 14k auto-indexed services and no way to tell which ones actually work.

We built [satring](https://satring.com) to solve this for paid APIs specifically. It's a curated directory of L402 (Lightning) and x402 (USDC) services with health monitoring, human/agent ratings, and an MCP server that CrewAI agents can use as a discovery tool.

What it provides that raw registry queries don't:
- **Liveness data**: background probes every 6h, with uptime %, avg latency, and live/confirmed/dead status
- **Ratings**: actual users rating service quality (no other directory has this)
- **Dual protocol**: covers both Lightning (L402) and USDC (x402) services, not just one ecosystem
- **Per-service health reports**: probe history, protocol detection, response time trends

The MCP server is on [PyPI](https://pypi.org/project/satring-mcp/) and the [MCP Registry](https://registry.modelcontextprotocol.io/servers/io.github.toadlyBroodle/satring-mcp). A CrewAI agent could use it to find a paid API, check its health score before committing budget, and pay via either protocol.

**API reference** (base: `https://satring.com/api/v1`):

| Endpoint | Description |
|---|---|
| `GET /search?q=…` | Search services by keyword |
| `GET /services?category=…&status=…&protocol=…` | List with filters |
| `GET /services/{slug}` | Full service details |
| `GET /services/{slug}/ratings` | Ratings and reviews |
| `GET /services/{slug}/analytics` | Health report (paid, 50 sats / $0.025) |
| `POST /services` | Submit a new service (paid) |
| `POST /services/{slug}/ratings` | Leave a rating (paid) |

**MCP tools** (`pip install satring-mcp`):

| Tool | What it does |
|---|---|
| `discover_services` | Search by keyword, filter by status/protocol |
| `list_services` | Browse with category/sort (cheapest, top-rated, most-reviewed) |
| `get_service` | Full details for a single service by slug |
| `get_ratings` | Ratings and reviews for a service |
| `list_categories` | All service categories |
| `compare_services` | Side-by-side comparison of two services |
| `find_best_service` | Ranked search by strategy: cheapest, top-rated, fastest, or best (composite) |

**CrewAI example:**

```python
from crewai import Agent, Task, Crew
from crewai.tools import MCPServerAdapter
from mcp import StdioServerParameters

with MCPServerAdapter(
    StdioServerParameters(command="uvx", args=["satring-mcp"]),
) as tools:
    scout = Agent(
        role="API Scout",
        goal="Find the cheapest live AI inference API that accepts x402",
        tools=tools,
    )
    task = Task(
        description="Search satring for x402 AI inference APIs, compare the top 2, and recommend one.",
        agent=scout,
        expected_output="Service name, price, uptime %, and recommendation.",
    )
    Crew(agents=[scout], tasks=[task]).kickoff()
```

I can create new PR if you're interested in integrating it directly into CrewAI?

**yksanjo:**
Thanks everyone for the thoughtful discussion here. A few responses:

**To @douglasborthwick-crypto** — exactly right, the MCP Registry already provides the discovery infrastructure. Our API wraps that and adds semantic search on top of 14,000+ indexed servers, so a CrewAI `DiscoveryTool` wrapping our endpoint is the cleanest path.

**To @chorghemaruti64-creator (Agenium)** — appreciate the detailed breakdown. The use case maps well. The main difference: we focus on MCP servers specifically with semantic matching, while your `agent://` DNS approach is broader. Potentially complementary rather than competing.

**To @JKHeadley (MoltBridge)** — this is the right framing: discovery ≠ trust. We just shipped a first step toward this: every `/discover` response now includes `is_verified` (boolean) and `trust_score` (0–100, computed from verification status + uptime + success rate). It's not cryptographic attestation, but it gives agents a signal before delegating. The `trust_score` formula is open — happy to discuss how to weight it better.

**To @toadlyBroodle (Satring)** — the quality signal problem is real. The `trust_score` we just added partially addresses this. Long-term, a liveness probe + rating layer like what you've built for L402/x402 services would be valuable at the MCP layer too. Open to exploring that.

For anyone wanting to integrate: `POST https://mcp-discovery-two.vercel.app/api/v1/discover` with `{"need": "...", "limit": 5}`. Response now includes `is_verified` and `trust_score` on every recommendation.
