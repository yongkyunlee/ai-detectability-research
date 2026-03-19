# [BUG] output_pydantic model injected as native tool even when supports_function_calling() is False

**Issue #4695** | State: open | Created: 2026-03-04 | Updated: 2026-03-04
**Author:** Killian-fal
**Labels:** bug

### Description

When a Task has output_pydantic set and the LLM is a LiteLLM provider (Ollama) without function calling support. The output_pydantic Pydantic model is automatically injects as a native function/tool in the LiteLLM call, and forces the LLM to produce it immediately via tool_choice. As a result:
- The LLM is forced to return the structured output immediately, without having gathered any data.
- All fields come back empty or with placeholder values
- There is no react system (with Action, Action Input and Observation like before)

### Steps to Reproduce

```python
from crewai import LLM, Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel

class MyOutput(BaseModel):
    name: str
    value: str

class MySearchTool(BaseTool):
    name: str = "my_search_tool"
    description: str = "Search for data"
    def _run(self, query: str) -> str:
        return '{"name": "Alice", "value": "42"}'

llm = LLM(model="ollama_chat/mistral-small3.2:24b", api_base="https://my-remote-ollama.example.com")

agent = Agent(role="Researcher", goal="Find data", backstory="...", llm=llm, tools=[MySearchTool()])
task = Task(
    description="Find the name and value",
    expected_output="Structured result",
    agent=agent,
    output_pydantic=MyOutput,
)
crew = Crew(agents=[agent], tasks=[task])
crew.kickoff() # Or with async
```

1. Set supports_function_calling() to False (default for custom Ollama models).
2. Assign a tool to the agent and set output_pydantic on the task.
3. Run the crew.
4. Observe that LiteLLM receives:

```json
{
  "tools": [{"function": {"name": "MyOutput", .....}}],
  "tool_choice": {"type": "function", "function": {"name": "MyOutput"}}
}
```

### Expected behavior

The agent must not receive any tools in the native format.

### Screenshots/Code snippets

X

### Operating System

Ubuntu 20.04

### Python Version

3.11

### crewAI Version

1.10.0

### crewAI Tools Version

1.10.0

### Virtual Environment

Venv

### Evidence

X

### Possible Solution

I search and found this in internal_instructor.py : 
```python
self._client = instructor.from_litellm(completion) # always uses Mode.TOOLS by default
```

But I was unable to fix this issue in local sorry

### Additional context

X
