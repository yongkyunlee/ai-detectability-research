# Using Tools in CrewAI Agents

Tools are what separate a chatbot from an agent. In CrewAI, a tool is any discrete capability an agent can invoke during task execution -- searching the web, reading files, querying a database, or calling an external API. Without tools, your agents are limited to whatever the language model already knows. With them, agents can interact with live systems and produce results grounded in real data.

## Defining Tools: Two Approaches

CrewAI offers two paths for equipping agents with tools. The first is subclassing `BaseTool`, which gives you full control over the input schema and execution logic. You define a Pydantic model for your arguments, set the tool's name and description, and implement the `_run` method:


from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class StockPriceInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")

class StockPriceTool(BaseTool):
    name: str = "stock_price_lookup"
    description: str = "Fetches the current stock price for a given ticker."
    args_schema: type[BaseModel] = StockPriceInput

    def _run(self, ticker: str) -> str:
        price = get_price_from_api(ticker)
        return f"{ticker}: ${price}"


The second approach uses the `@tool` decorator, which infers the argument schema directly from your function's type annotations and docstring. This is faster for simple tools where a full class feels heavy:


from crewai.tools import tool

@tool("currency_convert")
def currency_convert(amount: float, from_code: str, to_code: str) -> str:
    """Convert an amount between two currencies."""
    result = call_exchange_api(amount, from_code, to_code)
    return f"{amount} {from_code} = {result} {to_code}"


Both approaches produce objects that plug into an agent's `tools` list. The decorator path is convenient, but the class path is better when you need custom initialization, private state, or fine-grained caching control.

## How Tool Calling Actually Works

Understanding CrewAI's tool-calling mechanism matters because it affects reliability. CrewAI does not simply pass tool definitions to the LLM's native function-calling API and let the provider handle dispatch. Instead, it implements its own orchestration layer. The framework serializes each tool's name, description, and argument schema into the agent's system prompt, then parses the LLM's text output to detect when the model intends to call a tool.

The agent follows a Thought-Action-Action Input-Observation loop. When CrewAI's parser identifies an action and its input, it executes the corresponding tool and injects the real result back into the conversation as the observation. The agent then continues reasoning with that grounded information.

This design gives CrewAI uniform control over tool execution regardless of which LLM provider you use. But it also introduces a well-documented failure mode: the LLM can generate a fake observation and skip straight to a final answer without ever triggering actual tool execution. This happens more often with smaller or self-hosted models that do not reliably follow the expected output format. The parser sees a "Final Answer" tag and terminates the loop, never realizing the tool was never called.

One practical mitigation is adding explicit instructions in your task description telling the agent not to fill in the Observation field itself. Another is enabling verbose logging so you can verify whether tools were genuinely invoked. CrewAI's internal team has acknowledged this communication layer as an area under active improvement.

## Argument Validation and the Native Path

Recent versions of CrewAI introduced a native tool-calling code path that maps tool functions directly to `BaseTool.run()` without going through the structured validation layer that earlier versions relied on. This means that if the LLM returns empty or malformed arguments, the tool receives them without Pydantic validation, resulting in raw Python `TypeError` exceptions rather than clear validation errors.

When such an error surfaces, the agent treats it as a recoverable failure and retries the same call, potentially entering an infinite loop. This regression caught several users off guard after upgrading. The lesson for tool authors: always test your tools with missing and malformed arguments, and consider adding defensive defaults or explicit validation inside `_run` until the framework's native path matures.

## Caching, Rate Limits, and Usage Caps

CrewAI caches tool results by default. If an agent calls the same tool with the same arguments twice, the second call returns the cached result without hitting the external service. You can customize this behavior with a `cache_function` that inspects the arguments and result to decide whether caching is appropriate -- useful for tools where freshness matters.

For tools backed by rate-limited APIs, the agent-level `max_rpm` parameter throttles outgoing requests. And the `max_usage_count` parameter on individual tools hard-caps how many times a single tool can be invoked during a crew's execution, preventing runaway costs.

## Async Tools

If your tool performs network I/O or other blocking operations, CrewAI supports asynchronous execution. You can either decorate an async function with `@tool` or override `_arun` in a `BaseTool` subclass. The framework handles the event loop plumbing, so async and sync tools coexist seamlessly in the same agent's toolbelt.

## MCP and Dynamic Tool Discovery

One of the most requested features in the CrewAI community is integration with the Model Context Protocol. Today, agents are limited to tools configured at definition time. MCP would let agents discover tools dynamically -- querying a registry to find the right database connector or search API based on the task at hand, rather than requiring every possible tool to be wired up in advance. CrewAI already has basic MCP server adapter support, and proposals for semantic discovery layers are actively being discussed.

## Practical Tips

Write tool descriptions as if you are explaining the tool to a new colleague. The LLM uses that text to decide when and how to invoke it, so vague descriptions lead to misuse. Keep argument schemas tight -- require only what the tool needs and use descriptive field names. If a tool wraps another tool (common when post-processing results from a third-party integration), ensure your wrapper correctly forwards all required arguments through the schema.

Finally, treat observability as a first-class concern. Enable `verbose=True` during development, inspect the agent's thought traces, and confirm that observations come from real tool output rather than model-generated placeholders. Tools are the bridge between your agents and the real world. Making that bridge reliable is where the real engineering work lives.
