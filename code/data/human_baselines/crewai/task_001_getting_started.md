---
source_url: https://crewai.com/blog/build-your-first-crewai-agents
author: "João (Joe) Moura"
platform: crewai.com (official blog)
scope_notes: "Trimmed to focus on installation, environment setup, and first project creation. Removed later sections on configuration details, execution, and next steps."
---

A step-by-step guide to creating collaborative AI agent crews with the CrewAI framework.

If you've been exploring the AI agent ecosystem, you're likely aware of the potential behind coordinated multi-AI agent systems. CrewAI is an open-source framework designed specifically to simplify the development of these collaborative agent networks, enabling complex task delegation and execution without the typical implementation headaches.

## Prerequisites

Before diving in, ensure your environment meets these requirements:

- **`uv` Package Manager**: CrewAI leverages `uv` from Astral (creators of Ruff) for dependency management. This ultra-fast package manager significantly improves installation speed and reliability compared to traditional pip.
- **Python**: CrewAI requires Python `>3.10` and `<3.13`. Verify your version:

```
python3 --version
```

## Installation: Setting up your Environment

### 1. Install the `uv` package manager

Choose the appropriate method for your operating system:

**macOS / Linux:**

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:

```
uv --version
```

### 2. Install the CrewAI CLI

With `uv` ready, install the CrewAI command-line interface:

```
uv tool install crewai
```

If this is your first time using `uv tool`, you might see a prompt about updating your `PATH`. Follow the instructions (typically running `uv tool update-shell`) and restart your terminal if needed.

Verify your installation:

```
uv tool list
```

You should see `crewai` listed with its version number (e.g., `crewai v0.119.0`).

## Project Creation: Scaffolding your first Crew

CrewAI offers a structured project generator to set up the foundation for your agent crew. Navigate to your projects directory and run:

```
crewai create crew latest-ai-development
```

The CLI will prompt you to:

1. **Select an LLM Provider**: Choose your preferred Large Language Model provider (OpenAI, Anthropic, Gemini, Ollama, etc.)
2. **Select a Model**: Pick a specific model from the provider (e.g., `gpt-4o-mini`)
3. **Enter API Keys**: You can add these now or later

## Generated Project Structure

The CLI creates a well-organized directory structure:

```
latest-ai-development/
├── .env                  # Environment variables and API keys
├── .gitignore            # Pre-configured to prevent committing sensitive data
├── pyproject.toml        # Project dependencies and metadata
├── README.md             # Basic project information
├── knowledge/            # Storage for knowledge files (PDFs, etc.)
└── src/                  # Main source code
    └── latest_ai_development/
        ├── config/       # YAML configuration files
        │   ├── agents.yaml
        │   └── tasks.yaml
        ├── tools/        # Custom tool implementations
        │   └── custom_tool.py
        ├── crew.py       # Crew class definition
        └── main.py       # Entry point
```

## Execution: Running your Crew

With everything configured, install the project dependencies:

```
crewai install
```

This command uses `uv` to install and lock all dependencies defined in `pyproject.toml`.

Now, execute your crew:

```
crewai run
```

Watch your terminal as your agents come to life! You'll see the researcher agent using tools to search for information, the reporting analyst agent receiving the research findings, and both agents working cooperatively to generate the final report. When execution completes, you'll find the output file (`report.md`) in your project directory.
