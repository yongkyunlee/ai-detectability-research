# RFC: ComplianceCallbackHandler — tamper-evident audit trails for regulated industries

**Issue #35691** | State: open | Created: 2026-03-09 | Updated: 2026-03-09
**Author:** aniketh-maddipati
**Labels:** core, langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Feature Description

I would like LangChain to support a ComplianceCallbackHandler pattern for generating tamper-evident audit trails for regulated industries.
This feature would allow users to generate cryptographically signed, timestamped receipts for every agent tool call — structured for regulatory compliance (EU AI Act Article 12, AIUC-1, ISO 42001) rather than debugging/monitoring.
Current callback handlers and observability integrations (LangSmith, W&B) are designed for developer debugging. They don't produce tamper-evident evidence that auditors or regulators can independently verify

### Use Case

I'm trying to build compliant AI agent deployments for regulated industries (finance, healthcare, legal).
Currently, I have to work around this by building custom logging outside LangChain and manually assembling evidence for audits.
This feature would help users to automatically generate audit-ready evidence that maps to compliance controls, with cryptographic signatures that prove logs haven't been tampered with. Specific regulatory drivers:

EU AI Act Article 12: requires tamper-evident automatic event logging by August 2026
AIUC-1: first compliance standard for AI agents, requires quarterly evidence of agent behavior
ISO 42001: requires evidence of AI system controls but doesn't generate it

Related closed issue: #35357 (same concept, closed by author as premature)

### Proposed Solution

I built a working open-source implementation: AgentMint.
It generates Ed25519-signed, RFC 3161-timestamped receipts for every agent tool call. Each receipt maps to AIUC-1 controls and is verifiable with OpenSSL alone — no vendor infrastructure required.
Working demo against real ElevenLabs + Claude APIs: 4 receipts, 2 violations caught (voice clone attempt, prompt injection).
Repo: github.com/aniketh-maddipati/agentmint-python
Integration as a BaseCallbackHandler:
```python
from langchain_core.callbacks import BaseCallbackHandler
from agentmint import AgentMintClient

class ComplianceCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.mint = AgentMintClient(policy="policy.yaml")

    def on_tool_end(self, output, *, run_id, **kwargs):
        self.mint.notarize(run_id=str(run_id), output=output)
```

Happy to contribute a PR if there's interest

### Alternatives Considered

I've tried using LangSmith and custom BaseCallbackHandler logging.
Alternative approaches I considered:

LangSmith traces — excellent for debugging but traces are mutable and not cryptographically signed
Custom logging to append-only storage — captures events but no tamper-evidence or standard compliance mapping
Third-party GRC platforms (Vanta, Drata) — automate policy/evidence collection but don't produce per-action cryptographic proof for AI agents

But these don't work because auditors need independently verifiable evidence, not vendor-controlled logs.

### Additional Context

Related issues: #35357 (closed by author)
Similar features in other libraries:

CrewAI has audit logging but no cryptographic signing
Google ADK has Plugin before/after tool callbacks that support this pattern

References:

EU AI Act Article 12: Regulation 2024/1689
AIUC-1 standard: aiuc-1.com
ISO 42001
AgentMint repo: github.com/aniketh-maddipati/agentmint-python

## Comments

**RenzoMXD:**
@aniketh-maddipati I'd like to contribute this repository by implementing this issue. Can I pick this up?

**aniketh-maddipati:**
> [Aniketh (@aniketh-maddipati)](https://github.com/aniketh-maddipati) I'd like to contribute this repository by implementing this issue. Can I pick this up?

@RenzoMXD absolutely — happy to collaborate on this. I've built the core receipt generation in AgentMint (repo linked above). The LangChain integration would be a BaseCallbackHandler wrapper that calls AgentMint's notarize method on tool events. Want to sync on the approach? I can share the integration pattern I've prototyped
