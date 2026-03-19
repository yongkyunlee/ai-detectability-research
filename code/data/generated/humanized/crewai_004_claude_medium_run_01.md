# Using Tools in CrewAI Agents

An AI agent's intelligence doesn't matter much if it can't actually do anything. In CrewAI, tools are the callable functions that let agents search the web, query databases, write files, or talk to external systems. Getting this part right is, I think, the single most impactful thing you can do when building a reliable crew.

## Defining Tools: Two Approaches

You've got two patterns for creating tools. Subclassing `BaseTool` is the more structured route: you define a `name`, a `description` the agent reads when deciding if the tool is relevant, and an `args_schema` built on Pydantic's `BaseModel` for input validation. Your logic goes in a `_run()` method, with an optional `_arun()` for async.

Then there's the `@tool` decorator. Faster. You wrap a plain function and the framework infers the schema from type annotations and the docstring. Decorate, annotate, document, done. Both approaches produce the same underlying object, so your choice really comes down to whether you need lifecycle hooks and custom caching or just want something quick and simple.

A couple of properties are worth calling out. Setting `result_as_answer=True` tells the framework to pass raw output directly as the task result, skipping the agent's habit of summarizing or rephrasing. When you need exact data (a JSON payload from an API, for instance) delivered without modification, this is the way. There's also `max_usage_count`, which caps how many times a tool can be called during a single task; it protects you from runaway loops against rate-limited services.

## How Agents Choose and Call Tools

CrewAI supports two execution paths under the hood. The classic one follows a ReAct loop: the agent generates Thought, Action, Action Input, and Observation steps as text, and the framework parses that text to figure out which tool to call with which arguments. Any language model works here, since it only requires the model to follow a structured prompt format.

The newer path came around version 1.9. It uses native function calling for models that support it (OpenAI, Anthropic, etc.). Instead of parsing free-form text, the framework passes tool schemas directly to the model's API, and the model returns structured function call objects. More reliable with capable models, from what I can tell, because there's no ambiguity in parsing.

Trade-offs exist for each. ReAct is flexible but fragile: it depends on the model faithfully reproducing a specific text pattern, and smaller models sometimes fabricate observations instead of actually calling tools. Native calling eliminates the parsing problem but has historically introduced its own bugs around argument validation, since it bypasses some safety checks that the text-based path performs through Pydantic schema enforcement.

## Tool Hooks: Intercepting Execution

The hook system for tool calls is honestly one of CrewAI's more underappreciated features. You can register functions that run before or after any tool invocation. A before-hook receives a context object containing the tool name, arguments, the agent, and the current task. It can inspect or modify the input dictionary in place; returning `False` blocks execution entirely. So you get input sanitization, rate limiting, or safety guardrails that prevent an agent from, say, deleting production data.

After-hooks work on results. They can transform, redact, or log output before the agent sees it. Useful when your tool returns sensitive information that's only partially relevant to the task.

You can register hooks globally, scope them to a specific crew, or apply them via decorators. Keep them lightweight. They fire on every single invocation across every agent in the crew.

## MCP Integration

CrewAI supports the Model Context Protocol for discovering and calling tools on external servers. Two wrapper classes handle connection lifecycle: one creates a fresh client per invocation for safe parallel execution, the other manages persistent connections with timeout handling and exponential backoff retries.

Tools from MCP servers get automatically prefixed with the server name to avoid collisions, so `list_files` on a server named `mcp_docs` becomes `mcp_docs_list_files`. One gotcha that bit me: if your agent uses only MCP tools and no local ones, you must explicitly pass `tools=[]` rather than omitting the parameter. Passing nothing triggers a condition that skips MCP tool loading entirely.

## Common Pitfalls

The most frustrating issue I've run into is the agent appearing to use a tool without actually calling it. It generates a complete ReAct trace with fabricated observations. This happens most often with smaller models and stems from the framework's parser accepting a "Final Answer" block even when no real execution occurred.

Argument validation inconsistencies between the two execution paths can also cause headaches. In native function calling mode, if the model returns empty arguments for a tool that expects them, the resulting `TypeError` gets caught and retried indefinitely. No clear validation error surfaces. Known regression area, not 100% sure it's fully resolved yet.

Watch out when using structured output with `output_pydantic` too. Certain versions inject the output schema as a native tool, which can interfere with your actual tools being forwarded to the model. If your agent suddenly stops calling tools after you add output validation, that interaction is likely the culprit.

## Practical Advice

Write tool descriptions like you're explaining them to a junior colleague who's never seen your codebase. Agents select tools based almost entirely on these descriptions, so vague or overly technical language leads to poor choices. Test each tool in isolation before wiring it into an agent. This separates tool bugs from orchestration bugs and saves you a lot of debugging time.

For production, invest in before-hooks for input validation and after-hooks for logging. The observability they give you is essential when you're trying to figure out why an agent picked a particular tool or got unexpected results. Set `max_usage_count` on anything hitting an external service with rate limits or per-call costs.

One last thing: keep an eye on which execution path your model uses. If you're running one that supports native function calling, verify arguments are being passed correctly by logging the raw inputs your tools receive. The reliability gap between the two paths narrows with each release, but knowing where your specific model and provider combination falls still matters for building crews that work consistently.
