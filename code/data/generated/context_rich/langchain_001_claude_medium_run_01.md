# Getting Started with LangChain: Installation and Your First Chain

If you have spent any time building applications on top of large language models, you have probably heard of LangChain. The project bills itself as an agent engineering platform, and at version 1.2 it has matured considerably from the fast-moving early days that frustrated some adopters with constant API churn. Whether you want to wire up a quick prototype that calls GPT-4o or build a multi-step pipeline that retrieves documents and formats answers, LangChain gives you a set of composable parts that snap together through a shared interface. This post walks through installation, core vocabulary, and the construction of a first working chain so you can decide if the framework fits your project before committing to it.

## What LangChain Actually Is (and Is Not)

At its core LangChain provides a standard interface layer across models, embeddings, vector stores, and tools. You write against abstractions — a `BaseChatModel`, a `Runnable`, a `PromptTemplate` — and swap the concrete implementation later without rewriting application logic. Need to move from OpenAI to Anthropic because pricing shifted? Change one string. That interoperability is the strongest argument for using a framework instead of calling provider SDKs directly.

What LangChain is not is magic. Community discussions surface a recurring theme: prototypes come together fast, but production deployments demand work that the framework does not do for you — retry strategies, latency monitoring, failover when a provider goes down, response parsing across models that format output slightly differently. One practitioner described spending more time on the infrastructure surrounding the LLM call than on the call itself once real traffic arrived. Keep that in mind: LangChain accelerates the first 80 percent, but the remaining 20 percent is still yours.

## Installation

LangChain is distributed as a family of Python packages. The main one is simply `langchain`, and you can install it with pip or uv:

```bash
pip install langchain
```

This pulls in `langchain-core`, which contains the base abstractions every other package depends on: Runnables, prompt templates, output parsers, and the callback system. You will not import from `langchain-core` directly in most cases — it exists so that provider integrations can target a stable interface.

To talk to an actual model you need a provider package. The project maintains first-party integrations for OpenAI, Anthropic, Ollama, DeepSeek, xAI, and several others. Install whichever matches your use case:

```bash
pip install langchain-openai        # for GPT models
pip install langchain-anthropic     # for Claude models
pip install langchain-ollama        # for local models via Ollama
```

Each provider package is independently versioned. That design is deliberate — it lets the Anthropic integration ship a fix without waiting on a full LangChain release cycle, and it keeps your dependency tree narrow. If you only need OpenAI, you are not pulling in the Google Vertex SDK.

## Key Concepts in Sixty Seconds

**Chat models** are the primary interface for interacting with LLMs. LangChain wraps every provider behind the `BaseChatModel` class, which exposes `invoke`, `stream`, `batch`, and their async counterparts. The `init_chat_model` factory lets you instantiate any supported model from a single function call using a `provider:model` string format.

**Prompt templates** let you parameterize the text you send to a model. `ChatPromptTemplate` handles the common case of system-plus-user message pairs with variable placeholders. Templates are themselves Runnables, which means they participate in chain composition.

**Output parsers** transform raw model output into structured data. `StrOutputParser` extracts the text content from a message object. `JsonOutputParser` and `PydanticOutputParser` handle cases where you need typed structures back. That said, many current models support structured output natively through tool calling, so you may not need a parser at all for newer providers.

**Runnables and LCEL.** The LangChain Expression Language is the composition mechanism. Every component — prompt, model, parser — implements the `Runnable` interface, which means you can chain them together with the pipe operator (`|`). A chain built this way automatically inherits support for streaming, async execution, and batching without extra code.

## Building Your First Chain

Here is a minimal chain that takes a topic, asks a model to explain it, and returns plain text:

```python
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize the model
model = init_chat_model("openai:gpt-4o", temperature=0.7)

# Define a prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful technical writer."),
    ("human", "Explain {topic} in three concise paragraphs.")
])

# Build the chain using the pipe operator
chain = prompt | model | StrOutputParser()

# Run it
result = chain.invoke({"topic": "how TCP handles packet loss"})
print(result)
```

The pipe operator constructs a `RunnableSequence` under the hood. When you call `invoke`, the input dictionary flows through the prompt template (which fills in `{topic}`), then to the model (which returns an `AIMessage`), then through the output parser (which pulls out the string content). Each step's output becomes the next step's input.

Because every piece is a Runnable, you get streaming for free:

```python
for chunk in chain.stream({"topic": "how TCP handles packet loss"}):
    print(chunk, end="", flush=True)
```

You also get async support without rewriting anything:

```python
result = await chain.ainvoke({"topic": "how TCP handles packet loss"})
```

## Swapping Models Without Changing Logic

One of the concrete benefits of the abstraction layer is provider portability. Suppose you want to compare responses across models:

```python
anthropic_model = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0.7)
chain_anthropic = prompt | anthropic_model | StrOutputParser()

result_anthropic = chain_anthropic.invoke({"topic": "how TCP handles packet loss"})
```

The prompt template and output parser are unchanged. Only the model object differs. For more dynamic scenarios, `init_chat_model` supports configurable fields so you can select the provider at runtime through a configuration dictionary rather than hardcoding it.

## Where to Go from Here

A single prompt-model-parser chain is useful but limited. The natural next steps depend on what you are building:

- **Retrieval-augmented generation (RAG):** Combine a retriever with your chain so the model answers questions grounded in your own documents. LangChain integrates with dozens of vector stores.
- **Tool use and agents:** Bind external functions to the model using `bind_tools`, then let it decide when to call them. The `create_agent` function in `langchain` (backed by LangGraph under the hood) gives you a ReAct-style loop with middleware for retries, rate limiting, and human-in-the-loop approval.
- **Structured output:** Skip the output parser entirely and use `model.with_structured_output(MyPydanticModel)` to get validated, typed responses directly from models that support it.

LangChain's value grows with the complexity of your pipeline. For a single model call, the raw SDK is arguably simpler. But the moment you need prompt templating, model interchangeability, streaming, and structured output in the same workflow, having a shared protocol across all those components starts saving real time. Install it, build a chain, and see if the tradeoffs work for your situation.
