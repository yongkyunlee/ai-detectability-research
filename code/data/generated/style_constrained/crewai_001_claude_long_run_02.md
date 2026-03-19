# Getting Started with CrewAI: Installation and First Project

Multi-agent frameworks are multiplying fast. CrewAI is one of the more opinionated entries in the space, and it's worth understanding what it actually offers before you commit your architecture to it. I've spent time with the documentation, the source, and the community discussions. Here's what you need to know to go from zero to a running crew.

## What CrewAI Actually Is

CrewAI is a Python framework for orchestrating autonomous AI agents. It's built from scratch, fully independent of LangChain or any other agent framework. That independence matters. It means fewer transitive dependency conflicts, a smaller surface area to debug, and a runtime that isn't secretly routing through three abstraction layers you didn't ask for.

The framework is organized around two core concepts. **Crews** are teams of agents that collaborate on tasks with genuine autonomy, deciding how to delegate and divide work. **Flows** are event-driven workflows that give you precise, programmatic control over execution order, branching, and state. The recommended production pattern is to wrap your Crews inside Flows, giving you both the flexibility of autonomous agents and the predictability of a state machine. We'll stick to Crews for this getting-started walkthrough since that's the natural entry point.

CrewAI requires Python >=3.10 and <3.14. It uses `uv` from Astral for dependency management, which is a deliberate choice over pip or poetry. If you're already using `uv` in your projects, this will feel seamless. If not, you'll need to install it first.

## Installation

The install process has two steps: get `uv`, then get `crewai`.

On macOS or Linux, install `uv` with:


curl -LsSf https://astral.sh/uv/install.sh | sh


On Windows, use PowerShell:


powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"


Then install the CrewAI CLI itself:


uv tool install crewai


If you get a PATH warning after this, run `uv tool update-shell` to fix it. Verify the install with `uv tool list`, and you should see something like `crewai v0.102.0` in the output.

There's a choice to make here about extras. The base `crewai` package gives you the agent framework, but if you want the bundled tool library (web search, file reading, and so on), you need:


uv pip install 'crewai[tools]'


