# Multi-Agent Collaboration Patterns in CrewAI

CrewAI sells you a simple promise: define some agents, wire up tasks, and let them collaborate like a team. That promise is half-true. The framework does make multi-agent orchestration easier than rolling your own, but the collaboration model has sharp edges that you won't discover until you're debugging a crew that's been delegating in circles for twenty minutes while burning through your GPT-4o budget.

I want to break down how CrewAI's collaboration actually works, which patterns hold up, and where things fall apart.

## The Two Collaboration Primitives

Everything in CrewAI's collaboration model comes down to one flag: `allow_delegation=True`. Set it on an Agent, and the framework injects two tools into that agent's toolkit. The first is **Delegate Work**, which lets an agent hand off a subtask to a coworker by name. The second is **Ask Question**, which lets an agent query a colleague for specific information. Both tools take the same three parameters: a description string, a context string, and the coworker's role name.

That's the entire inter-agent communication surface. There's no shared blackboard, no pub/sub channel, no structured message bus. Agents talk to each other through tool calls that route by role name. It's simple, but it means your collaboration patterns are constrained by what you can express as a delegation or a question.

## Sequential: The Workhorse

The sequential process is where most teams should start. Tasks execute in list order, and the raw output of each task automatically feeds into the next one as context. You can override this with the `context` parameter on a Task to pull output from specific predecessor tasks instead.

A typical pipeline looks like research, then write, then edit - each agent picking up where the last one left off. The `context=[research_task]` parameter on the writing task ensures the writer sees exactly what the researcher produced.

Sequential is simpler than hierarchical, but hierarchical gives you dynamic task allocation without pre-assigning agents. That trade-off matters. If you know the workflow shape ahead of time, sequential is more predictable and easier to debug. If your tasks need to be routed based on content the manager discovers at runtime, hierarchical earns its complexity. Most production crews I've seen discussed in community forums end up on sequential because predictability wins.

## Hierarchical: The Manager Pattern

The hierarchical process emulates a corporate org chart. You either supply a `manager_llm` (like `"gpt-4o"`) or pass in a custom `manager_agent`, and CrewAI creates a manager that plans, delegates, and validates. Tasks don't need pre-assigned agents - the manager allocates work based on agent capabilities.

This sounds great on paper. The reality is messier. Issue #4783, filed against CrewAI 1.10.1, documents a fundamental problem: dynamically created manager agents can't actually delegate to worker agents. The manager ends up executing all tasks itself, making hierarchical behave identically to sequential. The root cause traced to `_update_manager_tools()` in `crew.py` - delegation tools weren't being wired to the correct agent list during dynamic manager creation. The workaround is to manually create your manager agent with explicit delegation configuration instead of relying on the auto-generated one.

So if you're going hierarchical, don't use the shorthand. Build your manager agent explicitly, set `allow_delegation=True` on the manager, set `allow_delegation=False` on every specialist, and verify the delegation tools are actually present before you trust the output.

## The Context Window Problem

Here's a production issue that doesn't show up in tutorials. CrewAI's `_get_context()` method concatenates all prior task outputs verbatim through `aggregate_raw_outputs_from_task_outputs()` in `formatter.py`. By the time you reach task five in a sequential crew, the prompt can carry 8,000+ tokens of unfiltered prior output. This causes either `ContextLengthExceeded` errors or quietly degraded output quality as the model struggles with a bloated prompt.

A proposed feature (issue #4661) would add `context_strategy="summarized"` at the crew level, compressing each task's output to a two-to-three sentence summary before passing it forward. The default would remain `"full"` for backward compatibility. But as of early 2026, this isn't merged. You're on your own for context management in long pipelines.

## Agent Reuse and State Leakage

Another bug worth knowing about: when you reuse the same agent across multiple sequential tasks - common in Flows with `@listen` decorators - the `agent_executor.messages` list never clears between tasks. Messages accumulate: four, then eight, then twelve. Duplicate system prompts stack up. Eventually the LLM returns an empty response, and you get `ValueError: Invalid response from LLM call - None or empty`. The experimental `AgentExecutor` in `crewai/experimental/agent_executor.py` correctly resets state; the main `CrewAgentExecutor` does not. Issue #4389 documents a fix: resetting `self.messages = []` and `self.iterations = 0` at the start of `invoke()`.

## Delegation Loops and Behavioral Repetition

Agents with mutual `allow_delegation=True` can delegate back and forth indefinitely. The documentation's own troubleshooting section recommends a clear hierarchy: manager delegates, specialists don't. But even with a proper hierarchy, agents can fall into behavioral loops - repeating the same tool calls, re-researching the same information, cycling without progress. The existing `max_iter` parameter (default 20) provides a crude upper bound but doesn't detect the repetition itself. A proposed `LoopDetector` middleware (issue #4682) would fingerprint recent actions and intervene when similarity exceeds a threshold, but this too remains unmerged.

## What Actually Works

The pattern that holds up best is a sequential pipeline with explicit context dependencies, specialists that don't delegate, and a single coordinator agent that handles routing. Keep your crews small - three to four agents. Write specific task descriptions that tell each agent exactly what to produce. And enable `verbose=True` during development so you can watch the delegation decisions happen.

CrewAI's collaboration model is straightforward to set up with `crewai create crew my_project`. It gets you running fast. But the gap between a working demo and a reliable production crew is filled with context window issues, state leakage bugs, and delegation patterns that look correct until they loop. Know where the edges are before you commit.
