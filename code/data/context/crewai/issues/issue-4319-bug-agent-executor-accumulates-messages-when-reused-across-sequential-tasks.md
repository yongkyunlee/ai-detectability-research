# [BUG] Agent executor accumulates messages when reused across sequential tasks

**Issue #4319** | State: closed | Created: 2026-01-31 | Updated: 2026-03-11
**Author:** kindaSys331
**Labels:** no-issue-activity

## Description

When the same agent is reused across multiple sequential tasks (common pattern in Flow with `@listen` decorators), the agent executor's message history is not cleared between tasks. This causes messages to accumulate, leading to:
- Duplicate system messages (1 → 2 → 3...)
- Duplicate user messages
- Confused LLM context that causes empty responses
- Eventually crashes with "Invalid response from LLM call - None or empty"

## Root Cause

**Location:** `crewai/agent/core.py`, lines 872-901, method `_update_executor_parameters()`

The method updates executor parameters when an agent is reused but **does not clear** `self.agent_executor.messages`:

```python
def _update_executor_parameters(
    self,
    task: "Task",
    tools: List[Any],
    raw_tools: List[Any],
    prompt: str,
    stop_words: List[str],
    rpm_limit_fn: Callable[[], None],
) -> None:
    """Update executor parameters without recreating instance."""
    # Updates tools, prompt, etc.
    # BUT DOES NOT CLEAR self.agent_executor.messages ❌
```

When agent is reused (lines 840-845):
```python
if self.agent_executor is not None:
    self._update_executor_parameters(...)  # Reuses executor
else:
    self.agent_executor = ...  # Creates new one
```

## Reproducible Test

```python
"""Minimal reproduction of message accumulation bug."""
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

@tool("example_tool")
def example_tool(text: str) -> str:
    """Example tool."""
    return f"Result: {text}"

def test_sequential_tasks():
    """Reproduce bug: messages accumulate across tasks."""

    llm = LLM(
        model="gpt-4",  # Any LLM
        api_key="your-key",
    )

    agent = Agent(
        role="Test Agent",
        goal="Execute tasks",
        backstory="Test agent for reproduction",
        tools=[example_tool],
        llm=llm,
        verbose=False,
    )

    # Execute 3 sequential tasks with SAME agent
    task1 = Task(description="Task 1", expected_output="Result", agent=agent)
    task2 = Task(description="Task 2", expected_output="Result", agent=agent)
    task3 = Task(description="Task 3", expected_output="Result", agent=agent)

    crew1 = Crew(agents=[agent], tasks=[task1])
    crew1.kickoff()

    if hasattr(agent, 'agent_executor') and agent.agent_executor:
        msgs1 = len(agent.agent_executor.messages)
        print(f"After Task 1: {msgs1} messages")

    crew2 = Crew(agents=[agent], tasks=[task2])
    crew2.kickoff()

    if hasattr(agent, 'agent_executor') and agent.agent_executor:
        msgs2 = len(agent.agent_executor.messages)
        system_count = sum(1 for m in agent.agent_executor.messages if m.get('role') == 'system')
        print(f"After Task 2: {msgs2} messages")
        print(f"System messages: {system_count}")  # Will show 2 instead of 1

    crew3 = Crew(agents=[agent], tasks=[task3])
    crew3.kickoff()

    if hasattr(agent, 'agent_executor') and agent.agent_executor:
        msgs3 = len(agent.agent_executor.messages)
        system_count = sum(1 for m in agent.agent_executor.messages if m.get('role') == 'system')
        print(f"After Task 3: {msgs3} messages")
        print(f"System messages: {system_count}")  # Will show 3 instead of 1

if __name__ == "__main__":
    test_sequential_tasks()
```

## Expected Behavior

```
After Task 1: 4 messages (1 system, 1 user, 2 assistant)
After Task 2: 4 messages (1 system, 1 user, 2 assistant)  ✅
After Task 3: 4 messages (1 system, 1 user, 2 assistant)  ✅
```

## Actual Behavior

```
After Task 1: 4 messages (1 system, 1 user, 2 assistant)
After Task 2: 8 messages (2 system, 2 user, 4 assistant)  ❌
After Task 3: 12 messages (3 system, 3 user, 6 assistant) ❌
```

Eventually leads to:
```
ValueError: Invalid response from LLM call - None or empty
```

## Impact

This affects any workflow where agents are reused:
- **Flow patterns** with `@listen` decorators (most common)
- Sequential task execution with same agent
- Any code that creates agent once and uses it multiple times

The accumulated messages cause:
1. Context window explosion
2. Confused LLM context (multiple system prompts for same task)
3. Model generates empty/invalid responses
4. Application crashes

## Proposed Fix

Clear messages when updating executor parameters:

```python
def _update_executor_parameters(
    self,
    task: "Task",
    tools: List[Any],
    raw_tools: List[Any],
    prompt: str,
    stop_words: List[str],
    rpm_limit_fn: Callable[[], None],
) -> None:
    """Update executor parameters without recreating instance."""

    # Existing parameter updates...
    self.agent_executor.tools = tools
    self.agent_executor.tools_handler.tools = raw_tools
    # ... other updates ...

    # FIX: Clear accumulated messages from previous tasks
    if hasattr(self.agent_executor, 'messages'):
        self.agent_executor.messages.clear()
```

## Workaround

Create new agent instances for each task (defeats purpose of agent reuse):

```python
# Instead of reusing agent:
agent = create_agent()
task1.agent = agent  # Reused ❌

# Create separate instances:
agent1 = create_agent()
agent2 = create_agent()
agent3 = create_agent()
task1.agent = agent1  # Works but inefficient ✅
```

## Environment

- **CrewAI version:** 0.95.0+ (issue present in current main branch)
- **Python version:** 3.11+
- **LLM:** Reproducible with any LLM provider

## Additional Context

The bug is deterministic and 100% reproducible with the test above. The docstring for `_update_executor_parameters()` says "Update executor parameters without recreating instance" but doesn't mention whether message history should be preserved or cleared - clearing makes more sense for sequential tasks to avoid context pollution.

## Comments

**Vidit-Ostwal:**
Just checked out devin's PR, looks good. (We can drop the 2nd test case though)
I think that should resolve this.

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
