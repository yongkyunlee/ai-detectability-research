# Using Tools in CrewAI Agents

When you hand an AI agent a task, the agent's intelligence matters far less than the actions it can take. In CrewAI, actions come in the form of tools — callable functions that let agents search the web, query databases, write files, or interact with any external system. Getting tool integration right is arguably the most consequential part of building a reliable crew. Here is what you need to know.

## Defining Tools: Two Approaches

CrewAI offers two primary patterns for creating tools. The first is subclassing `BaseTool`, which gives you fine-grained control. You define a `name`, a `description` that the agent reads when deciding whether the tool is relevant, and an `args_schema` built on Pydantic's `BaseModel` for input validation. Your actual logic goes into a `_run()` method, with an optional `_arun()` counterpart for asynchronous execution.

The second pattern is the `@tool` decorator, which wraps a plain function and infers the schema from its type annotations and docstring. This is the faster path for simple utilities. Decorate, annotate, document, and the framework handles the rest. Both approaches produce the same underlying object, so the choice comes down to whether you need lifecycle hooks and custom caching or just want something quick.

A few properties deserve special attention. Setting `result_as_answer=True` tells the framework to pass the tool's raw output directly as the task result, bypassing the agent's tendency to summarize or rephrase. This is indispensable when you need exact data — a JSON payload from an API, for instance — delivered without modification. The `max_usage_count` attribute caps how many times a tool can be invoked during a single task, which protects you from runaway loops against rate-limited services.

## How Agents Choose and Call Tools

Under the hood, CrewAI supports two execution paths. The classic path follows a ReAct loop: the agent generates a chain of Thought, Action, Action Input, and Observation steps as text, and the framework parses that text to identify which tool to call with which arguments. This works with any language model, since it relies only on the model's ability to follow a structured prompt format.

The newer path, introduced around version 1.9, leverages native function calling for models that support it, such as those from OpenAI or Anthropic. Instead of parsing free-form text, the framework passes tool schemas directly to the model's API, and the model returns structured function call objects. This tends to be more reliable with capable models because there is no ambiguity in the parsing step.

Each path has trade-offs. The ReAct approach is flexible but fragile — it depends on the model faithfully reproducing a specific text pattern, and smaller or less capable models sometimes fabricate observations instead of actually invoking tools. The native calling path eliminates parsing issues but has historically introduced its own bugs around argument validation, since it bypasses some of the safety checks that the ReAct path performs through Pydantic schema enforcement.

## Tool Hooks: Intercepting Execution

One of CrewAI's more powerful features is its hook system for tool calls. You can register functions that run before or after any tool invocation. A before-hook receives a context object containing the tool name, arguments, the agent, and the current task. It can inspect or modify the input dictionary in place, and returning `False` blocks execution entirely. This opens the door to input sanitization, rate limiting, or safety guardrails that prevent an agent from, say, deleting production data.

After-hooks work similarly but operate on results. They can transform, redact, or log the output before it reaches the agent. If your tool returns sensitive information that only partially relevant to the task, an after-hook can strip what the agent does not need to see.

Hooks can be registered globally, scoped to a specific crew, or applied via decorators. Keeping them lightweight matters, since they fire on every single tool invocation across every agent in the crew.

## MCP Integration

CrewAI also supports the Model Context Protocol for discovering and calling tools hosted on external servers. Two wrapper classes handle the connection lifecycle: one creates a fresh client per invocation for safe parallel execution, while the other manages persistent connections with timeout handling and exponential backoff retries.

MCP tools are automatically prefixed with their server name to avoid collisions — a tool called `list_files` on a server named `mcp_docs` becomes `mcp_docs_list_files`. One important gotcha: if your agent uses only MCP tools and no local ones, you must explicitly pass `tools=[]` rather than omitting the parameter. Passing nothing causes a condition that skips MCP tool loading entirely.

## Common Pitfalls

Several recurring issues show up in practice. The most frustrating is the agent appearing to use a tool without actually calling it — generating a complete ReAct trace with fabricated observations. This happens most often with smaller models and stems from the framework's parser accepting a "Final Answer" block even when no real tool execution occurred.

Argument validation inconsistencies between the two execution paths can also cause headaches. In native function calling mode, if the model returns empty arguments for a tool that expects them, the resulting `TypeError` gets caught and retried indefinitely rather than surfacing a clear validation error. This has been a known regression area.

When using structured output with `output_pydantic`, be aware that certain versions inject the output schema as a native tool, which can interfere with your actual tools being forwarded to the model. If your agent suddenly stops calling tools after you add output validation, this interaction is likely the cause.

## Practical Advice

Write tool descriptions as if you were explaining the tool to a junior colleague who has never seen your codebase. The agent selects tools based almost entirely on these descriptions, so vague or overly technical language leads to poor choices. Test tools in isolation before wiring them into an agent — this separates tool bugs from orchestration bugs and saves significant debugging time.

For production deployments, invest in before-hooks for input validation and after-hooks for logging. The observability they provide is essential when diagnosing why an agent chose a particular tool or why it received unexpected results. Set `max_usage_count` on any tool that hits an external service with rate limits or costs per call.

Finally, keep an eye on which execution path your model uses. If you are running a model that supports native function calling, verify that arguments are being passed correctly by logging the raw inputs your tools receive. The reliability gap between the two paths narrows with each release, but understanding where your specific model and provider combination falls remains important for building crews that work consistently.
