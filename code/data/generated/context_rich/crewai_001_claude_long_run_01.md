# Getting Started with CrewAI: Installation and Your First Project

Multi-agent AI systems have moved from research curiosity to practical tooling in a remarkably short time. Among the frameworks vying for developer attention, CrewAI has carved out a distinct position by offering a standalone Python framework—built from scratch, with no dependency on LangChain or other agent libraries—that lets you spin up teams of autonomous AI agents with relatively little boilerplate. Whether you want a pair of agents collaborating on a research report or an entire pipeline of specialists handling different stages of a business workflow, CrewAI provides the scaffolding to make it happen.

This post walks through installing CrewAI, creating your first project, and understanding the core abstractions well enough to start experimenting on your own.

## What CrewAI Actually Is

At its core, CrewAI is a framework for orchestrating role-playing, autonomous AI agents. You define agents—each with a role, a goal, and a backstory—and assign them tasks. The framework handles the execution loop: routing prompts, managing tool calls, passing context between tasks, and collecting outputs.

There are two main architectural patterns in CrewAI. **Crews** are teams of agents that collaborate autonomously, making decisions about how to accomplish tasks based on their defined roles and available tools. **Flows** provide event-driven, stateful workflows with explicit control over execution paths, conditional branching, and data movement. In practice, most production applications combine both: a Flow manages the high-level process, and individual steps delegate complex work to Crews.

For a first project, though, you only need to understand Crews. Flows are something you layer on once your use case demands more precise orchestration.

## Prerequisites

Before installing CrewAI, you need two things on your machine:

**Python 3.10 through 3.13.** CrewAI does not yet support Python 3.14. Check your version with `python3 --version` and grab an update from python.org if needed.

**uv, the Rust-based Python package manager.** CrewAI uses uv for dependency management rather than pip or poetry. If you have not installed uv yet, the quickest route on macOS or Linux is:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, the equivalent PowerShell command is:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Once uv is available on your PATH, you are ready to install CrewAI itself.

## Installing CrewAI

The recommended approach is to install CrewAI as a CLI tool via uv:

```
uv tool install crewai
```

You can verify the installation worked by running `uv tool list`, which should show something like `crewai v0.102.0` (or whatever the current release is).

If you later need to upgrade:

```
uv tool install crewai --upgrade
```

One thing worth noting: if you see a PATH warning after installation, run `uv tool update-shell` to fix it. On Windows, you might also encounter a build error related to `chroma-hnswlib` if you lack C++ build tools—installing Visual Studio Build Tools with the "Desktop development with C++" workload resolves that.

### The Optional Tools Extra

CrewAI ships a companion package called `crewai-tools` that bundles ready-made tools your agents can use—web search, file I/O, scraping, and more. To install the core library with tools support:

```
uv pip install 'crewai[tools]'
```

For a first project you can skip this and add tools later, but many of the interesting examples (like having an agent search the web) require it.

## Scaffolding a New Project

CrewAI includes a CLI command that generates the entire project structure for you:

```
crewai create crew latest-ai-development
```

This produces a directory layout like:

```
latest_ai_development/
├── .gitignore
├── pyproject.toml
├── README.md
├── .env
├── knowledge/
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
```

The key files are `agents.yaml`, `tasks.yaml`, `crew.py`, and `main.py`. The YAML files define your agents and tasks declaratively; the Python files wire everything together. The `.env` file is where you put API keys.

## Defining Agents

Open `src/latest_ai_development/config/agents.yaml`. This is where you describe each agent's personality and expertise. Here is a minimal two-agent setup—a researcher and a reporting analyst:

```yaml
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
```

Notice the `{topic}` placeholders. These get interpolated at runtime from inputs you pass when kicking off the crew, which makes your agent definitions reusable across different subjects.

Each agent has three required attributes. The **role** tells the LLM what kind of expert it is. The **goal** anchors the agent's decision-making around a specific objective. The **backstory** provides additional personality and context that shapes how the agent approaches its work. Getting these right matters more than you might expect—they directly influence prompt construction and, consequently, output quality.

## Defining Tasks

