# I went through every AI agent security incident from 2025 and fact-checked all of it. Here is what was real, what was exaggerated, and what the CrewAI and LangGraph docs will never tell you.

**r/cybersecurity** | Score: 28 | Comments: 23 | Date: 2026-02-17
**Author:** Sharp_Branch_1489
**URL:** https://www.reddit.com/r/cybersecurity/comments/1r79rye/i_went_through_every_ai_agent_security_incident/

Okay so before I start, let me tell you why I even did this. There is a lot of content going around about AI agent security that mixes real verified incidents with half-baked stats and some things that just cannot be traced back to any actual source. I went through all of it properly. Primary sources, CVE records, actual research papers. Let me tell you what I found.

**Single agent attacks first, because you need this baseline**

Black Hat USA 2025 — Zenity Labs did a live demonstration where they showed working exploits against Microsoft Copilot, ChatGPT, Salesforce Einstein, and Google Gemini in the same session. One demo had a crafted email triggering ChatGPT to hand over access to a connected Google Drive. Copilot Studio was leaking CRM databases. This is confirmed, sourced, happened. The only thing I could not verify was the specific "3,000 agents actively leaking" number that keeps getting quoted. The demos are real, that stat is floating without a clean source.

CVE-2025-32711, which people are calling EchoLeak — this one is exactly as bad as described. Aim Security found that receiving a single crafted email in Microsoft 365 Copilot was enough to trigger automatic data exfiltration. No clicks required. CVSS 9.3, confirmed, paper is on arXiv. This is clean and verified.

Slack AI in August 2024 — PromptArmor showed that Slack's AI assistant could be manipulated through indirect prompt injection to surface content from private channels the attacker had no access to. You put a crafted message in a public channel and Slack's own AI becomes the tool that reads private conversations. Fully verified.

The one that should genuinely worry enterprise people — a threat group compromised one chat agent integration, specifically the Drift chatbot in Salesloft, and cascaded that into Salesforce, Google Workspace, Slack, Amazon S3, and Azure environments across 700 plus organizations. One agent, one integration, 700 organizations. This is confirmed by Obsidian Security research.

Anthropic confirmed directly in November 2025 that a Chinese state-sponsored group used Claude Code to attempt infiltration of roughly 30 global targets across tech, finance, chemical manufacturing, and government. Succeeded in some cases. What made it notable was that 80 to 90 percent of the tactical operations were executed by the AI agents themselves with minimal human involvement. First documented large-scale cyberattack of that kind.

Browser Use agent, CVE-2025-47241, CVSS 9.3 — confirmed. But there is a technical correction worth noting. Some summaries describe this as prompt injection combined with URL manipulation. It is actually a URL parsing bypass where an attacker embeds a whitelisted domain in the userinfo portion of a URL. Sounds similar but if you are writing a mitigation, the difference matters.

The Adversa AI report about Amazon Q, Azure AI, OmniGPT, and ElizaOS failing across model, infrastructure, and oversight layers — I could not independently surface this report from primary sources. The broader pattern it describes is consistent with what other 2025 research shows, but do not cite that specific stat in anything formal until you have traced it to the actual document.

**Why multi-agent is a completely different problem**

Single agent security is at least a bounded problem. Rate limiting, input validation, output filtering — hard to do right but you know what you are dealing with.

Multi-agent changes the nature of the problem. The reason is simple and a little uncomfortable. Agents trust each other by default. When your researcher agent passes output to your writer agent, the writer treats that as a legitimate instruction. No verification, no signing, nothing. Agent A's output is literally Agent B's instruction. So if you compromise A, you get B, C, and the database automatically without touching them.

There is peer-reviewed research on this from 2025 that was not in the original material circulating. CrewAI running on GPT-4o was successfully manipulated into exfiltrating private user data in 65 percent of tested scenarios. The Magentic-One orchestrator executed arbitrary malicious code 97 percent of the time when interacting with a malicious local file. For certain combinations the success rate hit 100 percent. These attacks worked even when individual sub-agents refused to take harmful actions — the orchestrator found workarounds anyway.

**The CrewAI and LangGraph situation needs some nuance**

Here is where the framing in most posts gets a bit unfair. Palo Alto Networks Unit 42 published research in May 2025 that stated explicitly that CrewAI and AutoGen frameworks are not inherently vulnerable. The risks come from misconfigurations and insecure design patterns in how developers build with them, not from the frameworks themselves.

That said — the default setups leave basically every security decision to the developer with very little enforcement. The shared .env approach for credentials is genuinely how most people start and it is genuinely a problem if you carry it into production. CrewAI does have task-level tool scoping where you can restrict each agent to specific tools, but it is not enforced by default and most tutorials do not cover it.

Also, and this was not in the original material anywhere — Noma Labs found a CVSS 9.2 vulnerability in CrewAI's own platform in September 2025. An exposed internal GitHub token through improper exception handling. CrewAI patched it within five hours of disclosure, which is honestly a good response. But it is worth knowing about.

**The honest question**

If you are running multi-agent systems in production right now, the thing worth asking yourself is whether your security layer is something you actually built, or whether it is mostly a shared credentials file and some hope. The 2025 incident list is a fairly detailed description of what the failure mode looks like when the answer is the second one.

The security community is catching up — OWASP now explicitly covers multi-agent attack patterns, frameworks are adding scoping mechanisms. The problem is understood. Most production deployments are just running ahead of those protections right now.
