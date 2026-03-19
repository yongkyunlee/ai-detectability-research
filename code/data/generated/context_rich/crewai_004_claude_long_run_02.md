# Using Tools in CrewAI Agents

When an AI agent can only generate text, its usefulness has a hard ceiling. It can reason about a web search, but it cannot perform one. It can describe how to read a CSV file, but it cannot open one. Tools are what bridge that gap in CrewAI — they give agents the ability to act on the world rather than merely narrate about it. Getting tool integration right, however, involves more subtlety than the getting-started examples suggest. This post walks through how CrewAI's tool system actually works under the hood, where the sharp edges are, and how to avoid the most common pitfalls.

## The Two Paths to Defining a Tool

CrewAI offers two primary interfaces for creating tools. The first is subclassing `BaseTool`, which gives you full control over input validation, naming, and behavior. You define a Pydantic model for your arguments, give the tool a name and description, and implement a `_run` method:

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class StockPriceInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")

class StockPriceTool(BaseTool):
    name: str = "stock_price_lookup"
    description: str = "Fetches the current price for a given stock ticker."
    args_schema: type[BaseModel] = StockPriceInput

    def _run(self, ticker: str) -> str:
        # call your pricing API here
        return f"Price for {ticker}: $142.50"
```

The second approach is the `@tool` decorator, which is more concise. It pulls the tool's name from the function name (or a string argument) and its description from the docstring. Type annotations on the function parameters are introspected to build the argument schema automatically:

```python
from crewai.tools import tool

@tool("stock_price_lookup")
def stock_price_lookup(ticker: str) -> str:
    """Fetches the current price for a given stock ticker."""
    return f"Price for {ticker}: $142.50"
```

Both approaches produce objects that CrewAI internally converts into a `CrewStructuredTool` — a normalized wrapper the executor understands. The conversion step validates that the tool has a name, a description, and a well-formed argument schema. If the decorator approach seems easier for quick prototyping, the class-based approach pays off when you need custom caching logic, usage limits, or async execution.

## How Agents Actually Call Tools

Understanding the execution model clarifies many of the debugging headaches people encounter. CrewAI supports two distinct tool-calling paths, and the one your agent uses depends on whether the underlying language model supports native function calling.

**The ReAct path** is the text-based approach. The agent receives tool descriptions embedded in its system prompt and produces structured text — lines like `Action: stock_price_lookup` and `Action Input: {"ticker": "AAPL"}`. The executor parses this output, matches the action name to a registered tool, validates the input against the argument schema, and calls the tool. The result is injected back into the conversation as an observation, and the agent continues reasoning.

**The native function-calling path** is used when the LLM (GPT-4, Claude, and similar models) supports structured tool calls as part of its API. Here, tool definitions are converted to an OpenAI-compatible schema and passed alongside the prompt. The LLM returns typed `ToolCall` objects rather than free-text action strings, and the executor dispatches them directly.

The native path is generally more reliable because the model does not need to format text correctly — the API contract handles structure. But it introduces its own category of problems. One notable regression in CrewAI 1.9.x caused the native path to bypass argument validation entirely, sending empty dictionaries to tools that expected required parameters. A custom `BaseTool` wrapper that worked perfectly in version 1.6 could suddenly start failing with `TypeError: _run() missing 1 required positional argument` after an upgrade, because the executor skipped the Pydantic validation step that the ReAct path always performed.

A related issue affects models that return both text and tool calls in the same response. The executor's check order matters: if it sees text content before it checks for tool calls, it returns the text as the agent's answer and silently discards the tool invocations. This has been addressed in recent patches, but it illustrates why understanding the execution model matters for debugging.

## Caching: Saving Tokens and API Calls

Every tool in CrewAI participates in a caching layer by default. The `CacheHandler` stores results in memory, keyed by the combination of tool name and serialized input arguments. When an agent calls the same tool with the same arguments a second time, the cached result is returned without executing the tool again. This is protected by a read-write lock, making it safe for concurrent execution.

For most tools, default caching is exactly what you want. But sometimes you need finer control. The `cache_function` attribute on a tool lets you decide per-invocation whether to store the result. It receives the arguments and the result, and returns a boolean:

```python
def should_cache(args, result):
    # Only cache successful lookups
    return "error" not in result.lower()

