# Getting Started with LangChain: Installation and Your First Chain

If you've spent any time building apps on top of large language models, you've probably heard of LangChain. The project calls itself an agent engineering platform. At version 1.2 it's matured quite a bit from the early days that frustrated adopters with constant API churn. Whether you want to wire up a quick prototype calling GPT-4o or build a multi-step pipeline that retrieves documents and formats answers, LangChain gives you composable parts that snap together through a shared interface. This post walks through installation, core vocabulary, and building a first working chain so you can decide if the framework fits before you commit to it.

## What LangChain Actually Is (and Is Not)

LangChain provides a standard interface layer across models, embeddings, vector stores, and tools. You write against abstractions (a `BaseChatModel`, a `Runnable`, a `PromptTemplate`) and swap the concrete implementation later without rewriting application logic. Need to move from OpenAI to Anthropic because pricing shifted? Change one string. That interoperability is the strongest argument for using a framework instead of calling provider SDKs directly.

It's not magic, though. Community discussions keep surfacing a recurring theme: prototypes come together fast, but production deployments demand work the framework won't do for you. Retry strategies. Latency monitoring. Failover when a provider goes down. Parsing responses across models that format output slightly differently. One practitioner described spending more time on the infrastructure *surrounding* the LLM call than on the call itself once real traffic arrived. Honestly, that tracks with my own experience. The framework accelerates the first 80 percent, but the remaining 20 percent is still yours to figure out.

## Installation

LangChain ships as a family of Python packages. The main one is simply `langchain`, installed with pip or uv:


pip install langchain


This pulls in `langchain-core`, which holds the base abstractions every other package depends on: Runnables, prompt templates, output parsers, and the callback system. You won't import from it directly in most cases; it exists so provider integrations can target a stable interface.

To talk to an actual model you need a provider package. The project maintains first-party integrations for OpenAI, Anthropic, Ollama, DeepSeek, xAI, and several others. Install whichever one matches your use case:


pip install langchain-openai        # for GPT models
pip install langchain-anthropic     # for Claude models
pip install langchain-ollama        # for local models via Ollama


Each provider package is independently versioned, and that's deliberate. It lets the Anthropic integration ship a fix without waiting on a full release cycle, and it keeps your dependency tree narrow. Only need OpenAI? You're not pulling in the Google Vertex SDK.

## Key Concepts in Sixty Seconds

The primary way you interact with LLMs in LangChain is through **chat models**. Every provider gets wrapped behind the `BaseChatModel` class, which exposes `invoke`, `stream`, `batch`, and their async counterparts. There's a handy factory function called `init_chat_model` that lets you instantiate any supported model from a single call using a `provider:model` string.

Then there are **prompt templates**, which let you parameterize the text you send to a model. `ChatPromptTemplate` handles the common case of system-plus-user message pairs with variable placeholders. These templates are themselves Runnables, so they participate in chain composition (more on that in a second).

On the output side, **parsers** transform raw model responses into structured data. `StrOutputParser` extracts text content from a message object; `JsonOutputParser` and `PydanticOutputParser` handle cases where you need typed structures back. That said, many current models now support structured output natively through tool calling, so from what I can tell you may not even need a parser for newer providers.

The glue holding everything together is **LCEL**, the LangChain Expression Language. Every component implements the `Runnable` interface, which means you chain them with the pipe operator (`|`). A chain built this way automatically gets streaming, async execution, and batching without extra code. Pretty nice.

## Building Your First Chain

Here's a minimal chain that takes a topic, asks a model to explain it, and returns plain text:


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


The pipe operator constructs a `RunnableSequence` under the hood. When you call `invoke`, the input dictionary flows through the prompt template (which fills in `{topic}`), then to the model (which returns an `AIMessage`), then through the output parser (which pulls out the string content). Each step's output becomes the next step's input.

Because every piece is a Runnable, you get streaming for free:


for chunk in chain.stream({"topic": "how TCP handles packet loss"}):
    print(chunk, end="", flush=True)


Async support works the same way, no rewrite needed:


result = await chain.ainvoke({"topic": "how TCP handles packet loss"})


## Swapping Models Without Changing Logic

One concrete benefit of the abstraction layer is provider portability. Say you want to compare responses across models:


anthropic_model = init_chat_model("anthropic:claude-sonnet-4-5-20250929", temperature=0.7)
chain_anthropic = prompt | anthropic_model | StrOutputParser()

result_anthropic = chain_anthropic.invoke({"topic": "how TCP handles packet loss"})


The prompt template and output parser stay the same. Only the model object changes. For more dynamic scenarios, `init_chat_model` supports configurable fields so you can pick the provider at runtime through a configuration dictionary rather than hardcoding it.

## Where to Go from Here

A single prompt-model-parser chain is useful but limited. What comes next depends on what you're building.

If you need the model to answer questions grounded in your own documents, look into retrieval-augmented generation (RAG). LangChain integrates with dozens of vector stores, so you can pair a retriever with your chain and ground the responses in actual data you control. For something more agentic, you can bind external functions to the model using `bind_tools` and let it decide when to call them; `create_agent` (backed by LangGraph under the hood) gives you a ReAct-style loop with middleware for retries, rate limiting, and human-in-the-loop approval. And if you're tired of parsing model output yourself, `model.with_structured_output(MyPydanticModel)` returns validated, typed responses directly from models that support it. No parser needed.

For a single model call, the raw SDK is honestly simpler. But the moment you need prompt templating, model swapping, streaming, and structured output in the same workflow, having a shared protocol across all those pieces starts saving real time. Worth a try, at least.
