# Multi-Agent Collaboration Patterns in CrewAI

CrewAI has crossed 44,000 GitHub stars. That number doesn't tell you whether it actually works for production multi-agent systems, but it does mean a lot of engineers are trying. I've spent time reading through the framework's internals, its issue tracker, and the community discussions around it, and I want to share what I've found about how CrewAI handles agent collaboration — where it shines, where it breaks, and what patterns hold up under real workloads.

## The Three Processes (Well, Two and a Half)

CrewAI organizes multi-agent work around a concept it calls "processes." These are orchestration strategies that determine how tasks flow between agents. There are three defined in the `process.py` enum, but only two actually work today.

**Sequential** is the default. Tasks execute in a fixed order, and each task's output becomes context for the next. If you have a research agent feeding a writer agent feeding an editor agent, sequential is what you want. It's predictable. It's debuggable. And for most workflows, it's enough.

**Hierarchical** emulates a corporate org chart. You provide a `manager_llm` or a custom `manager_agent`, and CrewAI creates a coordinator that dynamically delegates work to the other agents. The manager doesn't just pass tasks along — it's supposed to analyze each task, pick the right agent based on expertise, and validate outputs before moving on. The setup looks clean: `Crew(agents=agents, tasks=tasks, process=Process.hierarchical, manager_llm="gpt-4o")`.

**Consensual** is listed in the codebase as planned but not implemented. The idea is a democratic approach where agents collaboratively decide how to execute tasks. Don't hold your breath on this one.

So in practice, your choice is between a pipeline and a hierarchy. Sequential is simpler, but hierarchical gives you dynamic routing when tasks don't map neatly to a fixed order. That trade-off shapes most of the design decisions you'll make.

## How Delegation Actually Works

The hierarchical process sounds great on paper. Under the hood, delegation relies on two tool classes injected into agents when `allow_delegation=True`: `DelegateWorkTool` and `AskQuestionTool`. These live in `crewai/tools/agent_tools/` and extend a `BaseAgentTool` that handles agent name resolution — normalizing whitespace, doing case-insensitive matching — before creating a new Task object and calling `selected_agent.execute_task()`.

When the crew starts, the `_create_manager_agent()` method in `crew.py` builds a manager with both delegation tools already attached. The manager's role, goal, and backstory come from i18n translation files, and it gets `AgentTools(agents=self.agents).tools()` as its toolkit. So the manager can delegate work and ask questions of any agent in the crew.

But there's a catch. Issue #4783 documents a bug where manager agents can't actually delegate to workers, even with everything configured correctly. The delegation tool injection logic breaks during dynamic manager creation — tools either don't get injected at all, get injected with wrong agent references, or filtering logic removes valid delegation targets. The result is that a hierarchical crew silently degrades into what's effectively sequential execution, with the manager doing all the work itself. A workaround exists: manually create the manager agent with explicit delegation configuration instead of relying on automatic creation. But you shouldn't have to do that.

## The Context Accumulation Problem

Here's a pattern that bites people hard. When you reuse the same agent across multiple sequential tasks — common in Flows with `@listen` decorators — the agent's executor accumulates messages between tasks. Issue #4319 documented the progression: Task 1 produces 4 messages in the LLM context. Task 2 gets 8. Task 3 gets 12. System messages duplicate, user messages duplicate, and eventually the LLM starts returning empty responses before crashing with "Invalid response from LLM call - None or empty."

The root cause is straightforward. The `_update_executor_parameters()` method refreshes tools and prompts but never clears `self.agent_executor.messages`. Issue #4389 confirms the same pattern from a different angle — `invoke()` and `ainvoke()` don't reset iteration counters or message history between task executions. The experimental agent executor in `crewai/experimental/agent_executor.py` already handles this correctly, which suggests the team knows about it but hasn't promoted the fix to the main code path.

The workaround is creating separate agent instances per task, but that defeats the purpose of having a reusable agent with accumulated knowledge. If you're building Flows that chain tasks through the same agent, this is something you need to test for before going to production.

## Memory: Powerful but Incomplete

CrewAI's unified memory system is genuinely ambitious. It uses LLM analysis to automatically infer scope, categories, and importance when you save content. Recall uses a composite score blending semantic similarity at 50%, recency at 30%, and importance at 20%, with a 30-day half-life for recency decay. The default storage backend is LanceDB, writing to `.crewai/memory/`, and consolidation automatically deduplicates similar records when they exceed a 0.85 similarity threshold.

Memory works at multiple scopes — hierarchical paths like `/project/alpha` or `/agent/researcher` or `/company/knowledge`. Agents can have private memories isolated per source, and the system supports "deep recall" where the LLM performs multi-step retrieval for complex queries. During task execution, the agent's `execute_task()` method queries memory with the task description, retrieves up to 5 matches, formats them, and appends them to the task prompt.

