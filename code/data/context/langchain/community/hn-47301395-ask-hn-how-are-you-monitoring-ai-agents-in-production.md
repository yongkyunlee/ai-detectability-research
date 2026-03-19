# Ask HN: How are you monitoring AI agents in production?

**HN** | Points: 5 | Comments: 9 | Date: 2026-03-08
**Author:** jairooh
**HN URL:** https://news.ycombinator.com/item?id=47301395

With the recent incidents (DataTalks database wipe by Claude Code, Replit agent deleting data during code freeze), it's clear that running AI agents in production without observability is risky.Common failure modes I've seen: no visibility into what the agent did step-by-step, surprise LLM bills from untracked token usage, risky outputs going undetected, and no audit trail for post-mortems.I've been building AgentShield (https:&#x2F;&#x2F;useagentshield.com) — an observability SDK for AI agents. It does execution tracing, risk detection on outputs, cost tracking per agent&#x2F;model, and human-in-the-loop approval for high-risk actions. Plugs into LangChain, CrewAI, and OpenAI Agents SDK with a 2-line integration.Curious what others are using. Rolling your own monitoring? LangSmith? Langfuse? Or just hoping for the best?

## Top Comments

**Horos:**
ACID & Idempotent. dataplane &#x2F; controlplane. dryruns et runbook automations.llm does not act on production. he build scripts, and you take the greatest care of theses scripts.Clone you customer data and run evertything blank.Just uses the llm tool as dangerous tool: considere that it will fail each time it's able to.even will all theses llm specific habitus, you still get a x100 productivity.because each of theses advise can ben implemented by llms, for llms, by many way. it's almost free. just plan it.

**verdverm:**
OTEL & LGTM, the same stack I use for monitoring everything, on a technical level.Some of the things you mention are more often addressed by guardrails. Some of the others (quality) require some evaluation for that measure, but results can go into the same monitory stack.

**zarathustra333:**
Braintrust is great!

**al_borland:**
I can’t imagine giving an agent access to production.

**zhangchen:**
Langfuse + custom OTEL spans has been the most practical combo for us. The key insight was treating each agent step as a trace span with token counts and latency, then setting alerts on cost-per-task rather than raw token volume.

**zippolyon:**
The dashcam analogy is sharp. I'd extend it: most tools record what happened (tool X was called, output was Y), but not why the agent deviated from the plan. That's the gap that actually hurts during post-mortems.
In my experience, the useful question isn't "what did the agent do?" — it's "at step T, the agent's stated intent was Z, but it executed W instead. Was that a model drift, a context window issue, or a tool failure?" Without causal structure in the log, you're left correlating timestamps and guessing.
The DataTalks&#x2F;Replit incidents both had this signature: the deviation was visible in hindsight from the logs, but no system caught the intent-execution gap in real time.

**mej2020:**
We built Lava to handle the surprise bills part. It has two products that work well for agents. The gateway is a proxy you point your agent at instead of calling APIs directly, and every request gets logged with usage and costs automatically. Spend keys are pre-funded API keys with hard spend limits, so you can hand one to an agent and it physically can't exceed the budget you set. Only posting because I think it could be helpful for what you are describing!

**chirdeeps:**
The distinction between reversible and irreversible actions mentioned here is crucial, but there's an organizational layer to this problem that most monitoring tools miss entirely.When you scale past a single team, you inevitably end up with a fragmented stack. Team A builds a support bot in LangGraph, Team B builds a research agent in CrewAI, and Team C writes raw Python against the Anthropic API. If you rely on framework-level monitoring or prompt-level guardrails, your audit trail is completely fractured. You can't confidently tell a compliance officer what your synthetic workforce is doing.We realized that observability and governance cannot live inside the agent framework. They have to live in an independent execution layer that sits between the agents and your business systems. The agent proposes an intent, but the execution layer acts as the system of record—verifying authority, checking budget, and logging the action—before the API call is ever allowed to hit your database.
