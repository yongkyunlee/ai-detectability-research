# Using Tools in CrewAI Agents: What Actually Works and What Will Bite You

Tools are what separate a useful agent from an expensive autocomplete. CrewAI ships over 40 pre-built tools and gives you two clean paths for building your own, but the gap between the documentation's happy path and a production deployment is wider than you'd expect. I've been digging through the framework's internals, its issue tracker, and the community discussions around it, and there's a lot worth unpacking here.

## The Basics: How Tools Plug Into Agents

CrewAI tools are Pydantic models. Every tool inherits from `BaseTool`, which lives in `crewai/tools/base_tool.py` and defines the contract: a `name`, a `description`, an `args_schema`, and an abstract `_run` method you implement. The framework validates inputs against your Pydantic schema before execution, tracks usage counts with a thread-safe lock, and handles caching by default.

You attach tools to agents through the `tools` parameter. That's it. The agent gets access, the LLM sees the tool descriptions in its prompt, and CrewAI's executor handles the invocation loop.


from crewai import Agent
from crewai_tools import SerperDevTool, FileReadTool

researcher = Agent(
    role="Market Research Analyst",
    goal="Provide up-to-date market analysis",
    tools=[SerperDevTool(), FileReadTool()],
    verbose=True
)


You can also override an agent's tools at the task level. So if your researcher normally has web search but a specific task should only read local files, pass `tools=[FileReadTool()]` on the `Task` instead. This is a nice design choice - it keeps agent definitions broad and lets tasks narrow the scope.

## Two Ways to Build Custom Tools

CrewAI gives you two approaches. Subclass `BaseTool` when you need full control: custom schemas, state, lifecycle hooks. Use the `@tool` decorator for simpler cases where a function with a docstring and type annotations is enough. The decorator requires both - a docstring for the tool description and type annotations for schema generation. Skip either and it raises a `ValueError`.

Here's the subclass approach:


from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    argument: str = Field(..., description="The search query.")

class MyCustomTool(BaseTool):
    name: str = "custom_search"
    description: str = "Searches an internal knowledge base."
    args_schema: type[BaseModel] = MyToolInput

    def _run(self, argument: str) -> str:
        return do_search(argument)


And the decorator:


from crewai.tools import tool

@tool("custom_search")
def custom_search(query: str) -> str:
    """Searches an internal knowledge base for relevant documents."""
    return do_search(query)


The decorator is simpler, but the subclass gives you access to things like `result_as_answer` - a flag that tells CrewAI to return the tool's output directly as the agent's final answer, skipping further reasoning. That's useful for tools where the output is already the finished product. Both approaches support `max_usage_count`, which caps how many times a tool can fire during execution. Set `max_usage_count=5` on a web search tool, and after five calls the agent gets back an error string telling it the tool is exhausted. The framework enforces this atomically with `threading.Lock`, so it's safe in concurrent setups.

## Caching: Simple by Default, Flexible When You Need It

Every tool caches results by default. Call the same tool with the same input twice, and the second call returns the cached value without re-executing. This is a sensible default for search tools and API calls, but sometimes you don't want it.

The `cache_function` parameter gives you control. It receives the arguments and the result, and returns a boolean - `True` to cache, `False` to skip. The documentation shows a multiplication tool that only caches even results, which is a contrived example, but the pattern is real. We've found it useful for tools that hit APIs with rate limits: cache successful responses, don't cache errors or partial results.

## Async Support

CrewAI handles async tools natively. You can define `_run` as an `async def` on your `BaseTool` subclass, or use the `@tool` decorator on an async function. The framework detects coroutines and awaits them appropriately. If you call `run()` on an async tool from a sync context, it falls back to `asyncio.run()`. And for Flow-based workflows, `crew.kickoff_async()` keeps everything non-blocking.

This works well enough for I/O-bound tools like HTTP requests or database queries. But don't expect parallel tool execution across multiple agents - that's a different layer of concurrency governed by the crew's process configuration, not the tool's async support.

## Where Things Get Rough

The tool system's design is clean, but real-world usage has exposed some sharp edges. I'll walk through the ones I think matter most.

**Tools That Don't Actually Execute.** Issue #3154 documented a genuinely alarming behavior: agents generating a full `Thought → Action → Observation → Final Answer` trace without ever calling `tool.run()`. The LLM would fabricate the observation text, making it look like the tool ran when it didn't. This happened because CrewAI's ReAct-style prompting left enough ambiguity for the LLM to fill in the `Observation:` field itself, short-circuiting actual execution. If you're not checking whether your tools are actually firing - with logging, with telemetry, with anything - you should start.