The gap is cross-crew memory. Issue #714 raised this back in May 2024: if you run crew1, then dynamically determine agents and tasks for crew2, there's no built-in way to pass memory between them. This matters for any workflow where you compose multiple crews — and Flows encourage exactly that pattern. A third-party project called SuperBrain SDK emerged to address this, offering distributed shared memory with sub-millisecond queries and roughly 5ms state handoff times. But the fact that you need a third-party solution for something this fundamental says a lot about where the framework's boundaries are.

## Context Window Explosion

A subtler problem appears as crews grow. Issue #4661 explains it well: in `Crew._execute_tasks()`, each task receives all prior raw task outputs concatenated together. By the time you reach task 5 in a five-task crew, the prompt contains 8,000+ tokens of unfiltered prior output. The result is either `ContextLengthExceeded` errors or degraded LLM quality as the model drowns in irrelevant context.

The proposed solution is a `context_strategy` field with a "summarized" option. After each task, a small LLM call compresses the output to a two or three sentence summary, and downstream tasks receive the summary instead of raw output. The fallback is truncation if the summary call fails. This isn't merged yet, but it addresses a real scaling limitation in sequential workflows. If you're running more than three or four sequential tasks, you'll likely hit this yourself.

The `_get_context()` function in `crew.py` controls this behavior. When a task's context is `NOT_SPECIFIED`, it aggregates raw outputs from all completed tasks. When you explicitly set `context=[research_task]` on a task, it only pulls output from that specific task. Being explicit about context dependencies is the best mitigation available today.

## What the Community Has Learned

The Reddit and Hacker News discussions paint a consistent picture. One user summarized it bluntly: "The autonomous part is actually the bug, not the feature." They reported agents looping on the same three URLs, re-summarizing the same five paragraphs ten times, and hitting a $15 bill before producing usable output. Their fix was switching to a linear flow with a single RAG step and a strict checklist — that worked nine out of ten times instead of two out of ten.

A debugging-focused discussion on Reddit identified five failure layers in multi-agent crews, ordered by how often people debug them wrong: manager routes the task to the wrong agent, tool failure surfaces as a reasoning failure, memory injects bad context into later steps, delegation drift pushes the crew off course, and a task that should terminate overwrites good work. The poster found that using a structured "first debug cut" approach — identifying which layer failed before applying fixes — reduced wasted debugging effort substantially.

The production-readiness thread on Hacker News produced a useful checklist: persistent memory across sessions, real tool use with error recovery, multi-model support, plugin extensibility, daemon-mode execution, and security boundaries with audit logs. Most frameworks nail one or two of these but fall apart on the rest. CrewAI covers memory, multi-model support, and extensibility reasonably well. It's weaker on observability and security sandboxing — the framework's abstractions hide what's happening at the agent-to-LLM boundary, making cost control and debugging harder than they should be.

## Flows: The Missing Orchestration Layer

Flows are CrewAI's answer to the "crews aren't enough" problem. They provide event-driven orchestration with decorator-based control flow: `@start()` marks entry points, `@listen()` chains method completions, `@router()` enables conditional branching, and `@human_feedback()` pauses for human approval. State management supports both unstructured dictionaries and typed Pydantic models.

The key pattern is combining multiple crews within a flow. You run a research crew, evaluate the output, conditionally route to either a deep-analysis crew or a summarization crew, then pass results to a final reporting crew. Each crew handles its own agent coordination, and the flow handles inter-crew orchestration. One community member praised this architecture specifically — the balance between crew-level autonomy and flow-level precision is, they said, exactly what the agent space needed.

But flows inherit the problems of their constituent crews. Message accumulation, context explosion, and memory isolation all compound when you chain crews together. And the debugging challenge multiplies: you now need to reason about which crew, which agent within that crew, and which layer within that agent is failing.

## Practical Recommendations

If you're building with CrewAI today, start with sequential processes and explicit context dependencies. Don't reach for hierarchical until you've confirmed your task routing actually needs to be dynamic — and if you do, create your manager agent manually instead of relying on automatic creation.

Be aggressive about setting `max_iter` (default is 20, which is generous) and `max_execution_time` on agents. Without these, a confused agent will burn through your token budget in a loop. Use separate agent instances per task in Flows until the message accumulation bug is fixed. And set `context` explicitly on every task rather than relying on the default behavior of concatenating all prior outputs.

The broader lesson from the community is this: reliability beats autonomy. A single well-prompted agent with specific tools will outperform a crew of autonomous agents for most tasks. Multi-agent patterns earn their complexity when you have genuinely distinct expertise domains — a researcher who searches, a writer who drafts, an analyst who evaluates — and clear handoff boundaries between them. If your agents are doing similar work and just talking to each other, you've added cost and latency without adding capability.

CrewAI gives you real building blocks for multi-agent systems. But the framework's ambitions outpace its stability in a few critical areas, and understanding those gaps before you ship is the difference between a demo that impresses and a system that runs.
