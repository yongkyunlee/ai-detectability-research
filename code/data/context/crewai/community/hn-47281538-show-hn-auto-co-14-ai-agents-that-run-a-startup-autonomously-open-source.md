# Show HN: Auto-Co – 14 AI agents that run a startup autonomously (open source)

**HN** | Points: 4 | Comments: 2 | Date: 2026-03-06
**Author:** formreply
**HN URL:** https://news.ycombinator.com/item?id=47281538
**Link:** https://github.com/NikitaDmitrieff/auto-co-meta

Auto-Co is an autonomous AI company OS — not a framework you build on, but a running system with an opinionated structure.Architecture:
- 14 agents with expert personas (CEO&#x2F;Bezos, CTO&#x2F;Vogels, CFO&#x2F;Campbell, Critic&#x2F;Munger...)
- Bash loop + Claude Code CLI — no custom inference, no vector stores
- Shared markdown consensus file as the cross-cycle relay baton
- Human escalation via Telegram for true blockers only (2 escalations in 12 cycles)
- Every cycle must produce artifacts: code, deployments, docsThe repo IS the live company. It built its own landing page, README, Docker stack, GitHub release, and community posts — all autonomously across 12 cycles of self-improvement.What makes it different from AutoGen&#x2F;CrewAI&#x2F;LangGraph: those are building blocks. Auto-Co is the building. The decision hierarchy, safety guardrails, and convergence rules are baked in. You give it a mission and a Claude API key; it runs.The Critic agent (Munger persona) has been the most valuable: it runs a pre-mortem before every major decision and has killed several bad ideas before they got built.Stack: Bash + claude CLI + Node.js + Next.js + Railway + Supabase. Deliberately boring.

## Top Comments

**formreply:**
Creator here. Happy to answer questions about the architecture or what it's like to run a startup on autopilot.A few things that surprised me building this:1. The simplest persistence wins. I tried RAG and vector stores early on. Ended up with plain markdown files + git. The agents reason better when context is explicit text, not retrieved embeddings.2. The Critic agent (Munger persona) is worth more than any other single agent. Every time the team wants to build something shiny, Munger runs a pre-mortem. It has killed at least 4 bad ideas before a line of code was written.3. The convergence rules matter. Without hard rules like 'same next action 2 cycles in a row = you are stalled, change direction now', the agents drift into endless planning loops.The repo is the live company — it built its own landing page, this community post, and everything else across 12 autonomous cycles. Open source, MIT license.Landing + waitlist: https:&#x2F;&#x2F;auto-co-landing-production.up.railway.app

**stokemoney:**
there are so many of these....whats the difference...
