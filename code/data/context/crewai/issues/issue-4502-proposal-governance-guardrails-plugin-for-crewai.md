# Proposal: Governance Guardrails Plugin for CrewAI

**Issue #4502** | State: closed | Created: 2026-02-17 | Updated: 2026-03-08
**Author:** imran-siddique

## Proposal: Governance Guardrails Plugin for CrewAI

### Problem

CrewAI excels at multi-agent orchestration with roles and tasks, but currently lacks a built-in governance/guardrails layer for enforcing safety policies on agent actions. As agent autonomy grows, organizations need:

- **Policy enforcement** — Cap token usage, limit tool calls, block dangerous patterns (regex/glob-aware)
- **Event hooks** — `on(POLICY_VIOLATION, callback)` for logging, alerting, circuit-breaking
- **Trust-gated delegation** — Verify agent trust scores before allowing inter-agent handoffs
- **Audit trails** — Tamper-evident logging with Merkle chain hashing

### What we've built (Apache-2.0)

We've been developing [AgentMesh](https://github.com/imran-siddique/agent-mesh) and [Agent-OS](https://github.com/imran-siddique/agent-os) with production-grade governance features:

1. **`GovernancePolicy`** — Declarative policy with YAML import/export, validation, diff/comparison
2. **`PatternType` enum** — Blocked patterns with substring, regex, and glob matching (pre-compiled)
3. **`GovernanceEventType` hooks** — `POLICY_CHECK`, `POLICY_VIOLATION`, `TOOL_CALL_BLOCKED`, `CHECKPOINT_CREATED`
4. **Semantic intent classifier** — Classifies actions into 9 threat categories (destructive, exfiltration, privilege escalation, etc.)
5. **Trust scoring engine** — 5-dimension trust scores with decay modeling
6. **Merkle audit chains** — Tamper-evident, offline-verifiable execution logs

### Proposed integration

We'd contribute a `crewai-guardrails` plugin (or PR to core) that wraps CrewAI's task execution with governance hooks:

`python
from crewai import Crew, Agent, Task
from crewai_guardrails import GovernancePolicy, GuardedCrew

policy = GovernancePolicy.load("policy.yaml")
crew = GuardedCrew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    policy=policy,  # Enforced on every agent action
)
crew.on("policy_violation", lambda e: alert(e))
result = crew.kickoff()
`

### Why this matters for CrewAI

- Enterprises adopting CrewAI need governance before production deployment
- No existing CrewAI extension provides this
- Our code is Apache-2.0, battle-tested (700+ tests), and framework-agnostic
- Aligns with CSA's [Agentic Trust Framework](https://cloudsecurityalliance.org/blog/2026/02/02/the-agentic-trust-framework-zero-trust-governance-for-ai-agents) direction

### Ask

Is there interest in this kind of contribution? Happy to:
1. Start with a minimal `before_task_execute` / `after_task_execute` hook PR
2. Or build a standalone `crewai-guardrails` package that integrates via CrewAI's existing callback system

Would love feedback from maintainers on the preferred approach.

## Comments

**ImL1s:**
Excellent proposal! This is exactly what the industry needs for safe AI agent deployment. 

**Relevance to OpenClaw ecosystem:**
- Aligns perfectly with our security focus (credential firewall, plugin validation)
- Complements OpenClaw's existing safety measures
- Critical for enterprise adoption of multi-agent systems

**Key strengths I noticed:**
1. **Merkle audit chains** - Essential for compliance and forensics
2. **Semantic intent classifier** - Proactive threat detection vs reactive
3. **Trust scoring engine** - Great foundation for agent reputation systems
4. **Event hooks** - Enables integration with existing monitoring tools

**Suggestion for OpenClaw integration:**
- Consider adopting similar governance patterns for the OpenClaw skill ecosystem
- The policy enforcement could prevent malicious skill execution
- Trust scoring could help users evaluate skill safety before installation

This would be a game-changer for CrewAI's production readiness. Apache-2.0 licensing is perfect for community adoption. Highly recommend pursuing this!

**imran-siddique:**
Thanks @ImL1s! Really appreciate the detailed feedback.

You're spot on about the Merkle audit chains — they're one of the most requested features from enterprise teams evaluating multi-agent deployments. Being able to prove *exactly* what happened during an agent execution, tamper-evident and offline-verifiable, is table stakes for regulated industries.

Great call on the OpenClaw integration angle too. The policy enforcement layer could absolutely prevent malicious skill execution, and trust scores would give users a quantitative signal before installing skills from unknown authors. Happy to explore that if there's interest from the OpenClaw side.

