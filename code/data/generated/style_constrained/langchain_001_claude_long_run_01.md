# Getting Started with LangChain: Installation and Your First Chain

LangChain has been around long enough that most backend engineers have heard the pitch. Framework for building LLM-powered applications. Composable components. Swap providers without rewriting your code. The pitch is real, but the getting-started experience has changed considerably since the early days. The project has matured into a monorepo with independently versioned packages, a new actively maintained `langchain` package, and a `langchain-core` library sitting underneath everything. If you haven't touched it recently, what you remember probably doesn't match what exists now.

I want to walk through what it actually takes to install LangChain today, initialize a model, and build your first chain. We'll stick to what the codebase and its documentation actually say, not what a two-year-old Medium post told you.

## The Package Landscape

The first thing that trips people up is the packaging. LangChain isn't one package anymore. It's a family of them, organized in a monorepo. The core abstractions live in `langchain-core` (currently at version 1.2.20). The main `langchain` package (version 1.2.12) sits on top and provides the high-level utilities most developers interact with. And then there's a constellation of integration packages - `langchain-openai`, `langchain-anthropic`, `langchain-ollama`, and so on - that connect you to specific model providers.

This matters because you don't install one thing and get everything. You install the base, then you install the provider packages you need. The upside is that you don't drag in dependencies for providers you'll never use. The downside is that your first `pip install` might not be your last.

Both `langchain-core` and `langchain` require Python 3.10 or higher. The project supports Python 3.10 through 3.14, which is broader than what many frameworks offer. The core dependency list is tight: pydantic (>=2.7.4), langsmith (>=0.3.45), and tenacity (>=8.1.0) are the main ones. If you've been on pydantic v1, you'll need to upgrade. There's no backward compatibility shim here.

## Installation

The quickstart is straightforward. Two commands, pick your package manager:

```bash
pip install langchain
```

Or, if you've adopted `uv` (which the LangChain team uses internally for their own development):

```bash
uv add langchain
```

That gives you the core framework. But you can't talk to a model yet. You need a provider package. Say you want OpenAI:

```bash
pip install langchain-openai
```

Or Anthropic:

```bash
pip install langchain-anthropic
```

The `langchain` package also supports optional dependency groups if you want to pull in a provider alongside the base install. For example, `pip install langchain[openai]` or `pip install langchain[anthropic]` will install the corresponding integration package. This is convenient, but I'd recommend installing provider packages explicitly so your requirements file makes dependencies visible.

One gotcha I've seen catch people: if a provider integration isn't installed and you try to use it, you'll get an `ImportError` with a message like `Initializing ChatAnthropic requires the langchain-anthropic package. Please install it with pip install langchain-anthropic`. It's a helpful message, but it can be confusing if you assumed everything came bundled.

## Your First Model Call

Once you've got the base package and a provider installed, the recommended entry point is `init_chat_model`. This is a factory function that lives in `langchain.chat_models` and gives you a unified interface across providers.

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5.4")
result = model.invoke("Hello, world!")
```

That colon syntax - `"openai:gpt-5.4"` - is the provider prefix format. The part before the colon names the provider, the part after names the model. You can also skip the prefix if your model name is unambiguous. LangChain will try to infer the provider: anything starting with `gpt-`, `o1`, or `o3` routes to OpenAI; `claude` routes to Anthropic; `gemini` routes to Google Vertex AI; `mistral` routes to Mistral; and so on. But I'd recommend being explicit. Inference is convenient until it guesses wrong, and with model names getting increasingly creative, explicit is safer.

You can also pass common model parameters directly:

```python
model = init_chat_model(
    "anthropic:claude-sonnet-4-5-20250929",
    temperature=0,
    max_tokens=1024,
)
```

The `init_chat_model` function supports over twenty providers out of the box. The full list in the source includes OpenAI, Anthropic, Azure OpenAI, Google Vertex AI, Google GenAI, AWS Bedrock, Cohere, Fireworks, Together, Mistral, HuggingFace, Groq, Ollama, DeepSeek, xAI, Perplexity, and more. Each maps to a specific integration package that must be installed separately.

## The Runnable Interface

Every model you create through `init_chat_model` returns a `BaseChatModel` instance, which implements the `Runnable` interface. This is the backbone of LangChain's composability. A Runnable is anything that takes an input and produces an output, with a standard set of methods:

- `invoke()` for single calls
- `stream()` for streaming token-by-token output
- `batch()` for processing multiple inputs
- `ainvoke()`, `astream()`, `abatch()` for async variants

So your first chain is, in a sense, already built. A single model is a Runnable. You can call `invoke`, `stream`, or `batch` on it immediately.

```python
# Synchronous call
response = model.invoke("Explain Python decorators in two sentences.")

