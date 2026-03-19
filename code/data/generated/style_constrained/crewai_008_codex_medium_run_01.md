# Multi-agent collaboration patterns in CrewAI

CrewAI gets more understandable once you stop treating “multi-agent” as one feature. The project draws a line between crews, which coordinate agents around tasks, and flows, which coordinate crews and control logic around state. As of CrewAI v1.11.0, dated March 18, 2026 in the project changelog, that split is still the cleanest way to reason about the framework.

## Pattern 1: Sequential handoffs for deterministic work

The default collaboration pattern in CrewAI is still the boring one, and that’s a compliment. A `Crew` runs with `process=Process.sequential` unless you choose otherwise. Tasks execute in order, and one task’s output can become input for the next through the task `context` field.

You can define the crew directly, or keep the shape in `config/agents.yaml` and `config/tasks.yaml` and let a `@CrewBase` class collect agents and tasks. Either way, the handoff is explicit.

But sequential crews aren’t free. The docs say task outputs become context for later tasks, and an open feature request from March 1, 2026 goes further by tracing the current code path that aggregates prior raw outputs. In that report, a five-task crew can push roughly 8,000 or more tokens of prior output into task five. So sequential is simpler, but it also makes context growth easy to ignore until quality drops or context limits bite.

Use sequential crews when the workflow is already known and you want deterministic handoffs. Keep outputs tight. Use structured outputs when data is meant to travel downstream. And don’t confuse “linear” with “cheap.”

## Pattern 2: Lead-agent collaboration inside a single task

CrewAI’s next layer is runtime collaboration inside one task. If you set `allow_delegation=True`, the agent automatically gets collaboration tools for handing work to coworkers and asking them questions.

This pattern fits work that has one accountable owner but still benefits from specialist input. A lead writer can own the deliverable while pulling in a researcher, and a coordinator can gather details without turning the whole crew into a manager hierarchy.

But delegation only works if the roles are sharp. The docs are very direct here: enable delegation for coordinators and generalists, and often disable it for specialists. That avoids the classic loop where agents keep bouncing questions back and forth because nobody has a final responsibility boundary. CrewAI also defaults `respect_context_window` to `True` on agents.

So this is the sweet spot for semi-open-ended jobs. You know who owns the answer. You don’t know which supporting expertise will be needed until execution starts.

## Pattern 3: Hierarchical crews when routing is the real problem

Once task ownership itself becomes dynamic, CrewAI pushes you toward `Process.hierarchical`. In that mode, the crew requires either `manager_llm` or `manager_agent`, and the source code enforces that requirement. The manager allocates work, reviews outputs, and decides whether the task is actually complete. If you provide a custom manager agent, CrewAI forces delegation on and rejects managers that bring their own tools. Otherwise, the framework creates a manager automatically.

CrewAI also lets you layer planning on top. Setting `planning=True` sends crew information to an `AgentPlanner` before each iteration and appends the resulting plan to task descriptions. The planning docs warn that the default planner model is `gpt-4o-mini`, which is useful detail because it means “turn on planning” can also mean “start making OpenAI calls” unless you override `planning_llm`.

Here the trade-off is pretty clean. Sequential crews are simpler, but hierarchical crews give you dynamic assignment, review, and validation. There’s also a reason to stay honest about maturity. An open bug report from March 9, 2026 claims some hierarchical setups with manager-created delegation don’t delegate as expected and can behave more like sequential execution. That doesn’t invalidate the pattern, but it does mean you should verify delegation through logs or callbacks instead of assuming the org chart exists just because the process flag says so.

## Pattern 4: Flows as the control plane above crews

The most useful CrewAI idea isn’t actually another crew pattern. It’s the decision to move orchestration up a level. Flows give you `@start`, `@listen`, and `@router` decorators, typed or untyped state, and composition points where one crew can feed another. The template docs put it well: crews give you autonomy, flows give you precision.

And this is where multi-agent collaboration starts looking like backend workflow design. Multiple `@start()` methods can run in parallel. `@router` can branch by result. `or_()` and `and_()` let you model join behavior. A flow can run a research crew, store `result.raw` in state, and pass that into a writing crew in the next listener. Or it can skip crews entirely and call an agent directly with `kickoff_async()`.

The flow layer also carries the production features you usually end up needing later. `@persist` adds SQLite-backed state persistence and recovery. `@human_feedback` is available in v1.8.0 and later, which lets a flow pause for review and resume with explicit feedback history. `flow.plot("my_flow")` generates an HTML visualization, which is exactly the kind of boring debugging aid these systems need more of.

But flows don’t magically erase the durability problem. A Hacker News discussion from March 12, 2026 makes the broader point that agent frameworks often have reasoning loops and tool execution, while durable workflow engines solve crash recovery and resumption at a different level. CrewAI’s persistence features help, but they don’t eliminate that architectural question.

One last pattern is worth calling out. CrewAI now treats A2A as a first-class delegation mechanism, so collaboration doesn’t have to stop at one local crew. The docs show `uv add 'crewai[a2a]'`, `A2AClientConfig`, and `.well-known/agent-card.json` endpoints. Once you cross that boundary, timeouts, auth, and completion semantics matter as much as prompts.

CrewAI’s collaboration model is strongest when you use the smallest pattern that matches the job. Start with sequential task handoffs. Add delegation when a lead agent needs specialist help. Move to hierarchical crews when assignment itself is uncertain. Bring in flows when you need state, branching, persistence, or multiple crews in one pipeline. We don’t need every agent system to look like a tiny company.
