# Getting started with CrewAI: installation and your first project

CrewAI is a Python framework for coordinating multiple AI agents around shared tasks. In its vocabulary, a **crew** is the agent team plus tasks and execution rules, while a **flow** is the more event-driven orchestration layer for larger systems. For a first project, the crew scaffold is the right place to start: it gives you a runnable layout, YAML-based configuration, and just enough Python to understand how the pieces fit together.

## Step 1: install the CrewAI CLI

CrewAI’s docs assume `uv` is available first. On a new machine, install `uv`, then install the CLI itself:

```bash
uv tool install crewai
```

You can confirm the installation with:

```bash
uv tool list
```

Two setup details matter immediately:

- Use a supported Python version: `>=3.10,<3.14`
- Expect `uv` to handle project setup, dependency sync, and execution

## Step 2: generate your first crew project

The documented starter command is:

```bash
crewai create crew latest-ai-development
```

One small but useful detail from the scaffold code: CrewAI normalizes the project name into a valid Python module name. Hyphens become underscores, which is why the docs create `latest-ai-development` but then tell you to `cd latest_ai_development`.

The CLI may also prompt for a provider, model, and API key, then write those values into `.env`. If you want a clean scaffold without that interactive setup, the generated reference file points to `--skip_provider`.

The generated crew project looks roughly like this:

```text
my_project/
├── knowledge/
├── pyproject.toml
├── README.md
├── .env
└── src/my_project/
    ├── main.py
    ├── crew.py
    ├── tools/
    │   └── custom_tool.py
    └── config/
        ├── agents.yaml
        └── tasks.yaml
```

## Step 3: learn what each file does

`agents.yaml` defines who your agents are. The default template creates a `researcher` and a `reporting_analyst`, each with a role, goal, and backstory. `tasks.yaml` defines the work units, including the task description, the expected output, and which agent owns each task.

Then `crew.py` turns those YAML entries into actual `Agent` and `Task` objects using `@CrewBase`, `@agent`, `@task`, and `@crew`. The template wires them into a `Crew` configured with `Process.sequential` and `verbose=True`, so the first project runs in a simple, predictable order.

Finally, `main.py` defines the inputs passed into `crew().kickoff(...)`. Those inputs are more important than they look because CrewAI interpolates them into the YAML files. If `agents.yaml` or `tasks.yaml` contains `{topic}`, then `inputs = {"topic": "AI Agents"}` in `main.py` fills that value at runtime.

## Step 4: make the smallest useful edits

For a first run, keep the edits small:

1. Put your model credentials in `.env`
2. Set or confirm the `MODEL` value if your scaffold created one
3. Change the topic in `main.py`
4. Tweak the YAML only if needed

A minimal `main.py` input block looks like this:

```python
inputs = {
    "topic": "AI agents",
    "current_year": "2026"
}
```

The default template already uses a good beginner pattern: one task gathers material, and the next task turns it into a markdown report. In the starter `crew.py`, the reporting task writes to `report.md`, so your first success condition is straightforward: the crew runs and leaves a file behind.

If you want to extend the project, the scaffold also gives you `tools/custom_tool.py`. The template shows the expected pattern: subclass `BaseTool`, define a Pydantic input schema, and implement `_run()`.

## Step 5: install project dependencies and run

From the project root:

```bash
crewai install
crewai run
```

Under the hood:

- `crewai install` syncs the environment with `uv`
- `crewai run` executes the project through `uv run`

The generated `pyproject.toml` also pins `crewai[tools]` to a specific version instead of floating on latest. That improves reproducibility, but it also tells you to be cautious with upgrades.

## What to watch out for

First, keep your initial project **sequential**. CrewAI supports hierarchical execution too, but that mode requires a manager model or manager agent. For a first project, more autonomy usually means more ambiguity when something breaks.

Second, treat dependency breadth as a cost. The issue tracker shows real examples of install and compatibility friction, including broken transitive versions like `tokenizers` and conflicts around `openai` when mixing CrewAI with observability tooling such as OpenLit. Start with the smallest set of packages that solves your problem, then add integrations one by one.

Third, do not assume the interactive provider prompt always reflects the newest model lineup. There is an open issue about stale model choices in `crewai create`. If the scaffold suggests older models, you are not stuck with them. You can edit `MODEL` in `.env`, set `llm:` directly in YAML, or configure an `LLM(...)` object in code.

Finally, debugging multi-agent systems is rarely just prompt tuning. Community discussions around CrewAI repeatedly point to a common failure mode: people patch the visible symptom instead of the failing layer. A bad final answer may come from task routing, missing tool output, or polluted context from an earlier step. Start with `verbose=True`, consider `output_log_file`, and use the CLI’s task-output and replay commands before rewriting prompts.

## Where CrewAI fits well

CrewAI’s sweet spot is the developer who wants something higher level than graph-based orchestration, but still wants a real project structure instead of a notebook demo. YAML-configured agents and tasks make the first project approachable, while the Python layer leaves room for custom tools, callbacks, memory, and logging later.

That convenience is also the trade-off. Compared with lower-level orchestration frameworks, CrewAI can feel more opaque once the system becomes large and highly stateful. But for a first project, that abstraction is useful: you can get a working multi-agent report generator running quickly, learn the framework’s mental model, and then decide whether to stay with crews or move into flows and stronger production controls.

If your goal is to get from zero to a working multi-agent app quickly, CrewAI’s documented path is solid: install with `uv`, scaffold a crew, edit YAML and inputs, run locally, and then layer in tools, search, memory, and observability.
