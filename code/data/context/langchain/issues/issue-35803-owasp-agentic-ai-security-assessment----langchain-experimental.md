# OWASP Agentic AI Security Assessment -- LangChain Experimental

**Issue #35803** | State: open | Created: 2026-03-12 | Updated: 2026-03-16
**Author:** razashariff
**Labels:** external

### OWASP Agentic AI Top 10 -- Security Assessment

Hi team,

We conducted an OWASP Agentic AI Top 10 (2025) assessment of 27 popular AI agent frameworks as part of ongoing agentic security research. This assessment was performed via **static analysis of public source code only** -- no systems were accessed or tested remotely.

---

#### Assessment Results -- LangChain (Experimental)

| Check | OWASP ID | Severity | Detail |
|-------|----------|----------|--------|
| Unsafe Execution | AA-03 | CRITICAL | `exec()` and `eval()` in Python REPL tool |
| Injection Pattern | AA-02 | CRITICAL | LLM-generated code executed directly in host process |
| Excessive Permissions | AA-04 | MEDIUM | High-risk permissions: execute |
| Inadequate Sandboxing | AA-09 | HIGH | No process isolation for code execution |

**Risk Score: 73/100 (FAIL)**

---

#### Published CVEs Referenced

This is not a new disclosure. These are all previously published:

| CVE | Detail |
|-----|--------|
| CVE-2023-29374 | Code injection via LLM output |
| CVE-2023-36258 | Code injection in PALChain |
| CVE-2023-39631 | Arbitrary code execution |
| CVE-2023-44467 | Code injection via prompt |

---

#### Why This Matters

LangChain is one of the most widely used AI agent frameworks. While the dangerous patterns are primarily in `langchain-experimental`, the Python REPL tool and code execution utilities use `exec()` and `eval()` to run LLM-generated code directly in the host process. For users building production AI agents, these patterns represent a significant attack surface documented in 4 published CVEs.

We recognise that `langchain-experimental` carries an explicit warning about its nature. This assessment is intended to help users who may be deploying these components in production understand the associated risks mapped to the OWASP Agentic AI Top 10.

---

#### Agent Security Gates

