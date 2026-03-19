# langchain-a2a-adapters

**Issue #35724** | State: open | Created: 2026-03-10 | Updated: 2026-03-12
**Author:** kevinbfrank
**Labels:** core, feature request, internal

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

I would like LangChain to provide a **`langchain-a2a-adapters`** package that wraps remote A2A agents as LangChain tools — mirroring the `langchain-mcp-adapters` pattern.

`langchain-mcp-adapters` solved the tool integration problem with a simple dict-based config. Enterprises now need the same for **agents** — the A2A protocol is the emerging standard for agent-to-agent communication, backed by Google and 150+ organizations.

While LangGraph Platform offers A2A support, there's no open-source adapter for self-hosted deployments.

### Use Case

Enterprises are adopting A2A to enable multi-vendor agent interoperability. Teams building with LangChain need to call agents built with other frameworks (AutoGen, CrewAI, Google ADK) as tools within their LangChain agents.

### Proposed Solution

A `langchain-a2a-adapters` package following the same pattern as `langchain-mcp-adapters`:

```python
from langchain_a2a_adapters.client import MultiAgentA2AClient
from langchain.agents import create_agent

client = MultiAgentA2AClient(
    {
        "research_agent": {
            "url": "http://localhost:9999/",
        },
        "coding_agent": {
            "url": "http://localhost:8888/",
            "headers": {"Authorization": "Bearer TOKEN"},
        }
    }
)

tools = await client.get_tools()
agent = create_agent("anthropic:claude-sonnet-4-20250514", tools)

response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Research quantum computing trends"}]}
)
```
### Generated Tool Signature

Each A2A agent tool would have a clear signature:

```python
def research_agent(message: str) -> str:
    """Research agent that can analyze topics and synthesize information.

    Skills:

topic_research: Deep research on any topic
summarization: Synthesize findings into reports
    
    Args:
        message: The task or question to send to the agent.

    Returns:
        The agent's response.
    """
```

### Session/Task Management

The adapter handles A2A task lifecycle internally:

**Stateless by default** (like `langchain-mcp-adapters`): Each `tool.invoke(message="...")` creates a new A2A task, waits for completion, returns the result
**Stateful sessions** (optional): For multi-turn conversations, the tool can accept an optional `task_id` parameter. If provided, it continues an existing A2A task instead of creating a new one. The `task_id` would be stored in LangGraph state:

```python
def research_agent(message: str, task_id: str | None = None) -> str:
    """Research agent that can analyze topics and synthesize information.

    Args:
        message: The task or question to send to the agent.
        task_id: Optional. Continue an existing A2A task instead of creating a new one.

    Returns:
        The agent's response.
    """
```

The returned `ToolMessage` artifact could include the `task_id` for the agent to persist in state if multi-turn is needed.

### Alternatives Considered

**LangGraph Platform A2A endpoint** — requires platform deployment, not available for self-hosted open-source users
**Custom implementations** — works but requires manual A2A client management

### Additional Context

Related issues:

#32645 (closed — pointed to LangGraph Platform, no open-source adapter)

References:

A2A Protocol: https://[google.github.io/A2A/specification/](https://google.github.io/A2A/specification/)
[`lang](https://google.github.io/A2A/specification/)chain-mcp-adapters`: https://[github.com/langchain-ai/langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
[A2A A](https://github.com/langchain-ai/langchain-mcp-adapters)gent Card schema: https://google.github.io/A2A/specification/#agent-card

## Comments

**kevinbfrank:**
@EliasLumer
