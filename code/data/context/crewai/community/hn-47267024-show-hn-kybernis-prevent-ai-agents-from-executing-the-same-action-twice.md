# Show HN: Kybernis – Prevent AI agents from executing the same action twice

**HN** | Points: 6 | Comments: 3 | Date: 2026-03-05
**Author:** wingrammer
**HN URL:** https://news.ycombinator.com/item?id=47267024
**Link:** https://kybernis.io

AI agents increasingly execute real system actions: issuing refunds, modifying databases, deploying infrastructure, calling external APIs.Because agents retry steps, re-plan tasks, and run asynchronously, the same action can sometimes execute more than once.In production systems this can cause duplicate payouts, repeated mutations, or inconsistent state.Kybernis is a reliability layer that sits at the execution boundary of agent systems.When an agent calls a tool:1. execution intent is captured
2. the action is recorded in an execution ledger
3. idempotency guarantees are attached
4. the mutation commits exactly onceRetries become safe.Kybernis is framework-neutral and works with agent frameworks like LangGraph, AutoGen, CrewAI, or custom systems.I built this after repeatedly seeing reliability failures when AI agents interacted with production APIs.Would love feedback from anyone building agent systems.

## Top Comments

**wingrammer:**
Hi HN – I'm the founder of Kybernis.The core problem we’re exploring is that AI agents are non-deterministic systems operating inside deterministic infrastructure.Traditional systems assume actions run once.Agents retry steps, re-plan tasks, and execute asynchronously.That combination makes duplicate execution surprisingly easy.Kybernis focuses on the execution boundary where agents trigger real mutations (payments, infrastructure changes, APIs).Curious if others deploying agents have run into similar reliability issues.

**jovanaccount:**
Interesting thread. One angle I'd add: when you run multiple AI agents, the coordination problem becomes the dominant failure mode.Specifically, shared state management — agents reading and writing concurrently without collision detection leads to silent failures that look like model quality issues but are actually concurrency bugs.We open-sourced a coordination layer for this: https:&#x2F;&#x2F;github.com&#x2F;Jovancoding&#x2F;Network-AI
