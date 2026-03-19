# Multi-Agent Collaboration Patterns in CrewAI

CrewAI ships two process types for coordinating agents: sequential and hierarchical. A third, consensual, is listed in the roadmap but doesn't exist in the codebase yet. Picking the right one isn't trivial, and the default choice shapes everything downstream -- how context flows between tasks, who decides what agent does what, and where token costs pile up.

I've been digging through the CrewAI 1.11.0 source, its open issue tracker, and the community discussion around production use. Here's what the collaboration model actually looks like under the hood, where it breaks, and what patterns hold up.

## Two Philosophies, One Framework

CrewAI draws a hard line between Crews and Flows. Crews give agents autonomy: they negotiate, delegate, and make their own judgment calls about how work gets done. Flows give the developer control: event-driven execution with explicit branching, state management via Pydantic models, and decorators like `@start()`, `@listen()`, and `@router()` that wire the whole thing together.

Most teams start with Crews because the abstraction is appealing. Define a role, a goal, a backstory. Assign tasks. Kick it off. But the real leverage comes from combining both -- using Flows for the predictable skeleton and Crews for the steps that genuinely benefit from agent reasoning.

## Sequential: The Boring Default That Works

Sequential is the default process type, and it does exactly what you'd expect. Tasks run in order. The output of each task becomes context for the next. Every task must have an agent assigned. Simple.

This is the pattern most people should start with. Context flows linearly. You can inspect what happened at each step. Debugging is straightforward because the execution path is deterministic.

But sequential doesn't mean isolated. Agents can still collaborate across tasks through two mechanisms. The first is the `context` parameter on Task, which lets you explicitly wire one task's output into another that isn't directly adjacent. The second is delegation -- if an agent has `allow_delegation=True`, it gets access to two built-in tools: "Delegate work to coworker" and "Ask question to coworker." Even in a sequential process, an agent can reach out to any other agent on the crew.

That delegation flag defaults to False. This is a deliberate choice. You have to opt into the complexity.

A typical sequential crew looks like a pipeline: a researcher gathers information, a writer produces a draft, an editor polishes it. Each task's `expected_output` constrains what the agent delivers. The final task's output becomes the crew's overall result. You can set up the project scaffolding with `crewai create crew my_project`, which generates `config/agents.yaml` and `config/tasks.yaml` alongside your Python entry points.

## Hierarchical: Powerful on Paper, Rough at the Edges

The hierarchical process introduces a manager agent that coordinates the crew. Instead of tasks being pre-assigned to specific agents, the manager decides who handles what based on capabilities. You enable it by setting `process=Process.hierarchical` and providing either a `manager_llm` or a custom `manager_agent`.

The idea is compelling. A manager evaluates the task, picks the best-suited agent, delegates, reviews the output, and moves on. This mirrors how real teams operate -- a project lead doesn't write every line of code, they allocate work.

So what's the catch? Issue #4783 documents a significant bug: in version 1.10.1, manager agents can't actually delegate to worker agents. The manager executes all tasks itself, which makes hierarchical behave identically to sequential. The root cause sits in `_update_manager_tools()`, where the delegation tool injection logic fails during dynamic manager creation. Tools either don't get injected at all, get injected with wrong agent references, or get filtered out incorrectly.

The workaround is to manually create a manager agent with explicit delegation configuration rather than letting CrewAI generate one. That means building the Agent object yourself, setting `allow_delegation=True`, and passing it as `manager_agent`. Auto-creation via `manager_llm` is the path that breaks.

This kind of issue illustrates a broader tension. Hierarchical process is the more ambitious design, but it has more surface area for bugs. Sequential is simpler, but sequential gives you predictable execution flow without the delegation machinery that can misfire. I'd recommend sticking with sequential unless your use case genuinely requires dynamic task allocation -- and if it does, test the delegation path end to end before shipping.

## The Delegation Trap

Delegation sounds great. Agent A realizes it needs specialized knowledge, asks Agent B, integrates the answer, moves on. The implementation is clean: when delegation is enabled, the agent gets those two coworker tools injected automatically. Any agent in the crew becomes reachable.

The problem is loops. Agent A delegates to Agent B, who delegates back to Agent A. Or worse, Agent A keeps re-researching the same information through delegation calls, burning tokens in circles. The `max_iter` parameter (defaulting to 20) provides a crude upper bound on iterations, but it doesn't detect behavioral repetition. An agent can take 20 unique-looking but equally useless steps before hitting the wall.

Issue #4682 proposes a loop detection middleware that watches for repetitive patterns using a sliding window of recent actions. The proposed design fingerprints actions with SHA-256, clusters them, and triggers intervention when a dominant action ratio exceeds a threshold. You'd configure it with something like a `similarity_threshold` of 0.8 and an action like `inject_reflection` or `escalate_to_manager`. It's not merged yet, but the problem it addresses is real.

The practical pattern that works today: give coordinators `allow_delegation=True` and specialists `allow_delegation=False`. Build a clear hierarchy. Don't let everyone talk to everyone. The constraint is the feature.

## Context Accumulation: A Hidden Cost

Here's something that surprises people. In `crew.py`, the `_get_context()` method calls `aggregate_raw_outputs_from_task_outputs()`, which concatenates all prior task raw outputs verbatim. By the fifth task in a crew, you're injecting the full uncompressed text of every preceding task's output into the prompt. Issue #4661 reports 8,000+ tokens of unfiltered context in a five-task crew, enough to trigger `ContextLengthExceeded` errors or severely degrade output quality.

