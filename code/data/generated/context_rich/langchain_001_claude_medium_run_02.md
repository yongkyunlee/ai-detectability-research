# Getting Started with LangChain: Installation and Your First Chain

If you've been paying attention to the Python AI ecosystem, you've probably noticed LangChain showing up everywhere. It started as a convenient wrapper around language model APIs and has since grown into what its maintainers call "the agent engineering platform." Whether that ambition appeals to you or makes you slightly nervous, the library remains one of the most widely installed packages in the LLM space, and understanding its basics is worth the time investment.

This post walks through installing LangChain, understanding its package structure, and building your first working chain. No prior experience with the framework required — just a working knowledge of Python.

## Understanding the Package Layout

Before installing anything, it helps to know what you're actually pulling in. LangChain is organized as a collection of independently versioned packages rather than a single monolithic library:

- **langchain-core** provides the base abstractions: the `Runnable` interface, prompt templates, output parsers, and the protocol that every integration implements. You generally won't install this directly since other packages depend on it automatically.
- **langchain** (the main package) gives you higher-level utilities and the `init_chat_model` factory function for quickly spinning up models from any supported provider.
- **Provider packages** like `langchain-openai`, `langchain-anthropic`, and `langchain-ollama` contain the actual model integrations. Each is maintained separately so that version bumps in one provider don't cascade into unrelated parts of your stack.

This modular design means your dependency tree only includes what you actually use. If you only talk to OpenAI, you never need to pull in Anthropic's SDK or Google's client libraries.

## Installation

The simplest starting point is to install the core framework alongside the provider you plan to use. For this walkthrough, we'll use OpenAI:

```bash
pip install langchain langchain-openai
```

If you prefer `uv` (the fast Python package manager that LangChain's own development team uses internally):

```bash
uv add langchain langchain-openai
```

LangChain requires Python 3.10 or later. The main package depends on `langchain-core`, `pydantic` (v2), and `langgraph`, all of which get pulled in automatically.

Make sure your OpenAI API key is available as an environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

## Your First Model Call

The fastest way to talk to a model is through `init_chat_model`, a factory function that resolves the right provider integration based on the model name you pass in:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")
response = model.invoke("Explain what a hash table is in two sentences.")
print(response.content)
```

The `"openai:gpt-4o"` string uses a `provider:model` format. LangChain can also infer the provider from the model name alone — passing `"gpt-4o"` without a prefix still routes to OpenAI because of the `gpt-` prefix matching. But being explicit avoids ambiguity, especially as the number of supported providers grows.

What comes back from `.invoke()` is an `AIMessage` object, not a plain string. It contains the text in `.content`, along with metadata like token usage and the model identifier. This structure becomes important once you start chaining components together.

## Building a Chain with LCEL

A single model call is useful, but LangChain's real value kicks in when you compose components into pipelines. The LangChain Expression Language (LCEL) lets you do this using the pipe operator (`|`), which connects any two objects that implement the `Runnable` interface.

Here's a minimal chain that takes a topic, fills in a prompt template, sends it to the model, and extracts a plain string from the result:

```python
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful technical writer."),
    ("human", "Write a brief explanation of {topic} suitable for a beginner.")
])

model = init_chat_model("openai:gpt-4o")
parser = StrOutputParser()

chain = prompt | model | parser

result = chain.invoke({"topic": "recursion"})
print(result)
```

Three components, piped together. The `ChatPromptTemplate` takes a dictionary with a `topic` key and produces formatted messages. The model takes those messages and returns an `AIMessage`. The `StrOutputParser` extracts just the text content as a plain string.

What makes this more than syntactic sugar is that the resulting `chain` object is itself a `Runnable`. That means it automatically supports `.invoke()`, `.stream()`, `.batch()`, and their async counterparts (`.ainvoke()`, `.astream()`, `.abatch()`). You get streaming and concurrency without writing any additional code.

## Streaming the Output

Speaking of streaming — you can consume model output as it arrives with one small change:

```python
for chunk in chain.stream({"topic": "recursion"}):
    print(chunk, end="", flush=True)
```

Each chunk is a string fragment that the model has generated so far. This matters for user-facing applications where waiting several seconds for a complete response feels sluggish.

## Swapping Providers

One advantage of the `init_chat_model` abstraction is that switching providers requires changing exactly one string. To use Anthropic's Claude instead of GPT-4o:

```bash
pip install langchain-anthropic
```

```python
model = init_chat_model("anthropic:claude-sonnet-4-5-20250929")
chain = prompt | model | parser
```

Everything else in your pipeline stays the same. The prompt template, the output parser, the streaming behavior — none of it cares which model sits in the middle. This interoperability is arguably the strongest practical reason to use LangChain rather than calling provider SDKs directly. When you want to benchmark three different models against the same prompt, you change a string instead of rewriting your integration layer.

## Where to Go Next

Once you're comfortable with basic chains, a few natural next steps present themselves. You can experiment with structured output, where the model returns typed Pydantic objects instead of free-form text — most modern models support this natively now, which LangChain exposes through the `.with_structured_output()` method. You can add tools to your model using `.bind_tools()`, letting the LLM call functions on your behalf. And when you need more complex control flow — branching, loops, persistent state — LangGraph extends the same Runnable interface into a full graph-based orchestration layer.

The important thing at the start is to keep your chains simple and understand what each component does before stacking on more complexity. A prompt template, a model, and a parser can take you surprisingly far.
