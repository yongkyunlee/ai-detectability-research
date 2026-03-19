# Getting Started with CrewAI: Installation and First Project

Multi-agent orchestration frameworks have proliferated over the past year. CrewAI is one of the more opinionated ones, and that's what makes it interesting. Rather than handing you a bare graph abstraction and wishing you luck, it pushes you toward a structure: agents with roles, tasks with expected outputs, and a crew that wires it all together. We've been evaluating it on our team, and I want to walk through the practical mechanics of going from zero to a working project.

## What CrewAI Actually Is

CrewAI is an open-source Python framework for building systems where multiple LLM-powered agents collaborate on tasks. Each agent gets a role, a goal, and a backstory - essentially a persona that shapes how the underlying model reasons. You assign agents to tasks, group everything into a crew, and kick it off.

The framework has two core architectural layers. Flows handle the overall application structure: state management, event-driven execution, conditional logic. Crews are the units of autonomous work within a flow - teams of agents that tackle specific problems. For production systems, the documentation recommends starting with a Flow and embedding Crews inside it for the parts that need agent autonomy. But for getting started, you can skip Flows entirely and just build a standalone Crew.

That distinction matters. A Crew with a sequential process is simpler to reason about, but a Flow gives you the scaffolding for real applications with branching logic and persistent state. I'd recommend starting with a Crew and graduating to Flows once you outgrow it.

## Prerequisites and Installation

CrewAI requires Python >=3.10 and <3.14. Check yours:

```bash
python3 --version
```

The framework uses `uv` as its dependency manager and package handler. If you don't have it, install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the CrewAI CLI itself:

```bash
uv tool install crewai
```

After installation, verify with `uv tool list` - you should see something like `crewai v0.102.0`. If you hit a PATH warning, run `uv tool update-shell` to fix it.

One thing the quickstart doesn't emphasize enough: CrewAI 0.175.0 requires `openai >= 1.13.3`. Even if you plan to use Anthropic or Gemini models, the OpenAI SDK is a transitive dependency. Don't fight it.

## Scaffolding a Project

CrewAI ships a CLI that generates project scaffolding. This is the recommended path, and having used it, I agree - the YAML-based configuration approach is cleaner than wiring everything up in raw Python.

```bash
crewai create crew latest-ai-development
cd latest_ai_development
```

This produces:

```
latest_ai_development/
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
```

Six files matter here. `agents.yaml` defines your agents. `tasks.yaml` defines your tasks. `crew.py` is where you wire them together in Python. `main.py` is the entry point. `.env` holds your API keys. And `knowledge/` is a directory for any domain-specific knowledge sources you want agents to reference.

## Defining Agents and Tasks

Agents in CrewAI are defined by three required fields: `role`, `goal`, and `backstory`. These aren't cosmetic. They go directly into the system prompt that shapes how the model behaves. A well-crafted backstory produces materially different outputs than a vague one.

Here's what the generated `agents.yaml` looks like after editing:

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

The `{topic}` variables are template placeholders. They get filled in at runtime when you call `kickoff(inputs={'topic': 'AI Agents'})`. This interpolation works across both agents and tasks YAML files, which keeps your configurations reusable.

Tasks follow a similar pattern:

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
    A fully fledge reports with the mains topics, each with a full section of information.
    Formatted as markdown without '```'
  agent: reporting_analyst
  output_file: report.md
```

One critical detail: the names in your YAML files must match the method names in your Python code. If your YAML defines `researcher`, your `crew.py` needs a method called `researcher` decorated with `@agent`. CrewAI uses this naming convention to automatically link configurations to code. Get it wrong and your task won't find its agent.

## Wiring It Together in Python

The `crew.py` file ties YAML configuration to executable Python. The `@CrewBase` decorator on the class handles automatic collection of agents and tasks, which means you don't manually build lists.

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class LatestAiDevelopmentCrew():
    """LatestAiDevelopment crew"""

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
            output_file='output/report.md'
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

The `@agent` and `@task` decorators register methods automatically. When you reference `self.agents` and `self.tasks` in the `@crew` method, CrewAI has already collected everything for you.

And `main.py` is straightforward:

```python
from latest_ai_development.crew import LatestAiDevelopmentCrew

def run():
    inputs = {'topic': 'AI Agents'}
    LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
