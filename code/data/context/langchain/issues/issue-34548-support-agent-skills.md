# Support Agent Skills

**Issue #34548** | State: open | Created: 2025-12-31 | Updated: 2026-03-16
**Author:** Fly-Playgroud
**Labels:** feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
- [ ] langchain-cli
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

https://agentskills.io/

CC has already established it as an open standard; please support it.

### Use Case

https://agentskills.io/

CC has already established it as an open standard; please support it.

### Proposed Solution

_No response_

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**vjacobsen:**
imo this would be a great addition to LangChain agents. I did some digging and it's already supported by the `deepagents-cli` package via [SkillsMiddleware](https://github.com/langchain-ai/deepagents/blob/bed960cc93c96d2c32093016bb66c445eedb6053/libs/deepagents-cli/deepagents_cli/skills/middleware.py#L102C7-L102C23), so implementing something similar for LangChain seems feasible.

## Proposed Implementation

A slightly different approach than `deepagents-cli` might be needed for LangChain, where we inject a `load_skill` tool (because create_agent doesn't include a `read_file` tool by default).

This would follow the **tool based** integration approach described here:  https://agentskills.io/integrate-skills#integration-approaches

Middleware hook: `wrap_model_call` or `before_agent`?

Action:
1. **List available skills** in the agent's directory (similar to `deepagents-cli`)
2. **Append skill metadata** (names, descriptions) to the system prompt (similar to `deepagents-cli`)
3. **Inject a `load_skill` tool**
   - This would be necessary for LangChain since the `read_file` tool isn't available by default for every agent
   - Similar to how `TodoListMiddleware` injects a `write_todos` tool and appends context to the system prompt

## Enhanced Progressive Disclosure

For even more granular control, we could expand the `load_skill` tool to load both the `skill.md` and reference files from the skill's directory as needed:

```
demo_pdf_creator_agent/skills/
├── pdf_processing/
│   ├── skill.md
│   ├── reference.md
│   ├── another_reference.md
│   └── template.md
```

**Example tool usage:**

```python
load_skill("pdf_processing")  # loads just skill.md
load_skill("pdf_processing", asset="template.md")  # loads pdf_processing/template.md
load_skill("pdf_processing", asset="reference.md")  # loads pdf_processing/reference.md
```

I'm sure there are other ways to approach this, curious to get suggestions and thoughts. The load_skill tool is basically a wrapper around file reader tool. 

EDIT: the above approach assumes skills only contain markdown files, not sure whether we'd include other file types like .py scripts.

## Next Steps

I've already started prototyping this for an agent I'm building, and it's working well but needs more polish. If the maintainers think this would be a valuable feature and it aligns with the project roadmap, I'd be happy to contribute a PR.

**jk123vip:**
Why doesn't LangChain support agent skills? It only allows loading a single skill.md file. How can we support references and scripts?

**ipassynk:**
LangChain should support skills out of the box. The whole industry is moving toward a skills-based architecture. I understand that LangChain might not have been designed with a rea/ls/grep tools for loading skills, but it could potentially work with a single lightweight load_skill mechanism combined with a dynamic tool system.

**taagarwa-rh:**
I started a langchain-skills-adapters package here: https://github.com/taagarwa-rh/langchain-skills-adapters
It offers two modes of usage:
1. As a tool: Loads your skill descriptions and adds them to an `activate_skill` tool description. The agent can activate the tool to get the full skill file content and see available resources.
2. As middleware: Adds skills descriptions to the system prompt of model calls. The agent can use the included ReadFileTool to read skill files and resources files as needed.

## What It Does

### As a tool

The created tool will have the following properties, as described in [skills disclosure section](https://agentskills.io/client-implementation/adding-skills-support#step-3-disclose-available-skills-to-the-model) of the Anthropic guide.

```yaml
name: activate_skill
description: The following skills provide specialized instructions for specific tasks. When a task matches a skill's description, call the activate_skill tool with the skill's name to load its full instructions. {skill-catalog}
args:
  - name: skill_name
    description: Name of the skill to activate
```

### As middleware

The following is added to the end of the agent's system prompt

```
The following skills provide specialized instructions for specific tasks.
When a task matches a skill's description, use your file-read tool to load
the SKILL.md at the listed location before proceeding.
When a skill references relative paths, resolve them against the skill's
directory (the parent of SKILL.md) and use absolute paths in tool calls.
{skill-catalog}
```

## Example Usage

### As a tool

```py
from langchain.agents import create_agent
from langchain_community.tools.file_management.read import ReadFileTool

from langchain_skills_adapters import SkillsTool

# Create the SkillsTool pointed to your skills directory
skills_dir = "/path/to/skills/"
skills_tool = SkillsTool(skills_dir)

# Optional: Add a file reading tool. Recommended if your agent needs to read resources from your skills directory (scripts, assets, etc.)
read_file_tool = ReadFileTool(root_dir=skills_dir)

# Create the agent
tools = [skills_tool, read_file_tool]
agent = create_agent("openai:gpt-5", tools=tools)
response = agent.invoke(input={"messages": {"role": "user", "content": "What skills do you have?"}})
```

### As middleware

```py
from langchain.agents import create_agent

from langchain_skills_adapters import SkillsMiddleware

# Create the SkillsTool pointed to your skills directory
skills_dir = "/path/to/skills/"
skills_middleware = SkillsMiddleware(skills_dir)

# Create the agent
agent = create_agent("openai:gpt-5", middleware=[skills_middleware])
response = agent.invoke(input={"messages": {"role": "user", "content": "What skills do you have?"}})
```

What are your thoughts on this approach? I would say it's very similar to what @vjacobsen described.
