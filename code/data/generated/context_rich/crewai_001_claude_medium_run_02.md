# Getting Started with CrewAI: Installation and First Project

Multi-agent AI systems have moved from research curiosity to practical tooling, and CrewAI sits at the center of that shift. Built as a standalone Python framework with no dependency on LangChain or other agent libraries, it gives developers a structured way to coordinate multiple AI agents around shared goals. Whether you want a team of agents collaborating on research, analysis, or content generation, CrewAI provides the scaffolding to make that happen without writing your own orchestration logic from scratch.

This guide walks through installing CrewAI, creating your first project, and understanding the core abstractions that make it work.

## Prerequisites

Before installing anything, confirm your Python version. CrewAI requires Python 3.10 or higher (and below 3.14). Check with:

```bash
python3 --version
```

If you're outside that range, grab a compatible version from the official Python downloads page. You'll also need `uv`, a fast dependency management tool from Astral that CrewAI adopted as its standard package handler. If you don't have it yet, installation is a single command on macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows users can install it through PowerShell instead. Once `uv` is available on your PATH, you're ready to go.

## Installing the CLI

CrewAI ships as a CLI tool that manages project creation, dependency locking, and execution. Install it globally with:

```bash
uv tool install crewai
```

Verify the installation landed correctly by running `uv tool list` — you should see `crewai` with its version number in the output. If the shell can't find the command, run `uv tool update-shell` to refresh your PATH.

One thing worth knowing upfront: CrewAI also requires `openai >= 1.13.3` as a runtime dependency, since it defaults to OpenAI models for agent reasoning. You don't have to use OpenAI — the framework supports Anthropic, local models via Ollama, and other providers — but the SDK needs to be present regardless.

## Scaffolding Your First Project

CrewAI's CLI generates a project skeleton with sensible defaults. Let's build a small crew that researches a topic and produces a summary report:

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

The design philosophy here is worth noting. Agent definitions and task specifications live in YAML files, while orchestration logic stays in Python. This split means you can adjust an agent's personality, goals, or task descriptions without touching code, and vice versa.

## Defining Agents and Tasks

Open `config/agents.yaml` and define two agents — a researcher and a reporting analyst. Each agent gets a role, a goal describing what it should optimize for, and a backstory that shapes how it approaches problems:

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

The `{topic}` placeholders get filled at runtime — a handy pattern for making crews reusable across different subjects.

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

An important detail: the names in your YAML files must match the method names in your Python code exactly. CrewAI uses this naming convention to automatically link configuration with implementation.

## Wiring It Together in Python

The `crew.py` file connects YAML definitions to actual agent and task objects. The `@CrewBase` decorator handles the plumbing:

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

The `Process.sequential` setting means tasks run in order — the researcher finishes before the analyst begins. CrewAI also supports a hierarchical process where a manager agent delegates work dynamically, which is better suited for complex workflows where task ordering depends on intermediate results.

## Running the Crew

Set your API keys in the `.env` file. At minimum, you'll need an OpenAI key (or the configuration for whichever model provider you prefer). Then install dependencies and launch:

```bash
crewai install
crewai run
```

With `verbose=True`, you'll see each agent's reasoning process in real time — what it's thinking, which tools it's invoking, and what output it produces. The final report gets written to `report.md` in your project root.

## What to Expect (and Watch Out For)

A few practical notes from the community that are worth internalizing early. First, token costs can accumulate quickly when agents communicate back and forth. For a learning project, consider using smaller models or setting `max_iter` on your agents to cap the number of reasoning loops. Second, when something goes wrong, resist the urge to immediately tweak prompts. The actual failure is often in task routing, tool configuration, or context passing between agents rather than in the wording of a backstory. Enabling verbose logging and reading the full execution trace will save you time compared to trial-and-error prompt editing.

Finally, CrewAI's architecture separates two complementary ideas: Crews handle autonomous agent collaboration, while Flows provide deterministic, event-driven workflow control. For a first project, Crews alone are sufficient. But as your use case grows more complex — conditional branching, state management across steps, integration with external services — combining both will give you the right balance between agent autonomy and predictable execution.

The framework is open-source under the MIT license, with an active community and regular releases. Starting with a small, well-scoped crew is the fastest way to build intuition for what agents handle well and where you'll want tighter control.
