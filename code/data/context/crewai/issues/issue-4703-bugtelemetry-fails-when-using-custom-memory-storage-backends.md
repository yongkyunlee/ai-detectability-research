# [BUG]Telemetry Fails When Using Custom Memory Storage Backends

**Issue #4703** | State: open | Created: 2026-03-04 | Updated: 2026-03-04
**Author:** MatthiasHowellYopp
**Labels:** bug

### Description

When using a custom `Memory` instance with an explicitly configured storage backend (including LanceDB), the crew fails to initialize with an OpenTelemetry error:

```
Invalid type Memory for attribute 'crew_memory' value. Expected one of ['bool', 'str', 'bytes', 'int', 'float'] or a sequence of those types
```

### Steps to Reproduce

1. Create a custom Memory instance with LanceDBStorage explicitly configured:
```python
from crewai import Agent, Crew, Task, LLM
from crewai.memory import Memory
from crewai.memory.storage.lancedb_storage import LanceDBStorage

# Explicitly configure LanceDB storage instead of using memory=True
storage = LanceDBStorage(path="./my_memory_db", vector_dim=1536)
memory = Memory(
    storage=storage,
    llm=LLM(model="gpt-4o-mini")
)
```

2. Create a simple crew with the custom memory instance:
```python
agent = Agent(
    role="Researcher",
    goal="Research topics",
    backstory="Expert researcher",
    llm=LLM(model="gpt-4o-mini")
)

task = Task(
    description="Research AI trends",
    expected_output="A summary of AI trends",
    agent=agent
)

crew = Crew(
    agents=[agent],
    tasks=[task],
    memory=memory,  # Passing Memory instance instead of True
)
```

3. Attempt to run the crew:
```python
crew.kickoff()
```

4. Observe the telemetry error during crew initialization

### Expected behavior

Custom Memory instances with explicitly configured storage backends should work without telemetry errors. The crew should initialize and run successfully, just as it does with `memory=True`.

### Screenshots/Code snippets

**Complete minimal reproduction:**
```python
from crewai import Agent, Crew, Task, LLM
from crewai.memory import Memory
from crewai.memory.storage.lancedb_storage import LanceDBStorage

# Explicitly configure storage (instead of using memory=True)
storage = LanceDBStorage(path="./custom_memory", vector_dim=1536)

memory = Memory(
    storage=storage,
    llm=LLM(model="gpt-4o-mini")
)

agent = Agent(
    role="Researcher",
    goal="Research topics",
    backstory="Expert researcher",
    llm=LLM(model="gpt-4o-mini")
)

task = Task(
    description="Research AI trends",
    expected_output="A summary",
    agent=agent
)

# This will fail with telemetry error
crew = Crew(
    agents=[agent],
    tasks=[task],
    memory=memory,  # Error: OpenTelemetry can't serialize Memory object
)

crew.kickoff()
```

**Error message:**
```
Invalid type Memory for attribute 'crew_memory' value. Expected one of ['bool', 'str', 'bytes', 'int', 'float'] or a sequence of those types
```

### Operating System

Other (specify in additional context)

### Python Version

3.11

### crewAI Version

1.10.1a1 (main branch)

### crewAI Tools Version

N/A

### Virtual Environment

Venv

### Evidence

**Root cause:** In `crewai/telemetry/telemetry.py` at line 276, the code attempts to serialize the `crew.memory` field directly without checking its type:

```python
self._add_attribute(span, "crew_memory", crew.memory)
```

When `memory=True`, this works because `crew.memory` is a boolean. However, when passing a custom `Memory` instance, `crew.memory` contains the Memory object itself, which OpenTelemetry cannot serialize.

### Possible Solution

Convert non-primitive memory values to a serializable representation in `telemetry.py`:

```python
# Line 273-276 in crewai/telemetry/telemetry.py
self._add_attribute(span, "python_version", platform.python_version())
add_crew_attributes(span, crew, self._add_attribute)
self._add_attribute(span, "crew_process", crew.process)

# Convert memory to serializable type for telemetry
memory_value = crew.memory if isinstance(crew.memory, (bool, str, int, float)) else str(type(crew.memory).__name__)
self._add_attribute(span, "crew_memory", memory_value)

self._add_attribute(span, "crew_number_of_tasks", len(crew.tasks))
```

This change:
1. Checks if `crew.memory` is a primitive type that OpenTelemetry can handle
2. If not, converts it to the class name string (e.g., "Memory")
3. Maintains backward compatibility with `memory=True` usage
4. Allows telemetry to track that custom memory is being used without failing

### Additional context

Os is MacOS Tahoe 26.3
