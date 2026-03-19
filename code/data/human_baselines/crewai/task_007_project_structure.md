---
source_url: https://crewai.com/blog/crewai-100x-speed-boost
author: "João (Joe) Moura"
platform: crewai.com (official blog)
scope_notes: "Full post preserved. Covers CLI tooling improvements, UV migration for dependency management, and project structure changes in version 0.74.0. Supplemented with project structure details from the 'Build your First CrewAI Agents' post (same author) for technical depth."
---

## CrewAI, 100x Speed Boost

CrewAI has released a significant update featuring a migration to UV that dramatically accelerates dependency installation -- a 10,000% improvement in installation speed.

### The Performance Challenge

Previously, installing CrewAI dependencies was a slow, cumbersome process that disrupted developer workflow. This was particularly problematic for engineers experimenting with multiple versions or iterating quickly on agent configurations.

### The UV Solution

The team migrated their dependency management system to leverage UV, which eliminated bottlenecks through optimized caching and parallelization. What previously took minutes now requires mere seconds.

UV, from Astral (creators of Ruff), serves as CrewAI's package manager and significantly improves installation speed and reliability compared to traditional pip. Installation is straightforward:

**macOS / Linux:**

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

With `uv` ready, install the CrewAI CLI:

```
uv tool install crewai
```

### Project Scaffolding with the CLI

CrewAI offers a structured project generator. The CLI creates a well-organized directory:

```
my-crew-project/
├── .env                  # Environment variables and API keys
├── .gitignore            # Pre-configured to prevent committing sensitive data
├── pyproject.toml        # Project dependencies and metadata
├── README.md             # Basic project information
├── knowledge/            # Storage for knowledge files (PDFs, etc.)
└── src/                  # Main source code
    └── my_crew_project/
        ├── config/       # YAML configuration files
        │   ├── agents.yaml
        │   └── tasks.yaml
        ├── tools/        # Custom tool implementations
        │   └── custom_tool.py
        ├── crew.py       # Crew class definition
        └── main.py       # Entry point
```

Key CLI commands include:

- `crewai create crew <name>` -- scaffold a new project
- `crewai install` -- install and lock dependencies via UV
- `crewai run` -- execute the crew

### Version 0.74.0 Features

Beyond speed improvements, the release includes:

- Adapted Tools CLI for UV compatibility
- Migration warnings from Poetry to UV
- New memory base for improved data handling
- Updated documentation reflecting all changes
- Bug fixes enhancing stability

The migration from Poetry to UV reflects CrewAI's commitment to making the CLI the fastest, most flexible tool in the developer's toolkit. The `crewai install` command now uses `uv` to install and lock all dependencies defined in `pyproject.toml`, and `crewai run` handles execution of the full agent crew pipeline.
