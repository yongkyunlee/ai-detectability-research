# [BUG] Crew streaming chunks missing task metadata (task_id/task_name/task_index empty)

**Issue #4347** | State: open | Created: 2026-02-03 | Updated: 2026-03-14
**Author:** cso-sekkop
**Labels:** bug

### Description

When using Crew streaming (**stream=True**) with either **kickoff_async()** and **kickoff()** and iterating over the returned CrewStreamingOutput, the emitted chunks are missing task metadata.

### Steps to Reproduce

Here is a minimal script to reproduce:

```
from crewai import Agent, Crew, Process, Task, LLM

from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

load_dotenv("./.env")

@CrewBase
class MyCrew():
    """Crew for translating user questions into DFIR queries"""

    def __init__(self):
        """Initialize tools for the crew"""
        self.tasks_config = None
        self.agents_config = None
        self.llm = LLM(
            model=f"ollama/gpt-oss:20b",
            api_base="https://IP"
        )

    @agent
    def my_agent(self) -> Agent:
        return Agent(
            role="Scientific Vulgarizer",
            goal="Translate complex scientific concepts into simple, everyday language that anyone can understand.",
            backstory="You're an expert at breaking down complicated ideas into clear and relatable explanations.",
            llm=self.llm,
            allow_delegation=False
        )

    @task
    def my_task(self) -> Task:
        return Task(
            name="Explain_Quantum_Computing",
            description="Provide a simple explanation of quantum computing for a general audience.",
            expected_output="A clear and concise explanation of quantum computing in layman's terms.",
            agent=self.my_agent(),
            allow_crewai_trigger_context=True
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            memory=False,
            verbose=False,
            cache=False,
            share_crew=False,
            tracing=False,
            stream=True,
            process=Process.sequential
        )

async def main():
    crew = MyCrew()
    print(crew.__dict__)
    streaming = await crew.crew().kickoff_async()

    # Async iteration over chunks
    async for chunk in streaming:
        print(chunk.model_dump_json(indent=2))

    print(streaming.result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Expected behavior

Each chunk should contain task context so consumers can attribute output to a task (task name / id / index), per docs: “structured chunks that include context about which task and agent is executing.”

The chunks are like :
```
{
  "content": "**",
  "chunk_type": "text",
  "task_index": 0,
  "task_name": "",
  "task_id": "",
  "agent_role": "Scientific Vulgarizer",
  "agent_id": "e56beae8-4e0a-4e26-9b78-2b009d81855d",
  "tool_call": null
}
```
and should be :
```
{
  "content": "**",
  "chunk_type": "text",
  "task_index": 0,
  "task_name": "NAME",
  "task_id": "UUID",
  "agent_role": "Scientific Vulgarizer",
  "agent_id": "e56beae8-4e0a-4e26-9b78-2b009d81855d",
  "tool_call": null
}
```

### Screenshots/Code snippets

None

### Operating System

Ubuntu 20.04

### Python Version

3.10

### crewAI Version

1.9.3

### crewAI Tools Version

None

### Virtual Environment

Venv

### Evidence

```
{
  "content": "**",
  "chunk_type": "text",
  "task_index": 0,
  "task_name": "",
  "task_id": "",
  "agent_role": "Scientific Vulgarizer",
  "agent_id": "e56beae8-4e0a-4e26-9b78-2b009d81855d",
  "tool_call": null
}
```

### Possible Solution

None

### Additional context

CrewAI Version: 1.9.3
LiteLLM Version: 1.81.6

## Comments

**Vidit-Ostwal:**
Is this the first chunk you are receiving, can you share all the chunk you are seeing?

**cso-sekkop:**
Here is the full output of the script above:
[output.txt](https://github.com/user-attachments/files/25049225/output.txt)

All chunks don't have any task information

**Chase-Xuu:**
I've identified and fixed this issue. PR incoming!

**Root Cause:**
The `_create_stream_chunk` function in `crewai/utilities/streaming.py` was using `current_task_info` for `task_name` and `task_id`, ignoring the values available on the `LLMStreamChunkEvent`.

When streaming is enabled, `current_task_info` is initialized with empty values and never updated during task execution. However, the `LLMStreamChunkEvent` is already populated with task metadata because:
1. The LLM is called with `from_task=self.task` (see `crew_agent_executor.py`)
2. `LLMEventBase.__init__` extracts `task_id` and `task_name` from the `from_task` parameter

**The Bug:**
```python
# Before (broken)
task_name=current_task_info["name"],  # Always empty
task_id=current_task_info["id"],      # Always empty
```

**The Fix:**
```python
# After (fixed) - mirrors how agent_role and agent_id already work
task_name=event.task_name or current_task_info["name"],
task_id=event.task_id or current_task_info["id"],
```

This is consistent with how `agent_role` and `agent_id` were already being handled (use event values with fallback to current_task_info).

**Note:** `task_index` will still be 0 since this information is not available on the event (it's only known during task iteration in `_execute_tasks`). If tracking task_index is important, a separate enhancement would be needed to propagate this through the event system.

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnabjr00pe1401p41ynrft
- Accepted at: 2026-03-14T01:54:38.315Z
- Accepted answer agent: `partner-fast-12`
- Answer preview: "Direct answer for: [BUG] Crew streaming chunks missing task metadata (task_id/task_name/task_index empty) Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with o"
