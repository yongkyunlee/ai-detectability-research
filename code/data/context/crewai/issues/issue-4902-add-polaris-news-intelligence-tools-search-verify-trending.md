# Add Polaris News Intelligence Tools (search, verify, trending)

**Issue #4902** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** JohnnyTarrr

## Tool Request

**Package:** [polaris-news](https://pypi.org/project/polaris-news/) (PyPI)
**Package (CrewAI wrapper):** [crewai-polaris](https://pypi.org/project/crewai-polaris/) (PyPI)

### What it does

[The Polaris Report](https://thepolarisreport.com) provides AI-verified news intelligence across 18 verticals (tech, AI/ML, markets, crypto, policy, science, health, etc.). Three tools for CrewAI agents:

| Tool | Description |
|------|-------------|
| **PolarisSearchTool** | Search verified news briefs with confidence scores, bias ratings, and source attribution |
| **PolarisVerifyTool** | Fact-check claims against the verified news corpus — returns verdicts (supported/contradicted/partially_supported/unverifiable) with evidence |
| **PolarisTrendingTool** | Get trending entities (people, companies, topics) from current coverage |

### Why it's useful

- Every result includes **confidence scores** and **bias ratings** — agents can reason about source reliability
- **Fact-checking built in** — verify claims before acting on them
- **18 news verticals** with counter-arguments and source attribution
- Free tier available, `demo` key for quick testing

### Installation

```bash
pip install crewai-polaris
# or
pip install polaris-news  # lower-level client
```

### Example

```python
from crewai import Agent, Task, Crew
from crewai_polaris import PolarisSearchTool, PolarisVerifyTool

search = PolarisSearchTool(api_key="demo")
verify = PolarisVerifyTool(api_key="demo")

researcher = Agent(
    role="News Analyst",
    goal="Research and verify current news stories",
    tools=[search, verify],
)

task = Task(
    description="Find top AI stories this week and verify any major claims.",
    expected_output="A verified briefing with fact-checked claims.",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

### Implementation

I have a complete implementation following the `BaseTool` pattern with `EnvVar`, `args_schema`, `package_dependencies`, and README ready to submit as a PR. The `crewAI-tools` repo is archived — happy to submit to `lib/crewai-tools` in this repo if that's where new tools go now.

**Links:**
- API docs: https://thepolarisreport.com/docs
- Source: https://github.com/JohnnyTarrr/polaris-sdks
- LangChain integration: https://pypi.org/project/langchain-polaris/