This pulls in `crewai-tools`, currently at version 1.11.0. The tools extra is simpler to start with, but it adds significant dependencies. If you only need one or two tools, you might prefer to write thin wrappers yourself and keep your dependency tree lean. The YAML-based scaffolding approach (which we'll use below) is simpler, but you trade that simplicity for less visibility into what's happening under the hood. That's a reasonable trade-off for getting started quickly, though production users on the CrewAI subreddit and HN threads consistently report that they eventually want more control over the agent-to-LLM boundary.

## Scaffolding Your First Project

CrewAI ships a CLI that generates project boilerplate. Run:


crewai create crew latest-ai-development


This creates a directory with the following structure:


latest-ai-development/
├── .gitignore
├── knowledge/
├── pyproject.toml
├── README.md
├── .env
└── src/
    └── latest_ai_development/
        ├── __init__.py
        ├── main.py
        ├── crew.py
        ├── tools/
        │   ├── custom_tool.py
        │   └── __init__.py
        └── config/
            ├── agents.yaml
            └── tasks.yaml


Six files matter. `agents.yaml` defines your agents' roles, goals, and backstories. `tasks.yaml` defines what those agents should do. `crew.py` wires agents and tasks together into a Crew object. `main.py` is the entry point. `.env` holds your API keys. And `knowledge/` is an empty directory where you can drop files for the agents to reference.

The YAML configuration approach is what the CrewAI team recommends. It separates your agent personality definitions from your Python logic. There's an important constraint here: the method names in `crew.py` must match the keys in your YAML files exactly. If your YAML defines an agent called `researcher`, the corresponding Python method must also be called `researcher`. CrewAI uses this naming convention to automatically link configurations to code. Get this wrong and your tasks won't find their agents.

## Defining Agents and Tasks

Open `src/latest_ai_development/config/agents.yaml` and define two agents:


researcher:
  role: >
    {topic} Senior Data Researcher
  goal: >
    Uncover cutting-edge developments in {topic}
  backstory: >
    You're a seasoned researcher with a knack for uncovering the latest
    developments in {topic}. Known for your ability to find the most relevant
    information and present it in a clear and concise manner.

reporting_analyst:
  role: >
    {topic} Reporting Analyst
  goal: >
    Create detailed reports based on {topic} data analysis and research findings
  backstory: >
    You're a meticulous analyst with a keen eye for detail. You're known for
    your ability to turn complex data into clear and concise reports, making
    it easy for others to understand and act on the information you provide.


The `{topic}` placeholders get interpolated at runtime from the inputs dictionary you pass in `main.py`. This is a nice touch. It means you can reuse the same crew definition across different domains without modifying the YAML.

Now define the tasks in `src/latest_ai_development/config/tasks.yaml`:


research_task:
  description: >
    Conduct a thorough research about {topic}
    Make sure you find any interesting and relevant information given
    the current year is 2025.
  expected_output: >
    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher

reporting_task:
  description: >
    Review the context you got and expand each topic into a full section for a report.
    Make sure the report is detailed and contains any and all relevant information.
  expected_output: >
    A fully fledge reports with the mains topics, each with a full section of information.
    Formatted as markdown without ''
  agent: reporting_analyst
  output_file: report.md


Each task specifies its assigned agent by name, a description of the work, and what the output should look like. The `output_file` field on the reporting task tells CrewAI to write the final result to disk. Tasks in a sequential process run in order, and the output of one task automatically becomes context for the next. So the reporting_analyst receives the researcher's findings without you having to wire that up manually.

## Wiring It Together in Python

The `crew.py` file connects your YAML definitions to actual CrewAI objects:


from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class LatestAiDevelopmentCrew():
    """LatestAiDevelopment crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


The `@CrewBase` decorator handles the heavy lifting. It automatically reads your YAML configs and populates `self.agents_config` and `self.tasks_config`. The `@agent` and `@task` decorators register methods so that `self.agents` and `self.tasks` are populated without explicit list construction.

The researcher agent gets a `SerperDevTool()`, which lets it search the web via the Serper API. The reporting_analyst gets no tools because its job is synthesis, not research. This is a sensible default pattern.

And `main.py` is dead simple:


import sys
from latest_ai_development.crew import LatestAiDevelopmentCrew

def run():
    inputs = {
        'topic': 'AI Agents'
    }
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)


## Running It

Before you run anything, set up your `.env` file with the necessary API keys. By default, CrewAI agents use OpenAI's models (defaulting to gpt-4 if `OPENAI_MODEL_NAME` isn't set). You'll also need a Serper API key for the web search tool:


OPENAI_API_KEY=sk-...
SERPER_API_KEY=YOUR_KEY_HERE


Navigate to the project directory and install dependencies:


cd latest_ai_development
crewai install


Then run:


crewai run


The crew will execute. With `verbose=True`, you'll see each agent's reasoning, tool calls, and outputs streamed to the terminal. The final report lands in `report.md` at the root of your project.

## Things You'll Hit Quickly

CrewAI has two process modes: sequential and hierarchical. Sequential is what we used above. Tasks run in order. Hierarchical introduces a manager agent that delegates tasks to worker agents dynamically, which requires you to set a `manager_llm` on the Crew. Sequential is straightforward and predictable. Hierarchical gives you more flexibility at the cost of higher token spend and less deterministic behavior. For a first project, stick with sequential.

Token costs deserve attention. Community discussions consistently flag this as a pain point. When agents operate autonomously, they can re-summarize the same information multiple times or loop on tool calls that fail. The `max_iter` parameter on agents (defaulting to 20) caps how many iterations an agent will attempt before giving its best answer. Setting this lower can save you money during development.

One known issue worth being aware of: if you reuse the same Agent object across multiple sequential tasks or Crew executions, the agent executor can accumulate messages from prior runs. This was filed as issue #4319. The messages pile up, the context window fills, and eventually you get a `ValueError: Invalid response from LLM call - None or empty`. The workaround is to create fresh agent instances for each crew, or wait for a fix in the executor's `_update_executor_parameters` method.

Verbose logging can also be noisy. Even with `verbose=False` set on agents, crews, and flows, some users on version 1.9.2 reported that Flow-level log output (the decorative box-drawing characters showing method status) still appeared. If you're embedding CrewAI in a larger application and need clean logs, be prepared to work around this.

## Where To Go Next

Once you're comfortable with a basic sequential crew, the natural next step is Flows. Flows let you define event-driven execution graphs with `@start`, `@listen`, and `@router` decorators, manage typed state with Pydantic models, and compose multiple crews into a larger pipeline with conditional branching. They're the production architecture the CrewAI team recommends for anything beyond prototyping.

You can also swap out OpenAI for other providers. CrewAI supports Anthropic, AWS Bedrock, Google Gemini, Ollama for local models, and others. The `LLM` class wraps these providers, and you can assign different models to different agents within the same crew.

CrewAI isn't without friction. The dependency tree is substantial, the abstraction layer can obscure what prompts actually reach the LLM, and observability in the open-source version is limited compared to what you get with the paid Crew Control Plane. But the scaffolding is solid, the YAML configuration keeps agent definitions readable, and the sequential crew pattern genuinely works for structured research-and-report workflows. For a team that wants to get a multi-agent prototype running in an afternoon, it's a reasonable starting point.