A proposed fix introduces `context_strategy="summarized"` at both the Crew and Task level. With this enabled, a lightweight LLM call (~100 tokens) would compress each task's output into a two-to-three-sentence summary before passing it downstream. The per-task override lets you keep full fidelity where it matters and summarize where it doesn't.

Until that ships, you can manage this yourself. Use the `context` parameter on Task to explicitly select which prior tasks feed into each step rather than accepting the default firehose. Be selective about dependencies. Not every task needs to see everything that came before it.

There's a related executor-level bug that compounds the problem. Issues #4319 and #4389 document the same defect across multiple versions: when the same agent handles multiple sequential tasks, the agent executor doesn't clear its message history between tasks. System messages duplicate, context windows bloat, and eventually the LLM returns empty responses or crashes with `ValueError: Invalid response from LLM call - None or empty`. The fix is a two-liner -- clear `self.messages` and reset `self.iterations` at the start of each invocation -- but as one commenter noted, five separate PRs were submitted for the same small bug.

## Memory: From Fragmented to Unified

Earlier CrewAI versions had separate short-term, long-term, entity, and external memory types. Version 1.11.0 replaces all of that with a single unified `Memory` class backed by LanceDB. The new system uses composite scoring for recall, combining semantic similarity, recency decay, and importance weighting with default weights of 0.5, 0.3, and 0.2 respectively.

Memory is organized in hierarchical scopes, like filesystem paths. An agent's memories might live under `/agent/researcher/findings` while project-level context sits at `/project/alpha`. You can create scoped views with `memory.scope()` or read-only cross-branch slices with `memory.slice()`. The LLM auto-infers scope when you don't specify one.

The consolidation behavior is worth understanding. On save, memories with similarity above 0.85 get deduplicated -- the LLM decides whether to keep, update, delete, or insert as new. Batch saves via `remember_many()` run a tighter dedup at 0.98 threshold and execute non-blocking in a background thread. A read barrier in `recall()` auto-drains pending writes before searching, so you won't miss freshly saved context.

For cross-crew collaboration -- a long-standing pain point documented in issue #714 -- the scoped memory model provides a real answer. Two Crew instances can share context through overlapping scopes without needing to share agents or task definitions. This wasn't possible in earlier versions, where people tried workarounds like reassigning agents and tasks on the same Crew instance and re-running kickoff, which caused errors.

Memory adds LLM calls, though. Every save triggers analysis for scope and importance inference. Deep recall runs a multi-step flow with LLM reasoning. There's a smart optimization -- queries under 200 characters skip LLM analysis -- but you should budget for the overhead. The default memory LLM is `gpt-4o-mini`, which keeps costs low, but it's still latency you're adding to every task transition.

## What the Community Says

The community conversation around CrewAI is polarized. On one side, the framework hit 44,000 GitHub stars by February 2026 and has certified over 100,000 developers through its learning platform. On the other side, production users report significant pain.

One Reddit user described spending an entire weekend on a research-to-Obsidian pipeline that failed because an agent looped on three URLs when a Playwright tool crashed on a cookie popup. Token spend hit $15 before producing usable output, with GPT-4o agents re-summarizing the same five paragraphs ten times. Their verdict was blunt: "the autonomous part is actually the bug, not the feature." They switched to a linear flow with a single RAG step and went from a 2/10 to 9/10 success rate.

Another common criticism, especially visible in the LangGraph comparison threads, is observability. Without paid tooling, you can't easily see what prompts are actually sent to the LLM. You can't inspect delegation decisions. When something goes wrong in a multi-agent crew, the failure surface is large -- was it the manager routing to the wrong agent, a tool failure masquerading as a reasoning failure, bad memory injection, or delegation drift pushing the crew down a wrong path?

## Patterns That Hold Up

After reading through the source, the bugs, and the battle reports, a few collaboration patterns emerge as reliable.

Use sequential process with explicit context wiring as your default. Reserve hierarchical for cases where you genuinely don't know which agent should handle a task at design time -- and use a custom manager agent, not the auto-generated one. Enable delegation sparingly: on coordinators, off for specialists. Think of `allow_delegation=False` as the guardrail, not the limitation.

Consider Flows for orchestration when you need conditional branching or state management between crews. The `@listen()` and `@router()` decorators give you the control that Crews intentionally don't provide. CrewAI's own documentation frames Crews and Flows as complementary, and the production experience confirms it: the autonomy of Crews works best when bounded by the structure of Flows.

Keep task contexts small. Don't rely on the default behavior that dumps every prior output into the next task's prompt. Be explicit about which tasks feed into which. And watch your token spend -- agent-to-agent communication is where costs accumulate fastest. A five-agent crew with delegation enabled can easily burn through an order of magnitude more tokens than the same workflow expressed as a simple pipeline.

The framework has real capabilities. The unified memory system is genuinely well-designed. The planning feature -- enabled with `planning=True` on Crew, backed by `gpt-4o-mini` by default -- gives agents step-by-step execution plans before they start working. But the gap between the abstraction and the implementation still shows up in production, particularly around hierarchical delegation and context management. Know where the edges are, and you'll build something that works.
