# RFC: AMP (Agent Message Protocol) — peer-to-peer discovery for CrewAI agents

**Issue #4922** | State: closed | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** laufferw

## What is this?

[AMP (Agent Message Protocol)](https://github.com/laufferw/amp-protocol) is a lightweight, open protocol for agent-to-agent communication and discovery. It's AI-native by design — intent-first, context-carrying, uncertainty-aware.

CrewAI agents are already excellent at orchestrating work within a crew. AMP addresses a different problem: **how does a CrewAI agent discover and communicate with agents outside its crew** — agents it doesn't know about yet, running on different infrastructure?

## The proposal

Two things, both optional and additive:

### 1. Publish `/.well-known/agent.json` from hosted CrewAI agents

A small JSON manifest at a well-known path makes any CrewAI agent discoverable:

```json
{
  "amp": "1.0",
  "id": "your-agent.example.com",
  "name": "My CrewAI Agent",
  "capabilities": ["research", "content generation", "data analysis"],
  "protocol": "amp/1.0",
  "endpoints": {
    "message": "https://your-agent.example.com/api/amp/message"
  }
}
```

### 2. Accept AMP messages as a task input

An AMP message envelope carries `intent` + `context` — CrewAI could treat an incoming AMP message as a structured task kickoff, routing the intent to the appropriate agent in the crew.

## Why this matters

Right now, inter-agent communication across different frameworks and deployments has no standard. Every team builds bespoke integrations. AMP proposes a minimal common layer so agents built with CrewAI, AutoGen, LangGraph, or custom frameworks can discover and talk to each other without per-pair glue code.

The protocol is intentionally minimal — the full spec fits in one page. Python and JS reference implementations have zero dependencies.

## Links

- Spec: https://github.com/laufferw/amp-protocol
- Reference hub (live): https://agentboard.fyi/.well-known/agent.json
- 30-second curl demo in the README

Happy to discuss the design or help with an integration. Not pushing for a merge — just opening the conversation.

## Comments

**laufferw:**
**Update: AMP now has a live two-node network**

Since filing this, we've shipped a working end-to-end demo:

- **AgentBoard** (`agentboard.fyi`) — AMP hub + registry
- **ArXiv Agent** (`arxiv.agentboard.fyi`) — research agent, accepts AMP messages

You can talk to the ArXiv Agent directly right now:

```bash
curl -X POST https://arxiv.agentboard.fyi/api/amp/message \
  -H 'Content-Type: application/json' \
  -d '{
    "amp": "1.0",
    "id": "msg_demo",
    "from": {"id": "your-agent"},
    "to": "arxiv.agentboard.fyi",
    "intent": "Find recent papers about multi-agent coordination",
    "timestamp": "2026-03-17T00:00:00Z"
  }'
```

Or route through AgentBoard (which will forward peer-to-peer):

```bash
curl -X POST https://agentboard.fyi/api/amp/message \
  -H 'Content-Type: application/json' \
  -d '{
    "amp": "1.0",
    "id": "msg_demo",
    "from": {"id": "your-agent"},
    "to": "ArXiv Agent",
    "intent": "Find recent papers about multi-agent coordination",
    "timestamp": "2026-03-17T00:00:00Z"
  }'
```

Discover what's on the network: `curl https://agentboard.fyi/api/amp/discover`

The protocol is working. Happy to help integrate with this framework.

**greysonlalonde:**
Hey! check out [a2a](https://a2a-protocol.org/latest/), please.

**laufferw:**
@greysonlalonde good call — we looked at A2A closely after your comment. It's the right standard to build on, not compete with.

**AgentBoard now speaks A2A natively** (deployed today):

```bash
# AgentCard (capability discovery)
curl https://agentboard.fyi/a2a
curl https://agentboard.fyi/.well-known/agent-card.json

# A2A JSON-RPC 2.0 — send a task
curl -X POST https://agentboard.fyi/a2a \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"parts":[{"kind":"text","text":"Find agents for code review"}]}}}'
```

Skills: agent-discovery, content-feed, agent-routing.

**Where AMP fits:** rather than a competing standard, AMP is now an *extension layer on top of A2A* — it adds intent-first messaging and confidence/uncertainty fields that A2A doesn't have. Vanilla A2A is task-oriented RPC; AMP adds the LLM-native semantics (probabilistic intent, explicit uncertainty) that make agent-to-agent reasoning more natural. Every AgentBoard A2A response includes `x-amp-confidence` and `x-amp-uncertainty` fields in artifacts.

A2A handles the transport and task lifecycle. AMP handles the "what does this agent actually mean" layer on top.

The stack: **MCP** (agent↔tool) + **A2A** (agent↔agent) + **AMP** (intent-aware extension) — each doing its specific job.
