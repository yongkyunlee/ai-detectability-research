# Using LangChain Agents and Tools for Autonomous Task Execution

Agents are the part of LangChain that people love to demo and hate to debug. The core idea is simple: give an LLM a set of tools, let it decide which ones to call, observe the results, and loop until it's done. That loop is where all the interesting engineering happens — and where most production systems fall apart.

We've been building with LangChain's agent primitives for a while now, and the framework has gone through real architectural churn in this space. The old `initialize_agent` function was deprecated back in version 0.1, replaced first by `create_react_agent` from LangGraph's prebuilt module, and then by the newer `create_agent` factory in the `langchain` v1 package. Each iteration reflects genuine lessons about what breaks when you hand an LLM the keys to your toolbox. So let's talk about what the current agent-and-tool system actually looks like under the hood, what works, and where you'll still need to bring your own engineering.

## How Tools Work in LangChain Core

A tool in LangChain is ultimately a subclass of `BaseTool`, which itself extends `RunnableSerializable`. That means every tool is a Runnable — it participates in the same composition and callback infrastructure as chains, models, and retrievers. The class defines a `name`, a `description` (which is what the LLM actually sees when deciding whether to use the tool), and an optional `args_schema` for input validation via Pydantic.

The simplest way to create a tool is the `@tool` decorator from `langchain_core.tools`. You write a function with type hints and a docstring, and LangChain infers the schema automatically. Pass `parse_docstring=True` and it'll even pull per-argument descriptions from Google-style docstrings into the JSON schema the model receives.

```python
from langchain_core.tools import tool

@tool(parse_docstring=True)
def search_docs(query: str, max_results: int = 5) -> str:
    """Search the documentation archive.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
    """
    return run_search(query, max_results)
```

This generates a `StructuredTool` with an `args_schema` derived from the function signature. The decorator is flexible enough to handle async functions, custom names, and a `response_format` of `"content_and_artifact"` for tools that return both a human-readable summary and raw structured data. But the decorator hides complexity. Under the covers, `create_schema_from_function` uses Pydantic's `validate_arguments` to build the model — and the codebase itself contains a comment noting this approach is deprecated and should be rewritten. It works, but it's technical debt the maintainers are aware of.

For more advanced cases, you can subclass `BaseTool` directly and implement `_run` (and optionally `_arun` for async). This gives you access to error handling through `ToolException` and `handle_tool_error`, which lets a tool signal failure without crashing the agent loop. You can return a string, a callable, or even `True` to just surface the exception message as the tool's observation. That's a critical design choice: it means the agent can see what went wrong and try a different approach, rather than the whole execution blowing up.

## The Agent Loop, Old and New

The classical LangChain agent architecture is described right in the `langchain_core.agents` module docstring. An agent gets a prompt, asks the LLM what to do, receives an `AgentAction` (containing a tool name, tool input, and a reasoning log), executes that action to produce an `AgentStep` with an observation, feeds the observation back, and repeats. When the LLM decides it's done, it returns an `AgentFinish` with the final answer.

That architecture powered `AgentExecutor`, which handled the loop, iteration limits, and early stopping. But `AgentExecutor` had real limitations. The `early_stopping_method="generate"` parameter, which was supposed to let the agent make a final prediction when hitting its iteration cap, has been broken since at least version 0.1 — the `BaseSingleActionAgent` and `BaseMultiActionAgent` classes never implemented it, and as of version 0.3.x the issue remains open and unfixed. Users on the GitHub issue have been asking about it for over two years.

The recommended path forward is `create_agent` from the `langchain` v1 package. This builds a LangGraph state graph under the hood: a model node, a tool-execution node, and routing logic that checks whether the LLM emitted any tool calls. If it did, tools execute and the result loops back. If it didn't, the agent exits. The function accepts a model (either a string identifier like `"openai:gpt-4"` or a `BaseChatModel` instance), a list of tools, an optional system prompt, and — notably — a `middleware` parameter.

## Middleware: Where Production Concerns Live

Middleware is the v1 answer to the question of how you layer production concerns onto an agent without forking the framework. An `AgentMiddleware` can hook into multiple points: `after_model` to inspect or modify the LLM's response, `wrap_model_call` to intercept the entire model invocation, and `wrap_tool_call` to intercept individual tool executions. This is where you'd add logging, PII detection, input sanitization, or tool-level authorization.

And middleware is where some of the sharpest current pain points live. Issue #35011 in the LangChain repo documents that streaming bypasses guardrails middleware entirely. If you configure a `PIIMiddleware` with `strategy="block"` on output and then stream responses with `stream_mode="messages"`, the tokens are delivered to the user before the middleware runs. The email address that should have been blocked has already been printed. A maintainer acknowledged this requires "a major architectural change in AgentMiddleware" to fix properly. The workaround — use `invoke` instead of `stream`, then fake-stream the result by tokenizing and printing character by character — works but defeats the purpose of streaming.

