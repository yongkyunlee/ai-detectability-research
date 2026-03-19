# Getting Started with CrewAI: Installation and First Project

Multi-agent AI systems aren't just research papers anymore. CrewAI is a standalone Python framework (no LangChain dependency) that gives you a structured way to coordinate multiple AI agents around shared goals. Research, analysis, content generation: you define the agents and tasks, and the framework handles orchestration so you don't have to write it from scratch.

This guide covers installing CrewAI, creating your first project, and understanding the core abstractions.

## Prerequisites

First, check your Python version. CrewAI needs Python 3.10 or higher, but below 3.14.

```bash
python3 --version
```

If you're outside that range, grab a compatible version from the official Python downloads page. You'll also need `uv`, a fast dependency management tool from Astral that CrewAI adopted as its standard package handler. If you don't have it, one command on macOS or Linux gets you there:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows users can install it through PowerShell instead. Once `uv` is on your PATH, you're good.

## Installing the CLI

CrewAI ships as a CLI tool that manages project creation, dependency locking, and execution. Install it globally:

```bash
uv tool install crewai
```

Verify by running `uv tool list`; you should see `crewai` with its version number in the output. If the shell can't find the command, run `uv tool update-shell` to refresh your PATH.

One thing to know upfront: CrewAI also requires `openai >= 1.13.3` as a runtime dependency because it defaults to OpenAI models for agent reasoning. You don't *have* to use OpenAI (the framework supports Anthropic, local models via Ollama, and other providers), but the SDK needs to be present regardless. Honestly, this surprised me the first time I set things up.

## Scaffolding Your First Project

The CLI generates a project skeleton with sensible defaults. Here we'll build a small crew that researches a topic and produces a summary report:

```bash
crewai create crew latest-ai-development
cd latest_ai_development
```

This creates a directory structure separating configuration from logic:

```
latest_ai_development/
├── .env
├── pyproject.toml
├── src/
│   └── latest_ai_development/
│       ├── main.py
│       ├── crew.py
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       └── tools/
│           └── custom_tool.py
```

The design choice here is interesting. Agent definitions and task specs live in YAML, while orchestration logic stays in Python. So you can tweak an agent's personality, goals, or task descriptions without touching code, and vice versa. I think it's a nice separation, though from what I can tell the tradeoff is that you need to keep the naming in sync between YAML and Python (more on that in a second).

## Defining Agents and Tasks

Open `config/agents.yaml` and define two agents: a researcher and a reporting analyst. Each gets a role, a goal describing what it should optimize for, and a backstory that shapes how it approaches problems.

```yaml
researcher:
  role: "{topic} Senior Data Researcher"
  goal: "Uncover cutting-edge developments in {topic}"
  backstory: >
    You're a seasoned researcher with a knack for uncovering
    the latest developments in {topic}. Known for finding the
    most relevant information and presenting it clearly.

reporting_analyst:
  role: "{topic} Reporting Analyst"
  goal: "Create detailed reports based on {topic} data analysis"
  backstory: >
    You're a meticulous analyst with a keen eye for detail.
    You turn complex data into clear, concise reports that
    others can easily understand and act on.
```

The `{topic}` placeholders get filled at runtime, which is a handy pattern for making crews reusable across different subjects.

Tasks go in `config/tasks.yaml`. Each task specifies what should happen, what the output should look like, and which agent handles it:

```yaml
research_task:
  description: "Conduct thorough research about {topic}"
  expected_output: "A list with 10 bullet points of the most relevant information"
  agent: researcher

reporting_task:
  description: "Expand the research into a full report with detailed sections"
  expected_output: "A complete report formatted as markdown"
  agent: reporting_analyst
  output_file: report.md
```

Here's the thing the docs don't make obvious: the names in your YAML files must match the method names in your Python code exactly. CrewAI uses this naming convention to automatically link configuration with implementation. Get it wrong and you'll get confusing errors.

## Wiring It Together in Python

The `crew.py` file connects your YAML definitions to actual agent and task objects. The `@CrewBase` decorator handles the plumbing:

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class LatestAiDevelopmentCrew():
    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], verbose=True)

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(config=self.agents_config['reporting_analyst'], verbose=True)

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def reporting_task(self) -> Task:
        return Task(config=self.tasks_config['reporting_task'], output_file='report.md')

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

`Process.sequential` means tasks run in order: the researcher finishes before the analyst begins. There's also a hierarchical process where a manager agent delegates work on the fly, which works better for workflows where task ordering depends on intermediate results.

## Running the Crew

Set your API keys in the `.env` file. At minimum you'll need an OpenAI key (or whatever provider you prefer). Then install dependencies and launch:

```bash
crewai install
crewai run
```

With `verbose=True`, you'll see each agent's reasoning process in real time: what it's thinking, which tools it's calling, and what output it produces. The final report gets written to `report.md` in your project root.

## What to Expect (and Watch Out For)

Token costs can sneak up on you. When agents communicate back and forth, the bills add up fast; for a learning project, consider using smaller models or setting `max_iter` on your agents to cap reasoning loops.

When something goes wrong, don't immediately start tweaking prompts. I've fallen into that trap. The actual failure is often in task routing, tool configuration, or context passing between agents, not the wording of a backstory. Enable verbose logging and read the full execution trace; it'll save you way more time than trial-and-error prompt editing.

One more thing. CrewAI separates two complementary ideas: Crews handle autonomous agent collaboration, while Flows provide deterministic, event-driven workflow control. For a first project, Crews alone are enough. But as your use case gets more complex (conditional branching, state management across steps, integration with external services), combining both gives you a good balance between agent autonomy and predictable execution. The framework is open-source under the MIT license with an active community, and starting with a small, well-scoped crew is honestly the fastest way to build intuition for where agents shine and where you'll want tighter control.
