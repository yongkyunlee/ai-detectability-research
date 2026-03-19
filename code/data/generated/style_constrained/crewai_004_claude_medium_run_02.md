# Using Tools in CrewAI Agents

Tools are how CrewAI agents touch the real world. Without them, your agents are just expensive text generators. With them, they can read files, search the web, query databases, and delegate work to each other. But the abstraction CrewAI provides isn't trivial, and there are design decisions worth understanding before you wire up your first `Agent`.

## Two Ways to Build a Tool

CrewAI gives you two paths for defining custom tools. You can subclass `BaseTool`, which extends Pydantic's `BaseModel`, or you can use the `@tool` decorator for something lighter. The subclass approach requires you to set `name`, `description`, and implement a `_run` method. You also get the option to define an `args_schema` using a Pydantic model for strict input validation. If you don't supply one, the framework will infer a schema from your `_run` method's signature automatically.

The decorator path is more concise. Slap `@tool("My Tool Name")` on a function with a docstring and type annotations, and you've got a working tool. Both the docstring and annotations are mandatory here - the decorator raises a `ValueError` if either is missing. This is a reasonable guardrail, because the description text gets embedded into the prompt the LLM sees when deciding which tool to invoke. A vague description means the agent picks the wrong tool.

So which should you reach for? The `@tool` decorator is simpler, but `BaseTool` gives you more control over caching, async behavior, and schema definitions. For a one-off utility, use the decorator. For anything you'll reuse or need to configure at runtime, subclass `BaseTool`.

## Argument Validation and the LLM Problem

Here's something that bit us. LLMs don't always produce clean tool-call arguments. They hallucinate extra fields, omit required ones, or pass the wrong types. CrewAI addresses this by running all keyword arguments through Pydantic validation before the tool executes. If validation fails, you get a `ValueError` with a schema hint showing the expected arguments and required fields. And critically, the usage counter doesn't increment on validation failure, so a botched call doesn't burn one of your limited invocations.

Extra kwargs that aren't in the schema get silently stripped. This is a pragmatic choice - it means a model that hallucinates an `extra_hallucinated_field` alongside your real arguments won't crash the tool. The test suite explicitly covers this case, which tells me the CrewAI team has dealt with this in production.

## Controlling Tool Usage

The `max_usage_count` parameter caps how many times an agent can invoke a given tool. Set `max_usage_count=5` on a `FileReadTool`, and after five calls the agent gets back a message saying the tool has reached its limit. The counter is thread-safe - a `threading.Lock` protects the increment - which matters when you're running crews with concurrent agent execution. You can also call `reset_usage_count()` to zero it out between runs.

This is more useful than it sounds. Agents in autonomous mode will sometimes loop on a tool, calling it repeatedly with slightly different inputs while burning through tokens. Capping usage forces the agent to move on and actually reason about what it has.

## Async Tools

CrewAI handles both sync and async tools. You can define `async def _run` on a `BaseTool` subclass, or pass an async function to the `@tool` decorator. The framework detects whether the result is a coroutine and calls `asyncio.run()` transparently when needed. For more control, implement both `_run` (sync) and `_arun` (async) on the same tool class. The `arun` method on `BaseTool` will use `_arun` directly in an async context, which avoids the overhead of spinning up a new event loop.

We found this especially useful for I/O-bound tools like web fetchers, where blocking the main thread defeats the purpose of running agents concurrently.

## Tool Hooks: Before and After

The hook system is where CrewAI gets genuinely interesting for production use. You can register `@before_tool_call` and `@after_tool_call` functions that intercept every tool invocation. A before-hook receives a `ToolCallHookContext` with the tool name, input dict, the agent, the current task, and the crew. It can modify inputs in-place, log the call, or return `False` to block execution entirely.

After-hooks get the same context plus the tool result, and can transform or sanitize the output. The documentation shows patterns for rate limiting, result redaction (stripping API keys and email addresses from tool output), and human approval gates where sensitive tools require explicit confirmation before running.

One subtlety: you must modify `context.tool_input` in-place. Reassigning the dict - `context.tool_input = {'query': 'new'}` - doesn't propagate. This is called out explicitly in the docs, which suggests people have been burned by it.

Hooks can be registered globally, via decorator, or scoped to a specific crew with `@before_tool_call_crew`. The scoped variant is the right call for multi-crew setups where different pipelines have different security requirements.

## Security: The CodeInterpreterTool Problem

Tools that execute code deserve extra scrutiny. Issue #4516 in the CrewAI repo documents a command injection vulnerability in `CodeInterpreterTool` where library names from an LLM pass directly to `os.system(f"pip install {library}")` without sanitization. A payload like `numpy; id #` executes arbitrary shell commands. The restricted sandbox mode fares worse - Python's introspection capabilities (`__class__.__bases__[0].__subclasses__()`) allow complete sandbox escape, rated CVSS 8.5-9.0.

The lesson generalizes beyond CrewAI. Python-level sandboxing is insufficient for untrusted code execution. A follow-up proposal (issue #4810) suggests WASM-based isolation via a `crewai-capsule` package, with cold starts around one second and subsequent runs at roughly 10ms. That's the right direction. If your agents run generated code, don't rely on attribute filtering - use process-level or container-level isolation.

## Built-in Agent Tools

CrewAI ships two collaboration tools automatically: `DelegateWorkTool` and `AskQuestionTool`. These let agents hand off subtasks or query coworkers by role name. They're wired in through the `AgentTools` class and formatted with the available coworker roles. You don't need to add them manually - they're injected when the crew has multiple agents.

The broader toolkit, installable via `pip install 'crewai[tools]'`, includes over 40 pre-built tools spanning file I/O, web scraping (Firecrawl, Selenium), RAG search across PDF/CSV/JSON/DOCX, database connectors for PostgreSQL and MySQL, and integrations with services like S3 and DALL-E.

## Practical Advice

Start with the `@tool` decorator and pre-built tools. Add `max_usage_count` early - it's cheaper than debugging infinite tool loops after the fact. Use hooks for observability from day one, because as community discussions consistently point out, tool failures often surface as reasoning failures, and without visibility into what the tool actually did, you'll debug the wrong layer first. And if any of your tools touch shell commands or execute code, treat that as a security boundary that demands real isolation, not Python-level filtering.
