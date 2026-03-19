# Getting Started with CrewAI: Installation and First Project

CrewAI is an opinionated framework for multi-agent orchestration. It gives you scaffolding, a CLI, and a YAML-driven configuration system that can get a working agent pipeline running in minutes. Whether that speed is worth the trade-offs depends on what you're building. I want to walk through the actual setup process and flag a few things the quickstart guide doesn't emphasize enough.

## What You Need Before You Start

CrewAI requires Python >=3.10 and <3.14. Check yours with `python3 --version`. The framework also leans heavily on `uv`, Astral's Rust-based package manager, for dependency management and project execution. If you've been using pip or poetry, this is a shift. On macOS or Linux, install uv with:


curl -LsSf https://astral.sh/uv/install.sh | sh


Windows users get a PowerShell one-liner instead. Once uv is available, install the CrewAI CLI itself:


uv tool install crewai


Run `uv tool list` to confirm. You should see something like `crewai v0.102.0` (or newer) in the output. If you get a PATH warning after installation, run `uv tool update-shell` to fix it. That catches most people on a fresh setup.

## Scaffolding Your First Project

CrewAI ships a `create` command that generates an entire project skeleton. Run this:


crewai create crew latest-ai-development


The CLI will prompt you to pick an LLM provider. It supports OpenAI, Anthropic, Google Gemini, Groq, and SambaNova out of the box. Select "other" if you want access to the full LiteLLM provider list. After you choose a provider and model, it'll ask for your API key.

What you get is a directory structure that looks like this:


latest_ai_development/
├── .env
├── pyproject.toml
├── knowledge/
└── src/
    └── latest_ai_development/
        ├── main.py
        ├── crew.py
        ├── config/
        │   ├── agents.yaml
        │   └── tasks.yaml
        └── tools/
            └── custom_tool.py


Two YAML files. Two Python files. That's the core. Everything else is plumbing.

## Agents, Tasks, and Crews

CrewAI's mental model revolves around three primitives. Agents are autonomous units defined by a role, a goal, and a backstory. Tasks are discrete assignments with a description and an expected output. A Crew groups agents and tasks together with an execution strategy.

The recommended approach is YAML configuration. Open `config/agents.yaml` and you'll find a template. Here's what a researcher agent looks like:


researcher:
  role: >
    {topic} Senior Data Researcher
  goal: >
    Uncover cutting-edge developments in {topic}
  backstory: >
    You're a seasoned researcher with a knack for uncovering the latest
    developments in {topic}.


The `{topic}` variable gets interpolated at runtime when you call `kickoff(inputs={'topic': 'AI Agents'})` from your main entry point. Tasks follow the same pattern in `tasks.yaml`, referencing agents by name.

One thing the docs stress but is easy to miss: the keys in your YAML files must match the method names in your Python code exactly. If your YAML defines `researcher`, your `crew.py` needs a method called `researcher` decorated with `@agent`. Break that naming convention and CrewAI won't link your config to your code. No error message, just silent failure to resolve the reference.

## The Python Glue

The `crew.py` file uses a decorator-based pattern. You annotate your class with `@CrewBase`, then define methods for each agent, task, and the crew itself:


from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class LatestAiDevelopmentCrew():
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


The `@agent` and `@task` decorators automatically collect your agents and tasks into lists. You don't manually wire them together. The crew's `process` parameter controls execution order. `Process.sequential` runs tasks one after another, with each task's output feeding into the next as context. `Process.hierarchical` introduces a manager agent that delegates tasks based on agent capabilities, but it requires a `manager_llm` or `manager_agent` to be set on the crew.

Sequential is simpler and predictable. Hierarchical gives you dynamic delegation but adds a layer of LLM-driven decision-making that can be harder to debug. For a first project, stick with sequential.

## Running It

Before the first run, lock and install dependencies:


crewai install


Then add any extra packages you need with `uv add <package-name>`. Set your API keys in the `.env` file. For the quickstart example, you'll need both your LLM provider key and a Serper API key if you're using the search tool.

Now run:


crewai run


As of version 0.103.0, `crewai run` handles both standard crews and flows. It reads `pyproject.toml` to detect what you're running. The output appears in your terminal, and if you've configured an `output_file` on your final task, you'll get a markdown report written to disk.

## Where It Gets Tricky

CrewAI is fast to scaffold. That's its strength. But community discussions consistently flag the same pain points: observability is limited in the open-source version, and debugging gets hard once the framework's abstractions kick in. You can't easily see what prompts are actually being sent to the LLM. When an agent loops or produces unexpected output, the first instinct is to tweak the prompt, but the real issue might be in task routing, context injection, or memory. Verbose mode helps, but it isn't a replacement for proper tracing.

And then there's cost. Agents talking to each other means LLM calls multiply fast. A sequential two-agent crew doing research and reporting isn't bad. But add delegation, retries, and longer tool chains, and token spend can surprise you.

CrewAI is a solid choice for getting a multi-agent proof of concept running quickly, and the YAML-plus-decorators pattern keeps configuration clean. But if you need fine-grained control over every step of the agent pipeline, a lower-level framework like LangGraph gives you more visibility at the cost of writing more code yourself. Know what you're optimizing for before you pick.
