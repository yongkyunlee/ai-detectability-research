# Feature: Cryptographic action receipts for multi-agent crew audit trails

**Issue #4754** | State: open | Created: 2026-03-06 | Updated: 2026-03-15
**Author:** Cyberweasel777

## Problem

When a CrewAI crew executes tasks across multiple agents, there's no standard way to cryptographically prove:
- Which agent executed which task
- What inputs each agent received
- What outputs each agent produced
- Whether any output was tampered with between agent handoffs

For enterprise deployments, this is a compliance blocker. For agent-to-agent commerce (x402, Stripe agent checkout), it's a trust gap.

## Proposed Solution: Agent Action Receipts (AAR)

[AAR v1.0](https://github.com/Cyberweasel777/agent-action-receipt-spec) is an open standard (MIT) for signed receipts that chain across agent actions:

- **Ed25519 signatures** over canonicalized JSON (JCS-SORTED-UTF8-NOWS)
- **SHA-256 input/output hashing** — verifiable without exposing raw data
- Each agent in the crew signs its task execution, creating a verifiable chain of custody
- Failed/partial tasks are explicitly marked (`status: 'failure' | 'partial'`)

### For CrewAI specifically

```python
# Conceptual integration
@task
def research_task(self, agent, context):
    result = agent.execute(context)
    receipt = sign_action_receipt(
        agent_id=agent.role,
        principal=crew.manager,
        action={'type': 'research', 'target': context.topic},
        input_hash=sha256(context),
        output_hash=sha256(result),
    )
    return result, receipt
```

Each crew execution produces a receipt chain — complete audit trail from delegation to final output.

### Ecosystem Compatibility

- [Mastercard Verifiable Intent](https://www.mastercard.com/us/en/news-and-trends/stories/2026/verifiable-intent.html) (announced March 5, 2026) — bidirectional mapping included
- [x402 (Coinbase)](https://github.com/coinbase/x402) — complementary payment verification standard
- Aztec L2 ZK-compatible — verify receipts on-chain without revealing contents

### SDK

TypeScript SDK live on npm:
```bash
npm install botindex-aar
```
Python SDK in development.

- **Spec:** https://github.com/Cyberweasel777/agent-action-receipt-spec
- **Landing:** https://aar.botindex.dev
- **npm:** https://www.npmjs.com/package/botindex-aar

Happy to contribute a PR for CrewAI integration. MIT licensed, single dependency.

## Comments

**Cyberweasel777:**
Update: we just shipped the identity layer companion — **Session Continuity Certificates (SCC)**.

AAR proves what a crew member did. SCC proves the crew member is the same entity across sessions — cryptographic identity continuity via hash-linked certificate chains.

For multi-agent crews, this means each agent maintains a verifiable identity chain. When Agent A delegates to Agent B, you can verify both *what B did* (AAR) and *that B is the same trusted agent from previous runs* (SCC).

- **SCC Spec:** https://github.com/Cyberweasel777/session-continuity-certificate-spec
- **SCC SDK:** `npm install botindex-scc`
- **AAR SDK:** `npm install botindex-aar` / `pip install botindex-aar`

Same crypto stack (Ed25519 + JCS + SHA-256), one keypair for both.

**manja316:**
The receipt chain concept is solid for multi-agent audit. Two complementary pieces that already exist in Python and could interop:

- **[ai-decision-tracer](https://github.com/LuciferForge/ai-decision-tracer)** — structured decision audit logging. Captures what/when/why for every agent action without the crypto overhead. Zero dependencies, works as a decorator or context manager. Handles the "what happened" layer.

- **[KYA](https://github.com/LuciferForge/KYA)** — Ed25519 agent identity cards (same crypto stack you're using for AAR signatures). Handles the "who did it" layer with portable, verifiable credentials.

The layering would be: KYA provides identity (who) -> ai-decision-tracer captures the decision context (what/why) -> AAR provides the cryptographic receipt chain (provable handoffs between agents).

Each layer is independently useful but the combination gives you full audit coverage. Interested to see where the Python SDK lands — interop at the signing layer would be straightforward since we're both on Ed25519.

**manja316:**
@Cyberweasel777 SCC is a clever complement to AAR — session continuity is a real gap in multi-agent systems.

On our side, [ai-decision-tracer](https://pypi.org/project/ai-decision-tracer/) v0.2.0 now has Ed25519 signed receipts with hash-chain verification:

```python
from ai_trace import Tracer
from ai_trace.receipts import generate_keypair

private_key, public_key = generate_keypair()
tracer = Tracer("crew_run", signing_key=private_key)

tracer.start_step("research")
tracer.end_step(output={"findings": data})
# Receipt auto-generated: SHA-256 content hash + Ed25519 signature + chain link

tracer.verify_receipts()  # Validates full chain integrity
tracer.save_receipts("audit_trail.json")  # Third-party verifiable
```

Each receipt links to the previous via `previous_hash`, so tampering with any step breaks the chain. Zero dependencies in core — `cryptography` is an optional extra (`pip install ai-decision-tracer[signed]`).

The interop angle is interesting: AAR for action-level receipts, SCC for session continuity, KYA for agent identity. Three orthogonal concerns that compose well. If there's interest in defining a shared receipt envelope format, that could make all three interoperable.

**saschabuehrle:**
Interesting direction. If this moves forward, it might help to define a minimal receipt schema first: actor, action, input hash, output hash, tool identity, timestamp, policy context, and signature chain.

Two design suggestions:
1) Make verification offline-friendly (deterministic canonical format)
2) Keep PII out of receipts by default (hash pointers instead of raw payloads)

That keeps auditability strong without turning receipts into another data-governance burden.

**Cyberweasel777:**
@saschabuehrle — both of these are already in the spec and SDK:

**1. Offline-friendly verification** — receipts use a deterministic canonical JSON format (sorted keys, no whitespace ambiguity). Verification is a single `nacl.sign.detached.verify()` call with zero network dependencies. The npm SDK (`botindex-aar`) does this in ~2 lines:

```typescript
import { verifyReceipt } from "botindex-aar";
const valid = verifyReceipt(receipt, publicKey);
```

**2. PII-free by default** — inputs and outputs are SHA-256 hashed before inclusion in the receipt. The receipt carries `inputHash` and `outputHash`, never raw payloads. The verifier can independently hash their copy of the data and compare, without the receipt itself becoming a data-governance liability.

The minimal schema you described maps 1:1 to what we shipped:

| Your suggestion | AAR field |
|----------------|-----------|
| actor | `agent` |
| action | `action` |
| input hash | `inputHash` (SHA-256) |
| output hash | `outputHash` (SHA-256) |
| tool identity | `scope` |
| timestamp | `timestamp` (ISO 8601) |
| policy context | `principal` |
| signature chain | Ed25519 detached signature + SCC chain anchoring |

We also just shipped hosted signing ($0.001/receipt) and SCC anchoring ($0.01/anchor) for teams that don't want to manage their own key infrastructure.

Spec: https://github.com/Cyberweasel777/agent-action-receipt-spec
SDK: https://www.npmjs.com/package/botindex-aar
Landing: https://aar.botindex.dev

Would be curious how this maps to what you're building at Lemony/cascadeflow — the workflow orchestration angle is exactly where provenance matters most.

**aelitium-dev:**
This maps closely to something we've been building.

AELITIUM implements cryptographic binding at the individual LLM call layer:

request_hash  — SHA-256 of the canonicalized request
response_hash — SHA-256 of the response
binding_hash  — sha256(canonical_json({request_hash,response_hash}))
Ed25519 signature over the binding_hash

Where AAR focuses on agent actions, AELITIUM focuses on proving what the model actually returned for a given input — and detecting when that changes across runs.

Two primitives that complement what you're describing:

aelitium verify-bundle ./evidence
→ STATUS=VALID / INVALID (fully offline, no server)

aelitium compare ./runA ./runB
→ REQUEST_HASH=SAME / RESPONSE_HASH=DIFFERENT

Conceptually this could sit beneath an AAR receipt chain — each agent action receipt referencing the AELITIUM bundle hash of the LLM calls it made, giving end-to-end cryptographic coverage.

Curious whether the AAR spec is planning an external evidence reference field, or if the intent is to keep receipts fully self-contained.

**Jovancoding:**
Great thread. The receipt chaining approach makes sense for proving what happened, but there's an upstream problem worth considering: **how do you ensure the state transitions between agents are valid before you sign them?**

If Agent A hands off corrupted or conflicting state to Agent B, you get a perfectly signed receipt chain of garbage. The cryptographic proof is intact but the data it certifies is wrong.

This is the gap we've been working on with [Network-AI](https://github.com/Jovancoding/Network-AI) — a coordination layer that enforces atomic state transitions between agents using a propose→validate→commit pattern. Each agent proposes a state change, it gets validated against the current state and other pending changes, and only then commits.

The interesting integration point: if you combine AAR receipts (@Cyberweasel777) with a coordination layer that guarantees valid state transitions, you get both **correctness** (the state is conflict-free) and **provability** (the receipt proves it). Right now those are treated as separate problems but they compose well.

For CrewAI specifically, this would mean the receipt chain not only proves which agent did what, but also that each handoff was validated — no state corruption between steps. Supports 14 frameworks including CrewAI.

**aelitium-dev:**
Good distinction — correctness and provability are different problems.

AELITIUM sits one layer below the coordination question: it proves what the model actually returned for each call. So if a handoff is later disputed, you can still verify the exact LLM output at that step.

The stack composes quite naturally:

LLM call → AELITIUM evidence bundle (what the model said)
state transition → coordination layer (was it valid?)
agent action → receipt chain (did it happen?)

Each layer proves a different part of the system.

**Cyberweasel777:**
@aelitium-dev — the LLM call binding layer is the right primitive to sit beneath action receipts. The stack you described (AELITIUM → coordination → AAR) is exactly how this should compose.

On your question: yes, we're adding an optional `evidenceRef` field to the AAR spec. The intent is a hash pointer to external evidence bundles — your AELITIUM bundle hash, an ai-decision-tracer audit trail, or any other structured proof artifact. The receipt stays self-contained for verification, but can reference deeper evidence for dispute resolution:

```json
{
  "agent": "research-crew/analyst",
  "action": "market_scan",
  "inputHash": "sha256:abc...",
  "outputHash": "sha256:def...",
  "evidenceRef": {
    "type": "aelitium/binding-bundle",
    "hash": "sha256:789...",
    "uri": "ipfs://Qm... | https://..."
  },
  "signature": "ed25519:..."
}
```

Verification stays offline and zero-dependency. The `evidenceRef` is optional metadata — if you have access to the bundle, you can verify deeper. If not, the receipt alone still proves the action happened.

@Jovancoding — the correctness vs provability distinction is important and you're right they compose. One additional layer worth considering: **regulatory validity**. We just shipped a [compliance signal desk](https://king-backend.fly.dev/api/botindex/compliance/overview) and [exposure scanner](https://king-backend.fly.dev/api/botindex/compliance/exposure?project=uniswap) that agents can query before executing. The full stack becomes:

1. **Discovery** — find the service (Agorion registry)
2. **Compliance check** — is this interaction regulatory-safe? (BotIndex compliance)
3. **State validation** — is the transition valid? (Network-AI coordination)
4. **Execution** — do the thing
5. **LLM evidence** — prove what the model returned (AELITIUM)
6. **Action receipt** — prove the agent did it (AAR)
7. **Identity continuity** — prove it's the same agent across sessions (SCC)

That's full-stack agent trust. Each layer is independently useful, all compose cleanly, and none require the others to function.

Will push the `evidenceRef` field to the spec this week.

**aelitium-dev:**
This is exactly the right interface.

AELITIUM bundles already expose the fields you'd need for deeper verification:

- request_hash — canonical hash of model + messages
- response_hash — hash of what the model returned
- binding_hash — sha256(canonical({request_hash, response_hash}))

So the `evidenceRef` you're describing resolves cleanly:

{
  "evidenceRef": {
    "type": "aelitium/binding-bundle",
    "hash": "sha256:...",
    "uri": "..."
  }
}

The receipt stays self-contained. Anyone with access to the bundle can run:

  aelitium verify-bundle ./bundle   → STATUS=VALID  
  aelitium compare bundleA bundleB  → REQUEST_HASH=SAME / RESPONSE_HASH=DIFFERENT

No network required, no service dependency.

Happy to align the bundle schema if useful for the AAR spec, or draft a minimal
`aelitium/binding-bundle` reference type that fits the `evidenceRef` field.
