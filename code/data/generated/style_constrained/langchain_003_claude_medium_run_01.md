# Using LangChain Agents and Tools for Autonomous Task Execution

Agents are the reason most of us looked at LangChain in the first place. The promise is straightforward: give an LLM a set of tools, define a goal, and let it figure out the steps. The reality is messier, and the framework has gone through significant architectural changes to close that gap. I want to walk through how agents and tools actually work under the hood, where the current design sits after the v1 rewrite, and what you should think about before handing the loop over to an LLM.

## The Core Loop

A LangChain agent follows a simple cycle. The LLM receives a prompt and a list of available tools. It decides whether to call a tool or return a final answer. If it calls a tool, the framework executes that tool, feeds the observation back into the LLM, and the cycle repeats. The code in `langchain-core` models this with three schemas: `AgentAction` (a request to execute a specific tool with specific input), `AgentStep` (the result of that execution), and `AgentFinish` (the signal that the agent is done and has a return value). That's it. Everything else is orchestration around this loop.

The `@tool` decorator is the quickest way to make a Python function available to an agent. You annotate a function, provide a docstring, and LangChain infers the argument schema from the type hints via Pydantic. The `StructuredTool` class handles multi-argument tools, where each parameter gets its own schema field. This matters because the LLM doesn't call your function directly — it generates a JSON payload matching that schema, and the framework validates and dispatches it.

## From `initialize_agent` to `create_agent`

The old entry point was `initialize_agent`. It's been deprecated since version 0.1.0 and is slated for removal in 1.0. The replacement is `create_agent`, which lives in `langchain.agents.factory` and builds a compiled LangGraph state graph under the hood. The signature tells you what changed:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="openai:gpt-4",
    tools=[my_tool],
    system_prompt="You are a helpful assistant.",
    middleware=[ModelRetryMiddleware(), ToolCallLimitMiddleware()],
)
```

Where `initialize_agent` took an `AgentType` enum and an `AgentExecutor`, `create_agent` takes a model (string or instance), tools, and — critically — a middleware list. The old `AgentExecutor` handled everything in one monolithic class. The new design decomposes cross-cutting concerns into composable middleware.

## Middleware: Where the Real Control Lives

The middleware system is arguably the most important change for production use. LangChain ships with built-in middleware classes including `ModelRetryMiddleware`, `ModelFallbackMiddleware`, `ToolCallLimitMiddleware`, `ModelCallLimitMiddleware`, `PIIMiddleware`, `HumanInTheLoopMiddleware`, `SummarizationMiddleware`, and `ShellToolMiddleware`, among others. Each middleware can hook into specific lifecycle points: `before_model`, `after_model`, `before_agent`, `after_agent`, `wrap_model_call`, and `wrap_tool_call`.

So instead of subclassing `AgentExecutor` and overriding methods — which people were doing constantly — you compose behaviors. Need to cap tool invocations? Add `ToolCallLimitMiddleware`. Need a human approval step before destructive operations? Add `HumanInTheLoopMiddleware`. Need PII redaction on outputs? Add `PIIMiddleware`. The composability is a real improvement.

But there are rough edges. Issue #35011 demonstrates that streaming currently bypasses middleware — if you're using `PIIMiddleware` with `strategy="block"` and streaming mode, the raw tokens reach the user before the middleware can intercept them. The middleware architecture runs as a post-processing step, which fundamentally conflicts with token-by-token streaming. The maintainers have acknowledged this requires an architectural change, not just a patch.

## Error Handling and Invalid Tool Calls

One area that deserves attention is how agents handle malformed tool calls. LLMs don't always produce valid JSON, especially when generating source code or complex nested structures. Issue #33504 documents a concrete problem: when the model generates an `invalid_tool_calls` entry instead of a valid `tool_calls` list, `create_agent`'s routing logic checks only `tool_calls` and silently exits the loop. The agent just stops. No retry, no error message back to the LLM.

The workaround is custom middleware that converts `invalid_tool_calls` into `ToolMessage` objects with error content, then jumps back to the model node so the LLM can see what went wrong and try again. Community contributors have shared working implementations of `PatchInvalidToolCallsMiddleware` that does exactly this. But as one commenter put it: "invalid tool call should be handled by framework, not user." I agree. For production robustness, this should be built in.

The older `AgentExecutor` had its own version of this problem. The `early_stopping_method="generate"` option was documented but never implemented for newer agent types that inherit from `BaseMultiActionAgent` (issue #16263, open since January 2024). People hit this across versions 0.1 through 0.3. It's the kind of gap that erodes trust.

## Tools and Security

Autonomous tool execution raises obvious security questions. Issue #4912, filed in May 2023, requested a permission model for tools — long-lived read access, short-lived write access, out-of-band approval for sensitive operations. The issue was closed as stale, but the need hasn't gone away. The middleware system gives you the hooks (`wrap_tool_call`) to implement authorization yourself, but LangChain doesn't ship a built-in permission layer.

One adversarial testing report from a Hacker News discussion found a 95% failure rate on a standard LangChain agent when subjected to prompt injection and encoding attacks. The agent decoded malicious Base64 inputs instead of rejecting them. This isn't a LangChain-specific problem — it's an LLM problem — but the framework sits at the enforcement boundary and currently offers limited out-of-the-box protection.

## The Trade-Off: Framework vs. Control

LangChain's `create_agent` is simpler than building your own LLM-tool loop from scratch, but LangGraph gives you full graph control if you need it. The `create_agent` function is really a convenience wrapper around LangGraph's `StateGraph` — it constructs nodes, edges, and routing for you. If your use case fits the standard agent pattern (model calls tools in a loop, stops when done), `create_agent` with middleware will save you a lot of boilerplate. If you need custom routing, parallel tool execution with complex fan-out logic, or multi-agent coordination, you'll want to drop down to LangGraph directly.

We see this tension reflected in community discussions. Some teams are stripping away frameworks entirely and writing raw Python loops for more control over prompt flow. Others find that middleware composition gets them most of the way without framework lock-in. The right choice depends on how much your agent's behavior deviates from the standard loop.

## What I'd Recommend

Start with `create_agent` and the `@tool` decorator. Don't reach for the old `initialize_agent` — it's dead code walking. Write middleware for error recovery early; don't wait until malformed tool calls break your production pipeline. And be honest about what autonomous means in your context. An agent with access to email, shell commands, or databases needs guard rails that LangChain won't provide by default. You'll need to build those yourself, likely through `wrap_tool_call` middleware that enforces your authorization policy at the framework level, where prompt injection can't bypass it.

The framework has come a long way from the days of `AgentType.ZERO_SHOT_REACT_DESCRIPTION`. The middleware system is a genuine architectural improvement. But the gaps — streaming safety, invalid tool call handling, built-in permissions — mean you'll still be writing meaningful glue code for production. That's not a dealbreaker. It's just the honest state of things.
