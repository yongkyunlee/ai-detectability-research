# Getting Started with CrewAI: installation and your first project

CrewAI is easiest to understand if you treat it like a Python scaffold for coordinating roles, tasks, and handoffs. The current repository source reports version `1.11.0`, and its package metadata requires `Python >=3.10, <3.14`. That baseline matters. The docs, templates, issues, and community discussions point to the same practical truth: CrewAI feels straightforward when you stay close to the generated scaffold, and it gets noisy when you bolt on every optional integration on day one.

So I wouldn’t start by debating frameworks. I’d start by installing the CLI cleanly, generating a crew, and reading the small amount of code CrewAI actually creates for you.

The official installation docs center `uv`, and that’s the path I’d follow. Use `uv` to install the `crewai` CLI, then let each project resolve its own environment later with `crewai install`. The repository README still shows `uv pip install crewai`, but the CLI-first route matches the rest of the onboarding better.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install crewai
uv tool list
```

But there’s a real trade-off here. CrewAI’s package metadata currently exposes `crewai-tools==1.11.0` as an optional extra. That’s convenient if you need web search, document search, or other packaged tools immediately. But the extra dependency surface is where friction shows up first. Issue reports from early 2026 describe conflicts with Google ADK around OpenTelemetry packages, and a February 20, 2026 installation breakage for CrewAI `1.9.3` tied to `tokenizers==0.20.3`. Base CrewAI is simpler. The tools extra gives you more capability, but it also gives you more dependency coordination work. For a first project, simple wins.

Once the CLI is installed, the project scaffold is the real starting point:

```bash
crewai create crew latest-ai-development
cd latest_ai_development
```

And yes, that hyphen-to-underscore shift is part of the documented flow. The command uses `latest-ai-development`, while the generated Python package directory is `latest_ai_development`.

The docs show the expected core structure: `pyproject.toml`, `.env`, `src/<project>/main.py`, `src/<project>/crew.py`, `tools/`, and `config/agents.yaml` plus `config/tasks.yaml`. If you read the scaffold code in `create_crew.py`, there’s a little more going on. The generator also creates `knowledge/`, `tests/`, and a starter `knowledge/user_preference.txt`. The scaffold is opinionated, but it isn’t hiding much.

`agents.yaml` defines the role, goal, and backstory for each agent. `tasks.yaml` defines the work, expected output, and which agent owns it. `crew.py` turns those definitions into `Agent`, `Task`, and `Crew` objects. And `main.py` is the narrow entry point that feeds runtime inputs into the crew. Under the hood, `@CrewBase` loads `config/agents.yaml` and `config/tasks.yaml` relative to the class file, and the `@agent`, `@task`, and `@crew` decorators wire the rest together.

That implementation detail explains one rule that beginners often miss: naming consistency is not optional. If your YAML defines `research_task`, your Python method should also be `research_task`. The framework is linking configuration to code by name.

For the first project, don’t invent a seven-agent architecture. The documented two-agent pattern is the right starting point. One agent researches. One agent writes. That keeps the handoff obvious and makes failures easy to localize.

The default scaffold already nudges you that way. The generated `agents.yaml` defines a `researcher` and a `reporting_analyst`. The generated `tasks.yaml` defines `research_task` and `reporting_task`. The generated `crew.py` runs them with `Process.sequential`, which means the reporting step waits for the research step to finish. That’s boring in the best possible way.

I also like one detail from the actual CLI template more than the quickstart page. Some doc examples hard-code a sentence like “the current year is 2025” into the task description. The template source is cleaner. Its `main.py` passes both `topic` and `current_year`, and its `tasks.yaml` interpolates `{current_year}` dynamically using `datetime.now().year`. Prompts should take inputs, not quietly fossilize.

You can stop there and still learn the core model. But the docs also show the next useful step: adding `SerperDevTool()` to the `researcher` agent for live web search. If you do that, you’ll need `SERPER_API_KEY` in `.env`, plus credentials for whichever model provider you choose. That’s a reasonable second move, not a required first move.

And this is where CrewAI’s own architecture story matters. The README frames Crews as the autonomy layer and Flows as the precision layer. That’s a real trade-off, not branding copy. A Crew is simpler because you mostly describe agents and tasks, then let the framework coordinate the sequence. A Flow gives you deterministic branching and tighter control, but it asks you to think like a workflow engine earlier than most first projects need. For onboarding, a sequential crew is the better default.

Running the project stays refreshingly short:

```bash
crewai install
crewai run
```

If you need extra project dependencies, the docs point you to `uv add <package-name>`. The CLI docs also expose follow-on commands like `crewai test`, `crewai replay`, and `crewai reset-memories`, and the generated `main.py` includes helper entry points for `train`, `replay`, and `test`.

One detail is worth noticing before you wire this into anything important. The shipped template writes the final artifact to `report.md` at the project root. Some newer guide examples route the result to `output/report.md` after explicitly creating that directory. Either choice is fine. What matters is the design choice underneath it: task output is explicit and file-backed, not trapped in terminal logs.

Community discussions around CrewAI keep circling the same concern: once abstractions get deep, debugging and observability can feel fuzzy compared with lower-level graph frameworks or plain SDK code. I think that criticism is fair. But it means the first project should stay small enough that you can still see the whole system.

So keep the first crew boring. Two agents. Sequential execution. Minimal tools. File-backed output. Read `agents.yaml`, `tasks.yaml`, `crew.py`, and `main.py` before you add anything clever. CrewAI is at its best when you treat the scaffold as transparent Python rather than magic. Install it cleanly, run the generated project, and only then decide whether you need more autonomy, more precision, or fewer abstractions.
