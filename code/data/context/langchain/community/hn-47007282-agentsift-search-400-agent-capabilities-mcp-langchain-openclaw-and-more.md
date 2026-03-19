# AgentSift – Search 400 agent capabilities – MCP, LangChain, OpenClaw, and more

**HN** | Points: 1 | Comments: 1 | Date: 2026-02-13
**Author:** onlyamicrowave
**HN URL:** https://news.ycombinator.com/item?id=47007282
**Link:** https://agentsift.ai

## Top Comments

**onlyamicrowave:**
Hi HN,I built AgentSift to solve a problem I kept hitting when building AI agents: every platform has its own capability registry, and there's no single place to search across all of them.*What it does:*
- Unified search across 7 agent platforms (MCP, LangChain, CrewAI, Composio, OpenAI, OpenClaw, NEAR AI)
- 341+ indexed capabilities (tools, skills, integrations)
- Fuzzy intent search (type "send email" and get every email-related capability, not just exact string matches)
- Safety ratings: every capability shows permission levels and risk ratings*Why the safety angle matters:*
When you're giving an agent a "file management" capability, you need to know if that means "list filenames" or "recursively delete everything." AgentSift shows permission breakdowns for every capability.*Tech:*
- Next.js 15 + PostgreSQL
- Fuse.js for fuzzy search
- Platform-specific scrapers that run nightly to keep the index updated*What's useful about this:*
Instead of checking MCP's server registry, then LangChain's tool docs, then Composio's integration list… you search once. Cross-platform capability discovery in one place.Still early, but it's live and usable. Planning to add a submission flow so developers can add capabilities directly, plus an API for agents to query programmatically.Built this in about 6 hours during a weekend sprint. Feedback welcome.
