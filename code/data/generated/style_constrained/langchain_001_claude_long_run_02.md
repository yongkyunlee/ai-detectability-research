# Getting Started with LangChain: Installation and First Chain

LangChain calls itself "the agent engineering platform." That's a bold tagline, but there's substance behind it. The framework gives you a standard interface for connecting to LLM providers, chaining operations together, and building agents — all without locking you into a single vendor. I wanted to walk through what it actually takes to go from zero to a working chain, because the ecosystem has grown enough that the onboarding path isn't always obvious.

## Why You'd Reach for LangChain

Before we install anything, a fair question: why not just call the OpenAI SDK directly? You can. For a one-off script that sends a prompt and prints a response, raw SDK calls are fine. The value of LangChain shows up when you need to swap between providers, compose multiple steps, or add retrieval and memory to a pipeline. Its abstractions keep the integration layer thin so you can switch from OpenAI to Anthropic to a local model running through Ollama without rewriting your application logic.

That said, there's a real trade-off. LangChain is simpler for getting started and switching providers, but rolling your own orchestration gives you total control over prompt flow and latency. A Hacker News thread from March 2026 put it well: the prototype works great, then real traffic shows up and you're spending more time on the infrastructure around the LLM call than the call itself. We'll come back to that tension later.

## Installation

The core package installs in one line:

```bash
pip install langchain
```

Or, if you're using `uv` (which LangChain's own monorepo uses internally):

```bash
uv add langchain
```

That gets you version 1.2.12 as of this writing — the base framework with `init_chat_model`, the foundational abstractions, and the `langchain-core` dependency. But here's the thing most tutorials skip: the base `langchain` package doesn't ship any provider integrations. You need to install those separately.

Want to use OpenAI models? Install `langchain-openai`. Anthropic? `langchain-anthropic`. Running something locally via Ollama? `langchain-ollama`. Each provider lives in its own package with its own version. This is deliberate. The monorepo used to bundle everything together, and the dependency sprawl was a nightmare. Splitting integrations into separate packages means you only pull in the SDKs you actually need.

A typical setup for someone who wants OpenAI and Anthropic support looks like this:

```bash
pip install langchain langchain-openai langchain-anthropic
```

Three packages. Clean dependency tree. No surprises.

## Your First Model Call

Once installed, the fastest path to a working call uses `init_chat_model`. This is the unified entry point that LangChain provides across all supported providers:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o", temperature=0)
result = model.invoke("Explain Python's GIL in two sentences.")
print(result.content)
```

The `provider:model` syntax is doing real work here. That colon tells `init_chat_model` to route to the OpenAI integration and pass `gpt-4o` as the model name. You don't have to use this format — LangChain can also infer the provider from model name prefixes. A model name starting with `gpt-` or `o3` routes to OpenAI. Names starting with `claude` go to Anthropic. Names starting with `gemini` hit Google's Vertex AI. The inference covers about a dozen providers, but I'd recommend the explicit `provider:model` format. It's clearer and doesn't break when a provider releases a model with an unexpected prefix.

Switching providers is exactly as boring as it should be:

```python
claude = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
response = claude.invoke("Explain Python's GIL in two sentences.")
```

Same interface. Same `.invoke()` call. Different model. That's the core promise working as advertised.

## Understanding the Package Architecture

LangChain's codebase is organized as a Python monorepo. Knowing the structure helps when you're debugging import errors or reading the source.

The `libs/` directory contains `core/` (the `langchain-core` package with base abstractions and interfaces), `langchain_v1/` (the actively maintained `langchain` package), and `partners/` (the provider integration packages like `langchain-openai` and `langchain-anthropic`). There's also a legacy `langchain/` directory labeled "langchain-classic" which isn't receiving new features.

This layered architecture matters in practice. The core layer defines interfaces like `BaseChatModel` and `Runnable`. The implementation layer provides utilities like `init_chat_model`. And the integration layer wires up specific providers. If you see an `ImportError` mentioning a missing class, it's usually because you're importing from the wrong layer. A good example from the issue tracker: `create_retriever_tool` moved from `langchain_community.agent_toolkits` to `langchain_core.tools`, and the old import path stopped working. If you hit that, the fix is straightforward:

```python
from langchain_core.tools import create_retriever_tool
```

These import reshuffles happen. Keep an eye on deprecation warnings in your terminal output.

## Building a Configurable Chain

One of the more practical features is the configurable model pattern. Instead of hardcoding a provider, you can create a model that accepts provider and model name at runtime:

```python
from langchain.chat_models import init_chat_model

