# [BUG] A2A client is not working in Jupyter Environments

**Issue #4671** | State: closed | Created: 2026-03-02 | Updated: 2026-03-03
**Author:** sunil37-aria
**Labels:** bug

### Description

RuntimeError                              Traceback (most recent call last)
Cell In[3], [line 28](vscode-notebook-cell:?execution_count=3&line=28)
     18 task = Task(
     19     description="Research the latest developments in quantum computing",
     20     expected_output="A comprehensive research report",
     21     agent=agent
     22 )
     24 crew = Crew(agents=[agent],
     25             tasks=[task],
     26 
     27             verbose=True)
---> [28](vscode-notebook-cell:?execution_count=3&line=28) result = crew.kickoff()

File ~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:743, in Crew.kickoff(self, inputs, input_files)
    740 inputs = prepare_kickoff(self, inputs, input_files)
    742 if self.process == Process.sequential:
--> [743](https://file+.vscode-resource.vscode-cdn.net/home/sunil/arias/aria-ip-ingest-iq-files/tests/~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:743)     result = self._run_sequential_process()
    744 elif self.process == Process.hierarchical:
    745     result = self._run_hierarchical_process()

File ~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:1150, in Crew._run_sequential_process(self)
   1148 def _run_sequential_process(self) -> CrewOutput:
   1149     """Executes tasks sequentially and returns the final output."""
-> [1150](https://file+.vscode-resource.vscode-cdn.net/home/sunil/arias/aria-ip-ingest-iq-files/tests/~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:1150)     return self._execute_tasks(self.tasks)
...
    206     )
    207 except RuntimeError as e:
    208     if "no running event loop" not in str(e).lower():

RuntimeError: execute_a2a_delegation() cannot be called from an async context. Use 'await aexecute_a2a_delegation()' instead.

### Steps to Reproduce
```python
from crewai import Agent, Crew, Task
from crewai.a2a import A2AClientConfig

agent = Agent(
    role="Research Coordinator",
    goal="Coordinate research tasks efficiently",
    backstory="Expert at delegating to specialized research agents",
    llm=llm,
    a2a=A2AClientConfig(
        endpoint="http://localhost:10001/.well-known/agent-card.json",
        timeout=120,
        max_turns=10,
        #trust_remote_completion_status=True

    ),
)

task = Task(
    description="Research the latest developments in quantum computing",
    expected_output="A comprehensive research report",
    agent=agent
)

crew = Crew(agents=[agent],
            tasks=[task],

            verbose=True)
result = crew.kickoff()
```
### Expected behavior

None

### Screenshots/Code snippets
```

╭─────────────────────────────────────────── 🚀 Crew Execution Started ───────────────────────────────────────────╮
│                                                                                                                 │
│  Crew Execution Started                                                                                         │
│  Name:                                                                                                          │
│  crew                                                                                                           │
│  ID:                                                                                                            │
│  c25e3f10-6e86-426d-9d19-2fd04eed9064                                                                           │
│                                                                                                                 │
│                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────── 📋 Task Started ────────────────────────────────────────────────╮
│                                                                                                                 │
│  Task Started                                                                                                   │
│  Name: Research the latest developments in quantum computing                                                    │
│  ID: 2f01754c-6488-49a1-baa9-05e85482ea0a                                                                       │
│                                                                                                                 │
│                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─────────────────────────────────────────────── 🤖 Agent Started ────────────────────────────────────────────────╮
│                                                                                                                 │
│  Agent: Research Coordinator                                                                                    │
│                                                                                                                 │
│  Task: Research the latest developments in quantum computing                                                    │
│                                                                                                                 │
│  IMPORTANT: You have the ability to delegate this task to remote A2A agents.                                    │
│                                                                                                                 │
│                                                                                           │
│                                                                                                                 │
│  {                                                                                                              │
│    "description": "A CrewAI-powered autonomous research agent capable of performing deep topic analysis and     │
│  generating structured research reports from natural language queries.",                                        │
│    "skills": [                                                                                                  │
│      {                                                                                                          │
│        "description": "Performs in-depth analytical research on scientific, technical, and business topics.     │
│  Produces structured research reports including insights, trends, risks, and future outlook.",                  │
│        "examples": [                                                                                            │
│          "Research latest developments in quantum computing",                                                   │
│          "Analyze AI impact on retail pricing",                                                                 │
│          "Create technology trend report",                                                                      │
│          "Provide research summary on LLM adoption"                                                             │
│        ],                                                                                                       │
│        "id": "deep_research",                                                                                   │
│        "name": "Deep Research Analyst",                                                                         │
│        "tags": [                                                                                                │
│          "research",                                                                                            │
│          "analysis",                                                                                            │
│          "technology",                                                                                          │
│          "ai",                                                                                                  │
│          "market research",                                                                                     │
│          "trend analysis",                                                                                      │
│          "quantum computing",                                                                                   │
│          "crewAI",                                                                                              │
│          "llm reasoning"                                                                                        │
│        ]                                                                                                        │
│      }                                                                                                          │
│    ],                                                                                                           │
│    "url": "http://0.0.0.0:10001/"                                                                               │
│  }                                                                                                              │
│                                                                                                                 │
│                                                                                          │
│                                                                                                                 │
│                                                                                                                 │
│                                                                                      │
│                                                                                                                 │
│                                                                                     │
│                                                                                                                 │
│                                                                                                                 │
│                                                                                                                 │
│                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────── ✅ Agent Final Answer ─────────────────────────────────────────────╮
│                                                                                                                 │
│  Agent: Research Coordinator                                                                                    │
│                                                                                                                 │
│  Final Answer:                                                                                                  │
│  a2a_ids=('http://localhost:10001/.well-known/agent-card.json',) message='Research the latest developments in   │
│  quantum computing' is_a2a=True                                                                                 │
│                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────── 📋 Task Failure ────────────────────────────────────────────────╮
│                                                                                                                 │
│  Task Failed                                                                                                    │
│  Name:                                                                                                          │
│  Research the latest developments in quantum computing                                                          │
│  Agent:                                                                                                         │
│  Research Coordinator                                                                                           │
│                                                                                                                 │
│                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────────── Crew Failure ──────────────────────────────────────────────────╮
│                                                                                                                 │
│  Crew Execution Failed                                                                                          │
│  Name:                                                                                                          │
│  crew                                                                                                           │
│  ID:                                                                                                            │
│  c25e3f10-6e86-426d-9d19-2fd04eed9064                                                                           │
│                                                                                                                 │
│                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
---------------------------------------------------------------------------
RuntimeError                              Traceback (most recent call last)
Cell In[3], [line 28](vscode-notebook-cell:?execution_count=3&line=28)
     18 task = Task(
     19     description="Research the latest developments in quantum computing",
     20     expected_output="A comprehensive research report",
     21     agent=agent
     22 )
     24 crew = Crew(agents=[agent],
     25             tasks=[task],
     26 
     27             verbose=True)
---> [28](vscode-notebook-cell:?execution_count=3&line=28) result = crew.kickoff()

File ~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:743, in Crew.kickoff(self, inputs, input_files)
    740 inputs = prepare_kickoff(self, inputs, input_files)
    742 if self.process == Process.sequential:
--> [743](https://file+.vscode-resource.vscode-cdn.net/home/sunil/arias/aria-ip-ingest-iq-files/tests/~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:743)     result = self._run_sequential_process()
    744 elif self.process == Process.hierarchical:
    745     result = self._run_hierarchical_process()

File ~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:1150, in Crew._run_sequential_process(self)
   1148 def _run_sequential_process(self) -> CrewOutput:
   1149     """Executes tasks sequentially and returns the final output."""
-> [1150](https://file+.vscode-resource.vscode-cdn.net/home/sunil/arias/aria-ip-ingest-iq-files/tests/~/miniconda3/envs/crewai_3.13/lib/python3.13/site-packages/crewai/crew.py:1150)     return self._execute_tasks(self.tasks)
...
    206     )
    207 except RuntimeError as e:
    208     if "no running event loop" not in str(e).lower():

RuntimeError: execute_a2a_delegation() cannot be called from an async context. Use 'await aexecute_a2a_delegation()
```
### Operating System

Ubuntu 22.04

### Python Version

3.12

### crewAI Version

1.9.3

### crewAI Tools Version

None

### Virtual Environment

Venv

### Evidence

None

### Possible Solution

None

### Additional context

None

## Comments

**greysonlalonde:**
Hi @sunil37-aria , are you running this from a Jupyter Notebook?

**sunil37-aria:**
Yes, Now i switched to .py file. now its working. 
Thanks

**greysonlalonde:**
> Yes, Now i switched to .py file. now its working. Thanks

Cool! I'll add support for Jupyter environments, but please use this workaround in the meantime.
