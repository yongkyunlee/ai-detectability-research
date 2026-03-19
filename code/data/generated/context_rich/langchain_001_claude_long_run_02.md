# Getting Started with LangChain: Installation and Your First Chain

If you have been following the rapid evolution of AI application development, you have probably encountered LangChain. Originally conceived as a tool for chaining together language model calls, the project has matured into something far more ambitious: a full-fledged agent engineering platform. Whether you want to build a simple chatbot, a document question-answering system, or an autonomous agent that uses tools and makes decisions, LangChain provides the scaffolding to get there without reinventing plumbing code every time.

This guide walks through installing LangChain, understanding its architecture at a high level, and building your first working interaction with a language model. By the end, you will have a functioning setup and enough conceptual grounding to start exploring more advanced patterns on your own.

## Why LangChain?

Before diving into code, it is worth understanding what problem LangChain actually solves. You can absolutely call the OpenAI or Anthropic APIs directly with a few lines of Python. So why add a framework?

The answer becomes clear once you move past "send a prompt, get a response." Real applications need to swap between model providers without rewriting business logic. They need to connect models to external data sources, manage conversation history, handle structured outputs, and coordinate multi-step workflows where a model decides which tools to call. Building all of that from scratch is tedious and error-prone. LangChain provides standardized interfaces for these concerns, letting you focus on what your application does rather than how it talks to various APIs.

The framework also acts as an insurance policy against the pace of change in this space. New models and providers appear constantly. A well-designed abstraction layer means you can adopt a new model by changing a string, not refactoring your entire codebase.

## Understanding the Package Structure

One common source of confusion for newcomers is LangChain's package architecture. The project is organized as a monorepo with several independently versioned packages, and understanding the boundaries between them saves a lot of headaches later.

At the foundation sits `langchain-core`, which defines the base abstractions and interfaces. You will rarely import from it directly, but everything else builds on its primitives: the `BaseChatModel` interface, the message types, the `Runnable` protocol, and so on.

The main `langchain` package provides the high-level utilities you will interact with most often, including `init_chat_model` for instantiating models and `create_agent` for building tool-calling agents. This is the package you install and import in your application code.

Then there are the integration packages, each scoped to a specific provider. Want to use OpenAI? Install `langchain-openai`. Anthropic? That is `langchain-anthropic`. Ollama for local models? `langchain-ollama`. This modular design means you only pull in dependencies for the providers you actually use.

There is also LangGraph, which handles agent orchestration under the hood. You do not need to understand LangGraph to get started, but it is useful to know it exists. When you call `create_agent`, LangChain constructs a LangGraph state machine behind the scenes to manage the loop of model calls and tool executions.

## Installation

LangChain requires Python 3.10 or higher. Setting up a virtual environment first is strongly recommended:


python -m venv langchain-env
source langchain-env/bin/activate


Install the core package:


pip install langchain


If you prefer `uv`, which is the tool the LangChain team themselves use for development:


uv add langchain


This pulls in `langchain-core` and `langgraph` as dependencies automatically. However, you still need to install the integration package for whichever model provider you plan to use. For OpenAI:


pip install langchain-openai


For Anthropic:


pip install langchain-anthropic


You can also install provider packages as extras of the main package, which is slightly more convenient:


pip install "langchain[openai]"


The available extras include `anthropic`, `openai`, `google-genai`, `ollama`, `groq`, `mistralai`, `deepseek`, and several others.

Before running any code that calls a model API, make sure you have the appropriate API key set as an environment variable. For OpenAI, that means `OPENAI_API_KEY`. For Anthropic, it is `ANTHROPIC_API_KEY`. The exact variable name depends on the provider, but the integration packages follow consistent conventions and will raise clear errors if the key is missing.

## Your First Model Call

The simplest entry point into LangChain is `init_chat_model`, a factory function that creates a chat model instance from any supported provider through a single, unified interface.


from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")
response = model.invoke("Explain what a hash table is in two sentences.")
print(response.content)


The `model` argument uses a `provider:model_name` format. LangChain can also infer the provider from the model name itself. If the name starts with `gpt-` or `o3`, it assumes OpenAI. If it starts with `claude`, it maps to Anthropic. Names beginning with `gemini` route to Google. This inference is convenient for quick experimentation, but specifying the provider explicitly avoids ambiguity:


claude = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
response = claude.invoke("What is the capital of Japan?")


The `invoke` method accepts a plain string, a list of message objects, or a prompt value. For anything beyond a simple question, you will typically work with message objects to control the conversation structure.

## Working with Messages

