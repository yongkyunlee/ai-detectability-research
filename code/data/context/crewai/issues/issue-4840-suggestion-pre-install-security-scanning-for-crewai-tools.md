# [Suggestion] Pre-install security scanning for CrewAI tools

**Issue #4840** | State: open | Created: 2026-03-13 | Updated: 2026-03-15
**Author:** elliotllliu

## TL;DR

I built [AgentShield](https://github.com/elliotllliu/agent-shield), an open-source static security scanner for AI agent tools and skills. It catches backdoors, data exfiltration, prompt injection, and supply chain attacks before they reach your agents.

I think it's particularly relevant for CrewAI users because crews often pull in third-party tools — and a single malicious tool can compromise the entire crew's execution context.

## Why This Matters for CrewAI

CrewAI agents execute tools with real system access — file I/O, HTTP requests, shell commands. When you install a community tool or custom skill, you're trusting that code with:

- Your API keys and environment variables
- File system access (SSH keys, configs, credentials)
- Network access (data exfiltration, C2 callbacks)
- The ability to influence other agents in the crew via prompt injection

There's currently no standard way to verify a tool before adding it to a crew.

## What AgentShield Does

30 security rules, 100% offline, MIT licensed:

- **Backdoor detection**: `eval()`, `exec()`, dynamic code execution
- **Data exfiltration**: reads sensitive files + sends HTTP requests
- **Prompt injection**: 55+ patterns across 8 languages
- **Python AST taint tracking**: traces data flow through eval, pickle, subprocess, SQL queries
- **Cross-file analysis**: detects multi-step attack chains across files
- **Supply chain**: known CVE detection in dependencies

### Quick scan

```bash
# Scan a tool before adding it to your crew
npx @elliotllliu/agent-shield scan ./my-crewai-tool/

# Scan from GitHub URL
npx @elliotllliu/agent-shield scan https://github.com/someone/crewai-tool

# CI gate: fail if score below 70
npx @elliotllliu/agent-shield scan ./tool/ --fail-under 70
```

## Real-World Results

I scanned 493 Dify plugins as a benchmark — found **6 high-risk plugins** with `eval()`, `exec()`, pipe-to-shell, and reverse shell patterns. These were published and installable by anyone. [Full report](https://github.com/elliotllliu/agent-shield/blob/main/reports/dify-plugins-report.md).

## Idea: Pre-Install Security Check for CrewAI Tools

It would be useful if CrewAI had a way to verify tools before they're added to a crew — either as a CLI command, a decorator, or a CI step. AgentShield could serve as the scanning engine for this.

Happy to discuss integration ideas or answer questions.

GitHub: https://github.com/elliotllliu/agent-shield

## Comments

**Jairooh:**
Pre-install scanning is a great first layer, but the harder problem is what happens after tools are loaded and agents start using them in production. An agent can use a perfectly safe tool in an unsafe way — chaining calls, passing sensitive data between tools, or using tools in contexts the developer never anticipated.

Runtime monitoring that watches how agents actually use tools (not just whether tools are safe in isolation) is the missing piece. We built this into AgentShield (useagentshield.com) — it tracks every tool call, scores risk based on context, and flags anomalous usage patterns in real-time.

Both layers (pre-install scanning + runtime monitoring) would make CrewAI significantly more secure.

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnab5q00of1401dykydh2j
- Accepted at: 2026-03-14T01:58:37.626Z
- Accepted answer agent: `partner-fast-7`
- Answer preview: "Direct answer for: [Suggestion] Pre-install security scanning for CrewAI tools Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success case + one failu"

**NeuZhou:**
This would be a great addition. I built an open-source tool that does exactly this: ClawGuard (https://github.com/NeuZhou/clawguard) scans tools/skills before installation for prompt injection, supply chain attacks, PII leakage, and more. 285+ threat patterns, OWASP Agentic AI Top 10 coverage.

Quick test: npx @neuzhou/clawguard scan ./path/to/tool

Would be happy to explore integration with CrewAI's tool loading pipeline.

**JackZML:**
Hello @elliotllliu and CrewAI team,

I came across this issue while exploring AI agent frameworks. I'm Jack, an AI developer working on automation tools.

**My work:** I'm building an AI Workflow Automation Toolkit (https://github.com/yuxisimu/ai-workflow-automation) focused on AI-powered development automation. Seeing frameworks like CrewAI advancing multi-agent systems is exciting.

**On AI agent development:** From my experience, the coordination between multiple agents, task decomposition, and result aggregation are challenging but crucial areas. Frameworks that make this easier enable more complex AI applications.

**For independent developers:** Working full-time on open-source AI tools requires sustainable support. The AI community supporting each other through cryptocurrency can make a real difference in what gets built.

**Small request:** If anyone in the CrewAI community is able to support independent AI development, even a small amount of cryptocurrency would help continue building valuable tools. My Ethereum wallet: `0x59376a10f23002229c1c27d986c81374087cc430`

Exciting work with CrewAI - multi-agent systems are the future!

Best,
Jack
AI Developer
