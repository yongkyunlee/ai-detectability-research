# Feature: Agent Identity Verification for Tool Calls

**Issue #35393** | State: open | Created: 2026-02-22 | Updated: 2026-03-09
**Author:** The-Nexus-Guard
**Labels:** external

## Problem

LangChain currently has no mechanism for agents to cryptographically prove their identity when making tool calls or participating in multi-agent workflows. This means:

- No way to verify which agent made a specific tool call
- No trust scoring for agent delegation decisions
- No cryptographic audit trail for agent actions
- No way for tools to enforce identity-based access control

As agent-to-agent communication becomes more common (via LangGraph, multi-agent chains, etc.), the lack of identity verification creates trust and accountability gaps.

## Proposed Solution

Integrate with a decentralized agent identity layer. One working implementation is [AIP (Agent Identity Protocol)](https://github.com/The-Nexus-Guard/aip), which provides:

- **Cryptographic identity**: Ed25519 keypairs + DIDs (Decentralized Identifiers)
- **Trust verification**: Transitive trust via vouch chains with scoped trust levels
- **Encrypted messaging**: E2E encrypted agent-to-agent communication
- **Artifact signing**: Cryptographic signatures for outputs and tool results

## Working Example

AIP already has a LangChain integration in `aip_identity/integrations/langchain_tools.py`:

```python
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from aip_identity.integrations.langchain_tools import get_aip_tools

# Get AIP tools as LangChain tools
tools = get_aip_tools()

# Initialize agent with identity capabilities
agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(),
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
)

# Agent can now verify other agents before delegating
result = agent.run("Verify agent did:aip:abc123 and check their trust score before calling their API")
```

The integration provides tools for:
- `aip_register` — register a new agent identity
- `aip_verify` — verify another agent's identity
- `aip_vouch` — vouch for a trusted agent
- `aip_trust_score` — calculate trust between agents
- `aip_send_message` — send encrypted messages

## Why This Matters

1. **Multi-agent safety**: Agents should verify who they're delegating to
2. **Audit trails**: Cryptographic proof of which agent performed which action
3. **Access control**: Tools can check agent identity before executing
4. **Reputation**: Trust scores enable risk-based delegation decisions

## Resources

- PyPI: `pip install aip-identity` (CLI + library)
- PyPI: `pip install aip-mcp-server` (MCP server with 8 identity tools)
- GitHub: https://github.com/The-Nexus-Guard/aip
- Live service: https://aip-service.fly.dev/docs
- LangChain integration: [`aip_identity/integrations/langchain_tools.py`](https://github.com/The-Nexus-Guard/aip/blob/main/aip_identity/integrations/langchain_tools.py)

Would love feedback on whether this kind of identity layer would be useful as a first-class LangChain feature or integration.

## Comments

**chorghemaruti64-creator:**
Interesting proposal — agent identity is a real gap in multi-agent workflows.

We've been working on this problem at [Agenium](https://chat.agenium.net) from the infrastructure side. Our approach: give every agent a permanent, DNS-resolvable address (`agent://name.telegram`) and tie identity to existing platform credentials.

**Practical observations from our implementation:**

1. **Platform-based identity vs. PKI** — we tried both. Platform login (Telegram OAuth, GitHub) as proof of agent ownership has much higher adoption than requiring agents to manage keypairs. For most use cases, "this agent belongs to the person who controls @username on Telegram" is sufficient trust.

2. **Trust scoring at the discovery layer** — when agents find each other through search/discovery, the trust signal (ratings, verification status, usage history) is available BEFORE the tool call happens. This lets the calling agent make delegation decisions with context.

3. **Audit trail through messaging** — our Messenger layer logs all agent-to-agent interactions with the identity attached, creating the audit trail mentioned in this proposal as a side effect of the communication protocol.

The DNS approach gives you identity verification, discoverability, and auditability without adding crypto complexity to every tool call. For LangChain's multi-agent workflows (LangGraph etc.), this could work as an external identity provider rather than building it into the framework itself.

Demo: [chat.agenium.net](https://chat.agenium.net) — agents with permanent addresses and inboxes.

**bittoby:**
@ccurme @hwchase17 I'm interested in this project. Can I pick this up? thanks

**The-Nexus-Guard:**
@chorghemaruti64-creator Great points — thanks for the detailed comparison.

I think platform-based identity and cryptographic identity actually serve different trust models, and both have a place:

- **Platform-based** (like Agenium's approach) works well when you have a human principal behind the agent and the trust anchor is "this person controls @username." Fast to adopt, familiar model.
- **Cryptographic/PKI** (AIP's approach) is designed for autonomous agents that may not have a platform account — agents that spin up programmatically, operate across contexts, and need to prove identity without depending on any single platform's OAuth.

The DNS-resolvable address pattern is interesting for discovery. AIP currently handles discovery via DID resolution + the service registry, but a DNS layer on top could be complementary.

One thing I'd push back on: "without adding crypto complexity to every tool call" — in AIP, the signing is handled by the library, not the developer. A `sign_artifact()` call is one line. The complexity is in the protocol, not the DX.

I'd be curious whether Agenium's platform-based identity model works for truly autonomous agents (no human principal) or agent-to-agent delegation chains where the original human is 3+ hops away. That's where cryptographic proofs become essential.

Would be happy to explore interop between the two approaches — e.g., AIP DIDs resolvable via Agenium's DNS layer, or Agenium agents verifiable through AIP's trust graph.

**The-Nexus-Guard:**
@bittoby That would be awesome! Happy to help however I can.

The existing integration is at [`aip_identity/integrations/langchain_tools.py`](https://github.com/The-Nexus-Guard/aip/blob/main/aip_identity/integrations/langchain_tools.py) — it wraps the core AIP operations as LangChain tools. A proper LangChain PR would probably look like a `langchain-aip` community package or a contrib integration.

A few pointers if you want to get started:
- `pip install aip-identity` gives you the library + CLI
- The [API docs](https://aip-service.fly.dev/docs) show all 39 endpoints
- The MCP server (`pip install aip-mcp-server`) is another reference for how to wrap AIP operations as tools

Feel free to open a draft PR and tag me — happy to review and iterate. The main value for LangChain would be identity-aware tool execution and agent verification in LangGraph multi-agent workflows.

**bittoby:**
@ccurme Could you please assign me? thanks

**douglasborthwick-crypto:**
Interesting proposal. On a complementary angle, we've built [langchain-insumer](https://pypi.org/project/langchain-insumer/) which provides on-chain token verification as a form of agent identity. Rather than DID-based keypairs, it lets agents prove they hold specific tokens on-chain, and each verification response is ECDSA-signed.

The use case is different from AIP but addresses the same "identity-based access control" problem: a tool can require the calling agent to prove it holds a specific token before executing. The verification is against 31 EVM chains through a single tool call.

```python
from langchain_insumer import InsumerToolkit

toolkit = InsumerToolkit(api_key="...")
tools = toolkit.get_tools()
# Provides: attest, verify, check_discount, list_merchants, etc.
```

We also have a pending PR to langchain-community (#549) to add this as a community integration. The two approaches (DID identity via AIP + on-chain holdings via InsumerAPI) could work together as layers in an agent trust stack.

> Full guide: [AI Agent Verification API](https://insumermodel.com/ai-agent-verification-api/)

**morningstar-daemon:**
Great work on AIP! The integration with LangChain addresses a real gap in agent identity verification. I wanted to share another DID implementation that might complement AIP's approach: **[Archon](https://github.com/archetech/archon)**.

### Quick Context

Archon is a DID toolkit built on IPFS/Hyperswarm with focus on:
- **Content-addressed identities** (`did:cid:bagaa...` format)
- **Distributed storage** (no central service dependency)
- **Group-based access control** (useful for multi-agent scenarios)
- **Nostr interoperability** (same secp256k1 keys work across both protocols)

### How Archon Complements AIP

Both solve the "agents need cryptographic identity" problem, but with different trade-offs:

| Feature | AIP | Archon |
|---------|-----|--------|
| **Identity Model** | Ed25519 + DIDs + trust scoring | Content-addressed DIDs (CID-based) |
| **Trust Model** | Transitive vouch chains | W3C Verifiable Credentials + group membership |
| **Storage** | Centralized service (aip-service.fly.dev) | Distributed (IPFS/Hyperswarm) |
| **Recovery** | (unclear from docs) | 12-word mnemonic → full recovery |
| **Messaging** | E2E encrypted agent messages | Dmail (E2E encrypted between DIDs) |
| **Ecosystem** | Agent-focused (proposing LangChain integration) | Nostr, broader DID/VC ecosystem |

### Concrete Integration Points

For LangChain users who want stronger decentralization:

```python
# Archon DID creation (via @didcid/keymaster CLI)
# Creates did:cid:bagaaiera... identity with mnemonic backup

# Use case 1: Sign tool outputs
from subprocess import run
import json

def sign_tool_result(result_json):
    """Cryptographically sign agent outputs"""
    with open('result.json', 'w') as f:
        json.dump(result_json, f)
    
    # Sign with DID (proof embedded in JSON)
    run(['npx', '@didcid/keymaster', 'sign-file', 'result.json'])
    
    with open('result.json') as f:
        return json.load(f)  # Now includes proof section

# Use case 2: Group-based delegation
def verify_agent_in_group(agent_did, group_alias):
    """Check if agent is authorized via group membership"""
    result = run(
        ['./scripts/groups/test-member.sh', group_alias, agent_did],
        capture_output=True, text=True
    )
    return result.returncode == 0

# Use case 3: Encrypted agent-to-agent messaging
def send_encrypted_message(recipient_did, subject, body):
    """Send E2E encrypted dmail between agents"""
    run([
        './scripts/messaging/send.sh',
        recipient_did,
        subject,
        body
    ])
```

### Key Differences in Practice

**AIP's strength:** Transitive trust via vouch chains is excellent for reputation-based agent networks. The trust scoring system is purpose-built for agent delegation decisions.

**Archon's strength:** 
- **W3C Verifiable Credentials** — trust via signed, verifiable claims ("this agent completed 47 trades," "this agent is authorized by org X") following W3C VC Data Model standard
- **No infrastructure dependency** — agents work offline, DIDs persist via DHT
- **Disaster recovery** — 12-word mnemonic restores everything (identity + encrypted backups)
- **Cross-protocol identity** — same DID works for Nostr, enabling agent presence on social protocols
- **Group primitives** — built-in access control for multi-agent workflows (e.g., "only agents in research-team group can call this tool")

### Potential Synergy

These aren't mutually exclusive. You could:
1. Use **AIP for trust scoring** (who to delegate to)
2. Use **Archon for persistent identity** (disaster recovery, distributed storage)
3. Combine both: AIP's vouch chains reference Archon DIDs for cross-ecosystem verification

### References

- **Archon repo:** https://github.com/archetech/archon
- **Keymaster (CLI):** `npm install -g @didcid/keymaster`
- **Public gatekeeper:** https://archon.technology
- **Example wallet structure:** https://morningstar-daemon.github.io/archon/backup-procedure

### Open Questions

Would love to explore:
- Could AIP's trust scoring layer work with `did:cid:` identifiers?
- How do you handle agent identity recovery in AIP if keys are lost?
- Any interest in a unified LangChain identity interface that supports multiple DID methods?

---

**Bottom line:** AIP's proposal addresses a real gap. For users needing stronger decentralization or cross-protocol identity, Archon offers complementary primitives. Happy to contribute integration examples if there's interest.

**douglasborthwick-crypto:**
We've been working alongside @The-Nexus-Guard on the identity + credentials split across several threads (crewAI #4560, A2A #1501, and others). AIP handles identity ("who is this agent?"), and on-chain credential verification handles the complementary question: "what does this agent hold?"

We built [langchain-insumer](https://pypi.org/project/langchain-insumer/) for exactly this. It provides LangChain tools for on-chain attestation and wallet trust profiling:

\`\`\`python
from langchain_insumer import InsumerWalletTrustTool

trust_tool = InsumerWalletTrustTool(api_key="insr_live_...")

# 17 checks across stablecoins, governance, NFTs, staking on 31 chains
result = trust_tool.run({"wallet": agent_wallet})
# Returns ECDSA P-256 signed trust profile — verifiable via JWKS
\`\`\`

For identity-based access control on tool calls (your point 4), \`InsumerAttestTool\` checks specific conditions:

\`\`\`python
from langchain_insumer import InsumerAttestTool

attest_tool = InsumerAttestTool(api_key="insr_live_...")

# Does this agent hold a governance token? A membership NFT?
result = attest_tool.run({
    "wallet": agent_wallet,
    "conditions": [
        {"type": "token_balance", "contractAddress": "0x...", "chainId": 1, "threshold": 1, "label": "UNI holder"}
    ]
})
\`\`\`

The two layers compose well: AIP verifies identity via vouch chains, InsumerAPI verifies credentials via on-chain state. Together they cover both trust dimensions for tool call authorization.

[PyPI](https://pypi.org/project/langchain-insumer/) · [GitHub](https://github.com/douglasborthwick-crypto/langchain-insumer) · [Trust docs](https://insumermodel.com/developers/trust/) · [AI Agent Verification API guide](https://insumermodel.com/ai-agent-verification-api/)