# Streaming
for chunk in model.stream("Explain Python decorators in two sentences."):
    print(chunk.content, end="")

# Batch
responses = model.batch([
    "What is a decorator?",
    "What is a context manager?",
    "What is a generator?",
])
```

This is where LangChain's abstraction starts paying for itself. The same three methods work regardless of whether your model is OpenAI, Anthropic, or a local Ollama instance. We've all written provider-specific API code. It works fine until you need to swap providers for cost or latency reasons, and then you're rewriting half your call sites.

## Building a Simple Chain

The real power of the Runnable interface shows up when you compose multiple steps. LangChain uses the pipe operator (`|`) to chain Runnables together, similar to Unix pipes.

A classic first chain combines a prompt template with a model. The prompt template is itself a Runnable, so it plugs right in:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that explains {topic} concepts."),
    ("human", "{question}"),
])

model = init_chat_model("openai:gpt-5.4", temperature=0)

chain = prompt | model
result = chain.invoke({"topic": "Python", "question": "What are generators?"})
```

The `prompt` Runnable takes a dictionary and produces a formatted prompt. The `model` Runnable takes that prompt and produces an `AIMessage`. Piping them together gives you a single Runnable that takes a dictionary and returns a model response. You can add more steps - output parsers, additional transformations - using the same pattern.

And because every step in the chain implements the same Runnable interface, your whole chain also supports `stream`, `batch`, and their async counterparts. You don't have to think about streaming plumbing at each step.

## Configurable Models

One feature that's easy to overlook is model configurability at runtime. If you call `init_chat_model` without specifying a model, it returns a configurable model that can be parameterized at invocation time:

```python
configurable_model = init_chat_model(temperature=0)

# Use GPT at invocation time
configurable_model.invoke(
    "What's your name?",
    config={"configurable": {"model": "gpt-4o"}},
)

# Same chain, different provider
configurable_model.invoke(
    "What's your name?",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},
)
```

This is useful for A/B testing models or letting users choose their preferred provider. But a word of caution: setting `configurable_fields="any"` opens up all parameters - including `api_key` and `base_url` - to runtime configuration. The source code explicitly warns that this could redirect model requests to a different service. Enumerate the configurable fields explicitly if you're accepting untrusted input.

## The Trade-Off You Should Know About

LangChain makes it fast to prototype. The unified interface, the provider abstraction, the composable Runnables - all of this gets you to a working demo quickly. But the community discussions around LangChain are candid about the trade-off: the abstraction layer that speeds up prototyping can make production debugging harder. When something goes wrong three layers deep in a chain, the stack trace walks through framework internals that aren't always transparent.

The `init_chat_model` approach is simpler than building raw API calls by hand, but it gives you less visibility into what's happening at the HTTP level. For prototyping and standard use cases, this trade-off makes sense. For production systems where you need fine-grained control over retries, timeouts, and error handling at the transport layer, you might find yourself reaching through the abstraction or supplementing with tools like LangSmith for observability.

That said, the framework is more modular now than it used to be. You don't have to buy into the whole ecosystem. Use `init_chat_model` for provider abstraction, use the Runnable interface for composability, skip the parts you don't need. The days of LangChain as a monolithic dependency are behind it.

## What Comes Next

Once you have a model and a basic chain running, the natural next steps are adding tools (so the model can take actions), adding memory (so conversations persist), and adding retrieval (so the model can reference your data). Each of these builds on the same Runnable primitives. And if your agent workflows get complex enough to need explicit state management and control flow, LangGraph - LangChain's orchestration framework - is designed for that.

But start here. Install the package, pick a provider, call `init_chat_model`, and invoke it. The abstraction holds up well for that first step, and you'll have a clear picture of whether LangChain's composition model fits how your team builds.