configurable_model = init_chat_model(temperature=0)

# Use GPT-4o for this call
response = configurable_model.invoke(
    "Summarize this document",
    config={"configurable": {"model": "gpt-4o"}}
)

# Use Claude for the next call
response = configurable_model.invoke(
    "Summarize this document",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}}
)
```

When you don't pass a model to `init_chat_model`, it defaults to making both `model` and `model_provider` configurable at runtime. This is genuinely useful for A/B testing different models or letting users pick their preferred provider. Be careful with the `configurable_fields="any"` option, though. The LangChain documentation explicitly warns that this exposes fields like `api_key` and `base_url` to runtime configuration, which could redirect model requests to a different service if you're accepting untrusted input. Enumerate your configurable fields explicitly when accepting user-provided configs.

## Deprecated Patterns to Avoid

The LangChain ecosystem has moved fast, and a lot of tutorial content on the internet is outdated. The biggest trap for new users: `initialize_agent`. This function was deprecated in version 0.1 and should not appear in any new code. The replacement is `langgraph.prebuilt.create_react_agent`, which lives in the LangGraph package.

We had an issue tracked on GitHub (issue #29277, opened January 2025) specifically to sweep deprecated `initialize_agent` references out of the official docs. Contributors have been working through the migration incrementally. But if you're following a blog post or tutorial that imports `initialize_agent`, close that tab. The API has moved on.

Another common stumbling block involves memory. If you're using `ConversationBufferMemory` with a chain that returns source documents, you'll hit a `ValueError: One output key expected` error. The chain returns both `answer` and `source_documents` as keys, and the memory object doesn't know which one to store. The fix is to specify the output key explicitly:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key='chat_history',
    return_messages=True,
    output_key='answer'
)
```

This was reported back in 2023 and still catches people. It's a reasonable API design — the memory shouldn't guess — but it's the kind of thing that wastes an afternoon if you don't know about it.

## From Chain to Production

So you've got a model call working. Where do you go from here?

The honest answer depends on your use case. For straightforward chains — prompt goes in, response comes out, maybe with some retrieval — LangChain's abstractions work well. You get provider interoperability, a clean invoke/stream/batch interface, and enough structure to keep your code organized.

For anything with complex control flow, branching logic, or long-running stateful agents, the LangChain team points you toward LangGraph. That's their lower-level orchestration framework for building agent workflows with deterministic and agentic steps. LangChain agents are built on top of LangGraph internally, so the two aren't competing — they're layered.

And for observability, there's LangSmith. It gives you tracing, evaluation, and debugging for LLM applications. Community discussions consistently flag observability as the thing that separates weekend projects from production systems. One commenter's checklist for production readiness included persistent memory, real tool use with error recovery, multi-model support, extensibility, and security boundaries. LangChain checks several of those boxes out of the gate, but the monitoring and evaluation story comes from LangSmith, not the core framework.

## What I'd Actually Do on Day One

Start small. Install `langchain` and one provider package. Get `init_chat_model` working with a simple `.invoke()` call. Verify that you can swap providers by changing the model string. Then try streaming with `.stream()` to see how token-by-token output works. Don't jump to agents or RAG pipelines on day one — those involve embeddings, vector stores, and retrieval strategies that each deserve their own learning session.

The LangChain monorepo includes over 20 built-in provider mappings in its `_BUILTIN_PROVIDERS` registry, covering everything from OpenAI and Anthropic to DeepSeek, Groq, Perplexity, and xAI. Each one follows the same `BaseChatModel` interface. Once you understand how one provider works, the rest are mechanical.

And keep the LangChain Academy (academy.langchain.com) bookmarked. The official courses are free and maintained by the LangChain team, which means they won't teach you deprecated patterns. Community tutorials from 2024 or early 2025 often will.

The framework has rough edges. Import paths change. Abstractions evolve. But the core idea — a standard interface for LLM operations with pluggable providers — is sound, and it's a better starting point than writing your own integration layer from scratch.
