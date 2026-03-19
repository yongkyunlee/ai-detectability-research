# Getting Started with CrewAI: Installation and First Project

The multi-agent AI space has exploded with frameworks over the past year, each promising to let you coordinate teams of LLM-powered agents that divide and conquer complex work. CrewAI stands out in this crowded field for a specific architectural choice: it was built from scratch as an independent Python framework, free from dependencies on LangChain or other agent libraries. That independence gives it a leaner footprint, faster execution, and more direct control over what happens under the hood. If you have been eyeing multi-agent systems but haven't taken the plunge yet, this post walks you through installing CrewAI, understanding its core abstractions, and building a working project from the ground up.

## The Core Mental Model

Before touching any code, it helps to understand the three building blocks that everything in CrewAI revolves around: Agents, Tasks, and Crews.

An **Agent** is an autonomous unit with a defined role, goal, and backstory. The role tells the agent what it specializes in ("Senior Data Researcher," for example). The goal describes what it should optimize for. The backstory provides personality and context that shape how the agent reasons and communicates. Under the hood, each agent is powered by a language model — GPT-4 by default, though you can swap in Anthropic, Google, Ollama, or anything else supported through LiteLLM. Agents can also be equipped with tools (web search, file reading, code execution) that extend what they can actually do beyond pure text generation.

A **Task** is a specific assignment given to an agent. It has a description of the work, an expected output format, and an optional set of tools that override the agent's defaults for that particular job. Tasks can depend on each other through a context mechanism — you can tell one task to wait for another's output before it starts. This makes it straightforward to chain research into analysis into report writing without manually threading data between steps.

A **Crew** ties agents and tasks together into a working unit. You choose an execution process — sequential (tasks run one after another in order) or hierarchical (a manager agent delegates and coordinates automatically) — and then kick the whole thing off. The crew handles orchestration, context passing, and result aggregation.

There is also a higher-level concept called **Flows** for production workflows. Flows give you event-driven, deterministic control over execution paths, state management, and conditional branching. You can embed a Crew inside a Flow as one step in a larger pipeline. But for getting started, Crews are the place to begin.

## Prerequisites and Installation

CrewAI requires Python 3.10 or newer (up through 3.13). The project recommends UV for dependency management, though pip works fine too.

The minimal install gets you the core framework:

```shell
pip install crewai
```

If you want the built-in tool suite — web search, file readers, RAG tools, code interpreter, and more — install the extras:

```shell
pip install 'crewai[tools]'
```

One dependency that occasionally trips people up is `tiktoken`, which requires a Rust compiler to build from source. If you hit a wheel-building error during installation, either install Rust (via `rustup`) or force a pre-built binary with `pip install tiktoken --prefer-binary`.

You will also need at least one LLM API key. OpenAI is the default, so having an `OPENAI_API_KEY` environment variable set is the path of least resistance for a first project. But CrewAI is genuinely model-agnostic — you can point any agent at a different provider by setting the `llm` parameter to a model string like `anthropic/claude-3-sonnet` or even a local Ollama instance.

## Scaffolding a Project with the CLI

CrewAI ships with a command-line interface that generates a project skeleton for you. This is the recommended way to start, because it establishes the YAML-based configuration pattern that keeps agent and task definitions cleanly separated from your Python logic.

```shell
crewai create crew my_research_crew
```

This produces a directory structure like:

```
my_research_crew/
├── pyproject.toml
├── .env
├── README.md
└── src/
    └── my_research_crew/
        ├── __init__.py
        ├── main.py
        ├── crew.py
        ├── config/
        │   ├── agents.yaml
        │   └── tasks.yaml
        └── tools/
            ├── __init__.py
            └── custom_tool.py
```

The CLI also prompts you to choose an LLM provider and model during project creation, and it will ask for your API key. These get stored in the `.env` file at the project root.

Four files do the real work here. `agents.yaml` declares your agents' roles, goals, and backstories. `tasks.yaml` defines the work to be done, including which agent handles each task and what the expected output looks like. `crew.py` is where you wire agents and tasks together into a Crew object using Python. And `main.py` is the entry point that kicks off execution.

## Building Your First Crew: A Research Report Generator

Let's walk through a concrete example. Say you want a system that researches a given topic and then writes up a structured report. You need two agents — a researcher and a reporting analyst — and two corresponding tasks.

Start by editing `agents.yaml`:

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

Notice the `{topic}` placeholders. These get filled in at runtime when you call `kickoff(inputs={'topic': 'AI Agents'})`, which means you can reuse the same crew definition across different subjects without changing any configuration.

Next, configure `tasks.yaml`:

