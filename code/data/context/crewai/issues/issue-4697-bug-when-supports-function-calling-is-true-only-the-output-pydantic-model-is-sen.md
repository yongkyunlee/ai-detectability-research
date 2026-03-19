# [BUG] When supports_function_calling() is True, only the output_pydantic model is sent to LiteLLM (the custom agent tools are discard)

**Issue #4697** | State: open | Created: 2026-03-04 | Updated: 2026-03-10
**Author:** Killian-fal
**Labels:** bug

### Description

When supports_function_calling() returns True (either natively or via override) and a output_pydantic is set, the custom agent tools are skip and only the output_pydantic model is send as a tool.

The result: the LLM only sees the output_pydantic Pydantic model as a native tool, not the agent's actual tools. The agent is forced to return structured output immediately without calling any of its tools.

**Note:** I believe CrewAI 1.10.0 introduced a major regression on Ollama + LiteLLM that renders CrewAI unusable. Perhaps more tests should be written for this specific feature to prevent this from happening in the future.

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

1. Set supports_function_calling() to True.
2. Add a tool to the agent and set output_pydantic on the task.
3. Run the crew.
4. Observe that LiteLLM only receives the output_pydantic model as a tool — the agent's my_search_tool is absent.

### Expected behavior

- When supports_function_calling() is True and the agent has tools, all agent tools should be forwarded to LiteLLM.
- The agent should be able to call its tools (e.g. my_search_tool) before returning the final structured output.

### Screenshots/Code snippets

X

### Operating System

Ubuntu 20.04

### Python Version

3.10

### crewAI Version

1.10.0

### crewAI Tools Version

1.10.0

### Virtual Environment

Venv

### Evidence

I've nothing to show sorry (with mlflow we can see that the tools are not send to litellm)

### Possible Solution

I tried to debug this issue and found that InternalInstructor intercepts even when params["tools"] is populated. And InternalInstructor create his own instance of litellm to call the provider. Maybe the bug is here ?

### Additional context

X

## Comments

**hidai25:**
Glad this got fixed. I dug into the same root cause independently — InternalInstructor 
  short-circuiting when params had tools. This is a good example of a silent agent
  regression where the output looks fine but the tools never get called. Worth having a
  regression test that asserts tool forwarding stays intact across future releases.