stock_price_tool.cache_function = should_cache
```

This is particularly useful for tools that hit external APIs with rate limits, or for tools where stale results are dangerous. A stock price lookup might be fine to cache within a single crew run, but a tool that checks system health probably should not be.

## MCP Integration: Dynamic Tool Discovery

The Model Context Protocol has become a significant part of how CrewAI agents discover and use external capabilities. Rather than hardcoding every tool into your agent definition, MCP lets agents connect to external servers that advertise their own tool catalogs.

CrewAI's MCP implementation uses a factory pattern internally — each tool invocation creates a fresh client connection, executes the call, and disconnects. This design avoids connection-sharing bugs that surface in concurrent scenarios, where a shared MCP client could produce cancel-scope errors or cross-contaminate state between parallel tool calls.

There is, however, a practical gotcha that has tripped up many users. If you define an agent with MCP servers but do not explicitly pass `tools=[]`, the MCP tools will not load. The initialization logic checks whether `self.tools is not None` before extending the tool list with MCP-discovered tools, and since the default value for `tools` is `None`, the condition fails silently. The fix is straightforward — always pass an empty list:

```python
agent = Agent(
    role="Analyst",
    goal="Analyze data from remote services",
    mcps=[MCPServerHTTP(url="http://localhost:8022/mcp")],
    tools=[],  # required for MCP tools to load
)
```

This kind of subtle default-value interaction is exactly the sort of thing that burns hours of debugging time, especially because the agent will still run — it just will not have any tools available.

## Common Pitfalls and How to Avoid Them

**Fabricated tool calls.** With the ReAct execution path, some language models — particularly smaller or less capable ones — will fill in the `Observation` field themselves instead of waiting for the executor to inject the real tool output. The agent appears to be using tools, but it is actually hallucinating results. Adding explicit instructions like "Do NOT fill in the Observation field; it will be provided after tool execution" to your task description helps, but switching to a model with native function calling support is the more robust fix.

**Provider-specific argument formats.** AWS Bedrock and OpenAI structure tool-call responses differently. OpenAI nests arguments under `function.arguments` as a JSON string, while Bedrock places them under `input` as a dictionary. CrewAI's argument extraction historically checked only the OpenAI format, causing Bedrock tool calls to arrive with empty argument dictionaries. If you are using Bedrock-hosted models, verify that your CrewAI version includes the fix for this format mismatch, or inspect the raw tool call objects to confirm arguments are being extracted.

**Security in code execution tools.** The `CodeInterpreterTool` has documented vulnerabilities around command injection and sandbox escape. Library installation calls that pass unsanitized strings to `os.system` can be exploited, and Python's object introspection methods (`__class__`, `__bases__`, `__subclasses__`) can break out of the restricted execution sandbox. If you need code execution, use Docker-based safe mode and treat any agent-generated code as untrusted input.

**Token cost spirals.** In multi-agent setups, agents that share context through delegation can end up re-summarizing the same tool results multiple times, compounding token usage. A researcher agent that calls a search tool, passes results to a writer agent, which then delegates back to the researcher for clarification, can burn through significant API costs on redundant processing. Setting `allow_delegation=False` where you do not need it and structuring tasks as linear pipelines rather than open-ended collaborations keeps costs predictable.

## Practical Recommendations

Start with a small number of well-defined tools rather than giving an agent access to everything. Each tool adds to the system prompt length and increases the chance of the model picking the wrong one. Use the `verbose=True` flag during development to see exactly which tools are being called and with what arguments.

If your tools hit external services, set `max_usage_count` to prevent runaway loops where an agent retries a failing API call until it exhausts its iteration budget. Pair this with `max_iter` on the agent itself to create a hard ceiling on total execution steps.

For production deployments, invest in observability before scaling. The event system emits `ToolUsageStartedEvent`, `ToolUsageFinishedEvent`, and `ToolUsageErrorEvent` — hook into these to build dashboards that show you which tools are being called, how often they fail, and how long they take. The debugging experience in multi-agent systems is notoriously difficult, and the developers who succeed in production are the ones who can trace exactly what happened when something goes wrong.

Tools are where CrewAI agents transition from interesting conversational systems to genuinely useful automation. The framework provides a flexible foundation — multiple definition styles, built-in caching, async support, MCP integration — but the gap between a working demo and a reliable production system lies in understanding the execution model, respecting the sharp edges, and building defensively around the failure modes that real-world usage inevitably exposes.
