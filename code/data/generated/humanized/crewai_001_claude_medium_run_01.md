# Getting Started with CrewAI: Installation and First Project

Multi-agent AI systems went from research curiosity to practical tooling faster than most of us expected. CrewAI has carved out a real niche among the frameworks competing for developer attention: it gives you a structured way to define teams of autonomous AI agents, assign them tasks, and let them collaborate toward a shared goal. If you've been curious about orchestrating multiple LLM-powered agents but found other frameworks too heavyweight or too tightly coupled to existing ecosystems, it's worth a serious look.

This post walks through installation, project scaffolding, and building your first functional crew from scratch.

## Prerequisites

You'll need Python 3.10 or newer (up through 3.13). CrewAI leans on UV, the fast Rust-based Python package manager from Astral, for dependency management. If you haven't installed UV yet, grab it first; it'll make the whole workflow smoother. You also need an API key for whichever LLM provider you plan to use. By default, CrewAI talks to OpenAI, but you can swap in Anthropic, Google Gemini, Groq, or even local models through Ollama via the LiteLLM integration layer.

## Installing CrewAI

The core installation is a single command:

```bash
uv pip install crewai
```

If you want the extra agent tools (web search, file reading, directory traversal, and more), install the tools bundle:

```bash
uv pip install 'crewai[tools]'
```

One dependency that occasionally trips people up is `tiktoken`, which requires a Rust compiler to build from source. If the install fails at that step, try `uv pip install tiktoken --prefer-binary` to pull a prebuilt wheel instead.

## Scaffolding a New Project

CrewAI ships with a CLI that generates a well-organized project skeleton. Run:

```bash
crewai create crew latest-ai-development
```

This produces a directory structure that separates configuration from logic:

```
latest-ai-development/
├── pyproject.toml
├── .env
└── src/
    └── latest_ai_development/
        ├── main.py
        ├── crew.py
        ├── tools/
        │   └── custom_tool.py
        └── config/
            ├── agents.yaml
            └── tasks.yaml
```

The YAML files are where you define your agents and tasks declaratively. Python files wire everything together. This separation matters because it keeps prompt engineering and role definitions out of your application logic, which becomes increasingly valuable as a project grows.

## Defining Agents

Agents in CrewAI are autonomous units with three core attributes: a role, a goal, and a backstory. The role establishes what the agent does. The goal drives its decision-making, and the backstory provides context that shapes how the LLM interprets instructions.

Open `config/agents.yaml` and define two agents:

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

Those `{topic}` placeholders get filled in at runtime when you kick off the crew, which makes the same definitions reusable across different subjects.

## Defining Tasks

Tasks represent the actual work each agent will perform. In `config/tasks.yaml`:

```yaml
research_task:
  description: >
    Conduct a thorough research about {topic}.
    Make sure you find any interesting and relevant information given
    the current year is 2025.
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

Two things to note here. The `agent` field links each task to whoever's responsible for it. And the `output_file` on the reporting task tells CrewAI to write the final result to disk automatically. In a sequential process, output from the research task feeds directly into the reporting task as context, so no explicit wiring is needed.

## Connecting It All in Python

In `crew.py`, you create a class decorated with `@CrewBase` that maps the YAML definitions to Python objects:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class LatestAiDevelopmentCrew():
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

The `@agent` and `@task` decorators automatically collect instances into `self.agents` and `self.tasks`, so you don't need to manually assemble lists. Method names must match the keys in your YAML files: `researcher` in the code maps to `researcher` in `agents.yaml`.

## Running the Crew

Before running, add your API keys to the `.env` file:

```
OPENAI_API_KEY=sk-...
SERPER_API_KEY=your_serper_key_here
```

Then from the project root:

```bash
crewai run
```

You'll see verbose output as the researcher agent queries the web, synthesizes findings, and passes its results to the reporting analyst. The final markdown report lands in `report.md`.

## Sequential vs. Hierarchical Execution

The example above uses `Process.sequential`, where tasks execute in the order they're defined. CrewAI also supports `Process.hierarchical`, which introduces a manager agent that delegates tasks to crew members based on their capabilities. The hierarchical approach requires specifying a `manager_llm` and works well when you want the system to figure out task assignment on the fly rather than following a fixed pipeline.

## Practical Advice for Beginners

Start with sequential execution and two or three agents. More agents or hierarchical mode means more LLM calls, which both increases cost and widens the surface area for unexpected behavior. Enable `verbose=True` during development so you can watch exactly what each agent is doing; honestly, observability is the difference between debugging productively and staring at a black box.

Watch your token spend. Agents in a sequential crew pass their full output as context to the next task, and that context accumulates fast. For longer workflows, consider breaking the pipeline into smaller crews or using the `context` parameter on tasks to explicitly control which outputs feed into which steps.

The YAML-based configuration isn't just a convenience, I think it's a forcing function for clean separation of concerns. Resist the temptation to define everything inline in Python. Keeping role definitions, task descriptions, and orchestration logic in separate layers pays off the moment you need to iterate on prompts without touching application code.

CrewAI won't magically solve every orchestration problem, but it gives you a sensible starting point with minimal boilerplate. Get a basic crew running, watch the logs, and iterate from there.
