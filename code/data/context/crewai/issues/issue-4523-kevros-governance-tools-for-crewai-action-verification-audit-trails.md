# Kevros Governance tools for CrewAI — action verification + audit trails

**Issue #4523** | State: open | Created: 2026-02-19 | Updated: 2026-03-04
**Author:** knuckles-stack

## Kevros Governance Tools for CrewAI

Pre-built CrewAI tools for AI governance. Verify agent actions before execution, maintain independently verifiable evidence trails.

### Ready-to-use integration

https://github.com/ndl-systems/kevros-governance-sdk/blob/main/crewai_tools.py

```python
from crewai_tools import get_governance_tools

tools = get_governance_tools(api_key="kvrs_...")
agent = Agent(role="Trader", tools=tools, ...)
```

### Tools

- **Governance Verify** — Pre-execution action verification ($0.01/call)
- **Governance Attest** — Signed evidence records ($0.02/call)
- **Governance Bind Intent** — Intent-to-action binding ($0.02/call)

### Why

Any agent executing trades, deployments, data changes, or API calls benefits from verifiable evidence of what was authorized and when. Evidence is signed with post-quantum cryptography (ML-DSA-87 / FIPS 204) and independently verifiable.

- Gateway: https://governance.taskhawktech.com
- SDK: `pip install kevros`
- Docs: https://governance.taskhawktech.com/docs

## Comments

**mikeargento:**
The goal of giving CrewAI agents a structured governance layer with audit trails is practical and worth pursuing. One question on the architecture: the verify/attest/bind-intent tools appear to be invoked by the agent itself as CrewAI tools, which means a compromised or misaligned agent could simply skip calling them and still produce durable side effects (trades, API calls, deployments) through other available tools. Hash-chained attestation solves log mutability, but if the attested path is not the only path to action execution, an agent that bypasses governance tools produces unauthenticated actions that are structurally indistinguishable from a scenario where governance was never configured. Is there an enforcement layer that makes the governance call a prerequisite for the downstream action, rather than a voluntary step the agent elects to take?

**knuckles-stack:**
@mikeargento Good question. At the tool layer, any tool call is voluntary — that's inherent to the tool-use pattern across all frameworks.

Kevros addresses this at the infrastructure layer. Verified actions produce signed attestations that downstream services can validate as a prerequisite. An agent that skips governance produces no valid attestation, so the action is rejected — not just unrecorded.

The CrewAI tools are the developer-facing integration. Enforcement is infrastructure-level, not agent-level.

-JM