```

## Running Your Crew

Before running, install dependencies:

```bash
crewai install
```

Set your API keys in `.env`. You'll need at minimum an LLM provider key. If your agents use `SerperDevTool` for web searches, add `SERPER_API_KEY` too. Then:

```bash
crewai run
```

With `Process.sequential`, tasks execute in the order they're defined. The output of one task feeds as context into the next. So the researcher runs first, produces its bullet points, and the reporting analyst receives that output to expand into a full report. The final result lands both in the console and in `output/report.md`.

## Choosing an LLM

By default, CrewAI uses whatever model is set in the `MODEL` environment variable, falling back to GPT-4 if nothing is configured. But you're not locked into OpenAI. CrewAI provides native SDK integrations for OpenAI, Anthropic, Google Gemini, Azure, and AWS Bedrock. For all other providers, it routes through LiteLLM.

You can set the model globally via environment variables, per-agent in YAML with `llm: provider/model-id`, or in Python code using the `LLM` class with fine-grained parameters like temperature, max_tokens, and timeout. Native integrations don't require extra packages beyond the provider-specific extras - for example, `uv add "crewai[anthropic]"` for Claude models. But if you're using providers that go through LiteLLM, you need `uv add 'crewai[litellm]'`.

The YAML approach is simpler for most cases, but direct code gives you more control. There's a real trade-off: YAML configuration is easier to version-control and share across a team, but code-based LLM setup lets you tune parameters like temperature, top_p, and stop sequences that aren't exposed in the YAML format.

## Sequential vs. Hierarchical: Pick Wisely

CrewAI supports two execution processes. Sequential runs tasks in order - predictable, easy to debug. Hierarchical introduces a manager agent that delegates tasks to other agents based on their capabilities and reviews outputs before proceeding.

I'd start with sequential. Hierarchical sounds appealing on paper, but it adds a layer of LLM decision-making to your control flow. The community feedback backs this up. People report that debugging hierarchical crews is substantially harder because failures can originate from the manager's routing decisions, not from the agents themselves. A tool failure can surface as a reasoning failure when there's a manager in between. And hierarchical requires you to specify a `manager_llm` or provide a custom `manager_agent`, which is more configuration to maintain.

Sequential gets you 80% of the way for most use cases. Graduate to hierarchical when you have a concrete need for dynamic task allocation.

## Things That'll Trip You Up

A few gotchas from the documentation and community worth calling out.

First, agent iteration limits. By default, an agent retries up to 20 iterations (`max_iter=20`) before it gives its best answer. If your agent seems stuck in a loop re-summarizing the same content, this is why - and you might want to lower it. Token costs accumulate fast when agents iterate.

Second, `verbose=True` is your friend during development. Without it, you're flying blind. The framework handles a lot of orchestration behind the scenes, and you need visibility into what each agent is doing and when. Several community members have pointed out that observability is the single most important concern with agent systems - if you can't see the moment an agent hallucinates a tool call, you're burning money.

Third, context windows matter. CrewAI has built-in context window management controlled by the `respect_context_window` parameter (defaults to `True`). When enabled, it automatically summarizes conversation history if it exceeds the model's limits. This is great for robustness but can silently drop information. For precision-critical tasks, consider setting it to `False` and using RAG tools instead.

Finally, the framework provides optional lifecycle hooks via `@before_kickoff` and `@after_kickoff` decorators. These let you modify inputs before the crew starts or post-process results after it finishes - useful for validation, logging, or injecting runtime context.

## Where to Go From Here

Once you've got a basic crew running, there are several directions to explore. Task guardrails let you add validation functions that check agent outputs before passing them to the next task - a function returning `(True, result)` or `(False, "error message")` that forces the agent to retry. Structured outputs via `output_pydantic` or `output_json` let you enforce typed responses using Pydantic models. And asynchronous task execution with `async_execution=True` lets you run independent tasks in parallel, which can significantly cut total execution time for crews with non-dependent work.

CrewAI isn't the right tool for everything. For a single model with a system prompt and a few tool calls, you're better off with the provider SDK directly. But when you genuinely need multiple specialized agents coordinating on a multi-step workflow, the framework's opinions about structure - YAML configs, role-based agents, sequential task pipelines - save real time compared to building that plumbing yourself.
