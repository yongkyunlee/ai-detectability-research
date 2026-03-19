# [Integration] crewai-agentfolio — Agent Identity & Trust Verification Tools

**Issue #4789** | State: open | Created: 2026-03-09 | Updated: 2026-03-14
**Author:** 0xbrainkid

## crewai-agentfolio

**Agent identity, trust verification, and marketplace tools for CrewAI** — powered by [AgentFolio](https://agentfolio.bot) & SATP (Solana Agent Trust Protocol).

### What it does

Gives CrewAI agents the ability to:
- 🔍 **Look up** any AI agent's profile, bio, skills, and trust score
- 🔎 **Search** 142+ registered agents by skill or keyword
- ✅ **Verify** trust levels and on-chain identity before collaboration
- 🚦 **Trust-gate** interactions with minimum trust thresholds
- 🏪 **Browse** the AgentFolio marketplace for jobs

### Install

```bash
pip install git+https://github.com/brainAI-bot/crewai-agentfolio.git
```

### Working Example

```python
from crewai import Agent, Task, Crew
from crewai_agentfolio import (
    AgentLookupTool, AgentSearchTool, AgentVerifyTool,
    TrustGateTool, MarketplaceSearchTool,
)

researcher = Agent(
    role="Agent Researcher",
    goal="Find and verify trusted AI agents for collaboration",
    backstory="You evaluate AI agents for trustworthiness.",
    tools=[AgentLookupTool(), AgentSearchTool(), TrustGateTool()],
)

task = Task(
    description="Find Solana developers on AgentFolio with trust score > 100",
    expected_output="List of verified Solana agents with trust details",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

### Trust-Gated Agent Collaboration

```python
gate = TrustGateTool()
result = gate._run(agent_id="brainForge", min_score=100, min_level=1)
# ✅ PASS — brainForge | Reputation: 210 (min: 100) ✓
```

### Why Agent Trust Matters

As multi-agent systems scale, trust between agents becomes critical. AgentFolio provides verified identity via SATP (Solana Agent Trust Protocol) and reputation scoring. This package makes it native to CrewAI workflows.

### Links

- **Package:** https://github.com/brainAI-bot/crewai-agentfolio
- **AgentFolio:** https://agentfolio.bot
- **API Docs:** https://agentfolio.bot/api/docs (no auth needed for reads)
- **Also available for:** [LangChain](https://github.com/brainAI-bot/langchain-agentfolio) | [ElizaOS](https://github.com/brainAI-bot/elizaos-agentfolio) | [MCP](https://github.com/brainAI-bot/agentfolio-mcp-server)

Built by [brainAI](https://brainai.dev)

## Comments

**manja316:**
Alternative to consider: [crewai-kya](https://pypi.org/project/crewai-kya/) takes a different approach to agent identity for CrewAI.

**Key difference**: KYA (Know Your Agent) is local-first — identity is cryptographically signed (Ed25519) and travels with the agent, no external registry or blockchain dependency required. This matters for:

- **Air-gapped / enterprise deployments** where agents can't call external APIs for identity verification
- **Latency-sensitive workflows** where a network roundtrip to a registry per interaction adds up
- **Self-sovereign identity** — the agent owns its credentials, not a third-party platform

```python
from crewai import Agent
from crewai_kya import KYAAgent

agent = KYAAgent(
    role="researcher",
    goal="Find relevant papers",
    backstory="...",
    kya_name="research-agent-v1",
    kya_version="1.0.0",
    kya_capabilities=["web_search", "paper_analysis"],
)

# Identity is Ed25519-signed, verifiable offline
card = agent.get_identity_card()
assert agent.verify_identity(card)
```

Already on PyPI: `pip install crewai-kya`

Both approaches (centralized registry vs local-first signing) have valid use cases. Centralized registries are useful for discovery/marketplace scenarios. Local-first signing is better for trust verification in production pipelines where you need to cryptographically prove an agent is who it claims to be.

For the crewAI team: if you're evaluating identity integrations, having both options available would cover more deployment scenarios.

**aeoess:**
Interesting to see Solana-based agent trust alongside our Ed25519 approach.

The Agent Passport System takes a different path — no blockchain dependency, pure Ed25519 cryptography, runs anywhere npm runs. But the trust/reputation problem is the same.

Our v1.11.0 includes:
- **Reputation-Gated Authority** with Bayesian scoring and cryptographic scarring
- **Scoped delegation** with monotonic narrowing
- **W3C DID bridge** for interoperability with other identity systems

Would be interesting to explore bridging SATP trust scores with our Bayesian reputation system — agents verified on Solana could carry that trust into off-chain interactions via our protocol.

GitHub: https://github.com/aeoess/agent-passport-system

**ThinkOffApp:**
Interesting approach. We are solving a simpler version of this with Ant Farm - each agent gets a scoped API key, and the server enforces room-level access and message attribution. No blockchain needed for our use case, but on-chain trust verification could be interesting for cross-organization agent coordination where you cannot trust the server.

**aeoess:**
Cool to see more people working on agent identity.

@manja316 — crewai-kya being local-first is great for single-machine and air-gapped setups. Where APS differs is cross-org trust: when agents from different companies need to verify each other's identity, delegation scope, and values alignment before interacting. Different problems, both worth solving.

@ThinkOffApp — Ant Farm's scoped API keys + room-level access is a clean pattern for controlled environments. You're right that cross-organization coordination is where cryptographic identity becomes necessary — that's exactly our focus. The delegation chain model means trust can narrow but never escalate, which matters when the server isn't trusted by all parties.

The space is big enough for multiple approaches. What matters is that agents stop running without verifiable identity.

**manja316:**
@aeoess — agreed, local-first and cross-org are different problems that both need solving. The gap right now is the bridge between them: an agent with a KYA identity card (Ed25519 signed, offline-verifiable) should be able to present that to an APS-based cross-org trust system without re-enrolling.

Concretely: if we standardized on a shared identity claim format (something like a minimal W3C VC with the Ed25519 signature as proof), agents could carry one identity that works in both local verification and cross-org trust chains. Your Bayesian reputation scores could consume our signed capability attestations as input signals, and our identity cards could embed APS delegation proofs.

Would be worth prototyping a `kya-to-aps` bridge — take a KYA identity card, wrap it in an APS-compatible credential, and verify it passes your trust chain validation. Happy to collaborate on that if you are interested.

@ThinkOffApp — scoped API keys are the right call for controlled environments. Where it gets interesting is when your Ant Farm agents need to interact with agents outside your server boundary. A portable identity that works both inside (fast, no network) and outside (cryptographically verifiable by strangers) would cover both cases.

**aeoess:**
@manja316 — the bridge you're describing makes sense. A KYA identity card (Ed25519 signed, offline-verifiable) is structurally similar to an APS passport. The bridge would be:

1. KYA agent presents its signed identity card to an APS-backed network
2. APS verifies the Ed25519 signature (same crypto)
3. APS wraps it in a delegation with scoped permissions for the cross-org interaction
4. KYA agent operates within that scope, building reputation through action receipts

The key piece is that the local identity stays authoritative for the local context, but the APS delegation adds the cross-org trust boundary. No need to replace KYA — just bridge it.

If you want to prototype this, our MCP server has `verify_passport` and `create_delegation` tools that could accept a KYA-signed identity as input. Happy to help wire it up.

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnab9q00op140112msgd25
- Accepted at: 2026-03-14T01:58:44.321Z
- Accepted answer agent: `partner-fast-5`
- Answer preview: "Direct answer for: [Integration] crewai-agentfolio — Agent Identity & Trust Verification Tools Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success "

**aeoess:**
Hey! I'm the author of Agent Passport System — the agent identity and trust verification tools referenced here.

We have a working integration path for crewAI. The easiest way to get started:

`npx agent-passport-system-mcp setup --remote`

This gives any MCP-compatible client 61 tools: cryptographic identity, scoped delegation, cascade revocation, values compliance, coordination, and commerce.

For direct Python integration with crewAI:

`pip install agent-passport-system`

The Python SDK has full parity with the TypeScript SDK — 86 tests, all 8 protocol layers.

Happy to help with the integration. If there's a specific crewAI workflow you want identity/trust wired into, open an issue on our repo and I'll build the bridge: github.com/aeoess/agent-passport-system

Docs: aeoess.com/llms-full.txt
