# Getting Started with CrewAI: Installation and First Project

CrewAI is a multi-agent orchestration framework. That's the short version. The longer version is that it gives you a structured way to define AI agents with distinct roles, hand them tasks, and let them collaborate - sequentially or through a managed hierarchy - to produce a combined output. We've been evaluating it for internal tooling, and I wanted to document the setup process while it's still fresh.

## What You're Actually Getting

The framework is built around two core abstractions: Crews and Flows. Crews are teams of agents that collaborate on tasks. Flows are the event-driven scaffolding that manage state and control execution around those crews. For a first project, you don't need Flows at all. A single Crew with a sequential process will get you surprisingly far.

Each agent gets three required attributes: a `role`, a `goal`, and a `backstory`. These shape how the underlying LLM behaves when processing that agent's tasks. It sounds a bit theatrical, but the role-playing approach does produce noticeably different outputs compared to a single prompt with everything jammed in. Agents can also carry tools - search APIs, file readers, custom functions - and they'll decide when to invoke them during task execution.

The YAML-based configuration is simpler than wiring everything up in pure Python, but it gives you less flexibility for dynamic setups. For a getting-started project, YAML is the right call.

## Installation

CrewAI requires Python >=3.10 and <3.14. It uses `uv` as its dependency manager, which is a deliberate choice - `uv` is fast and handles virtual environments without ceremony. If you don't have it installed:


curl -LsSf https://astral.sh/uv/install.sh | sh


Then install the CrewAI CLI itself:


uv tool install crewai


You can verify the installation with `uv tool list`. You should see something like `crewai v0.102.0` in the output. If you get a PATH warning after install, run `uv tool update-shell` to fix it.

One dependency worth noting: CrewAI 0.175.0 requires `openai >= 1.13.3`. Even if you're planning to use Anthropic or Google models, the OpenAI SDK is still a transitive dependency you'll need to satisfy.

## Scaffolding Your First Project

The CLI generates a project skeleton for you:


crewai create crew latest-ai-development
cd latest_ai_development


This produces a clean directory layout with `src/latest_ai_development/config/agents.yaml`, `tasks.yaml`, a `crew.py` orchestration file, a `main.py` entry point, and a `.env` for your API keys. There's also a `knowledge/` directory for RAG-style knowledge bases, though you won't need it right away.

The naming convention matters here. Agent names in `agents.yaml` must match the method names in `crew.py`. Same for tasks. CrewAI uses this convention to wire YAML configs to Python decorators automatically. If the names drift, your tasks won't find their assigned agents, and the errors aren't always obvious about why.

## Defining Agents and Tasks

In `agents.yaml`, you define each agent's personality and purpose. Variables like `{topic}` get interpolated at runtime from inputs you pass to the crew:


researcher:
  role: >
    {topic} Senior Data Researcher
  goal: >
    Uncover cutting-edge developments in {topic}
  backstory: >
    You're a seasoned researcher with a knack for uncovering the latest
    developments in {topic}.


Tasks go in `tasks.yaml`. Each task specifies a description, an expected output format, and the agent responsible:


research_task:
  description: >
    Conduct a thorough research about {topic}
  expected_output: >
    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher


In `crew.py`, the `@CrewBase` decorator connects everything. You define methods decorated with `@agent` and `@task` that return configured `Agent` and `Task` objects. The `@crew` method assembles them into a `Crew` with a chosen process - `Process.sequential` runs tasks in order, with each task's output feeding into the next as context.

So the wiring is: YAML defines what, Python defines how, and the decorator system glues them together.

## Running It

Before your first run, lock and install dependencies:


crewai install


Then set your environment variables in `.env`. You'll need an API key for your LLM provider and, if you're using the search tool from the quickstart example, a Serper API key as well. The default model configuration uses OpenAI's GPT-4, but you can swap to any provider by setting the `MODEL` environment variable or specifying `llm` directly in your agent YAML.

To kick it off:


crewai run


The crew executes each task sequentially, and you'll see verbose output in the console if you've set `verbose=True`. The final output lands both in stdout and in any `output_file` you specified on your last task.

## Where It Gets Tricky

I want to be honest about the trade-offs. CrewAI's YAML-plus-decorator approach is simpler to get started with than something like LangGraph's explicit node-and-edge graphs, but you give up visibility into exactly what prompts are being sent to the LLM. Community discussions consistently flag observability as a pain point - when an agent starts looping or hallucinating a tool call, it's hard to tell which layer is actually failing. Is it the prompt? The tool? The routing between agents? Token costs can also climb fast with multi-agent setups, since agents re-summarize context as they pass it between tasks.

For a first project, stick with `Process.sequential` and two or three agents. The hierarchical process mode, which requires a `manager_llm` or `manager_agent`, adds a delegation layer that's powerful but introduces another surface area for debugging. Get comfortable with the basics before you introduce a manager agent deciding which worker handles what.

And keep `verbose=True` on during development. You'll want to see every step the agents take. That's the closest thing you get to observability out of the box on the open-source tier.

## Is It Worth It?

For prototyping multi-agent workflows quickly, yes. The scaffolding CLI, YAML configs, and decorator system mean you can go from zero to a working two-agent pipeline in under an hour. That's genuinely useful for evaluating whether a multi-agent approach makes sense for your problem before you invest in a more custom solution.
