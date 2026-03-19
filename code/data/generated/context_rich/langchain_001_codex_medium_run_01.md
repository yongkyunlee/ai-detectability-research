# Getting Started with LangChain: Installation and Your First Chain

LangChain is easier to learn once you separate the current entry points from older tutorials. The project now centers on a maintained `langchain` package, shared primitives in `langchain-core`, and provider-specific integrations such as `langchain-openai` or `langchain-anthropic`. That split explains both installation and why some old examples no longer feel right.

If you want the shortest path to a useful first project, ignore agents, memory, and retrieval for a moment. Start with a single model call, then turn it into a chain by composing a prompt, a model, and an output parser. That is the simplest mental model that still matches how modern LangChain is designed.

## Step 1: Install LangChain and one model integration

The base package gives you the high-level LangChain interface:

```bash
pip install langchain
```

If you use `uv`, the equivalent is:

```bash
uv add langchain
```

That alone is not enough to talk to a hosted model provider. LangChain’s current design expects provider integrations to be installed separately. For OpenAI:

```bash
pip install langchain-openai
```

For Anthropic:

```bash
pip install langchain-anthropic
```

This adds one more installation step, but it also keeps provider support modular and lets LangChain expose one common interface across many backends through `init_chat_model`.

You should also set the provider API key in your environment. The OpenAI integration reads `OPENAI_API_KEY` by default, and the Anthropic integration reads `ANTHROPIC_API_KEY`.

## Step 2: Start with a single model call

LangChain’s top-level README shows the current quickstart pattern:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5.4")
result = model.invoke("Hello, world!")
print(result.content)
```

There are three details worth noticing. `init_chat_model` is the main chat-model entry point in the maintained package. A provider prefix such as `openai:gpt-5.4` makes the backend explicit, even though LangChain can infer some providers automatically. And `invoke()` returns a message object, so printing `result.content` is the simplest way to get readable text. The docs also recommend exact provider model IDs over loose aliases when reliability matters.

## Step 3: Build your first chain

The project’s current composition model revolves around runnables. In practice, that means you build a chain by connecting components with the `|` operator. Under the hood, LangChain turns that into a `RunnableSequence`, which the core library treats as the main composition primitive.

Here is a minimal first chain:

```python
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You explain technical topics clearly."),
        ("human", "Explain {topic} for a Python developer in 3 bullet points."),
    ]
)

model = init_chat_model("openai:gpt-5.4", temperature=0)
chain = prompt | model | StrOutputParser()

response = chain.invoke({"topic": "how LangChain chains work"})
print(response)
```

This chain has three stages.

`ChatPromptTemplate` formats structured chat messages from your input variables. In this case, it produces a system instruction and a human question, with `{topic}` filled in at runtime.

`model` takes that formatted prompt and generates a response.

`StrOutputParser()` converts the model’s message object into plain text. Without the parser, your chain would return an AI message. With the parser, it returns a string, which is often more convenient for logging, display, or downstream processing.

That is the core LangChain pattern:

```python
chain = prompt | model | StrOutputParser()
```

Once that clicks, the rest of the framework feels much less magical. A chain is not a mysterious special object. It is a sequence of composable steps where one output becomes the next input.

## Why this is the right beginner path

A lot of community frustration around learning LangChain comes from outdated syntax. The repo’s issue tracker shows repeated documentation fixes around deprecated functions, moved imports, and examples that no longer match the maintained API surface. Community discussions in the local corpus reflect the same problem: beginners often find tutorials that still teach older patterns and then hit import errors or deprecation warnings immediately.

The most important example is the shift away from older “classic” chain abstractions. In the codebase, `LLMChain` is explicitly deprecated in favor of runnable composition such as `prompt | llm`. That is not a cosmetic change. It tells you how the project wants you to think: small interoperable parts first, higher-level orchestration later.

That is why a first chain should stay boring. Do not begin with agents, multi-step tool use, or retrieval pipelines just because LangChain supports them. A prompt-model-parser chain gives you the right foundation without hiding what is happening.

## What LangChain gives you, and what it does not

LangChain is strong when you want reusable composition. The same prompt-and-chain structure can survive model swaps, and the runnable interface gives you more than just `invoke()`. A `RunnableSequence` also supports async execution, batching, and streaming-aware composition when the components allow it.

But the trade-off is real. The ecosystem is large, and the abstraction surface is wider than what a thin provider SDK wrapper would give you. Community discussion around production use reflects that tension: LangChain is great for getting something working quickly, but concerns like retries, latency, observability, and provider-specific behavior still need deliberate engineering.

That is why the best way to get started is not to learn “all of LangChain.” It is to learn one dependable pattern:

1. Install `langchain`
2. Install exactly one provider integration
3. Initialize a model with `init_chat_model`
4. Build a chain with `prompt | model | parser`
5. Call `invoke()` with a small input dictionary

If you are comfortable with that loop, you are ready for the next layer. Retrieval, tools, and agents all make more sense once you already understand that LangChain is fundamentally a composition framework for runnables. For a first success, keep the scope narrow: one reusable prompt, one model, one parser, one `invoke()` call. That teaches the current LangChain design better than a flashy agent demo and keeps you on the maintained path instead of the legacy one.
