# Add Kevros Governance tools — action verification + hash-chained audit trails

**Issue #35338** | State: open | Created: 2026-02-19 | Updated: 2026-03-09
**Author:** knuckles-stack
**Labels:** external

## Feature Request: Kevros Governance Tool Integration

### Description

Governance-as-a-service tools for LangChain agents. Verify actions before executing, create tamper-evident audit trails, and generate compliance evidence bundles.

### Tools

- **GovernanceVerifyTool** — Verify action against policy bounds (ALLOW/CLAMP/DENY)
- **GovernanceAttestTool** — Create hash-chained provenance record
- **GovernanceBindTool** — Bind intent to command cryptographically
- **GovernanceVerifyOutcomeTool** — Verify action achieved its intent
- **GovernanceBundleTool** — Generate compliance evidence package

### Integration Code

Already built and tested: https://github.com/ndl-systems/kevros-governance-sdk/blob/main/kevros_tools.py

\`\`\`python
from kevros_tools import get_governance_tools

tools = get_governance_tools(api_key="kvrs_...")
agent = initialize_agent(llm, tools + your_other_tools, ...)
\`\`\`

### Use Case

Any agent taking high-stakes actions (trades, deployments, data mutations) where you need to prove what the AI decided and why. EU AI Act, NYC Law 144, SEC/FINRA audit compliance.

### Links

- Gateway: https://governance.taskhawktech.com
- SDK: `pip install git+https://github.com/ndl-systems/kevros-governance-sdk.git`
- OpenAI function definitions also included: https://github.com/ndl-systems/kevros-governance-sdk/blob/main/openai_tools.json

## Comments

**desiorac:**
Great initiative on governance tools! With the EU AI Act coming into full enforcement in 2026, frameworks like LangChain will need built-in compliance verification and audit trails for AI systems.

Key compliance requirements that governance tools should address:
- Transparency: Who called what, when, and with what inputs
- Audit trails: Hash-chained event logs for non-repudiation
- Documentation: Model cards, risk assessments, consent logs
- Risk classification: Detecting high-risk AI practices (automated decision-making on protected attributes, etc.)

We built an open-source EU AI Act compliance scanner (free, no signup) that detects regulatory violations across frameworks. If helpful for this initiative: https://arkforge.fr/mcp

This could help test governance workflows against real compliance requirements!

**desiorac:**
Perfect timing — this aligns with compliance needs. Have you looked at EU AI Act requirements for AI governance? We're working on a scanner that flags governance gaps. Very relevant here.

**desiorac:**
Governance and audit trails are essential for AI compliance. EU AI Act requirements emphasize action verification and model accountability—this feature helps organizations meet those standards.

**desiorac:**
Governance tools with audit trails are foundational for AI systems operating under regulatory oversight. Having hash-chained verification enhances transparency and compliance posture. This aligns well with emerging EU AI Act requirements — solid initiative.

**mikeargento:**
The use case is real and the tooling looks well-structured for the LangChain ecosystem. One architectural question worth clarifying: the hash-chained audit trail and attestation records appear to be created alongside or after the action, meaning an agent (or compromised pipeline) that bypasses the governance tools entirely can still execute the underlying action and produce durable state without any provenance record. Does Kevros enforce that the governed action is unreachable except through the governance verification path, or is the enforcement advisory, relying on the agent framework to always route through the tools? This distinction matters for the compliance claims, since regulators will likely ask whether the audit trail's existence proves policy was enforced, or merely that a logging call was made. If unauthenticated side paths to the same actions remain open, the hash chain documents what was logged but does not constrain what could have happened.

**knuckles-stack:**
@mikeargento You're right to distinguish between logging and enforcement. Kevros issues a cryptographic release token on ALLOW decisions. Downstream services require that token as a prerequisite for execution - the governed path is the only path to authenticated action. An agent or pipeline that bypasses the governance tools doesn't get a token, and the action is rejected at the service layer.

To your auditor question directly: the provenance record's existence proves policy was enforced, not merely that a logging call was made. The LangChain tools are the developer integration surface; enforcement operates below the agent framework.

-JM