Next, open `src/latest_ai_development/config/tasks.yaml`:

```yaml
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
    A fully fledged report with the main topics, each with a full section of information.
    Formatted as markdown.
  agent: reporting_analyst
  output_file: report.md
```

Tasks have a description, an expected output format, and an assigned agent. The `output_file` attribute on the reporting task tells CrewAI to write the final result to disk. One important naming convention: the keys in your YAML files (`researcher`, `research_task`) must match the corresponding method names in your Python code. CrewAI uses this naming to automatically link configurations to code.

## Wiring It Up in Python

The `crew.py` file connects your YAML definitions to actual CrewAI objects:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class LatestAiDevelopmentCrew():
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
        return Task(config=self.tasks_config['research_task'])

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

The `@CrewBase` decorator does most of the heavy lifting, automatically loading your YAML configs and populating `self.agents` and `self.tasks`. The `@agent`, `@task`, and `@crew` decorators register each method so the framework knows how to assemble everything.

The researcher agent gets a `SerperDevTool`, which lets it search the web via the Serper API. The reporting analyst has no tools—it works purely from the context passed to it by the previous task. The crew itself uses `Process.sequential`, meaning tasks execute in order, with each task's output flowing as context to the next.

Finally, `main.py` provides the entry point:

```python
from latest_ai_development.crew import LatestAiDevelopmentCrew

def run():
    inputs = {'topic': 'AI Agents'}
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
```

## Setting Up API Keys and Running

Before running, you need API keys in your `.env` file. At minimum:

- An OpenAI API key (or whichever LLM provider you choose): `OPENAI_API_KEY=sk-...`
- A Serper API key if your agents use web search: `SERPER_API_KEY=YOUR_KEY_HERE`

CrewAI defaults to OpenAI's GPT-4 for the underlying LLM, but you can point agents at Anthropic, Google, or local models through Ollama by setting the `llm` attribute in your YAML config or in code. The `MODEL` environment variable provides a global default.

Now install dependencies and run:

```
cd latest_ai_development
crewai install
crewai run
```

You should see verbose output in your terminal as each agent works through its task. When the crew finishes, a `report.md` file appears in your project directory with the final output.

## Sequential vs. Hierarchical Execution

The example above uses sequential processing, where tasks execute in the order you list them. CrewAI also supports a hierarchical process, which introduces a manager agent that dynamically assigns tasks to workers based on their capabilities. To use it, specify `Process.hierarchical` and provide a `manager_llm`:

```python
crew = Crew(
    agents=my_agents,
    tasks=my_tasks,
    process=Process.hierarchical,
    manager_llm="gpt-4o"
)
```

In hierarchical mode, you do not need to pre-assign agents to tasks—the manager handles delegation. This is useful when the optimal assignment depends on runtime conditions, but it introduces another layer of LLM calls and can be harder to debug.

## Practical Advice for Getting Started

**Start simple.** A two-agent sequential crew is enough to learn the framework's conventions. Add complexity—more agents, tools, hierarchical processes, Flows—incrementally.

**Watch your token spend.** Multi-agent systems can burn through API credits fast, especially when agents pass large context between tasks or retry failed tool calls. Enable `verbose=True` while developing so you can see exactly what each agent is doing.

**Naming consistency matters.** If your YAML keys do not match your Python method names, CrewAI will fail to link agents to tasks. This is a common source of confusion for newcomers.

**Treat agent definitions like prompts.** The role, goal, and backstory fields are not cosmetic—they are injected into the system prompt. Investing time in clear, specific descriptions pays off in output quality. Vague backstories produce vague results.

**Know when to step down from full autonomy.** Community experience suggests that fully autonomous multi-agent setups can be unpredictable for production workloads. If you find agents looping or producing inconsistent results, consider tighter task descriptions, fewer agents, or switching to a Flow-based architecture where you control each step explicitly.

CrewAI has a growing community, solid documentation, and an active issue tracker if you get stuck. The framework strikes a practical balance between the simplicity of a single-prompt approach and the flexibility of a full agent orchestration system. For anyone looking to move beyond basic LLM calls into coordinated multi-agent workflows, it is a strong place to start.