As part of this research, we have built an open agent security assessment at **[agentsign.dev](https://agentsign.dev)** where developers and security teams can:

- **Scan any AI agent** against the OWASP Agentic AI Top 10 (free, no account required)
- **Get an identity and trust score** for agents before deploying to production
- **Gate agent execution** via API -- block agents that fail security checks

Out of 27 agents assessed, 17 passed and 10 failed. Full results available on the platform.

---

#### Context

We are not claiming to have discovered these vulnerabilities -- all CVEs referenced above were reported by their original researchers. This assessment maps existing known issues to the OWASP Agentic AI Top 10 framework.

Happy to discuss any of these findings.

**Raza Sharif**
Founder, CyberSecAI Ltd
[agentsign.dev](https://agentsign.dev)

## Comments

**Anakintano:**
Hi! Thanks for sharing this assessment.

From what I understand, the concern is mainly around the use of `exec()` / `eval()` in the Python REPL tool within the `langchain-experimental` module, where LLM-generated code may end up being executed directly in the host process. That could allow arbitrary code execution if the tool is used in an unsafe environment or with untrusted inputs.

Since this module is marked experimental, I assume the current behavior might be intentional for flexibility, but it does raise the OWASP concerns you highlighted (unsafe execution, sandboxing, permissions).

I'd be interested in helping explore possible mitigations or guardrails (for example safer execution wrappers, sandboxing options, or stronger warnings in documentation).

Before I dig deeper:
• Are there specific mitigation directions the maintainers would consider acceptable?
• Would a PR that adds optional sandboxing or safer execution modes be useful?
• Are there particular success criteria you’d want to see for a fix?

Happy to investigate further if this would be a helpful contribution.

**razashariff:**
Hi @Anakintano -- thanks for the thoughtful response and willingness to contribute.

You've summarised the core concern accurately. The primary risk surface is `exec()` / `eval()` in `langchain_experimental.utilities.python.PythonREPL` and related tools where LLM-generated code executes directly in the host process with full access to the Python runtime, filesystem, network, and any credentials in the environment.

### Mitigation Directions

From our assessment (mapped to OWASP Agentic AI Top 10), here are the concrete mitigation layers we'd consider meaningful:

**1. Process Isolation (AA-09 -- Inadequate Sandboxing)**
- Execute LLM-generated code in a subprocess with restricted permissions (`seccomp`, `AppArmor`, or at minimum `subprocess` with `preexec_fn` dropping capabilities)
- Alternatively, integrate with existing sandbox runtimes like [E2B](https://e2b.dev), [gVisor](https://gvisor.dev), or Docker-based isolation
- A `SandboxedPythonREPL` class that wraps execution in an isolated environment would be a strong addition

**2. Input Validation and AST Filtering (AA-03 -- Unsafe Code Execution)**
- Pre-parse generated code via Python's `ast` module before execution
- Block or flag dangerous patterns: `import os`, `import subprocess`, `open()` on sensitive paths, `__import__`, `eval()` within generated code, network calls
- This doesn't replace sandboxing but adds defence-in-depth

**3. Permission Scoping (AA-04 -- Excessive Permissions)**
- Introduce an explicit permission model: `PythonREPL(allow_imports=["pandas", "numpy"], deny_imports=["os", "subprocess", "shutil"])`
- Default-deny for dangerous modules, opt-in for safe ones
- This is the pattern used by several frameworks that passed our assessment (e.g., Google ADK's tool permission model)

**4. Timeout and Resource Limits**
- Enforce execution timeouts (prevent infinite loops from LLM-generated code)
- Memory limits via `resource.setrlimit()` on Unix systems
- These are basic but currently absent

**5. Documentation and Warnings (Quick Win)**
- Stronger warnings in the `PythonREPL` docstring and README specifically referencing the 4 published CVEs
- A "Security Considerations" section in the experimental module docs
- Clear guidance: "Do not use `PythonREPL` in production without sandboxing"

### Success Criteria

From an OWASP Agentic AI compliance perspective, a fix would move LangChain from FAIL to WARN or PASS if:

1. **Default-safe**: Out of the box, code execution is sandboxed or requires explicit opt-in to unsafe mode
2. **Defence-in-depth**: At least two mitigation layers (e.g., AST filtering + process isolation)
3. **Documented risk**: Users who bypass safeguards do so explicitly, not accidentally

### Our Registry

We track these assessments publicly at [registry.agentsign.dev](https://registry.agentsign.dev) -- LangChain's status would be updated if mitigations are merged. We also provide a free [GitHub Action](https://github.com/razashariff/agentsign-action) that scans agent code against these same OWASP rules on every PR, which could be useful for validating any changes.

### Suggested Approach

If you're looking to contribute, I'd suggest starting with **option 2 (AST filtering)** as it's the lowest-friction change that doesn't require external dependencies. A `SafePythonREPL` class that pre-validates code against a configurable blocklist before calling `exec()` would be a meaningful first step.

Happy to review or provide feedback on any PR. This is exactly the kind of community-driven security improvement the ecosystem needs.

**Raza Sharif**
Founder, CyberSecAI Ltd
[agentsign.dev](https://agentsign.dev) · [registry.agentsign.dev](https://registry.agentsign.dev)

**Anakintano:**
Can I please be assigned to this issue to me ? That should allow my 
PR to stay open and move into the review queue ?

**razashariff:**
We cannot assign issues (not maintainers), but we fully support your contribution. A LangChain maintainer would need to assign you.

If you are working on a PR, the mitigations we outlined above map directly to the OWASP Agentic AI controls. The highest-impact change would be a SandboxedPythonREPL wrapper in langchain-experimental -- even if opt-in initially, it gives users a secure path.

Happy to review your PR from a security perspective if that would help.

**Anakintano:**
Hi @langchain-ai/core-maintainers — I've implemented the AST Filtering mitigation (OWASP AA-03) discussed in this issue and submitted PR #35828. The PR was auto-closed because I'm not yet assigned to this issue.

Could a maintainer please assign me to this issue so the PR can be reopened? The implementation includes:
- `SafePythonREPL` class with AST-based pre-validation
- Configurable blocklists for dangerous imports and function calls
- `mode="block"` (default) and `mode="warn"` for defence-in-depth

Happy to make any changes based on your feedback. Thank you!

**razashariff:**
Great work @Anakintano! The AST-based pre-validation approach is exactly what this issue needed -- blocking dangerous imports and calls at the syntax level before execution is the right defence-in-depth layer.

The configurable blocklist + block/warn modes give teams flexibility to adopt incrementally without breaking existing workflows.

@langchain-ai/core-maintainers -- would be great to get Anakintano assigned so PR #35828 can be reopened. Happy to review the security aspects if useful.

**Anakintano:**
@RazaSharif – Thank you so much for the thoughtful feedback and validation. Your guidance on starting with AST filtering as the foundational layer was instrumental—it's gratifying to see that approach land well.  😀

**razashariff:**
Thanks Aditya -- your AST filtering work is solid and exactly the right foundation.

Wanted to share that the assessment work here led to building **MCPS (MCP Secure)** -- a cryptographic security layer for the Model Context Protocol. It adds agent passports, message signing, tool integrity verification, replay protection, and trust levels (L0-L4).

We've now scanned 39 agent frameworks against the OWASP Agentic AI Top 10:
- **13 FAIL** (AutoGPT, Open Interpreter, MetaGPT, Browser Use...)
- **17 WARN** (LangChain, CrewAI, AutoGen, n8n...)
- **9 PASS** (Anthropic SDK, Vercel AI SDK, LlamaIndex...)

Full scan results: https://mcp-secure.dev/#registry

The SDK is MIT licensed:
```
npm install mcp-secure
pip install mcp-secure
```

Your AST filtering addresses AA-03 at the code level. MCPS addresses it at the protocol level -- signed messages, verified identities, tamper-proof tool definitions. Together they'd cover most of the OWASP Agentic AI Top 10.

Spec: https://github.com/razashariff/mcps/blob/main/SPEC.md
Landing page: https://mcp-secure.dev

**Jairooh:**
Great initiative bringing OWASP standards to the agentic AI space. The challenge with agent security is that static analysis and pre-deployment testing only catch what you can predict. In production, agents chain tool calls, escalate permissions, and make decisions in ways no test suite anticipated.

We've been working on this problem at AgentShield (useagentshield.com) — runtime risk scoring on every agent action as it happens. It integrates via LangChain callbacks so you get real-time visibility into what agents actually do in production, not just what they should do.

The OWASP framework + runtime monitoring would be a strong combination for production agent security.

**razashariff:**
Thanks @Jairooh — agreed, static analysis and pre-deployment verification only cover one side of the problem. Runtime visibility into what agents actually do in production is the missing piece.

MCPS is focused on the transport/identity layer — cryptographic proof of *who* is calling, message integrity, and tool authenticity. Runtime risk scoring on *what* agents do once authenticated is a complementary layer that closes the loop.

The combination makes sense: MCPS ensures the agent is who it claims to be and the tool definitions haven't been tampered with, then runtime monitoring catches unexpected behaviour patterns during execution. Different layers, both necessary.

Will take a look at AgentShield — the LangChain callback integration is a smart approach for adoption.
