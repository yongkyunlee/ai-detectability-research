# Using LangChain Agents and Tools for Autonomous Task Execution

LangChain's agent system has gone through a significant overhaul. The old `initialize_agent` function, deprecated since version 0.1, is gone. Its replacement — `create_agent` in the `langchain` v1 package — runs on top of LangGraph and introduces a middleware architecture that fundamentally changes how you build and control autonomous tool-calling loops. We've been working with this stack for a while now, and the shift is worth understanding.

## The Core Loop

An agent, at its simplest, is a loop. The model receives a prompt, decides whether to call a tool, gets the result, and decides again. LangChain wraps this into a state graph: a `model` node calls the LLM, a `tools` node executes whatever the model requested, and a routing edge checks `last_ai_message.tool_calls` to decide whether to loop back or exit. That routing logic — the function `_make_model_to_tools_edge` in `langchain/agents/factory.py` — is deceptively important. If `tool_calls` is empty, the agent stops. If it's populated, the tools run.

So the agent is autonomous in the sense that the LLM drives the iteration count. You hand it a set of tools, it decides which ones to invoke and in what order, and the framework handles execution. But "autonomous" doesn't mean "unsupervised." The reality of running this in production is messier than the happy-path demo suggests.

## Defining Tools

LangChain gives you two main ways to define tools. The `@tool` decorator wraps a plain function and infers the schema from its type annotations. Subclassing `BaseTool` gives more control — you define `args_schema` as a Pydantic model and implement `_run`. Both approaches generate the JSON schema that gets sent to the model so it knows what arguments to provide.

One gotcha here: don't name your tool arguments `config`. That name collides with LangChain's internal `RunnableConfig` parameter. The framework silently injects its own `config` object, and your function never receives the user-supplied value. Issue #34029 documented this in detail — the tool crashes with a `TypeError: missing 1 required positional argument` and gives you no useful explanation. A PR is now up to raise a `ValueError` at definition time, but until that lands you just have to know this.

If you need to inject runtime state that the model shouldn't see — database connections, auth tokens, session objects — use `InjectedToolArg` from `langchain_core.tools`. You annotate the parameter with `Annotated[YourType, InjectedToolArg]`, and the framework hides it from the schema while passing it through at invocation time.

## Middleware: Where the Real Control Lives

The middleware system is what makes `create_agent` genuinely useful for production work. Middleware classes subclass `AgentMiddleware` and can hook into several points: `after_model` runs after each LLM response, `wrap_tool_call` intercepts tool invocations, and `after_agent` fires when the loop terminates. You pass them as a list when creating the agent.

There's a growing collection of built-in middleware in the `langchain.agents.middleware` package: `PIIMiddleware` for redacting sensitive data, `LLMToolSelectorMiddleware` for dynamically filtering which tools the model sees, `tool_call_limit` and `model_call_limit` for bounding loop iterations, `human_in_the_loop` for approval gates, and `model_retry` for handling transient failures. The `@wrap_tool_call` decorator provides a lighter-weight option for simple tool interception without writing a full class.

This architecture is simpler than writing custom LangGraph nodes, but it gives you less granular control over the graph topology. That's the fundamental trade-off: `create_agent` with middleware is faster to ship and covers the common cases, while dropping down to raw LangGraph gives you arbitrary graph structures, conditional branching, and parallel node execution.

## Error Handling Is Not Solved

Agents fail. Models produce malformed JSON. Tool calls include wrong argument types. APIs time out. And the framework's handling of these failures is still rough around several edges.

The biggest open issue is `invalid_tool_calls`. When the model generates a tool call but the JSON can't be parsed, the call lands in `invalid_tool_calls` on the `AIMessage` instead of `tool_calls`. The routing logic only checks `tool_calls`. If that list is empty, the agent exits — even though it just produced a malformed call that it could retry if given feedback. Issue #33504 documents this with a reproduction script running against `langchain` version 1.0.0a14. The agent exits silently after one call instead of retrying.

The community has developed middleware workarounds. One approach uses `after_agent` with `@hook_config(can_jump_to=["model"])` to catch invalid tool calls, append error `ToolMessage` objects to the conversation, and jump back to the model node. It works, but it requires clearing `invalid_tool_calls` from the `AIMessage` to avoid infinite loops. This is the kind of thing the framework should handle natively, and multiple users in the issue tracker have said as much.

The older `AgentExecutor` had `handle_parsing_errors=True` as a first-class parameter. The new `create_agent` doesn't yet. That's a regression.

## Security Gaps

Autonomous execution means autonomous risk. Adversarial testing on a standard LangChain agent showed a 5.2% robustness score, with 57 out of 60 adversarial tests failing — including a 0% pass rate on both encoding attacks and prompt injection. The agent decoded malicious Base64 inputs instead of rejecting them.

The permission model for tools is still a community-driven effort. Issue #4912, opened back in May 2023, asked for simple read/write permission boundaries on tool access — long-standing read permissions on email tools with short-lived write permissions requiring approval. The issue was closed without a native solution. The community answer is external guardrail libraries that hook into `before_tool_call` at the framework level, where prompt injection can't bypass them.

And there's a confirmed bug where streaming bypasses guardrails entirely. If you use `stream_mode="messages"` with `PIIMiddleware`, tokens reach the user before the middleware runs. The `after_model` hook fires only after the stream is fully consumed. So your PII detection catches the email address and raises `PIIDetectionError` — but only after the response has already been printed to the client. The maintainers acknowledge this needs an architectural change to the middleware system.

## Running This in Practice

The pattern that works: start with `create_agent`, bind your tools, add middleware for the failure modes you know you'll hit, and monitor aggressively. Set `tool_call_limit` and `model_call_limit` middleware to prevent runaway loops. Use `model_retry` for transient API failures. Write custom `wrap_tool_call` middleware for any tool that touches external systems.

Don't rely on the agent loop to be self-correcting. Test your tools in isolation before giving them to an agent. And be prepared to write more middleware than you expected — the framework provides the hooks, but the production hardening is still largely on you.

LangChain's agent system is a real tool for real work. It's also a framework that's evolving fast and isn't done yet. The middleware architecture is the right idea. The execution has gaps. If you go in knowing where those gaps are, you can ship something that works.
