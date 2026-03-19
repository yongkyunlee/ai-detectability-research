# Getting Started with LangChain: Installation and Your First Chain

If you've been paying attention to AI application development lately, you've almost certainly run into LangChain. The project started as a way to chain language model calls together, but it's grown into something bigger: a full platform for building agents. Chatbots, document Q&A systems, autonomous agents that pick their own tools. It handles all of that, and it saves you from writing the same glue code over and over.

This guide covers installation, the high-level architecture, and building your first working interaction with a language model. By the end you'll have a functioning setup and enough context to explore more advanced patterns on your own.

## Why Bother with a Framework?

You can call the OpenAI or Anthropic APIs directly with a few lines of Python. So why add a layer on top?

Honestly, the answer doesn't click until you move past "send a prompt, get a response." Real applications need to swap between model providers without rewriting business logic, connect models to external data, manage conversation history, handle structured outputs, and coordinate multi-step workflows where a model decides which tools to call. Building all of that from scratch is tedious and error-prone. LangChain gives you standardized interfaces for these concerns so you can focus on what your app actually does.

There's also a practical hedge against how fast this space moves. New models and providers show up constantly; a well-designed abstraction layer means you can adopt one by changing a string, not refactoring your entire codebase.

## The Package Structure

One thing that trips up newcomers is how the project is organized. It's a monorepo with several independently versioned packages, and understanding the boundaries between them early saves real headaches.

At the foundation sits `langchain-core`. It defines the base abstractions and interfaces. You'll rarely import from it directly, but everything else builds on its primitives: the `BaseChatModel` interface, the message types, the `Runnable` protocol, and so on. The main `langchain` package provides the high-level utilities you'll actually use in your code, things like `init_chat_model` for creating model instances and `create_agent` for building tool-calling agents.

Then there are the integration packages, each scoped to a specific provider. Want to use OpenAI? Install `langchain-openai`. Anthropic? That's `langchain-anthropic`. Ollama for local models? `langchain-ollama`. You only pull in dependencies for the providers you actually need, which I think is a nice design choice.

LangGraph is another piece worth knowing about. It handles agent orchestration under the hood. You don't need to understand it to get started, but when you call `create_agent`, LangChain constructs a LangGraph state machine behind the scenes to manage the loop of model calls and tool executions.

## Installation

Python 3.10 or higher is required. Set up a virtual environment first:

```bash
python -m venv langchain-env
source langchain-env/bin/activate
```

Install the core package:

```bash
pip install langchain
```

If you prefer `uv` (the LangChain team themselves use it for development):

```bash
uv add langchain
```

This pulls in `langchain-core` and `langgraph` as dependencies automatically. You still need the integration package for whichever provider you plan to use, though. For OpenAI that's `pip install langchain-openai`; for Anthropic it's `pip install langchain-anthropic`. You can also install provider packages as extras of the main package (`pip install "langchain[openai]"`), which is slightly more convenient. Available extras include `anthropic`, `openai`, `google-genai`, `ollama`, `groq`, `mistralai`, `deepseek`, and several others.

Before running any code that calls a model API, make sure you have the right API key set as an environment variable. For OpenAI that means `OPENAI_API_KEY`, for Anthropic it's `ANTHROPIC_API_KEY`. The integration packages follow consistent naming conventions and will raise clear errors if the key is missing.

## Your First Model Call

The simplest entry point is `init_chat_model`, a factory function that creates a chat model instance from any supported provider through one unified interface.

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")
response = model.invoke("Explain what a hash table is in two sentences.")
print(response.content)
```

The model argument uses a `provider:model_name` format. LangChain can also infer the provider from the name itself. If it starts with `gpt-` or `o3`, it assumes OpenAI; names beginning with `claude` map to Anthropic; `gemini` routes to Google. This inference is handy for quick experiments, but specifying the provider explicitly avoids ambiguity:

```python
claude = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
response = claude.invoke("What is the capital of Japan?")
```

The `invoke` method accepts a plain string, a list of message objects, or a prompt value. For anything beyond a simple question, you'll typically work with message objects to control the conversation structure.

## Working with Messages

Conversations are represented as lists of typed message objects. The three you'll use most are `SystemMessage` (sets the model's behavior), `HumanMessage` (user input), and `AIMessage` (model output).

```python
from langchain_core.messages import HumanMessage, SystemMessage

model = init_chat_model("openai:gpt-4o", temperature=0.7)

