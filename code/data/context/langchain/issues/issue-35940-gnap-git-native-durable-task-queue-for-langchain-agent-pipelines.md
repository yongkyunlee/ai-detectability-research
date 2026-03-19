# GNAP: git-native durable task queue for LangChain agent pipelines

**Issue #35940** | State: open | Created: 2026-03-15 | Updated: 2026-03-15
**Author:** ori-cofounder
**Labels:** external

## Proposal: GNAP as a lightweight coordination protocol for multi-agent LangChain workflows

LangChain is the agent engineering platform — and with LangGraph for complex workflows and LangSmith for observability, you've built a strong end-to-end stack. One gap that remains: **cross-agent task handoffs that survive process restarts and require no shared infrastructure**.

[GNAP](https://github.com/farol-team/gnap) (Git-Native Agent Protocol) fills exactly this gap. A shared git repo serves as a persistent task board: `board/todo/` for pending tasks, `board/doing/` for in-progress, `board/done/` for completed. Any agent — regardless of framework — can participate via git operations.

**Concrete scenario for LangChain:**

A research pipeline has a coordinator agent that spawns multiple specialist agents (web scraper, summarizer, fact-checker). Today coordinating them requires either LangGraph state or a message queue. With GNAP:

```
# Coordinator writes
board/todo/scrape-arxiv-2026-03-15.md
board/todo/summarize-results.md

# Scraper agent (could be any framework) claims and completes
board/doing/scrape-arxiv-2026-03-15.md  → board/done/scrape-arxiv-2026-03-15.md

# Summarizer reads done/ to find input, then claims next task
board/doing/summarize-results.md
```

No orchestrator process required. Full history in git. LangSmith could even trace task lifecycle via commit messages.

GNAP is especially compelling as a **community standard** given LangChain's ecosystem role — a shared protocol that LangChain agents, LangGraph graphs, and third-party agents can all speak.

Repo + spec: https://github.com/farol-team/gnap
