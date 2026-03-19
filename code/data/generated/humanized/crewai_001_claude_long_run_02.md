# Getting Started with CrewAI: Installation and First Project

A lot of multi-agent AI frameworks have popped up in the past year. CrewAI caught my attention because it was built from scratch as an independent Python framework, with no dependency on LangChain or other agent libraries. That matters. It means a leaner install, faster execution, and more direct control over what's happening under the hood. If you've been curious about multi-agent systems but haven't tried one yet, this post covers installing CrewAI, understanding its core abstractions, and building a working project.

## The Core Mental Model

Three building blocks make up everything in CrewAI: Agents, Tasks, and Crews. Worth understanding these before writing any code.

Think of an **Agent** as an autonomous unit with a defined role, goal, and backstory. Its role tells it what it specializes in (something like "Senior Data Researcher"); the goal describes what it should work toward; and the backstory gives it personality and context that shape how it reasons. Under the hood, each one runs on a language model (GPT-4 by default, though you can swap in Anthropic, Google, Ollama, or anything else through LiteLLM). You can also equip them with tools like web search, file reading, and code execution so they can do more than just generate text.

A **Task** tells an agent exactly what to do: here's the work, here's the expected output format, and optionally here are some tools that override the agent's defaults for that particular job. Through a context mechanism, one task can wait for another's output before starting. This makes it easy to chain research into analysis into report writing without manually passing data between steps.

A **Crew** ties agents and tasks together into a working unit. You pick an execution process (sequential, where tasks run in order, or hierarchical, where a manager agent delegates automatically) and kick the whole thing off; it handles orchestration, context passing, and result aggregation.

There's also a higher-level concept called **Flows** for production workflows, which give you event-driven, deterministic control over execution paths, state management, and conditional branching. You can embed a Crew inside a Flow as one step in a larger pipeline. For getting started though, Crews are the right entry point.

## Prerequisites and Installation

CrewAI requires Python 3.10 or newer (up through 3.13). The project recommends UV for dependency management, though pip works fine too.

The minimal install gets you the core framework:

```shell
pip install crewai
```

If you want the built-in tool suite (web search, file readers, RAG tools, code interpreter, and more), install the extras:

```shell
pip install 'crewai[tools]'
```

One dependency that occasionally trips people up is `tiktoken`, which requires a Rust compiler to build from source. If you hit a wheel-building error during installation, either install Rust via `rustup` or force a pre-built binary with `pip install tiktoken --prefer-binary`.

You'll also need at least one LLM API key. OpenAI is the default, so having an `OPENAI_API_KEY` environment variable set is the path of least resistance. CrewAI is genuinely model-agnostic though; you can point any agent at a different provider by setting the `llm` parameter to a model string like `anthropic/claude-3-sonnet` or even a local Ollama instance.

## Scaffolding a Project with the CLI

CrewAI ships with a CLI that generates a project skeleton. I'd recommend using it, because it sets up the YAML-based configuration pattern that keeps agent and task definitions cleanly separated from your Python logic.

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

During project creation, the CLI prompts you to choose an LLM provider and model, and it asks for your API key. These get stored in the `.env` file at the project root.

Four files do the real work. `agents.yaml` declares your agents' roles, goals, and backstories. `tasks.yaml` defines the work to be done, including which agent handles each task and what the expected output looks like. `crew.py` is where you wire everything together into a Crew object using Python. And `main.py` is the entry point that kicks off execution.

## Building Your First Crew: A Research Report Generator

Let's walk through a concrete example. Say you want a system that researches a topic and then writes a structured report. Two agents are needed (a researcher and a reporting analyst) along with two corresponding tasks.

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

Notice the `{topic}` placeholders. These get filled in at runtime when you call `kickoff(inputs={'topic': 'AI Agents'})`, which means you can reuse the same crew definition across different subjects without touching any configuration.

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

The `output_file` attribute on the reporting task tells CrewAI to write the final result to disk automatically. Useful when you want a persistent artifact at the end of a run.

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

