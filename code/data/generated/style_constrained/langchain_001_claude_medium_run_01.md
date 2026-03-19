# Getting Started with LangChain: Installation and First Chain

LangChain has opinions. So do I. After setting it up on a few backend services, I've formed a clear picture of where this framework shines and where it gets in your way. This post covers what you actually need to get from zero to a working chain, without the usual hand-waving.

## What LangChain Is (and Isn't)

LangChain is a Python framework for building LLM-powered applications and agents. It gives you a standard interface for models, embeddings, vector stores, and retrieval - the kind of plumbing you'd otherwise write yourself. The pitch is model interoperability: you swap providers without rewriting application logic.

That's real. But LangChain is also a monorepo that has grown fast. The main package at version 1.2.12 requires Python 3.10 or higher. Its core dependencies pull in `langchain-core`, `langgraph`, and `pydantic`. That's already three packages before you've chosen a model provider. And once you install optional integrations or the community package, things can get heavy. One production team on Reddit reported that pandas and a PDF splitter were getting installed despite only needing inference - bloating their Docker images for no reason.

So keep that trade-off in mind. LangChain is simpler to start with than writing raw orchestration loops, but it gives you less control over exactly what's in your dependency tree.

## Installation

The install itself is straightforward. You have two options:

```bash
pip install langchain
```

Or, if you're using `uv` (which the LangChain team themselves use internally):

```bash
uv add langchain
```

That gets you the core framework. You'll also need an integration package for your model provider. Want OpenAI? Add `langchain-openai`. Anthropic? `langchain-anthropic`. Ollama for local models? `langchain-ollama`. The `pyproject.toml` lists optional dependency groups for each - `pip install langchain[openai]` works too.

I'd recommend installing only the provider you need. Don't reach for `langchain-community` unless you have a specific reason. It drags in a wider set of packages, and most teams only talk to one or two model APIs.

## Your First Chain

The quickstart in the official README is honest and minimal. Here's the core of it:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5.4")
result = model.invoke("Hello, world!")
```

Three lines. That's a real working call. The `init_chat_model` function takes a provider-prefixed model string, handles the right client instantiation under the hood, and returns a model object with a standard interface. You can swap `"openai:gpt-5.4"` for an Anthropic or Ollama model string and the rest of the code stays the same. This is the interoperability promise made concrete.

But a single `.invoke()` call isn't a chain. A chain means composing steps - a prompt template, a model call, maybe a parser for the output. The framework gives you building blocks for that composition. You wire a prompt into a model into an output parser, and LangChain handles passing the output of each step as input to the next.

## Agents and the Deprecation You Need to Know About

If you've read older tutorials, you'll see references to `initialize_agent`. Don't use it. That function has been deprecated since version 0.1, and GitHub issue #29277 documents the ongoing effort to scrub it from the official docs. The replacement is `langgraph.prebuilt.create_react_agent`, which builds on LangGraph for features like durable execution, streaming, and human-in-the-loop workflows.

This matters because a lot of tutorials and Stack Overflow answers still show the old pattern. We encountered this ourselves when onboarding a junior engineer - they'd followed a guide that used `initialize_agent`, and nothing matched the current API surface. The docs are catching up, but the migration isn't complete. If you see `initialize_agent` in a code sample, treat it as a red flag that the resource is outdated.

## Where Things Get Tricky

The framework's memory abstractions have rough edges. A well-known example: `ConversationalRetrievalChain` doesn't play nicely with `ConversationBufferMemory` when you enable `return_source_documents=True`. The memory object expects a single output key, but returning source documents gives it two - `answer` and `source_documents` - and it throws a `ValueError`. The workaround is to explicitly set `output_key='answer'` on the memory object:

```python
memory = ConversationBufferMemory(
    memory_key='chat_history', return_messages=True, output_key='answer')
```

That issue (GitHub #2303) has been open since April 2023 and was still receiving comments into 2026. It's a small thing, but it's representative. LangChain moves fast, and the seams between components don't always line up cleanly.

There's also the question of how many ways there are to do the same thing. The framework offers three or four different approaches for creating a ReAct-style agent. That flexibility comes at a cost: newcomers struggle to know which path is canonical. A Reddit thread from early 2026 captured this well - a developer with solid Python skills described feeling "overwhelmed by the ecosystem" and unsure about the "order of operations."

## Should You Use It?

For prototyping and getting an LLM-backed service running quickly, yes. The model interoperability is genuine. The ability to swap between OpenAI, Anthropic, and local models through a consistent interface saves real time during evaluation. And `langchain-core` is described by the team as having the largest install base in the LLM ecosystem, so you aren't adopting something fringe.

For production, the calculus changes. Some teams are moving toward custom orchestration - writing their own Python loops for prompt flow - because they want more control and a thinner dependency footprint. One developer put it bluntly: "the frameworks are getting heavier and heavier." Adversarial testing has revealed weaknesses too. One chaos engineering test against a standard LangChain agent reported a 5.2% robustness score, with 57 out of 60 adversarial tests failing, including a 0% pass rate on prompt injection attacks.

We use LangChain for rapid iteration and evaluation. We don't use it as a black box in production without understanding what each layer does. That seems like the right stance for now: adopt the abstractions that save you time, but don't let the framework make security or architecture decisions you haven't reviewed.

Start with `pip install langchain`, build a three-line chain, then grow from there. Read the migration notes before you trust any tutorial older than six months. And keep your dependency tree lean.
