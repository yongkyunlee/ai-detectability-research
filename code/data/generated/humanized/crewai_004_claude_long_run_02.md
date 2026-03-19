# Using Tools in CrewAI Agents

An AI agent that can only generate text hits a ceiling fast. It can reason about a web search but can't actually perform one. It can describe how to read a CSV file, but opening it? Not happening. Tools are what close that gap in CrewAI, giving agents the ability to act on the world instead of just talking about it. Getting tool integration right involves more subtlety than the getting-started examples suggest, though. I want to walk through how the tool system actually works under the hood, where the sharp edges are, and how to dodge the most common pitfalls.

## The Two Paths to Defining a Tool

CrewAI gives you two interfaces for creating tools. The first is subclassing `BaseTool`, which hands you full control over input validation, naming, and behavior. You define a Pydantic model for your arguments, give the tool a name and description, and implement a `_run` method:


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


Then there's the `@tool` decorator, which is more concise. It pulls the tool's name from the function name (or a string argument you pass in) and its description from the docstring. Type annotations on the function parameters get introspected to build the argument schema automatically:


from crewai.tools import tool

@tool("stock_price_lookup")
def stock_price_lookup(ticker: str) -> str:
    """Fetches the current price for a given stock ticker."""
    return f"Price for {ticker}: $142.50"


Both approaches produce objects that CrewAI internally converts into a `CrewStructuredTool`, a normalized wrapper the executor understands. The conversion step validates that the tool has a name, a description, and a well-formed argument schema. The decorator approach is easier for quick prototyping; the class-based approach pays off when you need custom caching logic, usage limits, or async execution.

## How Agents Actually Call Tools

Understanding the execution model clears up a lot of debugging headaches. CrewAI supports two distinct tool-calling paths, and which one your agent uses depends on whether the underlying language model supports native function calling.

The ReAct path is the text-based approach. The agent gets tool descriptions embedded in its system prompt and produces structured text: lines like `Action: stock_price_lookup` and `Action Input: {"ticker": "AAPL"}`. The executor parses this output, matches the action name to a registered tool, validates the input against the argument schema, and calls it. The result is injected back into the conversation as an observation, and the agent continues reasoning.

The native function-calling path is what you get when the LLM (GPT-4, Claude, and similar models) supports structured tool calls through its API. Here, tool definitions are converted to an OpenAI-compatible schema and passed alongside the prompt. The model returns typed `ToolCall` objects rather than free-text action strings, and the executor dispatches them directly.

Going native is generally more reliable because the model doesn't need to format text correctly; the API contract handles structure. But it introduces its own category of problems. One notable regression in CrewAI 1.9.x caused the native path to bypass argument validation entirely, sending empty dictionaries to tools that expected required parameters. A custom `BaseTool` wrapper that worked perfectly in version 1.6 could suddenly start failing with `TypeError: _run() missing 1 required positional argument` after an upgrade. Why? Because the executor skipped the Pydantic validation step that the ReAct path always performed.

A related issue affects models that return both text and tool calls in the same response. The executor's check order matters here: if it sees text content before it checks for tool calls, it returns the text as the agent's answer and silently discards the tool invocations. Recent patches have addressed this, but it shows why understanding the execution model matters when something breaks.

## Caching: Saving Tokens and API Calls

Every tool in CrewAI participates in a caching layer by default. The `CacheHandler` stores results in memory, keyed by the combination of tool name and serialized input arguments. When an agent calls the same tool with the same arguments a second time, the cached result comes back without re-executing the tool. A read-write lock protects this, making it safe for concurrent execution.

For most tools, default caching is exactly what you want. Sometimes you need finer control, though. The `cache_function` attribute on a tool lets you decide per-invocation whether to store the result. It receives the arguments and the result, and returns a boolean:


def should_cache(args, result):
    # Only cache successful lookups
    return "error" not in result.lower()

stock_price_tool.cache_function = should_cache


This comes in handy for tools that hit external APIs with rate limits, or for cases where stale results would be dangerous. A stock price lookup might be fine to cache within a single crew run. A tool that checks system health? Probably not.

## MCP Integration: Dynamic Tool Discovery