The `@CrewBase` decorator and the `@agent`, `@task`, `@crew` annotations handle a lot of boilerplate. They automatically collect all decorated agents and tasks so you can reference `self.agents` and `self.tasks` without manually building lists. One thing the docs don't make obvious: the YAML keys must match the Python method names. So `researcher` in YAML corresponds to `def researcher(self)` in code.

Finally, `main.py` triggers execution:

```python
from my_research_crew.crew import MyResearchCrew

def run():
    inputs = {'topic': 'AI Agents'}
    MyResearchCrew().crew().kickoff(inputs=inputs)
```

Before running, make sure your `.env` file has the necessary keys (at minimum `OPENAI_API_KEY`, and `SERPER_API_KEY` if you're using the web search tool). Then from the project root:

```shell
crewai run
```

You should see verbose output in the terminal showing each agent reasoning through its task, and a `report.md` file will appear with the final write-up.

## Things That Will Bite You Early On

Once you've got a working crew, a few stumbling blocks tend to hit newcomers pretty quickly.

Token costs can add up fast. In sequential mode, the output of task one becomes context for task two. That's great for continuity, but it means later tasks process an ever-growing prompt. If your agents are verbose or produce long outputs, costs snowball. I'd recommend keeping `expected_output` descriptions specific and concise to guide agents toward tighter responses.

Debugging is harder than you'd expect. When a crew produces bad output, the instinct is to tweak the final agent's prompt. Often the real failure is upstream though: a research task that returned irrelevant results, or a tool that silently failed and produced a fallback response instead. Set `verbose=True` on both your agents and the crew so you can trace execution step by step. CrewAI also supports `output_log_file` on the Crew for persistent logs, which honestly I wish I'd discovered sooner.

Start sequential. Not hierarchical. The hierarchical process sounds appealing (a manager agent that delegates work intelligently), but it introduces an extra layer of LLM decision-making that can misroute tasks or create coordination overhead. Sequential execution is predictable and easy to debug. Switch to hierarchical only when dynamic delegation genuinely adds value, and even then, provide a good `manager_llm` or explicit `manager_agent` to guide things.

Watch your tool API keys. Built-in tools like `SerperDevTool` or `ScrapeWebsiteTool` require their own credentials, separate from your LLM key. Here's the frustrating part: a missing Serper key doesn't raise a clean error. The agent just "hallucinates" search results instead. That confused me for longer than I'd like to admit.

## Where to Go from Here

Once your first sequential crew runs reliably, there's quite a bit to explore.

Task dependencies with `context` let you explicitly declare that one task depends on another's output instead of relying on implicit sequential ordering. This gets especially useful when you have tasks that can run in parallel (`async_execution=True`) and then feed into a downstream task that synthesizes their results. From what I can tell, getting the dependency graph right takes some experimentation, but it's worth the effort for complex workflows.

Tasks also accept a `guardrail` parameter (either a Python function or a natural-language description) that validates output before passing it to the next step. If validation fails, the agent receives feedback and retries automatically up to a configurable limit. Great for ensuring structured output quality without manual review.

Building custom tools is pretty simple: subclass `BaseTool` or use the `@tool` decorator. If your workflow involves proprietary APIs, databases, or internal services, custom tools are how you plug them into agent workflows.

For conditional branching, state management across multiple crew invocations, or deterministic orchestration beyond what a single crew can handle, look into Flows. You decorate methods with `@start()`, `@listen()`, and `@router()` to create directed graphs of execution steps, some of which can themselves be full Crews.

CrewAI has a solid community and an active issue tracker, so real-world patterns and pitfalls are well documented by now. It isn't without rough edges; dependency conflicts with other packages surface occasionally, and the autonomous agent loop can still burn through tokens if prompts aren't carefully scoped. But for getting multi-agent systems off the ground quickly, it's one of the more approachable options I've found. Start small. Keep your agents focused. Iterate.