```yaml
research_task:
  description: >
    Conduct a thorough research about {topic}.
    Make sure you find any interesting and relevant information given
    the current year is 2026.
  expected_output: >
    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher

reporting_task:
  description: >
    Review the context you got and expand each topic into a full section
    for a report. Make sure the report is detailed and contains any and
    all relevant information.
  expected_output: >
    A fully fledged report with the main topics, each with a full section
    of information. Formatted as markdown.
  agent: reporting_analyst
  output_file: report.md
```

The `output_file` attribute on the reporting task tells CrewAI to write the final result to disk automatically — useful when you want a persistent artifact at the end of a run.

Now wire it all together in `crew.py`:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class MyResearchCrew():
    """Research and reporting crew"""

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
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

The `@CrewBase` decorator and the `@agent`, `@task`, `@crew` annotations handle a lot of boilerplate. They automatically collect all decorated agents and tasks so you can just reference `self.agents` and `self.tasks` without manually building lists. The YAML method names must match the Python method names — `researcher` in YAML corresponds to `def researcher(self)` in code.

Finally, `main.py` triggers execution:

```python
from my_research_crew.crew import MyResearchCrew

def run():
    inputs = {'topic': 'AI Agents'}
    MyResearchCrew().crew().kickoff(inputs=inputs)
```

Before running, make sure your `.env` file has the necessary keys — at minimum `OPENAI_API_KEY`, and `SERPER_API_KEY` if you are using the web search tool. Then from the project root:

```shell
crewai run
```

You should see verbose output in the terminal showing each agent reasoning through its task, and a `report.md` file will appear with the final write-up.

## Things That Will Bite You Early On

Having built a working crew, it is worth calling out a few stumbling blocks that hit newcomers regularly.

**Token costs can escalate fast.** When agents operate in sequential mode, the output of task one becomes context for task two. This is powerful for continuity, but it also means later tasks process an ever-growing prompt. If your agents are verbose or your tasks produce long outputs, costs add up. Keep `expected_output` descriptions specific and concise to guide agents toward tighter responses.

**Debugging requires observability.** When a crew produces bad output, the instinct is to tweak the final agent's prompt. But the real failure is often upstream — a research task that returned irrelevant results, or a tool that silently failed and produced a fallback response. Set `verbose=True` on both your agents and your crew so you can trace execution step by step. CrewAI also supports `output_log_file` on the Crew for persistent logs.

**Start sequential, not hierarchical.** The hierarchical process sounds appealing — a manager agent that delegates work intelligently. But it introduces an extra layer of LLM decision-making that can misroute tasks or produce coordination overhead. Sequential execution is predictable and debuggable. Switch to hierarchical only when you have tasks where dynamic delegation genuinely adds value, and even then, provide a good `manager_llm` or explicit `manager_agent` to guide the coordination.

**Tools need API keys.** Built-in tools like `SerperDevTool` (web search) or `ScrapeWebsiteTool` require their own API credentials, separate from your LLM key. Read the error messages carefully — a missing Serper key manifests as the agent "hallucinating" search results rather than raising a clean error, which can be confusing.

## Where to Go from Here

Once your first sequential crew is running reliably, several directions open up.

**Task dependencies with `context`.** Instead of relying on implicit sequential ordering, you can explicitly declare that one task depends on the output of another. This is especially useful when you have tasks that can run in parallel (`async_execution=True`) and then feed into a downstream task that synthesizes their results.

**Guardrails for output validation.** Tasks accept a `guardrail` parameter — either a Python function or a natural-language description — that validates the agent's output before passing it to the next step. If validation fails, the agent gets feedback and retries automatically (up to a configurable limit). This is invaluable for ensuring structured output quality without manual review.

**Custom tools.** CrewAI makes it straightforward to build your own tools by subclassing `BaseTool` or using the `@tool` decorator. If your workflow involves proprietary APIs, databases, or internal services, custom tools are how you integrate them into agent workflows.

**Flows for production.** When you need conditional branching, state management across multiple crew invocations, or deterministic orchestration that goes beyond what a single crew can handle, Flows provide the event-driven architecture to build production-grade pipelines. You decorate methods with `@start()`, `@listen()`, and `@router()` to create directed graphs of execution steps — some of which can be full Crews.

CrewAI has accumulated a substantial community and an active issue tracker, which means real-world patterns and pitfalls are well documented. The framework is not without rough edges — dependency conflicts with other packages surface occasionally, and the autonomous agent loop can still burn through tokens if prompts are not carefully scoped. But for getting a multi-agent system off the ground quickly, the combination of a clean CLI scaffold, YAML-driven configuration, and a thoughtful abstraction layer makes CrewAI one of the more approachable options available today. Start small, keep your agents focused, and iterate from there.
