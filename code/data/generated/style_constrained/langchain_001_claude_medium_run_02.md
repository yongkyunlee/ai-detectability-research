# Getting Started with LangChain: Installation and First Chain

LangChain has opinions. So do I. And after spending time with the framework's current architecture, I think it's worth understanding what you're actually installing before you write your first chain.

The framework has gone through significant restructuring. The actively maintained package is now `langchain` version 1.2.12, built on top of `langchain-core` 1.2.20. The older monolith has been renamed to `langchain-classic` and isn't receiving new features. This matters because a lot of tutorials floating around still reference the old package layout, and you'll hit confusing import errors if you don't know which version you're working with.

## Installation: Less Is More

The base install is straightforward:


pip install langchain


That gives you the core framework, but it doesn't give you a model to talk to. LangChain has split every provider into its own package. Want OpenAI? That's `langchain-openai`. Anthropic? `langchain-anthropic`. Ollama for local models? `langchain-ollama`. You get the idea.

You can install provider packages individually, or use extras:


pip install langchain[openai]


This modular approach is simpler than it sounds, and it solves a real problem. One Reddit thread from early 2026 captured the frustration well: a production team complained that LangChain pulled in pandas and PDF splitters when all they needed was inference. The current architecture addresses this. You only install what you use. Your Docker images stay lean. But the trade-off is that you need to know which provider package to grab, and the `ImportError` messages will tell you exactly what to install if you forget.

Python 3.10 or higher is required. The framework depends on Pydantic v2 (specifically >=2.7.4), so if you're locked into an older Pydantic version, you'll need to sort that out first.

## Your First Model Call

Before building a chain, make sure you can talk to a model. The `init_chat_model` function is the unified entrypoint, and it's genuinely useful. It accepts a provider-prefixed model string and handles the rest.


from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")
result = model.invoke("Explain Python generators in two sentences.")
print(result.content)


That `openai:` prefix tells LangChain which provider package to load. You can also skip the prefix if the model name is unambiguous - names starting with `gpt-` resolve to OpenAI, `claude` resolves to Anthropic, `gemini` resolves to Google, and so on. I'd recommend always using the explicit prefix. It makes your code readable and avoids surprises when new model names collide across providers.

We can swap models without changing anything else:


claude = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
response = claude.invoke("Explain Python generators in two sentences.")


This is where LangChain earns its keep. The interface is identical regardless of the backend. Every model supports `.invoke()`, `.stream()`, `.batch()`, and their async counterparts. That consistency isn't free - there's abstraction overhead - but for teams that need to evaluate multiple providers, it removes a lot of boilerplate.

## Building Your First Chain

A chain in LangChain is a sequence of composable steps. The framework calls these steps "Runnables," and they connect using the pipe operator. The core idea is that any component implementing the Runnable interface can be linked to any other.

Here's a minimal prompt-to-model chain:


from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that explains concepts concisely."),
    ("human", "{question}")
])

model = init_chat_model("openai:gpt-4o", temperature=0)

chain = prompt | model

response = chain.invoke({"question": "What is a hash table?"})
print(response.content)


The `|` operator creates a `RunnableSequence`. The prompt template formats your input into messages, then passes them to the model. Each component in the pipeline implements the same protocol: it takes input, produces output, and supports sync, async, batch, and streaming modes automatically.

You can extend this pattern. Add an output parser to extract structured data. Add a retriever to pull context from a vector store. Chain as many steps as you need. And every step remains independently testable.

## The Runnable Protocol

This is the architectural insight that makes LangChain either powerful or over-engineered, depending on who you ask. Every component - prompts, models, parsers, retrievers - implements the same `Runnable` interface. That means `.invoke()`, `.ainvoke()`, `.stream()`, `.astream()`, `.batch()`, and `.abatch()` all work everywhere.

Community sentiment on this is split. Some engineers find the abstraction layers make debugging difficult - one Hacker News commenter described it as "abstraction soup." Others, particularly those with complex multi-model requirements, find that the consistency pays for itself. The honest assessment: if you're wrapping a single API call, LangChain adds unnecessary indirection. If you're building workflows that span multiple models, tools, and data sources, the uniform interface saves real time.

## Configurable Models

One feature worth knowing about early: `init_chat_model` supports runtime configurability. You can create a model that defers the provider choice until invocation time.


configurable_model = init_chat_model(temperature=0)

# Use GPT-4o for this call
configurable_model.invoke(
    "Summarize this document.",
    config={"configurable": {"model": "gpt-4o"}}
)

# Use Claude for this one
configurable_model.invoke(
    "Summarize this document.",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}}
)


This is handy for A/B testing models or building user-facing apps where the model choice varies per request. Be cautious with `configurable_fields="any"`, though - the docs explicitly warn that it exposes parameters like `api_key` and `base_url` to runtime configuration, which could redirect model requests if you're accepting untrusted input.

## What Comes Next

Once you're comfortable with basic chains, the natural next steps are tool binding (letting models call functions), structured output (forcing models to return typed data), and retrieval-augmented generation. All of these build on the same Runnable protocol and pipe-based composition.

So start small. Install the base package and one provider. Get `init_chat_model` working. Build a two-step chain with a prompt and a model. And only then decide whether the framework's abstractions are earning their weight for your specific use case.
