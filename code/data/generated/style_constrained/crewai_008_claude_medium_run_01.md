# Multi-Agent Collaboration Patterns in CrewAI

CrewAI gives you two process modes for coordinating agents: sequential and hierarchical. That's the pitch. The reality is messier, and the gap between these two modes is where most of the design decisions live. I've been digging through CrewAI's documentation, source code, and the issues people are filing, and there are clear patterns emerging for how teams actually wire agents together — and clear pitfalls for the unwary.

## Sequential: The Workhorse

Sequential execution is the default. Tasks run in order, each one's output becomes context for the next. It's simple and predictable. You define a list of tasks, assign each to an agent, and CrewAI walks through them one by one.

The `context` parameter on a Task is where things get interesting. By default, the previous task's output feeds into the next task automatically. But you can override this by explicitly passing a list of tasks whose outputs should serve as context. This is how you set up fan-in patterns — two research tasks running with `async_execution=True`, then a writing task that waits on both via `context=[research_ai_task, research_ops_task]`. The framework handles the synchronization for you.

So sequential doesn't mean strictly linear. You can run parallel branches and rejoin them. It's a directed graph masquerading as a list.

One thing to watch: context accumulation. In a five-task crew, Task 5's prompt receives the concatenated raw output from every preceding task. Issue #4661 in the CrewAI repo documents the problem well — in long chains, this can push past 8,000 tokens of unfiltered prior output, triggering context-length errors or degrading LLM quality. There's an open feature request for an opt-in `context_strategy="summarized"` to compress inter-task context, but it hasn't landed yet. For now, you'll want to be deliberate about which tasks genuinely need earlier outputs and use the `context` parameter to limit the blast radius.

## Hierarchical: Powerful but Fragile

The hierarchical process introduces a manager agent that coordinates workers. You either provide a `manager_agent` directly or specify `manager_llm` (e.g., `manager_llm="gpt-4o"`) and let CrewAI create one automatically. The manager decides which worker handles which subtask, reviews outputs, and orchestrates the whole flow.

This sounds great on paper. The trouble is reliability. Issue #4783 — filed as recently as March 2026 against version 1.10.1 — reports that dynamically created manager agents sometimes fail to delegate at all. The manager just does everything itself, making the hierarchical process behave exactly like sequential. The root cause appears to be in the delegation tool injection logic: the delegation tools don't always get the correct agent references when the manager is created dynamically.

The workaround is to create the manager agent explicitly rather than relying on dynamic creation. Set `allow_delegation=True` on your manager and `allow_delegation=False` on your specialists. This avoids the delegation loop problem too — where agents bounce tasks back and forth indefinitely because both have delegation enabled.

## Delegation as a Collaboration Primitive

Delegation is opt-in via `allow_delegation=True` on any agent. When enabled, the agent gets two built-in tools: "Delegate work to coworker" and "Ask question to coworker." These let agents dynamically route work to teammates or gather information mid-task, without the calling code needing to define that routing upfront.

This is CrewAI's take on emergent coordination. An agent decides on its own that it needs help from a colleague. It works, but the decision is made by the LLM, which means it's non-deterministic. Sometimes the agent delegates when it shouldn't. Sometimes it doesn't delegate when it should. And sometimes it asks the same question three times because the LLM forgot it already got an answer.

We've found a practical rule: enable delegation on coordinator agents and disable it on specialists. This gives you a clear hierarchy without the chaos of every agent potentially delegating to every other agent.

## Flows: The Higher-Level Orchestrator

Crews handle agent-to-agent collaboration within a single unit of work. Flows handle coordination across multiple crews and arbitrary Python code. The `@start` and `@listen` decorators define an event-driven DAG, and you can mix plain Python functions with crew kickoffs.

The `crewai create flow name_of_flow` command scaffolds a project with the right folder structure — crews live in their own directories under `crews/`, each with `config/agents.yaml` and `config/tasks.yaml`. Your `main.py` wires them together with Flow decorators. And you run it with `crewai flow kickoff` or, starting from version 0.103.0, the unified `crewai run` command.

Flows also bring state management. You can use unstructured state (a plain dict on `self.state`) or structured state via a Pydantic BaseModel. The `@router` decorator enables conditional branching — return a string label and downstream methods can `@listen` for that specific label. The `@human_feedback` decorator (requires version 1.8.0+) pauses the flow for human review, a critical feature for approval gates in production workflows.

One real gotcha with Flows: agent executor state doesn't reset between tasks. Issues #4319 and #4389 document how the `CrewAgentExecutor` accumulates messages when the same agent is reused across sequential tasks. System messages pile up — 1, then 2, then 3 — confusing the LLM and eventually crashing with a `ValueError: Invalid response from LLM call - None or empty`. The experimental `AgentExecutor` fixes this, but the main executor still has the bug as of the latest reports.

## Memory Across Collaboration Boundaries

Sharing memory between crews has been a pain point since at least May 2024 (issue #714). The unified Memory system introduced later solves this. You can now create a single `Memory()` instance and pass it to multiple crews, or use `memory.scope()` to give individual agents their own private slice while sharing a common knowledge base. A researcher agent might get `memory.scope("/agent/researcher")` for private findings, while a writer reads from the shared crew memory.

Memory persists to disk (LanceDB by default, stored under `.crewai/memory`), so it survives across flow runs. This enables workflows that accumulate knowledge over time — a genuinely useful capability for iterative research pipelines.

## The Trade-Off

Sequential process is simpler, but hierarchical gives you dynamic task assignment. That's the fundamental trade-off. Sequential requires you to decide the task ordering at design time, which means less flexibility but more predictability and fewer surprises. Hierarchical lets the manager agent figure out the routing, which is more flexible but introduces the LLM's judgment — and its occasional failures — into your orchestration layer.

For most production work, I'd start with sequential and explicit `context` wiring. Add delegation selectively. Graduate to hierarchical only when you genuinely need dynamic task assignment that can't be determined at design time. And wrap everything in a Flow if you need conditional branching, state management, or multi-crew coordination. The framework gives you the tools. The patterns for using them reliably are still being discovered.
