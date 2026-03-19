# Getting Started with LangChain: Installation and Your First Chain

Building apps on top of large language models used to mean a lot of manual plumbing. Prompt formatting, response parsing, retry logic, chaining multiple calls together. All by hand. LangChain came along to solve that, and despite how fast AI tooling moves, it's still one of the most widely used frameworks for orchestrating LLM-powered workflows. This guide covers getting the right packages installed, understanding how the pieces fit together, and writing your first functional chain.

## The Package Ecosystem

One thing that trips up newcomers right away is the sheer number of packages. The project isn't a single monolithic library; it's been split into several independently versioned pieces, each serving a distinct purpose.

`langchain-core` sits at the foundation. It defines the base abstractions everything else builds on: the `Runnable` interface, prompt templates, output parsers, message types, and the callback system. Intentionally lightweight, with minimal dependencies. You won't often import from it directly when starting out, but nearly every other package in the ecosystem depends on it under the hood.

`langchain` is what most developers install first. It bundles higher-level utilities, pre-built agent architecture, and convenience functions for common tasks. Running `pip install langchain` gets you this package, and it pulls in `langchain-core` automatically.

Then there are the partner packages for specific model providers. Rather than stuffing every integration into one enormous package, the team maintains dedicated libraries like `langchain-openai`, `langchain-anthropic`, `langchain-ollama`, and `langchain-google-vertexai`. They're versioned and released independently, so a breaking change in the OpenAI SDK won't force a new release of the whole framework. There used to be a catch-all `langchain-community` package for third-party integrations, but it's been largely deprecated in favor of this partner model. You might still run into references to it in older tutorials.

The practical upshot: install `langchain` for the framework, then add whichever provider package matches the model you want to use.

## Installation

Installation is the easy part. Using pip:

```bash
pip install langchain
```

Or if you prefer a modern package manager like uv:

```bash
uv add langchain
```

Next, grab a provider package. For OpenAI models:

```bash
pip install langchain-openai
```

For Anthropic's Claude:

```bash
pip install langchain-anthropic
```

For running models locally through Ollama:

```bash
pip install langchain-ollama
```

You'll also need authentication for your chosen provider. Most cloud-hosted models expect an API key through an environment variable: `OPENAI_API_KEY` for OpenAI, `ANTHROPIC_API_KEY` for Anthropic. Local inference through Ollama doesn't need an API key, but you'll need the Ollama server running and your model pulled locally.

LangChain requires Python 3.10 or later and relies on Pydantic v2 for data validation. If your project is still pinned to Pydantic v1, you'll need to sort that out first.

## Core Concepts: Runnables and LCEL

Before writing any code, it helps to understand the design philosophy behind the framework. One idea ties everything together. LangChain is built around **Runnables**: any component that takes input, processes it, and produces output. Prompt templates, language models, output parsers: they all qualify.

Because every component shares the same interface, you can snap them together into pipelines. The syntax for doing this? **LCEL**, the LangChain Expression Language. In practice it just means the pipe operator (`|`).

Writing `prompt | model | parser` constructs a `RunnableSequence`. Data flows left to right: the prompt template formats input variables into messages, the model generates a response, and the parser extracts what you care about. Each step handles sync and async execution, streaming, and batching automatically. You write the composition once and get all those modes for free.

## Your First Chain

Let's build a minimal working example. The chain takes a topic from the user, asks a language model to explain it, and returns the response as a plain string.

### Step 1: Initialize a Chat Model

LangChain provides `init_chat_model` to handle provider-specific setup:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")
```

The string format is `provider:model_name`. Swapping providers means changing that single argument (`"anthropic:claude-sonnet-4-20250514"`, `"ollama:llama3"`, and so on). If you want more explicit control, import directly from the partner package:

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")
```

Both approaches produce a Runnable that accepts messages and returns an AI response.

### Step 2: Define a Prompt Template

Hard-coding prompts as raw strings works for quick experiments but falls apart once you need to reuse them with different inputs. `ChatPromptTemplate` lets you define a template with placeholder variables:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable technical writer who explains concepts clearly and concisely."),
    ("user", "Explain {topic} in a few paragraphs.")
])
```

The `from_messages` class method takes a list of tuples, each a role-content pair. The `{topic}` placeholder gets filled in when you invoke the chain, and you can include as many variables as your template needs.

### Step 3: Add an Output Parser

When a chat model responds, it returns an `AIMessage` object wrapping the text along with metadata like token usage. If all you want is the text, `StrOutputParser` strips away the wrapper:

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
```

