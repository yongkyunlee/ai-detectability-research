# Using Tools in CrewAI Agents

Tools are what turn a CrewAI agent from a fancy chat wrapper into something that can actually do work. Without them, your agent is just an LLM with a persona. With them, it can read files, hit APIs, query databases, scrape the web, and delegate tasks to other agents. The tool system in CrewAI is straightforward to get started with, but there's real depth once you start thinking about caching, usage limits, hooks, and MCP integration.

I want to walk through how tools work under the hood, how to build your own, and where things get tricky in practice.

## The Basics: What a Tool Actually Is

A tool in CrewAI is a Python class or decorated function that an agent can invoke during task execution. Every tool has three things: a name, a description, and a callable that does the actual work. The description matters more than you'd think. It's what the LLM reads to decide whether and how to use the tool, so a vague description means the agent won't call it correctly.

CrewAI ships with over 40 built-in tools in the `crewai-tools` package. You install them with `pip install 'crewai[tools]'`. The catalog covers file I/O (FileReadTool, DirectoryReadTool), web scraping (ScrapeWebsiteTool, SeleniumScrapingTool, FirecrawlCrawlWebsiteTool), search (SerperDevTool, EXASearchTool, BraveSearchTool), databases (PGSearchTool, MySQLTool, NL2SQLTool), vector stores (QdrantVectorSearchTool, WeaviateVectorSearchTool), RAG (RagTool, PDFSearchTool, CSVSearchTool), and AI services (CodeInterpreterTool, DallETool, VisionTool). The list is broad enough that most common agent workflows don't require custom tools at all.

Assigning tools to an agent is dead simple. You pass a list to the `tools` parameter:


from crewai import Agent
from crewai_tools import SerperDevTool, FileReadTool

researcher = Agent(
    role="Market Research Analyst",
    goal="Provide up-to-date market analysis",
    backstory="An expert analyst with a keen eye for market trends.",
    tools=[SerperDevTool(), FileReadTool()],
)


That's it. The agent now knows it can search the web and read files, and it'll decide when to use each based on the task description and its own reasoning loop.

## Building Custom Tools

There are two paths to creating a custom tool. The first is subclassing `BaseTool` from `crewai.tools`. You define `name`, `description`, and an `args_schema` (a Pydantic model), then implement the `_run` method. The second is the `@tool` decorator, which is more concise and works well for simpler tools.

The decorator approach looks like this:


from crewai.tools import tool