There's a similar gap around invalid tool calls. When an LLM generates malformed JSON for a tool call — common when producing source code with nested quotes or complex escape sequences — the call lands in `invalid_tool_calls` on the `AIMessage`. But the routing logic in `create_agent` only checks `tool_calls`, not `invalid_tool_calls`. So the agent sees zero tool calls, exits the loop, and the user gets a silent failure. The community has built middleware workarounds like `PatchInvalidToolCallsMiddleware` that convert these to error `ToolMessage` objects and jump back to the model node, but the consensus in the issue thread is clear: this should be handled by the framework, not the user.

## Security and the Permission Gap

Tool security is a conversation the LangChain community has been having since at least 2023. Issue #4912 asked for a permission model — the ability to grant an agent long-lived read access to email but require explicit approval for writes. The issue was opened, went stale, was reopened, went stale again, and was eventually closed without a first-party solution. Third-party projects have since built authorization layers that hook into `before_tool_call` at the framework level rather than relying on prompt instructions the model can be jailbroken past.

An adversarial testing report from early 2026 demonstrated the scope of the problem: a standard LangChain agent scored a 5.2% robustness rate against adversarial mutations, with a 0% pass rate on both encoding attacks (the agent decoded malicious Base64 instead of rejecting it) and basic prompt injection. Latency spiked to approximately 30 seconds under stress. These numbers don't mean LangChain agents are uniquely vulnerable — most agent frameworks share these weaknesses. But they underscore that tool-calling agents are inherently attack surface, and the framework doesn't ship with guardrails by default.

The recursive tool calling issue is another angle. The codebase allows tool invocations without cycle detection or depth limits, which means a malicious or malformed input can trigger infinite recursion, stack overflow, or resource exhaustion. A security scanner flagged this as a medium severity finding. The recommended mitigations — a max recursion depth counter, call-history-based cycle detection, and configurable timeouts — are all things you'd need to implement yourself.

## The Abstraction Trade-off

A recurring theme in community discussion is whether LangChain's abstractions earn their weight. One Hacker News commenter put it bluntly: "LangChain was great for getting something running in 5 minutes, but the 'abstraction soup' makes debugging a nightmare in production." Another team reported spending more time on retry logic, failover, latency monitoring, and response parsing — the "stuff around the LLM call" — than on the call itself. Their Slack bot that pinged when latency crossed 5 seconds mostly taught them how often latency crosses 5 seconds.

But there's a counterpoint that's equally valid. If you need multi-model support, structured output validation, observability hooks, and a middleware pipeline, writing that from scratch means building most of what LangChain already provides. A controlled comparison building the same chat application across four frameworks — Pydantic AI, LangChain, LangGraph, and CrewAI — found that the frameworks all produce the same API and behavior, differing only in the AI layer implementation. The abstraction cost is real, but so is the cost of maintaining your own orchestration code.

The honest assessment is this: `create_agent` with the `@tool` decorator is simpler to get started with, but LangGraph gives you explicit control over state transitions, branching, and error recovery. That's the fundamental trade-off in this ecosystem. The convenience of `create_agent` is real — you pass a model string, a list of tools, and a system prompt, and you get a working agent in five lines of code. But the moment you need streaming-aware guardrails, invalid-tool-call recovery, or fine-grained permission control, you're either writing middleware or dropping down to LangGraph's graph primitives.

## Practical Recommendations

If you're building a tool-calling agent today, start with `create_agent` from the v1 `langchain` package — not the deprecated `initialize_agent`, and not raw `AgentExecutor`. Use the `@tool` decorator with `parse_docstring=True` for clean schema generation. Write your tool descriptions carefully; they're the primary mechanism the LLM uses to decide when to call a tool, and vague descriptions produce unreliable routing.

Set `handle_tool_error=True` on tools that interact with external services. This converts exceptions to observations the agent can reason about, which is far better than crashing the loop. If you're using models that occasionally produce malformed JSON tool calls, add middleware to catch `invalid_tool_calls` and feed error messages back to the model — the framework doesn't handle this yet.

Don't stream if you're relying on output middleware for safety. That's not a design choice; it's a current limitation. And if your agent has access to tools that perform writes, mutations, or external API calls, build explicit authorization into the tool implementation rather than trusting prompt instructions to keep the agent in line.

The agent-and-tool pattern works. It's the right abstraction for tasks where the LLM genuinely needs to choose between multiple capabilities based on context. But treat it as infrastructure, not magic. The loop is simple. Everything around the loop is where the engineering lives.