For more structured outputs, there's `JsonOutputParser`, `PydanticOutputParser`, and `XMLOutputParser`, among others. But `StrOutputParser` is the right starting point.

### Step 4: Compose the Chain

Connect the three components with the pipe operator:

```python
chain = prompt | model | parser
```

That single line creates a complete pipeline. Under the hood, LangChain builds a `RunnableSequence` that feeds input variables into the prompt template to produce formatted messages, sends them to the chat model, then extracts the plain text via the parser.

### Step 5: Run It

```python
result = chain.invoke({"topic": "how TCP handles packet loss"})
print(result)
```

`invoke` accepts a dictionary whose keys match the placeholder variables in your prompt. Because of the `StrOutputParser` at the end, you get a plain string back.

Want to see tokens arrive as the model generates them?

```python
for chunk in chain.stream({"topic": "how TCP handles packet loss"}):
    print(chunk, end="", flush=True)
```

Streaming works out of the box since every Runnable in the sequence supports it. Nothing extra to configure.

## Putting It All Together

Here's the complete script:

```python
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = init_chat_model("openai:gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable technical writer who explains concepts clearly and concisely."),
    ("user", "Explain {topic} in a few paragraphs.")
])

parser = StrOutputParser()

chain = prompt | model | parser

result = chain.invoke({"topic": "how TCP handles packet loss"})
print(result)
```

Twelve lines of meaningful code. You've got a reusable, streamable, async-capable chain. Swapping the model, prompt, or output format means changing one component without touching the rest.

## Beyond the Basics

Once your first chain works, a few directions open up.

A single prompt-response cycle has no memory of prior exchanges. LangChain addresses this with `RunnableWithMessageHistory` and a `MessagesPlaceholder` in the prompt template, which maintain context across turns. You pass a session identifier, and the framework handles storing and retrieving past messages.

Language models get a lot more useful when they can call external functions to search the web, query a database, or run calculations. LangChain's `@tool` decorator lets you expose Python functions to the model. It's flexible about argument types and return values, though the docs don't make this super obvious. One requirement: your function needs a docstring. That's how the framework tells the model what the tool does.

```python
from langchain_core.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b
```

If you want the model deciding which tools to call and in what order, that's an agent. The current recommended approach is `create_react_agent` from LangGraph, which provides a structured reasoning-and-acting loop. Older tutorials reference `initialize_agent`, but that's been deprecated. The LangGraph version gives you more control and better reliability in production.

You can also ask a model to produce output conforming to a Pydantic schema instead of parsing free-form text. `PydanticOutputParser` validates responses automatically and gives you typed Python objects rather than raw strings.

## Common Pitfalls

A few things to watch for.

The ecosystem can feel overwhelming, and honestly, that's my biggest gripe with getting started. Dozens of vector stores, embedding providers, document loaders, text splitters. Don't try to evaluate them all up front. Pick one provider, get a working prototype, then branch out when specific needs come up.

Stale examples are everywhere. Blog posts and Stack Overflow answers from 2023 or 2024 often reference deprecated APIs like `LLMChain`, `ConversationChain`, and `initialize_agent`, all of which have been replaced by LCEL pipe syntax and LangGraph agents.

Provider-specific quirks can pop up when you least expect them. Different models handle tool calling, structured output, and streaming in subtly different ways. LangChain papers over many of these differences, but edge cases exist; when something behaves oddly, check whether it's a framework issue or a model-level limitation.

## Is LangChain Worth Learning?

Community opinion in 2026? Mixed, but worth parsing.

From what I've seen, developers building RAG systems, multi-step agents, or apps supporting multiple model providers get real value from the framework. The abstractions save time, the integration ecosystem is large, and LangGraph plus LangSmith (LangChain's observability platform) give you a clear path to production. Critics counter that the abstraction overhead isn't worth it for simple cases, and they're not wrong; if your app makes a single LLM call with a static prompt, you can probably skip it entirely. Some teams prefer calling model APIs directly or reaching for lighter alternatives like Pydantic AI.

My take: LangChain earns its keep when your application has real moving parts. Start small, get a chain running, and let your use case tell you how deep to go.