LangChain represents conversations as lists of typed message objects. The three most common types are `SystemMessage` (sets the model's behavior), `HumanMessage` (user input), and `AIMessage` (model output).


from langchain_core.messages import HumanMessage, SystemMessage

model = init_chat_model("openai:gpt-4o", temperature=0.7)

messages = [
    SystemMessage(content="You are a concise technical writer. Answer in three sentences or fewer."),
    HumanMessage(content="What are the trade-offs between SQL and NoSQL databases?"),
]

response = model.invoke(messages)
print(response.content)


This pattern gives you precise control over the prompt structure. The system message establishes context and constraints, while human messages carry the actual queries. When you build multi-turn conversations, you append each response as an `AIMessage` and each follow-up as a `HumanMessage`, maintaining the full dialogue history.

## Streaming Responses

For interactive applications where you want to display output as it is generated, LangChain supports streaming out of the box:


model = init_chat_model("anthropic:claude-sonnet-4-5-20250929")

for chunk in model.stream("Write a haiku about debugging code."):
    print(chunk.content, end="", flush=True)


Each chunk contains a partial response. The `stream` method returns an iterator, so you process tokens as they arrive rather than waiting for the complete output. There is also an async variant, `astream`, for use in asynchronous applications.

## Building Your First Agent

Where LangChain really differentiates itself from raw API calls is in agent construction. An agent is a model that can decide which tools to call, execute them, examine the results, and continue reasoning until it has enough information to answer the original question.

Here is a minimal agent that has access to a single tool:


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


The `create_agent` function takes a model (as a string identifier or an instantiated model object), a list of tools, and an optional system prompt. Tools can be plain Python functions, and LangChain automatically inspects the function signature and docstring to generate the tool schema that gets sent to the model.

Under the hood, the agent runs a loop: it calls the model, checks if the response includes tool calls, executes any requested tools, feeds the results back to the model, and repeats until the model produces a final response without any tool calls. This loop is managed by a LangGraph state machine, which handles message accumulation and routing automatically.

## Switching Between Providers

One of LangChain's strongest practical benefits is provider interoperability. Suppose you have been prototyping with OpenAI but want to test how Anthropic handles the same task. With `init_chat_model`, the change is a single string:


# Switch from OpenAI to Anthropic — no other code changes needed
agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[check_weather],
    system_prompt="You are a helpful assistant that can check the weather.",
)


You can even create configurable models that defer provider selection to runtime:


configurable_model = init_chat_model(temperature=0)

# Use OpenAI for this call
configurable_model.invoke("Hello", config={"configurable": {"model": "gpt-4o"}})

# Use Anthropic for this call
configurable_model.invoke("Hello", config={"configurable": {"model": "claude-sonnet-4-5-20250929"}})


This is particularly useful for A/B testing different models or letting users choose their preferred provider.

## Common Pitfalls and Practical Advice

A few things are worth calling out for anyone just getting started.

First, be mindful of package versions. LangChain has evolved rapidly, and tutorials from even six months ago may reference deprecated APIs. The older `initialize_agent` function, for instance, has been replaced by `create_agent`. If you encounter `ImportError` or deprecation warnings, check that you are using the latest package versions and consulting current documentation.

Second, keep your integration packages aligned. Mixing old versions of `langchain-core` with new versions of `langchain-openai` can produce subtle compatibility issues. When upgrading, update all LangChain-related packages together.

Third, start simple. It is tempting to immediately build complex multi-agent systems with custom middleware and structured outputs. Resist that urge initially. Get comfortable with `init_chat_model` and basic `invoke` calls first. Move to `create_agent` when you need tool use. Explore middleware, structured output strategies, and multi-agent patterns only when your application genuinely requires them.

Finally, take advantage of LangSmith for debugging. When your agent makes unexpected tool calls or produces odd outputs, tracing the full execution through LangSmith reveals exactly what messages were sent, what the model returned, and where things went sideways. It is far more efficient than trying to debug agent behavior through print statements.

## Where to Go Next

With your environment set up and a working model interaction under your belt, you have several natural paths forward. If you want to build document question-answering systems, explore LangChain's retrieval integrations and vector store abstractions. If autonomous agents interest you, dig into the middleware system that lets you intercept and modify agent behavior at each stage of execution. And if you need fine-grained control over agent workflows, LangGraph gives you the tools to design custom state machines that go well beyond the standard tool-calling loop.

The LangChain ecosystem moves fast, but the core concepts — models, messages, tools, and agents — remain stable. Master those foundations, and adapting to new features and providers becomes straightforward.