**Native Tool Calling Regressions.** Version 1.9.3 introduced a regression where custom `BaseTool` wrappers lost their arguments during native tool-calling mode. The error message was clear enough: `ParsedBedrockKBRetrieverTool._run() missing 1 required positional argument: 'query'`. The root cause was that the native path in `agent_utils.py` mapped directly to `tool.run` instead of going through `CrewStructuredTool.invoke()`, which meant Pydantic validation got skipped and arguments weren't properly unpacked. This worked correctly in version 1.6.1. If you're building custom tools for AWS Bedrock, test on every minor release.

**Message Accumulation Across Tasks.** Issues #4319 and #4389 documented a state pollution bug where the agent executor didn't reset its message history between sequential tasks. Task two would see all of task one's messages, task three would see both, and so on. The result was confused LLM context, duplicate system messages, and eventually empty or nonsensical responses. This is the kind of bug that doesn't show up in demos with one task but ruins any real workflow.

**Bedrock Format Mismatches.** AWS Bedrock uses `input` where OpenAI uses `arguments` in tool call responses. CrewAI's extraction logic in version 1.10.1 used `.get("arguments", "{}")`, which returns a truthy empty JSON string and prevents the fallthrough to Bedrock's `input` field. The result: every Bedrock tool call received empty arguments. If you're running on Bedrock, this is a must-know.

## Security: The CodeInterpreterTool Problem

Issue #4516 reported two vulnerabilities in `CodeInterpreterTool` that deserve attention. The first is command injection in `run_code_unsafe()` at lines 378-379, where `os.system(f"pip install {library}")` passes unsanitized input directly to the shell. The second is a sandbox escape through Python's object introspection - `type`, `getattr`, `__class__`, `__bases__`, and `__subclasses__()` aren't blocked, so a crafted payload can walk the class hierarchy to access arbitrary modules. The first vulnerability has a CVSS score in the 7.5-8.0 range. The second is worse, at 8.5-9.0. Don't run `CodeInterpreterTool` on untrusted input without Docker isolation.

## The Observability Gap

A recurring theme across community discussions - on Reddit, on Hacker News, in issue comments - is that you can't see what's happening between your agent and the LLM. You hand tools to an agent, kick off a crew, and get output. But you don't see the actual prompts sent to the model. You don't see which tools were considered and rejected. You don't see why the agent chose one tool over another. And when something goes wrong, you're left guessing.

One Reddit comparison between CrewAI and LangGraph put it bluntly: CrewAI's abstractions hide the agent-to-LLM boundary, which is exactly the boundary you most need to inspect. LangGraph's explicit graph model with LangSmith integration lets you see every prompt at every node. CrewAI is simpler to get started with, but LangGraph gives you the visibility you need to debug production issues. That's a real trade-off you should weigh before committing.

## MCP Integration: Promising but Incomplete

CrewAI added Model Context Protocol support, letting agents discover and use tools hosted on MCP servers. The feature request landed as issue #1813 and eventually shipped. But bugs followed. Version 1.7.2 had a conditional check - `if mcps and self.tools is not None` - that prevented MCP tool loading when `tools` was left as `None` instead of an empty list. The workaround was passing `tools=[]` explicitly, which is easy enough once you know about it but baffling if you don't.

Community projects have started building discovery and trust layers on top of MCP integration, with semantic search across servers and capability matching. The foundation is there. It just needs more hardening.

## Practical Advice

Keep your tool descriptions precise. The LLM selects tools based on the description text - CrewAI uses fuzzy matching with a `SequenceMatcher` ratio threshold above 0.85, but the initial selection still depends on the model understanding what each tool does. Vague descriptions lead to wrong tool choices.

Use `verbose=True` during development. It surfaces tool usage counts, execution flow, and selection decisions. Set `function_calling_llm` on your agent if you want to use a cheaper model for tool selection while keeping an expensive model for reasoning - CrewAI supports splitting these concerns.

Test tool execution explicitly. Don't trust that a clean final output means your tools actually ran. Add logging inside `_run`. Check your telemetry. The fabricated-observation problem from issue #3154 proves that an agent can produce plausible output while doing nothing real.

And pin your CrewAI version. The framework requires Python 3.10+ and moves fast - regressions in tool calling between 1.6.1 and 1.9.3, format bugs in 1.10.1 - and the tool layer is where breaking changes hit hardest. Install with `pip install 'crewai[tools]'` and lock the version in your requirements file.

Tools are the most useful part of CrewAI, and the most fragile. Get them right, verify they're actually running, and don't assume the framework handles edge cases that it doesn't document. That's where the real engineering happens.