messages = [
    SystemMessage(content="You are a concise technical writer. Answer in three sentences or fewer."),
    HumanMessage(content="What are the trade-offs between SQL and NoSQL databases?"),
]

response = model.invoke(messages)
print(response.content)
```

This gives you precise control over prompt structure. The system message establishes context and constraints, while human messages carry the queries. For multi-turn conversations, you append each response as an `AIMessage` and each follow-up as a `HumanMessage`, keeping the full dialogue history intact.

## Streaming Responses

For interactive apps where you want to show output as it's generated, streaming works out of the box:

```python
model = init_chat_model("anthropic:claude-sonnet-4-5-20250929")

for chunk in model.stream("Write a haiku about debugging code."):
    print(chunk.content, end="", flush=True)
```

Each chunk contains a partial response. The `stream` method returns an iterator, so you process tokens as they arrive rather than waiting for everything. There's also `astream` for async applications.

## Building Your First Agent

This is where LangChain really pulls ahead of raw API calls. An agent can decide which tools to call, execute them, look at the results, and keep reasoning until it has enough information to answer the original question.

Here's a minimal example with a single tool:

```python
from langchain.agents import create_agent

def check_weather(location: str) -> str:
    """Return the weather forecast for the specified location."""
    return f"It's 72°F and sunny in {location}"

agent = create_agent(
    model="openai:gpt-4o",
    tools=[check_weather],
    system_prompt="You are a helpful assistant that can check the weather.",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather like in San Francisco?"}]}
)

for message in result["messages"]:
    print(f"{message.type}: {message.content}")
```

`create_agent` takes a model (as a string or an instantiated object), a list of tools, and an optional system prompt. Tools can be plain Python functions. LangChain automatically inspects the function signature and docstring to generate the tool schema that gets sent to the model, which honestly surprised me the first time I saw it work.

Under the hood, the agent runs a loop: call the model, check if the response includes tool calls, execute any requested tools, feed results back, repeat until the model produces a final answer with no tool calls. LangGraph manages message accumulation and routing through all of this.

## Switching Between Providers

One of LangChain's strongest practical benefits is provider interoperability. Say you've been prototyping with OpenAI but want to test how Anthropic handles the same task. The change is a single string:

```python
agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[check_weather],
    system_prompt="You are a helpful assistant that can check the weather.",
)
```

You can even create configurable models that defer provider selection to runtime:

```python
configurable_model = init_chat_model(temperature=0)

# Use OpenAI for this call
configurable_model.invoke("Hello", config={"configurable": {"model": "gpt-4o"}})

# Use Anthropic for this call
configurable_model.invoke("Hello", config={"configurable": {"model": "claude-sonnet-4-5-20250929"}})
```

This is great for A/B testing different models or letting users choose their preferred provider.

## Pitfalls and Practical Advice

A few things I wish someone had told me when I started.

Be mindful of package versions. LangChain has evolved fast, and tutorials from even six months ago may reference deprecated APIs. The older `initialize_agent` function, for instance, has been replaced by `create_agent`. If you hit `ImportError` or deprecation warnings, check that you're on the latest versions and reading current docs.

Keep your integration packages aligned. Mixing old versions of `langchain-core` with new versions of `langchain-openai` can produce subtle compatibility issues that are painful to debug. When upgrading, update all the related packages together.

Start simple. I know it's tempting to immediately build multi-agent systems with custom middleware and structured outputs. Don't. Get comfortable with `init_chat_model` and basic `invoke` calls first, move to `create_agent` when you need tool use, and explore middleware and multi-agent patterns only when your application genuinely requires them.

Take advantage of LangSmith for debugging. When your agent makes unexpected tool calls or produces odd outputs, tracing the full execution reveals exactly what messages were sent, what the model returned, and where things went sideways. It's far more efficient than print-statement debugging, from what I can tell.

## Where to Go Next

With your environment set up and a working model interaction under your belt, you've got several natural directions. Document Q&A systems are a popular next step; check out LangChain's retrieval integrations and vector store abstractions for those. If autonomous agents interest you, dig into the middleware system that lets you intercept and modify agent behavior at each stage. And if you need fine-grained control over workflows, LangGraph lets you design custom state machines that go well beyond the standard tool-calling loop.

The core concepts (models, messages, tools, agents) have stayed stable even as the ecosystem moves fast. Get those foundations down and adapting to new features becomes pretty straightforward.