@tool("Currency Converter")
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another using current exchange rates."""
    # your conversion logic
    return f"{amount} {from_currency} = {converted} {to_currency}"


The docstring becomes the tool description. The function signature becomes the args schema. CrewAI infers it automatically using Pydantic's `create_model`. If the function lacks a docstring, the framework raises a ValueError. And if it lacks type annotations, you get another error. These aren't optional.

For the class-based approach, you get more control. You can define a proper Pydantic `BaseModel` as the `args_schema`, which gives you field-level descriptions, validators, and defaults. The framework uses `generate_model_description` internally to produce a JSON schema representation of the arguments, which gets injected into the tool description sent to the LLM.

One detail worth noting: `BaseTool` extends Pydantic's `BaseModel`, so tool instances are themselves Pydantic models. This means field validation runs at instantiation, and you can serialize tools cleanly.

## Async Tools

CrewAI supports async tools natively. You can either decorate an async function with `@tool` or subclass `BaseTool` and implement `_arun` alongside `_run`. The framework detects whether a tool function is a coroutine and routes execution accordingly. If you only provide a sync `_run` and the agent tries to call it in an async context, CrewAI falls back to `asyncio.run`. If you provide `_arun`, it uses the async path directly.

This is useful for I/O-bound tools that make network requests or hit databases. But don't overthink it. If your tool is a quick computation or a local file read, sync is fine. Async tools matter when you're hitting external APIs under load and don't want to block the executor.

## Caching, Usage Limits, and result_as_answer

Three features on the `BaseTool` class deserve attention.

**Caching** is on by default. When an agent calls a tool with the same arguments twice, CrewAI returns the cached result instead of re-executing. You can override this with a custom `cache_function` that takes `(args, result)` and returns a boolean. If it returns `False`, the result won't be cached. This is handy for tools where the output changes over time, like a live stock price lookup.

**Usage limits** were added to prevent runaway tool calls. Set `max_usage_count` on any tool, and the framework will stop the agent from calling it beyond that threshold. The `BaseTool` source implements this with a thread-safe lock in `_claim_usage`, so it works correctly even in concurrent scenarios. Once the limit is hit, the agent gets back an error message telling it the tool is exhausted.

**result_as_answer** is a flag that forces the tool output to become the task result directly, bypassing any post-processing or summarization by the agent. Set `result_as_answer=True` when you instantiate the tool. This is useful when you want the raw tool output without the agent paraphrasing or modifying it.

Using the `@tool` decorator with `max_usage_count=5` is simpler than subclassing for many cases, but the class-based approach gives you finer control. That's the real trade-off here: the decorator is simpler, but `BaseTool` subclassing gives you explicit args schemas, custom caching logic, and both sync and async implementations in one class.

## Tool Call Hooks

CrewAI v1.11.0 introduced tool call hooks, and they're a substantial feature for production systems. Hooks intercept tool execution at two points: before the tool runs and after it completes. A before hook receives a `ToolCallHookContext` object and can inspect the tool name, input arguments, the agent, and the current task. It returns `False` to block execution, or `None`/`True` to allow it.

After hooks can modify the result string or leave it unchanged by returning `None`.

Registration happens three ways. Global hooks apply to all crews and agents:


from crewai.hooks import register_before_tool_call_hook

def audit_log(context):
    print(f"Tool: {context.tool_name}, Agent: {context.agent.role}")
    return None

register_before_tool_call_hook(audit_log)


Decorator-based registration uses `@before_tool_call` and `@after_tool_call`. And crew-scoped hooks use `@before_tool_call_crew` and `@after_tool_call_crew` on methods within a `@CrewBase` class, so they only apply to that specific crew.

The practical use cases are safety guardrails (blocking destructive tools), human approval gates (prompting a user before `send_email` runs), input sanitization, result redaction (stripping API keys or PII from tool output), rate limiting, and analytics. An important implementation detail: you must modify `context.tool_input` in-place. Replacing the dict reference with a new object doesn't work because the framework holds a reference to the original dictionary.

## MCP Integration

The Model Context Protocol gives CrewAI agents access to external tool servers over a standardized protocol. CrewAI supports three transports: stdio for local processes, Server-Sent Events for streaming, and Streamable HTTP for remote servers. The simplest approach is the DSL integration using the `mcps` field directly on an agent:


agent = Agent(
    role="Research Analyst",
    mcps=["https://mcp.exa.ai/mcp?api_key=your_key", "snowflake"]
)


Tools from MCP servers are automatically discovered and made available. For more control, use `MCPServerStdio`, `MCPServerHTTP`, or `MCPServerSSE` with explicit configuration. Tool filtering is supported through `create_static_tool_filter` for allow/block lists and dynamic filter functions that can make context-aware decisions.

Connection management is handled automatically when you use `@CrewBase`. The adapter starts lazily on first use and shuts down after kickoff completes. The default connection timeout is 30 seconds, configurable via `mcp_connect_timeout`. If an MCP server is unreachable, the agent continues with its other tools and logs a warning.

## Where Things Go Wrong

The tool system isn't without rough edges. A few known issues are worth knowing about.

The `CodeInterpreterTool` had a reported sandbox escape vulnerability (issue #4516) where Python's introspection capabilities could bypass the restricted sandbox. The v1.11.0rc1 changelog confirms a fix was applied, but the broader lesson is clear: Python-level attribute filtering isn't a reliable security boundary for code execution. If you need real isolation, run code in a container.

There's a bug where native tool calls get discarded if the LLM returns both text and tool calls in the same response (issue #4788, reported against version 1.10.1). The text response takes precedence because of check ordering in the LLM response handler. A fix was submitted to reorder the checks so tool calls are returned first.

Bedrock users have hit issues where Claude models return empty input parameters on MCP tool calls (issue #4470), while the same setup works fine with Gemini. This appears to be a schema compatibility issue between Bedrock's Claude implementation and CrewAI's tool schema format.

And if you reuse the same agent across multiple sequential tasks, the executor's message history accumulates and doesn't get cleared (issue #4319). After a few tasks, the context window fills up with duplicate system messages and the LLM starts returning empty responses. The workaround is creating fresh agent instances for each task, which defeats the purpose of reuse.

## Practical Advice

Keep tool descriptions concise but specific. The LLM uses the description to decide when a tool applies. If two tools have overlapping descriptions, the agent will pick the wrong one. CrewAI's tool selection uses a `SequenceMatcher` with a 0.85 similarity threshold for fuzzy matching, which means a close-but-wrong tool name from the LLM still resolves correctly. But ambiguous descriptions confuse the model before it even gets to the name.

Start with the built-in tools. The `crewai-tools` package covers most common needs, and the tools handle error cases you'd otherwise have to write yourself. Custom tools make sense when your agent needs to hit internal APIs or perform domain-specific logic.

Use `verbose=True` on agents during development. CrewAI logs tool selection, argument parsing, cache hits, usage counts, and errors. Without verbose output, debugging a misused tool is guessing.

And consider tool hooks early if you're building anything that touches external systems. A before hook that logs every tool call costs almost nothing and saves hours of debugging when an agent starts behaving unexpectedly. The hooks system is one of CrewAI's strongest recent additions, and it's the kind of infrastructure that separates a prototype from something you'd run in production.

Tools are the interface between your agent's reasoning and the real world. Get them right, and the agent can do genuinely useful work. Get them wrong, and you're watching an LLM hallucinate tool calls while your API bill climbs. CrewAI gives you a solid foundation here. The framework handles caching, error recovery, argument validation, and usage tracking out of the box. Your job is to give the agent the right tools with the right descriptions and let it work.
