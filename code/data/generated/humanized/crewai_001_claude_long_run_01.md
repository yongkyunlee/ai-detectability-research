# Getting Started with CrewAI: Installation and Your First Project

Multi-agent AI systems went from research curiosity to practical tooling fast. Like, surprisingly fast. Among the frameworks competing for developer attention, CrewAI has carved out a real position by being a standalone Python framework built from scratch, with no dependency on LangChain or other agent libraries. You can spin up teams of autonomous AI agents without much boilerplate. A pair of agents collaborating on a research report, an entire pipeline of specialists handling different stages of a business workflow: it gives you the scaffolding for all of that.

This post walks through installing it, creating your first project, and understanding the core abstractions well enough to start experimenting on your own.

## What CrewAI Actually Is

Think of it as a framework for orchestrating role-playing, autonomous AI agents. You define agents (each with a role, a goal, and a backstory), assign them tasks, and the framework handles the execution loop: routing prompts, managing tool calls, passing context between tasks, collecting outputs.

Two main architectural patterns exist here. **Crews** are teams of agents that collaborate autonomously, deciding how to accomplish tasks based on their roles and available tools. **Flows** give you event-driven, stateful workflows with explicit control over execution paths, conditional branching, and data movement. In practice, most production apps combine both: a Flow manages the high-level process while individual steps delegate work to Crews.

For a first project, though, Crews are all you need. Flows come later.

## Prerequisites

Two things need to be on your machine before you install.

**Python 3.10 through 3.13.** CrewAI doesn't support Python 3.14 yet. Check your version with `python3 --version` and grab an update from python.org if needed.

**uv, the Rust-based Python package manager.** CrewAI uses uv for dependency management rather than pip or poetry. If you haven't installed it yet, the quickest route on macOS or Linux is:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Once uv is on your PATH, you're good.

## Installing CrewAI

Install it as a CLI tool via uv:

```
uv tool install crewai
```

Verify by running `uv tool list`, which should show something like `crewai v0.102.0` (or whatever the current release is). To upgrade later:

```
uv tool install crewai --upgrade
```

If you see a PATH warning after installation, `uv tool update-shell` fixes it. On Windows you might hit a build error related to `chroma-hnswlib` if you don't have C++ build tools; installing Visual Studio Build Tools with the "Desktop development with C++" workload sorts that out.

### The Optional Tools Extra

There's a companion package called `crewai-tools` that bundles ready-made tools your agents can use: web search, file I/O, scraping, and more. To install with tools support:

```
uv pip install 'crewai[tools]'
```

You can skip this for now and add tools later, but many of the interesting examples (like having an agent search the web) require it.

## Scaffolding a New Project

CrewAI includes a CLI command that generates the entire project structure:

```
crewai create crew latest-ai-development
```

This produces:

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

The files that matter are `agents.yaml`, `tasks.yaml`, `crew.py`, and `main.py`. YAML defines your agents and tasks declaratively; the Python files wire everything together. API keys go in `.env`.

## Defining Agents

Open `src/latest_ai_development/config/agents.yaml`. This is where you describe each agent's personality and expertise. Here's a minimal two-agent setup, a researcher and a reporting analyst:

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

Notice the `{topic}` placeholders. They get interpolated at runtime from inputs you pass when kicking off the crew, which makes agent definitions reusable across different subjects.

Each agent has three required attributes. The **role** tells the LLM what kind of expert it is. The **goal** anchors decision-making around a specific objective, and the **backstory** provides personality and context that shapes how the agent approaches work. Honestly, getting these right matters more than you'd expect; they directly influence prompt construction and, by extension, output quality.

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

Tasks have a description, an expected output format, and an assigned agent. The `output_file` attribute on the reporting task tells CrewAI to write the final result to disk. One thing to watch: the keys in your YAML files (`researcher`, `research_task`) must match the corresponding method names in your Python code. The framework uses this naming convention to automatically link configs to code.

## Wiring It Up in Python

`crew.py` connects your YAML definitions to actual CrewAI objects:

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

`@CrewBase` does most of the heavy lifting. It automatically loads your YAML configs and populates `self.agents` and `self.tasks`. The other decorators (`@agent`, `@task`, `@crew`) register each method so the framework knows how to assemble everything.

The researcher gets a `SerperDevTool` for searching the web via the Serper API. The reporting analyst has no tools; it works purely from context passed by the previous task. The crew uses `Process.sequential`, meaning tasks execute in order, with each one's output flowing as context to the next.

`main.py` provides the entry point:

```python
from latest_ai_development.crew import LatestAiDevelopmentCrew

def run():
    inputs = {'topic': 'AI Agents'}
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
```

## Setting Up API Keys and Running

You need API keys in your `.env` file before running. At minimum, an OpenAI API key (or whichever LLM provider you choose) set as `OPENAI_API_KEY=sk-...`, and a Serper API key if your agents use web search: `SERPER_API_KEY=YOUR_KEY_HERE`.

CrewAI defaults to OpenAI's GPT-4 for the underlying LLM, but you can point agents at Anthropic, Google, or local models through Ollama by setting the `llm` attribute in your YAML config or in code. The `MODEL` environment variable provides a global default.

Install dependencies and run:

```
cd latest_ai_development
crewai install
crewai run
```

You should see verbose output in your terminal as each agent works through its task. When the crew finishes, `report.md` appears in your project directory.

## Sequential vs. Hierarchical Execution

The example above uses sequential processing, where tasks run in the order you list them. But there's also a hierarchical process that introduces a manager agent. This manager dynamically assigns tasks to workers based on their capabilities:

```python
crew = Crew(
    agents=my_agents,
    tasks=my_tasks,
    process=Process.hierarchical,
    manager_llm="gpt-4o"
)
```

In hierarchical mode, you don't need to pre-assign agents to tasks; the manager handles delegation. This can be useful when the best assignment depends on runtime conditions, but it adds another layer of LLM calls and, from what I can tell, it's noticeably harder to debug.

## Practical Advice

Start simple. A two-agent sequential crew is enough to learn the framework's conventions; add complexity (more agents, tools, hierarchical processes, Flows) incrementally.

Keep an eye on token spend. Multi-agent systems can burn through API credits fast, especially when agents pass large context between tasks or retry failed tool calls. I'd keep `verbose=True` on while developing so you can actually see what each agent is doing.

Naming consistency trips people up. If your YAML keys don't match your Python method names, CrewAI won't link agents to tasks. This is probably the most common source of confusion for newcomers.

Treat your agent definitions like prompts, because that's what they are. The role, goal, and backstory fields get injected into the system prompt. Spending time on clear, specific descriptions pays off in output quality; vague backstories produce vague results.

And don't be afraid to step back from full autonomy. Community experience suggests that fully autonomous multi-agent setups can be unpredictable for production workloads. If agents loop or produce inconsistent results, consider tighter task descriptions, fewer agents, or switching to a Flow-based architecture where you control each step yourself. I think a lot of people try to go too autonomous too early.

The docs are solid and there's an active issue tracker if you get stuck. For moving beyond basic LLM calls into coordinated multi-agent workflows, it's a good starting point.
