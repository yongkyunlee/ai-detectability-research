# Getting Started with LangChain: Installation and Your First Chain

Building applications on top of large language models used to involve a lot of manual plumbing. You had to manage prompt formatting, parse model responses into usable structures, handle retries, and wire together multiple calls by hand. LangChain emerged to solve exactly that problem, and despite the rapid churn in the AI tooling landscape, it remains one of the most widely adopted frameworks for orchestrating LLM-powered workflows. If you have been eyeing the ecosystem and wondering where to begin, this guide walks through the essentials: getting the right packages installed, understanding how the pieces fit together, and writing your first functional chain.

## The Package Landscape

One of the first things that trips up newcomers is the sheer number of packages in the LangChain ecosystem. The project is not a single monolithic library. It has been split into several independently versioned pieces, each with a distinct role.

**langchain-core** sits at the foundation. It defines the base abstractions that everything else builds on: the `Runnable` interface, prompt templates, output parsers, message types, and the callback system. The package is intentionally kept lightweight with minimal dependencies. You rarely import from it directly when getting started, but nearly every other LangChain package depends on it under the hood.

**langchain** is the main package most developers install first. It bundles higher-level utilities, pre-built agent architecture, and convenience functions for common tasks. When you run `pip install langchain`, this is what you get, and it pulls in `langchain-core` automatically.

**Partner packages** handle integrations with specific model providers. Rather than stuffing every integration into one enormous package, the LangChain team maintains dedicated libraries like `langchain-openai`, `langchain-anthropic`, `langchain-ollama`, and `langchain-google-vertexai`. Each provider's package is versioned and released independently, which means a breaking change in the OpenAI SDK does not force a new release of the entire framework.

There used to be a catch-all `langchain-community` package for third-party integrations. That has largely been deprecated in favor of the partner package model, though you may still encounter references to it in older tutorials.

The practical upshot: install `langchain` for the framework itself, then install whichever provider package matches the model you want to use.

## Installation

The installation itself is straightforward. Using pip:


pip install langchain


If you prefer a modern package manager like uv:


uv add langchain


Next, install a provider package. For OpenAI models:


pip install langchain-openai


For Anthropic's Claude:


pip install langchain-anthropic


For running models locally through Ollama:


pip install langchain-ollama


You will also need to set up authentication for your chosen provider. Most cloud-hosted models expect an API key passed through an environment variable. For OpenAI, that means setting `OPENAI_API_KEY`; for Anthropic, `ANTHROPIC_API_KEY`. Local inference through Ollama does not require an API key but assumes you have the Ollama server running and the model pulled locally.

LangChain requires Python 3.10 or later. It relies on Pydantic v2 for data validation, so if your project is still pinned to Pydantic v1, you will need to address that before proceeding.

## Core Concepts: Runnables and LCEL

Before writing any code, it helps to understand the design philosophy that holds the framework together. LangChain is built around a concept called **Runnables**. A Runnable is any component that accepts an input, does some processing, and produces an output. Prompt templates are Runnables. Language models are Runnables. Output parsers are Runnables.

The power of this abstraction is composability. Because every component implements the same interface, you can snap them together into pipelines. The syntax for doing this is called **LCEL**---the LangChain Expression Language. In practice, LCEL boils down to the pipe operator (`|`), which connects Runnables into a sequence.

When you write `prompt | model | parser`, you are constructing a `RunnableSequence`. Data flows left to right: the prompt template formats input variables into messages, the model generates a response, and the parser extracts the content you care about. Each step in the pipeline automatically handles both synchronous and asynchronous execution, streaming, and batching. You write the composition once and get all of those modes for free.

## Your First Chain

Let us build a minimal working example. The chain will take a topic from the user, ask the language model to explain it, and return the response as a plain string.

### Step 1: Initialize a Chat Model

LangChain provides a convenient `init_chat_model` function that handles provider-specific instantiation for you:


from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")


The string format is `provider:model_name`. You can swap providers by changing this single argument---`"anthropic:claude-sonnet-4-20250514"`, `"ollama:llama3"`, and so on. If you prefer explicit control, you can import directly from the partner package:


from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")


Both approaches produce a Runnable that accepts messages and returns an AI response.

### Step 2: Define a Prompt Template

Hard-coding prompts as raw strings works for quick experiments but falls apart once you need to reuse them with different inputs. `ChatPromptTemplate` lets you define a template with placeholder variables:


from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a knowledgeable technical writer who explains concepts clearly and concisely."),
    ("user", "Explain {topic} in a few paragraphs.")
])