For context, we've recently shipped similar integrations that have been merged upstream:
- **[Dify](https://github.com/langgenius/dify-plugins/pull/2060)** (65K ⭐) — Trust verification plugin with dynamic trust scoring
- **[LlamaIndex](https://github.com/run-llama/llama_index/pull/20644)** (47K ⭐) — Trust-verified agent workers
- **[Microsoft Agent-Lightning](https://github.com/microsoft/agent-lightning/pull/478)** (15K ⭐) — Governed RL training
- **[LangGraph](https://pypi.org/project/langgraph-trust/)** — Just published `langgraph-trust` on PyPI

Would love to see this land in CrewAI as well. Waiting on maintainer feedback on whether they'd prefer a core PR or standalone package approach.

**imran-siddique:**
Sharing some working code to make this concrete. We have two packages ready:

**1. [crewai-agentmesh](https://github.com/imran-siddique/agentmesh-integrations/tree/master/crewai-agentmesh)** — Trust layer for CrewAI with:
- **`TrustedCrew`** — Trust-verified crew member selection based on agent capabilities and trust scores
- **`CapabilityGate`** — Ensures agents only get tasks matching their verified capabilities (all/any mode)
- **`TrustTracker`** — Tracks trust scores across crew runs with configurable reward/penalty and decay

```python
from crewai_agentmesh import TrustedCrew, AgentProfile

agents = [
    AgentProfile(did="did:mesh:researcher", name="Researcher",
                 capabilities=["research", "analysis"], trust_score=800),
    AgentProfile(did="did:mesh:writer", name="Writer",
                 capabilities=["writing"], trust_score=700),
]
crew = TrustedCrew(agents=agents, min_trust_score=500)
selected = crew.select_for_task(required_capabilities=["research"])
```

**2. [pydantic-ai-governance](https://github.com/imran-siddique/agentmesh-integrations/tree/master/pydantic-ai-governance)** — Shows the governance pattern with semantic intent classification, policy enforcement, and audit trails (57 tests). Similar approach could be adapted for CrewAI's guardrails/before_kickoff hooks.

Both are Apache-2.0. Would love maintainer feedback on the preferred integration approach for CrewAI — standalone package, core PR, or OpenClaw skill.

**imran-siddique:**
Update: Our agent governance patterns just got **merged into github/awesome-copilot** (21.6K stars) — all 3 PRs accepted by GitHub staff:

- [PR #755](https://github.com/github/awesome-copilot/pull/755) — Governance skill with CrewAI integration examples
- [PR #756](https://github.com/github/awesome-copilot/pull/756) — Threat detection hook (data exfiltration, privilege escalation, prompt injection, system destruction, credential exposure)
- [PR #757](https://github.com/github/awesome-copilot/pull/757) — Safety instructions + governance reviewer agent

The governance patterns in these PRs include CrewAI-specific code examples. Combined with our [crewai-agentmesh](https://github.com/imran-siddique/agentmesh-integrations/tree/master/crewai-agentmesh) trust layer, this gives the CrewAI ecosystem a complete governance story.

Would love to see native governance support in CrewAI core — happy to contribute a PR whenever the team decides on the preferred approach (core integration, OpenClaw skill, or standalone package).

**darfaz:**
Great proposal! The governance layer for agent orchestration is critical, and the pattern-based policy enforcement approach here is solid.

One angle worth considering alongside the prompt/orchestration-level guardrails: **host-level security**. Even with perfect governance policies, agents still have direct access to the host machine's filesystem and credentials.

For example, a compromised tool call could exfiltrate `~/.ssh/id_rsa` or `~/.aws/credentials` before any orchestration-level policy catches it. The governance layer sees "tool_call: read_file" — but doesn't know the file is a forbidden zone.

We've been working on this at [ClawMoat](https://github.com/darfaz/clawmoat) (MIT licensed) — it enforces permission tiers and forbidden zones at the OS level, complementing the orchestration-level governance described here. Could potentially integrate as an additional policy layer:

```
agent_guardrails:
  orchestration: crewai-governance  # policy, trust scores, audit
  host_security: clawmoat           # forbidden zones, credential monitoring
```

The Merkle audit chain idea is particularly interesting — would love to see it extended to include host-level events (credential access attempts, network egress) alongside the agent-level events.

Happy to collaborate on making these layers work together!

**imran-siddique:**
Great thinking @darfaz — host-level security is the layer we don't cover, and you're right that it's a critical gap. An agent can have perfect orchestration-level governance but still exfiltrate `~/.ssh/id_rsa` through a file-read tool that passes policy checks.

The layered model makes a lot of sense:

```
Orchestration layer: crewai-governance (policy, trust, audit)
     ↕
Host layer: ClawMoat (forbidden zones, credential monitoring)
     ↕
Kernel layer: agent-os (sandbox, execution rings, import hooks)
```

Two integration points I see:

1. **ClawMoat as a policy signal** — When a host-level forbidden zone violation is detected, it should emit an event that our governance layer can consume. This way the Merkle audit chain captures both orchestration AND host events in a single timeline. Something like:

```python
clawmoat.on("forbidden_zone_access", lambda e: governance.record_violation(
    agent_id=e.agent_id,
    violation_type="host_security",
    details={"path": e.path, "action": e.action}
))
```

2. **Policy-driven zone configuration** — The governance policy YAML could declare forbidden zones that ClawMoat enforces:

```yaml
host_security:
  forbidden_zones:
    - "~/.ssh/**"
    - "~/.aws/**"
    - "/etc/shadow"
  credential_monitoring: true
```

Would be great to prototype this integration. Happy to open an issue on ClawMoat to discuss the event API surface, or we can sketch it here. What format works best for you?

**imran-siddique:**
Circling back with concrete progress — we shipped two new modules this week that align well with @darfaz's layered security model:

**1. MCP Security Scanner** (just merged)
Addresses tool poisoning at the orchestration layer before tools reach agents:
- Scans MCP tool descriptions for hidden instructions, injection patterns
- Fingerprints tools with SHA-256 hashes for rug pull detection
- Cross-server impersonation detection (typosquatting, duplicate tool names)

**2. LlamaFirewall Integration Adapter**
Chains Meta's LlamaFirewall with our detector for defense-in-depth:
- 4 modes: CHAIN_BOTH, VOTE_MAJORITY, single-scanner
- Lazy imports — works with or without LlamaFirewall installed

These + ClawMoat's host-level forbidden zones would create a genuine 4-layer defense:
1. **Prompt layer** — PromptInjectionDetector + LlamaFirewall PromptGuard 2
2. **Tool layer** — MCPSecurityScanner (poisoning, rug pulls)
3. **Orchestration layer** — GovernancePolicy (RBAC, approval gates)
4. **Host layer** — ClawMoat (filesystem, network, process isolation)

@darfaz — would you be open to defining a simple event API contract? Happy to open an issue on ClawMoat if that'd help.

**darfaz:**
@imran-siddique This is fantastic progress — the MCP Security Scanner fills a gap we've been eyeing too (we just shipped our own `McpFirewall` in v0.8.0 that handles the runtime enforcement side: read-only mode, field-level redaction, tool allowlisting).

The 4-layer model you mapped out is exactly right. Each layer catches what the others miss:
- Prompt layer stops injection before it reaches the agent
- Tool layer stops poisoned tools before they're invoked
- Orchestration layer enforces who can do what
- Host layer is the last line — if everything above fails, the agent still can't touch `~/.ssh` or exfiltrate credentials

**Re: event API contract — absolutely yes.** Here's what I'm thinking:

```js
// ClawMoat emits events that orchestration layers can subscribe to
clawmoat.on('file.blocked', { path, reason, severity })
clawmoat.on('network.blocked', { url, reason })
clawmoat.on('secret.detected', { type, redacted })
clawmoat.on('transaction.pending', { id, amount, requiresApproval })

// Orchestration layers can feed context down
clawmoat.setContext({ agentId, taskId, permissionTier })
```

Open the issue on our repo — happy to spec it out together. This could become the reference architecture for secure agent deployments.

One thought: if we're both pointing at this 4-layer model, it might be worth co-authoring a short RFC or blog post. "Defense-in-Depth for AI Agents" with concrete code from both projects would get attention.

**WulfAI:**
Interesting thread — the layered approach @darfaz describes (orchestration governance + host security) resonates with something we have been working through.

One pattern we have found useful in practice: **versioning governance policies alongside agent definitions in Git**, so policies are reviewable, diffable, and auditable the same way code is. Rather than a separate policy engine, the governance rules live as structured files (YAML/Markdown) in the same repo as the agent configs, and changes go through PRs with approval gates.

This gives you a few things runtime enforcement alone does not:
- **Audit trail for free** — Git history shows who changed what policy and when, without building a separate audit system
- **Policy-as-code review** — humans review policy changes before they take effect, same workflow as code review
- **Drift detection** — if runtime behavior diverges from declared policy, the diff is obvious

We have been modeling this as "repo-native governance" in [wlfghdr/agentic-enterprise](https://github.com/wlfghdr/agentic-enterprise) — the quality policies, agent boundaries, and approval workflows are all Git artifacts. It is not a replacement for runtime guardrails (you still need those), but it provides the governance layer _above_ runtime enforcement: the rules about what rules the runtime should enforce.

The MCP Security Scanner work is a good complement — that is exactly the runtime layer. The question is how the two layers talk to each other: does the repo-declared policy feed into the runtime scanner config, or are they independent?

**imran-siddique:**
Closing - project moved to [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit). Will re-submit fresh proposals from the Microsoft repo. Thank you!
