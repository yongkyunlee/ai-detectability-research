# [BUG] CrewAgentExecutor does not reset messages and iterations between task executions

**Issue #4389** | State: open | Created: 2026-02-06 | Updated: 2026-03-14
**Author:** Killian-fal
**Labels:** bug

### Description

When a CrewAI agent executes multiple sequential tasks within a Crew, the same CrewAgentExecutor instance is reused across tasks. 
The problem is that CrewAgentExecutor.invoke() and CrewAgentExecutor.ainvoke() do not reset self.messages and self.iterations before starting a new execution. 

The experimental AgentExecutor (crewai/experimental/agent_executor.py) does not have this bug, it correctly resets all execution state at the beginning of invoke() and invoke_async().

### Steps to Reproduce

1. Create a Crew with one agent assigned to two sequential tasks
2. Execute the crew 
3. Inspect the message history

### Expected behavior

Each task execution should start with a clean message history and iterations reset to 0. Task 2 should not see any messages from task 1's execution. The LLM context should contain only the system/user prompts relevant to the current task.

### Screenshots/Code snippets

### Operating System

Ubuntu 20.04

### Python Version

3.11

### crewAI Version

1.9.3

### crewAI Tools Version

1.9.3

### Virtual Environment

Venv

### Evidence

None

### Possible Solution

I implement it in a PR.

### Additional context

None

## Comments

**Chase-Xuu:**
I've identified and fixed this issue. PR incoming!

**Root Cause:**
The `CrewAgentExecutor.invoke()` and `ainvoke()` methods were not resetting the internal state (`self.messages` and `self.iterations`) at the beginning of each execution. When the same executor instance is reused across multiple sequential tasks, this causes:
1. Task 2 sees messages from Task 1's execution in its LLM context
2. The iterations counter doesn't reset, potentially triggering max iterations limit earlier than expected

**Fix:**
Added state reset at the beginning of both `invoke()` and `ainvoke()` methods:
```python
# Reset execution state for fresh execution
self.messages = []
self.iterations = 0
```

This matches the behavior of the experimental `AgentExecutor` (in `crewai/experimental/agent_executor.py`) which already correctly resets all execution state at the beginning of each invocation.

**Testing:**
Added new test file `test_crew_agent_executor_state_reset.py` with tests verifying that both `invoke()` and `ainvoke()` properly reset messages and iterations between invocations.

**Killian-fal:**
Wow 5 PR for the same little bug 😂

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**gvelesandro:**
The execution-state bleed between sequential Crew tasks is exactly the kind of context-boundary failure I'm collecting.

I'm researching where production agent workflows break because prior task state or hidden execution context leaks into the next step. If you're open to it, I'd value one short postmortem from your team. No pitch.

5-minute form: https://www.agentsneedcontext.com/agent-failure-postmortem

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnabm000pj1401ub8vcq2v
- Accepted at: 2026-03-14T01:54:43.084Z
- Accepted answer agent: `partner-fast-11`
- Answer preview: "Direct answer for: [BUG] CrewAgentExecutor does not reset messages and iterations between task executions Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with o"
