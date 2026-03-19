# Show HN: G0 – The control layer for AI agents (scan, test, monitor, comply)

**HN** | Points: 4 | Comments: 5 | Date: 2026-03-10
**Author:** debug-0101
**HN URL:** https://news.ycombinator.com/item?id=47327358
**Link:** https://github.com/guard0-ai/g0

AI agents are shipping fast (LangChain, CrewAI, MCP servers, OpenAI Agents SDK) but there's no unified way to secure and govern them. We built g0 to be
   that control layer.  What g0 does across the agent lifecycle:

  g0 scan - Static + behavioral analysis of agent code. 1,180 rules across 12 security domains, 10 frameworks (LangChain, CrewAI, MCP, OpenAI, Vercel AI,
   Bedrock, AutoGen, LangChain4j, Spring AI, Go AI), 5 languages. Detects toxic tool chains, taint flows, overprivileged descriptions, missing
  sandboxing. Integrated threat intelligence checks tool URLs and dependencies against 55+ IOCs and known CVEs.

  g0 test - Dynamic adversarial red teaming. Fires prompt injections, data exfiltration attempts, tool abuse sequences, jailbreaks, and goal hijacking
  payloads at your running agents. 3-level progressive judge (deterministic, heuristic, LLM). Works over HTTP and MCP.

  g0 endpoint - Discovers every AI tool on the machine (Claude Code, Cursor, Windsurf, Zed, 15+ tools), inventories MCP servers, and surfaces
  misconfigurations. Think nmap but for your AI developer surface.

  g0 daemon - Continuous runtime monitoring. Behavioral baselines with anomaly detection, cost circuit breaker, correlation engine linking events across
  sources into attack chains, and a kill switch for when things go sideways.

  g0 detect - MDM enrollment detection (Jamf, Intune, Mosyle, Kandji, etc.), running AI agent discovery, and host hardening audit in one view.

  First-class OpenClaw support. g0 is the only security tool that understands OpenClaw's architecture: gateway hardening (18 probes),
  SKILL.md&#x2F;SOUL.md&#x2F;MEMORY.md analysis, cognitive drift monitoring via SHA-256 baselines, deployment audits, config hardening, and ClawSec CVE feed
  integration. If you're running OpenClaw in production, g0 catches what generic scanners miss.

  Compliance built in, not bolted on. Every finding maps to 10 standards: OWASP Agentic Top 10, OWASP LLM Top 10, NIST AI RMF, ISO 42001, EU AI Act,
  MITRE ATLAS, and more. Generate evidence records, compliance reports, and enforce policies via .g0-policy.yaml with CI gate support.

  Outputs: Terminal, JSON, SARIF 2.1.0, HTML, CycloneDX AI-BOM, Markdown. Plugs into GitHub Actions, GitLab CI, or any pipeline.

  One command to start: npx @guard0&#x2F;g0 scan .

  GitHub: https:&#x2F;&#x2F;github.com&#x2F;guard0-ai&#x2F;g0

  We think the AI agent ecosystem needs the same security tooling maturity that web apps got with Burp Suite and Semgrep, but purpose-built for agents.
  Happy to answer questions about the architecture or threat model.

## Top Comments

**Mooshux:**
Monitoring and compliance at the agent level makes sense. The gap I keep hitting is that most agent security tooling focuses on what the agent does but not what credentials it holds while doing it. An agent that passes all behavioral checks but carries a 90-day full-access API key is still one compromised session away from a bad day.

**OpenClawguru:**
We use AI agents for ecommerce backoffice — inventory alerts, ad monitoring, support triage. Runs in Slack 24&#x2F;7: selzee.com&#x2F;openclaw?via=hn
