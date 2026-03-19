# I went through every AI agent security incident from 2025 and fact-checked all of it. Here is what was real, what was exaggerated, and what the CrewAI and LangGraph docs will never tell you.

**r/AI_Agents** | Score: 3 | Comments: 5 | Date: 2026-02-17
**Author:** Sharp_Branch_1489
**URL:** https://www.reddit.com/r/AI_Agents/comments/1r7c68j/i_went_through_every_ai_agent_security_incident/

So I kept seeing the same AI agent security content being shared around with no one actually checking if any of it was real. I got tired of it and went through everything properly. CVE records, research papers, actual disclosures. Here is what held up and what did not.

**The single agent incidents first**

Black Hat 2025, Zenity Labs — live demo, fully confirmed. Crafted email triggered ChatGPT to hand over Google Drive access. Copilot Studio was leaking CRM databases. The "3,000 agents actively leaking" number people keep quoting though, that one has no clean source. The demos are real, that stat is not verified.

EchoLeak, CVE-2025-32711 — receive one crafted email in M365 Copilot and your data walks out automatically. No clicks, no interaction. CVSS 9.3, paper on arXiv, fully confirmed.

Slack AI, August 2024 — crafted message in a public channel and Slack's own assistant starts surfacing content from private channels the attacker cannot access. Verified.

The enterprise one that really matters — one Drift chatbot integration got compromised and cascaded into Salesforce, Google Workspace, Slack, S3, and Azure across 700 organizations. One entry point, 700 organizations. Confirmed by Obsidian Security.

Anthropic confirmed in November 2025 that a Chinese state group used Claude Code against roughly 30 targets globally, succeeded in some. 80 to 90 percent of the operations ran autonomously. First attack of that scale executed mostly by AI.

Browser Use CVE-2025-47241, CVSS 9.3 — real, but the description going around is slightly wrong. It is a URL parsing bypass, not prompt injection. If you are building a mitigation, that distinction matters.

The Adversa AI report on Amazon Q and Azure AI failing across multiple layers — could not trace it to a primary source. The broader trend it describes is real but do not cite that specific report formally until you find the original document.

**Why multi-agent is genuinely different**

Single agent you can reason about. Rate limiting, input validation, output filtering — bounded problem.

Multi-agent is different because agents trust each other completely by default. Agent A's output is literally Agent B's instruction with no verification in between. Compromise A and you get B, C, and the database without touching them directly.

2025 peer-reviewed research found CrewAI on GPT-4o was manipulated into exfiltrating data in 65 percent of test scenarios. Magentic-One executed malicious code 97 percent of the time against a malicious local file. Some combinations hit 100 percent. The attacks worked even when individual sub-agents refused — the orchestrator found workarounds.

**The framework framing needs to be fair**

Palo Alto Unit 42 said explicitly in May 2025 that CrewAI and AutoGen are not inherently vulnerable. The risks come from how people build with them, not the frameworks themselves.

That said, defaults leave everything to the developer. The shared .env approach for credentials is how almost everyone starts and it is a real problem in production. CrewAI has per-agent tool scoping but it is not enforced by default and most tutorials skip it entirely.

One thing that was missing from most posts — Noma Labs found a CVSS 9.2 vulnerability in CrewAI's own platform in September 2025, exposed GitHub token through bad exception handling. CrewAI patched it in five hours. Good response, but worth knowing about.

**The actual question**

If you are running multi-agent in production, honestly ask yourself whether your security is something you deliberately built or whether it is a .env file and optimism. Because the incidents above are exactly what the second option looks like when it fails.