The `from_messages` class method accepts a list of tuples where each tuple is a role-content pair. The `{topic}` placeholder will be filled in at invocation time. You can include as many variables as your template needs.

### Step 3: Add an Output Parser

When a chat model responds, it returns an `AIMessage` object that wraps the text content along with metadata like token usage. If all you need is the text itself, `StrOutputParser` strips away the wrapper:


from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()


For more structured outputs, LangChain offers `JsonOutputParser`, `PydanticOutputParser`, and `XMLOutputParser`, among others. But `StrOutputParser` is the right starting point.

### Step 4: Compose the Chain

Now connect the three components with the pipe operator:


chain = prompt | model | parser


That single line creates a complete pipeline. Under the hood, LangChain constructs a `RunnableSequence` that will:

1. Pass input variables to the prompt template, producing formatted messages
2. Send those messages to the chat model, receiving an AI response
3. Extract the plain text from the response via the parser

### Step 5: Run It


result = chain.invoke({"topic": "how TCP handles packet loss"})
print(result)


The `invoke` method accepts a dictionary whose keys match the placeholder variables in your prompt. The return value is a plain string because of the `StrOutputParser` at the end.

If you want to see the response token by token as the model generates it:


for chunk in chain.stream({"topic": "how TCP handles packet loss"}):
    print(chunk, end="", flush=True)


Streaming works out of the box because every Runnable in the sequence supports it. There is nothing extra to configure.

## Putting It All Together

Here is the complete script:


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


Twelve lines of meaningful code, and you have a reusable, streamable, async-capable chain. Changing the model, the prompt, or the output format is a matter of swapping one component without touching the rest.

## Beyond the Basics

Once the first chain is working, the natural next steps branch in a few directions.

**Adding conversation memory.** A single prompt-response cycle has no recollection of prior exchanges. LangChain provides `RunnableWithMessageHistory` and a `MessagesPlaceholder` in the prompt template to maintain context across turns. You pass a session identifier, and the framework handles storing and retrieving past messages.

**Using tools.** Language models become far more capable when they can call external functions---search the web, query a database, run calculations. LangChain's `@tool` decorator lets you expose Python functions to the model. The decorator is flexible: your function can accept any combination of argument types and return whatever type makes sense. The one requirement is that the function must have a docstring, since LangChain uses it to tell the model what the tool does.


from langchain_core.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b


**Building agents.** An agent is a system where the model decides which tools to call and in what order. The current recommended approach is to use `create_react_agent` from LangGraph, which provides a structured loop for reasoning and acting. Older tutorials may reference `initialize_agent`, but that pattern has been deprecated in favor of the LangGraph-based approach, which gives you more control over the agent's behavior and better reliability in production.

**Structured output.** Instead of parsing free-form text, you can ask the model to produce output conforming to a Pydantic schema. The `PydanticOutputParser` validates responses automatically and gives you typed Python objects rather than raw strings.

## Common Pitfalls

A few things to watch out for as you explore further.

The ecosystem can feel overwhelming. There are dozens of vector stores, embedding providers, document loaders, and text splitters. Resist the urge to evaluate all of them upfront. Pick one provider, get a working prototype, and branch out as specific needs arise.

Deprecated patterns persist in search results. Blog posts and Stack Overflow answers from 2023 or 2024 often use APIs that have since been replaced. If you encounter `LLMChain`, `ConversationChain`, or `initialize_agent`, know that these have modern replacements. The LCEL pipe syntax and LangGraph agents are the current standard.

Provider-specific quirks can surface in unexpected ways. Different models handle tool calling, structured output, and streaming differently. LangChain abstracts over many of these differences, but edge cases exist. When something behaves oddly, check whether it is a framework issue or a model-specific limitation.

## Is LangChain Worth Learning?

Community opinion in 2026 is mixed but informative. Developers building RAG systems, multi-step agents, or applications that need to support multiple model providers consistently find value in the framework. The abstractions save time, the integration ecosystem is extensive, and the transition path to production through LangGraph and LangSmith (LangChain's observability platform) is well-trodden.

Critics point to the abstraction overhead. If your application makes a single LLM call with a static prompt, LangChain adds complexity you do not need. Some teams prefer calling model APIs directly or using lighter alternatives like Pydantic AI for simpler workflows.

The honest answer: LangChain earns its keep when your application has moving parts---multiple models, tool use, conversation history, retrieval, or agent loops. For those scenarios, the investment in learning the Runnable abstraction and LCEL pays off quickly. Start small, get a chain running, and let the complexity of your use case guide how deep you go.
