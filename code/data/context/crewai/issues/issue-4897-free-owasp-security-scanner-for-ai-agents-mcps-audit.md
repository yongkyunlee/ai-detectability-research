# Free OWASP security scanner for AI agents: mcps-audit

**Issue #4897** | State: open | Created: 2026-03-15 | Updated: 2026-03-18
**Author:** razashariff

## Summary

Sharing a free tool we built: **mcps-audit** scans AI agent code against the OWASP Agentic AI Top 10 + OWASP MCP Top 10.

```bash
npx mcps-audit ./my-agent
```

We ran it against CrewAI's codebase (public repo, static analysis):

- **500 files** scanned, 113,094 lines
- **834 findings**: 25 CRITICAL, 81 HIGH, 710 MEDIUM, 18 LOW
- Key findings: code execution patterns in tracking scripts, data exfiltration patterns in HTTP calls, missing logging in many modules

All findings are pattern-based static analysis — the tool does not execute code or send data anywhere.

## What It Checks

12 rules mapped to OWASP Agentic AI Top 10 (exec/eval, hardcoded secrets, excessive permissions, prompt injection, SQL/XSS, missing sandboxing, supply chain, excessive agency, unsafe output, no logging, data exfiltration, no auth) plus 10 OWASP MCP Top 10 protocol risks.

Generates a professional PDF report with file/line/snippet and remediation for each finding.

## Links

- **npm**: https://www.npmjs.com/package/mcps-audit
- **GitHub**: https://github.com/razashariff/mcps-audit
- **Sample PDF**: https://agentsign.dev/sample-report.pdf

MIT licensed. Node.js 18+, one dependency (pdfkit).

## Comments

**Jairooh:**
Scanning before deployment is valuable. Monitoring after deployment is essential. Agents in production face data and conditions that no scanner can predict. AgentShield (useagentshield.com) provides runtime risk scoring on every CrewAI agent action — catches behavioral drift and anomalies as they happen.
