# Will langchain support create_agent with pimono-like loop in loop capability.

**Issue #35452** | State: open | Created: 2026-02-26 | Updated: 2026-03-09
**Author:** lylingzhen
**Labels:** core, langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Feature Description

I would like langchain to support loop in loop react agent. Just like pi-mono-agent-core.

### Use Case

This feature would help user to build loop-in-loop agent pattern which can support 'interrupt', 'append' actions like pi-mono-agent-core while agent is running.
Furthermore, we can also provide time travel base on session tree.

### Proposed Solution

_No response_

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**saadsaleem01:**
Hi @lylingzhen — PR #35459 addresses this with two new APIs:

### `create_agent_tool` — Loop-in-loop pattern

Wraps a compiled agent as a tool, so an outer agent can delegate to an inner agent that runs its own full loop:

```python
from langchain.agents import create_agent, create_agent_tool

researcher = create_agent(
    model="openai:gpt-4o",
    tools=[search, summarize],
    system_prompt="Research assistant",
)
research_tool = create_agent_tool(
    researcher, name="research", description="Delegate research tasks"
)

orchestrator = create_agent(model="openai:gpt-4o", tools=[research_tool, write_report])
```

### `AgentSession` — Interrupt/resume + time-travel branching

Convenience wrapper for session management with interrupt, append, and checkpoint branching:

```python
from langchain.agents import create_agent, AgentSession
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4o",
    tools=[my_tool],
    checkpointer=InMemorySaver(),
    interrupt_before=["tools"],
)
session = AgentSession(agent)

result = session.run("What's the weather?")
state = session.get_state()        # inspect pending actions
result = session.resume()          # continue after interrupt
result = session.resume(           # append messages during resume
    update={"messages": [HumanMessage("Also check tomorrow")]}
)

# Time-travel: branch from any checkpoint
history = list(session.get_history())
branch = session.branch(checkpoint_id=history[-1].config["configurable"]["checkpoint_id"])
result = branch.run("Try a different approach")
```

Both are exported from `langchain.agents` and covered by 25 unit tests.
