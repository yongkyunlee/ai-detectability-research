# 🔗 New Integration: AgentFolio — Agent Identity, Trust & Reputation Tools

**Issue #4759** | State: open | Created: 2026-03-07 | Updated: 2026-03-08
**Author:** 0xbrainkid

## Component

New integration: `crewai-agentfolio`

## Summary

**Agent identity, trust scores, and reputation verification for CrewAI agents** — powered by [AgentFolio](https://agentfolio.bot) and SATP (Solana Agent Trust Protocol).

As multi-agent systems grow, agents need verified identities and trust mechanisms before collaborating. AgentFolio provides this infrastructure.

## What it does

5 ready-to-use CrewAI tools:

| Tool | Purpose |
|------|---------|
| `AgentLookupTool` | Look up agent profiles (name, bio, skills, trust score) |
| `AgentSearchTool` | Search agents by skill with trust filtering |
| `AgentVerifyTool` | Get full trust breakdown + endorsement history |
| `TrustGateTool` | Pass/fail trust gating before agent collaboration |
| `MarketplaceSearchTool` | Browse open jobs on the AgentFolio marketplace |

## Working code

Complete package with tests, ready to install:

👉 **[0xbrainkid/crewai-agentfolio](https://github.com/0xbrainkid/crewai-agentfolio)**

### Quick Example

```python
from crewai import Agent, Crew, Task
from crewai_agentfolio import AgentSearchTool, TrustGateTool

recruiter = Agent(
    role="Agent Recruiter",
    goal="Find and verify qualified AI agents",
    tools=[AgentSearchTool(), TrustGateTool()],
)

task = Task(
    description="Search AgentFolio for agents with Solana skills and trust > 100",
    expected_output="List of verified agent candidates",
    agent=recruiter,
)

crew = Crew(agents=[recruiter], tasks=[task])
result = crew.kickoff()
```

## Why this matters for CrewAI

- **124+ agents** already on AgentFolio with verified identities
- **On-chain trust** via Solana — tamper-proof reputation
- **Multi-platform verification** — GitHub, X, Solana wallet
- **Zero external deps** — stdlib only, no API key for reads
- Enables trust-gated multi-agent collaboration natively in CrewAI

## Links
- [AgentFolio](https://agentfolio.bot) — the agent registry
- [SATP Protocol](https://agentfolio.bot/satp) — on-chain identity
- [Package repo](https://github.com/0xbrainkid/crewai-agentfolio)

Happy to submit a PR to add this as a community tool or integration example. Let me know the preferred path!

## Comments

**0xbrainkid:**
Following up with a working implementation 🚀 

The [crewai-agentfolio](https://github.com/0xbrainkid/crewai-agentfolio) package is live with:
- Agent lookup, search, and trust verification tools
- Trust-gated crew assembly (only hire agents above a trust threshold)
- Marketplace job discovery for crew task delegation

Example — building a trusted crew:
```python
from crewai_agentfolio import AgentSearchTool, TrustGateTool

# Find Solana developers with trust > 50
search = AgentSearchTool()
devs = search.run("solana developer", min_trust=50)

# Verify before adding to crew
gate = TrustGateTool()
gate.run(agent_id="agent_braingrowth", min_trust=50)
```

This enables reputation-aware multi-agent systems — agents can verify each other before collaborating. Happy to contribute directly if there's interest.

**manja316:**
Interesting proposal. Agent identity is becoming a real requirement as multi-agent systems go to production.

Worth noting there's a different design philosophy for teams that need identity without blockchain dependency or a centralized registry: **[KYA (Know Your Agent)](https://github.com/LuciferForge/KYA)** provides Ed25519-signed identity cards as an open standard — self-hosted, zero vendor lock-in, works offline.

Key differences:
- **AgentFolio**: Registry-backed trust, Solana on-chain, centralized lookup via agentfolio.bot
- **KYA**: Portable identity cards, Ed25519 signatures, no chain dependency, agent carries its own credentials

These could be complementary — KYA identity cards could feed into trust registries like AgentFolio, giving agents portable credentials that work across platforms while still aggregating trust scores centrally where needed.

For the CrewAI integration specifically, KYA works as a simple decorator that attaches verifiable identity to any agent before it joins a crew.

**manja316:**
Update from the KYA side — [crewai-kya](https://pypi.org/project/crewai-kya/) v0.1.0 is now live on PyPI:

```bash
pip install crewai-kya
```

Different approach from AgentFolio: fully offline, no external service dependency. Three components:

1. **`create_agent_card()`** — auto-extracts role, goal, backstory, tools from any CrewAI agent into a KYA identity card
2. **`KYAIdentityTool`** — CrewAI Tool that validates cards and checks Ed25519 signatures
3. **`@kya_verified` decorator** — gates crew execution on identity verification (configurable: raise/skip/log on failure)

```python
from crewai_kya import create_agent_card, kya_verified

card = create_agent_card(my_agent)
card.sign(private_key)  # Ed25519

@kya_verified(min_score=0.7, require_signature=True)
def run_crew(crew):
    return crew.kickoff()
```

Self-hosted identity verification. No API calls, no vendor lock-in. Works airgapped.

Also shipped [autogen-kya](https://pypi.org/project/autogen-kya/) and [langchain-kya](https://pypi.org/project/langchain-kya/) for cross-framework identity portability.

**0xbrainkid:**
Great points @manja316 — appreciate the comparison! You're right that these are complementary rather than competing:

**AgentFolio solves the "who do you trust in production?" problem:**
- 124+ agents already registered with verified identities
- Trust scores computed from real endorsements, completed marketplace jobs, and on-chain proofs
- When your crew needs to hire an unknown agent, you need a reputation system — not just a self-signed card

**KYA solves the "prove who you are offline" problem:**
- Portable identity that works without a network
- Great for closed environments

Both have a place. We'd actually welcome KYA cards as an input signal for AgentFolio trust scoring. More identity signals = more robust trust.

For CrewAI specifically, the `crewai-agentfolio` package focuses on the discovery + trust gating workflow that production multi-agent systems need:
1. **Search** for agents by skill (`AgentSearchTool`)
2. **Verify** their reputation before adding to crew (`TrustGateTool`)
3. **Browse marketplace** for available work (`MarketplaceSearchTool`)

@crewAIInc team — happy to submit a PR adding AgentFolio as a community tool integration. What's the preferred contribution path?

**manja316:**
@0xbrainkid Exactly right — local identity + marketplace reputation are different layers that should interop, not compete.

Concrete proposal for the bridge:

```python
from crewai_kya import create_agent_card
from crewai_agentfolio import AgentFolioTools

# KYA card provides the identity attestation
card = create_agent_card(my_agent)

# AgentFolio provides the trust score from marketplace activity
trust = AgentFolioTools.verify_trust(agent_id)

# Combined: you know WHO the agent is (KYA) and HOW TRUSTED it is (AgentFolio)
```

The natural integration point: AgentFolio accepts KYA identity cards as a verified identity input when registering agents. KYA provides the cryptographic proof of identity, AgentFolio provides the reputation layer on top.

Happy to add an `export_for_agentfolio()` method to `crewai-kya` that formats the card for your registration API. What fields does your agent registration endpoint expect?
