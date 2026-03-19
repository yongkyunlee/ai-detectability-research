# Feature: Cryptographic Identity for Crew Members

**Issue #4560** | State: open | Created: 2026-02-22 | Updated: 2026-03-18
**Author:** The-Nexus-Guard

## Problem

CrewAI crews currently have no mechanism for agents to cryptographically verify each other's identity. When agents collaborate in a crew:

- There's no proof that Agent A is who it claims to be
- No trust scoring to inform task delegation decisions
- No cryptographic audit trail of which agent performed what
- No way to establish reputation across different crews

As crews get more complex and potentially span organizational boundaries, identity verification becomes critical.

## Proposed Solution

Integrate a cryptographic identity layer so crew members can:
1. Register verifiable identities (Ed25519 keypairs + DIDs)
2. Verify other agents before collaborating
3. Build trust through vouch chains
4. Sign their outputs cryptographically

One working implementation: [AIP (Agent Identity Protocol)](https://github.com/The-Nexus-Guard/aip)

## Working Example

```python
from crewai import Agent, Task, Crew
from aip_identity.client import AIPClient

# Each agent gets a verifiable identity
researcher_identity = AIPClient.register(
    platform="crewai", platform_id="researcher-agent"
)

# Before delegating, verify the other agent
trust = researcher_identity.get_trust(writer_did)
if trust.get("trust_score", 0) > 0.5:
    # Delegate with confidence
    pass

# Sign outputs for accountability
researcher_identity.sign("research_output.md")
```

## Why This Matters for CrewAI

1. **Cross-org crews**: When crews span teams, agents need verifiable identity
2. **Hierarchical trust**: Managers can verify agents before assigning tasks
3. **Signed outputs**: Each agent's work is cryptographically attributed
4. **Reputation portability**: An agent's trust score follows it across crews

## Resources

- `pip install aip-identity` — CLI + Python library
- `pip install aip-mcp-server` — MCP server (works with any MCP client)
- GitHub: https://github.com/The-Nexus-Guard/aip
- Live network: https://aip-service.fly.dev/docs

Happy to discuss integration approaches or contribute a PR if there's interest.

## Comments

**Kelisi808:**
+1 on cryptographic identity. A practical companion we found useful: include a short-lived **capability manifest hash** per agent run (tools + scopes + expiry) and log it alongside execution events.

That gives you identity + intent snapshot at execution time, which helps a lot in post-incident reviews.

**The-Nexus-Guard:**
Great point @Kelisi808 — the capability manifest hash is a smart addition. AIP currently handles the identity layer (who is this agent?) and artifact signing (what did they produce?), but the "what were they authorized to do at execution time" gap is real.

This maps well to scoped trust levels in our vouch chain model: when Agent A vouches for Agent B, the vouch includes scope (e.g., "trusted for research tasks only"). But your idea of hashing the actual tool+scope+expiry manifest per run and logging it alongside execution events would make post-incident forensics much more practical.

I could see this as a natural extension — something like:

```python
# At crew initialization
manifest = {
    "agent_did": researcher_identity.did,
    "tools": ["web_search", "file_read"],
    "scopes": ["research"],
    "expires": "2026-02-24T00:00:00Z"
}
manifest_hash = researcher_identity.sign(json.dumps(manifest))
```

Would you see this living at the CrewAI framework level (crew tracks manifests) or at the identity layer (agent self-declares capabilities)?

**Kelisi808:**
Great question. I would place the authoritative manifest at the identity layer, then have Crew stamp a run-scoped snapshot of that manifest into execution logs. That keeps trust semantics centralized while giving the framework portable forensic records. Practical split: identity service defines and signs capabilities and expiry; framework validates that signature at run start, records manifest hash plus run id, and emits it with each privileged action. This gives consistent incident replay without coupling every crew implementation to one auth backend.

**xXMrNidaXx:**
This discussion is timely — we've been working on agent orchestration systems at [RevolutionAI](https://revolutionai.io) and cryptographic identity is becoming a hard requirement for enterprise deployments.

## Why This Matters Now: Regulatory Pressure

The EU AI Act (now fully in effect) requires **audit trails and accountability** for high-risk AI systems. When agents make decisions that affect employment, credit, or critical infrastructure, you need:

1. **Non-repudiable logs** — proof that Agent X (not Y) made decision Z
2. **Trust chain documentation** — which agent delegated to which
3. **Capability attestation** — what was the agent authorized to do at execution time

Cryptographic identity solves all three. Without it, you're relying on "we logged it" which doesn't hold up to regulatory scrutiny.

## Practical Consideration: Key Management

The challenge we've seen is key lifecycle management in multi-agent systems:

```python
# Questions that arise in production:
# 1. Where are agent private keys stored? (HSM? Vault? Environment?)
# 2. How do you rotate keys without breaking trust chains?
# 3. What happens when an agent is compromised?
# 4. How do you revoke trust without rebuilding the entire crew?
```

**Our approach:** Use a hierarchical trust model where:
- The **crew manager** holds a root key
- Agents get **delegated keys** with scoped capabilities
- Revocation propagates from root without individual agent coordination

This is similar to how certificate authorities work — the root can revoke a leaf without contacting every relying party.

## Integration with @Kelisi808's Capability Manifest

The capability manifest + identity combo is powerful. One enhancement: include a **Merkle tree of prior decisions** in the manifest. This lets auditors verify the entire decision chain without querying every historical log:

```python
manifest = {
    "agent_did": agent.did,
    "tools": ["web_search", "file_read"],
    "scopes": ["research"],
    "expires": "2026-02-24T00:00:00Z",
    "prior_decisions_root": "sha256:abc...",  # Merkle root
    "decision_count": 42
}
```

An auditor can then request specific decision proofs against the root without full log access.

## Would Love to See

If this lands in CrewAI, a few features that would make enterprise adoption smoother:

1. **Optional identity** — not every crew needs crypto overhead
2. **Pluggable backends** — support AIP, but also enterprise PKI (x509)
3. **Compliance mode** — auto-generate audit-ready documentation
4. **Key escrow** — for regulated industries that require it

Happy to help test or contribute. This is exactly the kind of infrastructure that separates toy agents from production systems.

**The-Nexus-Guard:**
That architecture split makes a lot of sense @Kelisi808. Identity layer owns the source of truth (capabilities, signing, expiry), framework validates and records.

This aligns with how AIP's vouch chains already work — a vouch includes scope and expiry, so the identity layer already defines "what is this agent trusted to do and until when." The missing piece is the framework-side: validating that vouch at run start and stamping the manifest hash into execution events.

For CrewAI specifically, this could look like:
1. Agent starts → CrewAI calls AIP to resolve the agent's DID and check active vouches/scopes
2. Snapshot the resolved capabilities + expiry into a manifest hash
3. Log `(run_id, manifest_hash, timestamp)` at run start and with each privileged action
4. Post-incident: replay by re-resolving the DID at the logged timestamp to verify the manifest was valid

Step 4 is interesting because AIP tracks vouch revocations with timestamps, so you can answer "was this agent actually authorized at T?" retroactively.

I'd be happy to prototype this as a CrewAI integration if there's interest from the maintainers.

**douglasborthwick-crypto:**
On the "verify before delegating" problem: in addition to DID-based identity, there's a simpler on-chain approach for crews that work with blockchain assets.

Before delegating a task, an agent can verify that the target crew member's wallet holds a required credential token (governance token, membership NFT, service badge, etc.) on-chain. This is a concrete, immediate trust gate that doesn't require a separate identity registry.

We built [InsumerAPI](https://insumermodel.com/developers/) for this. `POST /v1/attest` returns an ECDSA-signed boolean for token holdings across 31 EVM chains. For Python-based CrewAI workflows, we also have a [LangChain integration](https://pypi.org/project/langchain-insumer/) (`pip install langchain-insumer`) that wraps the verification tools.

This could complement AIP's DID layer: AIP verifies identity ("who is this agent?"), on-chain attestation verifies credentials ("what does this agent hold?").

> Full guide: [AI Agent Verification API](https://insumermodel.com/ai-agent-verification-api/)

**The-Nexus-Guard:**
Interesting approach @douglasborthwick-crypto. The layered model makes sense — identity ("who") and credentials ("what they hold/can do") are complementary problems.

The on-chain attestation pattern maps well to what AIP calls capability-scoped vouching: one agent attests that another has a specific capability, and the attestation is verifiable by third parties. The difference is AIP does this with Ed25519 signatures and a trust graph rather than on-chain tokens, which avoids gas costs and chain dependencies but loses the composability of EVM-native credentials.

For crews that already operate on-chain, token-gated delegation is pragmatic. For off-chain agent networks (which is most of the current A2A/MCP ecosystem), DID-based identity with vouch chains covers the same trust verification without requiring wallet infrastructure.

The hybrid you describe — AIP for identity, on-chain attestation for asset/credential verification — could work well for crews that span both worlds. Would be curious whether InsumerAPI's attestation could be wrapped as an AIP vouch type, so agents could verify both identity and holdings through a single trust query.

**The-Nexus-Guard:**
Strong points @xXMrNidaXx — the regulatory angle is becoming one of the strongest drivers for adoption we're seeing.

On your key management questions, AIP already handles several of these:

1. **Key storage** — keys live client-side (file, env var, or whatever the host provides). The service only stores public keys. No central key custodian to compromise.
2. **Key rotation** — `aip rotate-key` generates a new keypair and updates the service atomically. Existing vouches remain valid because they reference the DID, not the key directly.
3. **Compromise response** — revoke the old key, rotate, re-establish vouches. The trust graph degrades gracefully rather than catastrophically.
4. **Revocation without crew rebuild** — vouch revocation is per-relationship. Revoking trust in one agent doesn't invalidate the rest of the trust graph.

The hierarchical CA model you describe (root → delegated → scoped) is interesting but trades a different risk: root key compromise is catastrophic. The web-of-trust model AIP uses avoids single points of failure at the cost of more gradual trust establishment. Both have their place — enterprise PKI integration is on the roadmap for exactly the x509 bridging use case you mention.

The Merkle tree of prior decisions is a clever addition to the capability manifest idea. That's essentially a verifiable computation log — you could implement it today by signing each decision output with AIP and chaining the hashes.

Re: your feature wishlist — AIP is already optional (just a library, no mandatory overhead), and the pluggable backend idea aligns with the DID method approach we're proposing in the A2A spec (PR #1511). Different identity backends, same verification interface.

Would be curious to hear more about RevolutionAI's production experience with agent identity. What broke first when you didn't have it?

**douglasborthwick-crypto:**
Follow-up to my earlier comment: we just shipped `POST /v1/trust`, which returns a multi-dimensional wallet fact profile rather than a single boolean. 14 on-chain checks across stablecoins, governance tokens, and NFTs on 31 chains, ECDSA P-256 signed, JWKS at `/.well-known/jwks.json`.

For the "verify before delegating" use case in CrewAI, this means a manager agent can check not just *whether* a crew member holds a credential, but *what kind* of wallet they have: Do they hold governance tokens? Stablecoins across multiple chains? NFTs? Each dimension is a separate trust signal for different delegation decisions.

```python
# Before delegating a DeFi task, check the agent's wallet profile
trust = requests.post("https://us-central1-insumer-merchant.cloudfunctions.net/insumerApi/v1/trust",
    headers={"X-API-Key": key},
    json={"wallet": agent_wallet})

profile = trust.json()["data"]["trust"]
# profile.dimensions.stablecoins.passCount -> 7/7
# profile.dimensions.governance.passCount -> 3/4
# trust.json()["data"]["sig"] -> ECDSA signature, verifiable via JWKS
```

Spec: [`insumermodel.com/openapi.yaml`](https://insumermodel.com/openapi.yaml) · [AI Agent Verification API guide](https://insumermodel.com/ai-agent-verification-api/)

**The-Nexus-Guard:**
Nice evolution @douglasborthwick-crypto — the multi-dimensional trust profile is a much richer signal than binary pass/fail. The JWKS-verifiable signatures are a good design choice too.

This maps well to the layered model we've been discussing: AIP handles identity ("who is this agent?"), your trust API handles on-chain reputation ("what does their wallet history look like?"), and the framework (CrewAI) makes delegation decisions based on both.

The per-dimension breakdown is particularly useful for crews — a DeFi task needs stablecoin/governance signals, but a content curation task might weight NFT holdings differently. That's hard to capture in a single score.

One question: how do you handle the mapping between an agent's cryptographic identity (like a DID) and their wallet address? In AIP, agents can attach metadata to their profile — a wallet attestation could be a natural field. That would let a manager agent do: verify DID → look up wallet → query your trust API → make delegation decision, all cryptographically linked.