The Model Context Protocol has become a big part of how CrewAI agents discover and use external capabilities. Rather than hardcoding every tool into your agent definition, MCP lets agents connect to external servers that advertise their own tool catalogs.

CrewAI's MCP implementation uses a factory pattern internally. Each tool invocation creates a fresh client connection, executes the call, and disconnects. This design avoids connection-sharing bugs that surface in concurrent scenarios, where a shared MCP client could produce cancel-scope errors or cross-contaminate state between parallel tool calls.

There's a practical gotcha here that has tripped up a lot of people. If you define an agent with MCP servers but don't explicitly pass `tools=[]`, the MCP tools won't load. The initialization logic checks whether `self.tools is not None` before extending the tool list with MCP-discovered tools, and since the default value for `tools` is `None`, the condition fails silently. The fix is simple:


agent = Agent(
    role="Analyst",
    goal="Analyze data from remote services",
    mcps=[MCPServerHTTP(url="http://localhost:8022/mcp")],
    tools=[],  # required for MCP tools to load
)


Honestly, this one surprised me. It's the kind of subtle default-value interaction that burns hours of debugging time, especially because the agent will still run; it just won't have any tools available.

## Common Pitfalls and How to Avoid Them

**Fabricated tool calls.** With the ReAct execution path, some language models (particularly smaller or less capable ones) will fill in the `Observation` field themselves instead of waiting for the executor to inject real tool output. The agent looks like it's using tools, but it's hallucinating results. Adding explicit instructions like "Do NOT fill in the Observation field; it will be provided after tool execution" to your task description helps. Switching to a model with native function calling support is the more reliable fix.

**Provider-specific argument formats.** AWS Bedrock and OpenAI structure tool-call responses differently. OpenAI nests arguments under `function.arguments` as a JSON string, while Bedrock places them under `input` as a dictionary. CrewAI's argument extraction historically only checked the OpenAI format, causing Bedrock tool calls to arrive with empty argument dictionaries. If you're using Bedrock-hosted models, verify that your CrewAI version includes the fix for this format mismatch. Or inspect the raw tool call objects yourself to confirm arguments are actually being extracted.

**Security in code execution tools.** The `CodeInterpreterTool` has documented vulnerabilities around command injection and sandbox escape. Library installation calls that pass unsanitized strings to `os.system` can be exploited, and Python's object introspection methods (`__class__`, `__bases__`, `__subclasses__`) can break out of the restricted execution sandbox. If you need code execution, use Docker-based safe mode and treat any agent-generated code as untrusted input. No exceptions.

**Token cost spirals.** In multi-agent setups, agents that share context through delegation can end up re-summarizing the same tool results multiple times, compounding token usage. Picture this: a researcher agent calls a search tool, passes results to a writer agent, which then delegates back to the researcher for clarification. That loop can burn through significant API costs on redundant processing. Setting `allow_delegation=False` where you don't need it and structuring tasks as linear pipelines rather than open-ended collaborations keeps costs predictable.

## Practical Recommendations

Start with a small number of well-defined tools rather than giving an agent access to everything. Each tool adds to the system prompt length and increases the chance of the model picking the wrong one. Turn on `verbose=True` during development so you can see exactly which tools are being called and with what arguments.

If your tools hit external services, set `max_usage_count` to prevent runaway loops where an agent retries a failing API call until it exhausts its iteration budget. Pair this with `max_iter` on the agent itself to create a hard ceiling on total execution steps.

For production deployments, I'd say invest in observability before you even think about scaling. The event system emits `ToolUsageStartedEvent`, `ToolUsageFinishedEvent`, and `ToolUsageErrorEvent`. Hook into these to build dashboards showing which tools are being called, how often they fail, and how long they take. Debugging multi-agent systems is notoriously painful, and from what I can tell, the teams that succeed in production are the ones who can trace exactly what happened when something goes wrong.

Tools are where CrewAI agents go from interesting conversational toys to genuinely useful automation. The framework gives you a flexible foundation (multiple definition styles, built-in caching, async support, MCP integration), but the gap between a working demo and a reliable production system comes down to understanding the execution model, respecting the sharp edges, and building defensively around the failure modes that real-world usage will inevitably expose.
