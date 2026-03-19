Getting Started with LangChain: installation and your first chain

LangChain is easiest to understand when you stop treating it like a monolith. It isn't one giant AI framework that does everything for you. It's a composition layer for models, prompts, parsers, tools, retrievers, and agents.

That framing matters because the current Python project is deliberately split. In this repo snapshot, `langchain` is version `1.2.12`, `langchain-core` is `1.2.20`, and `langchain-openai` is `1.1.11`. The main `pyproject.toml` for `langchain` also sets `requires-python = ">=3.10.0,<4.0.0"`. So start with Python 3.10 or newer, and don't expect the base package to magically include every model provider.

The official README keeps the first step minimal:

```bash
pip install langchain
```

or, if your team uses `uv`:

```bash
uv add langchain
```

That gets you the framework package. It does not get you a provider integration. The source makes that explicit. `langchain` depends on `langchain-core`, `langgraph`, and `pydantic`, while provider packages such as OpenAI live separately. For an OpenAI-backed example, install the integration package too:

```bash
pip install -U langchain-openai
export OPENAI_API_KEY="your-api-key"
```

There is a `uv` path for that as well:

```bash
uv add langchain-openai
```

I like this split, even if it annoys people coming from older tutorials. It keeps the base install smaller and the provider boundary explicit. But it also means stale guides fail in confusing ways, because they often imply `pip install langchain` is the whole story. The issue tracker shows that pattern clearly. A March 10, 2026 docs issue around `langchain-huggingface` exists for exactly this reason: users followed a minimal install, then discovered extra dependencies only when runtime imports failed. Install the framework, then install the provider you actually plan to call.

Once the packages are in place, do the smallest possible smoke test before you build a chain. The top-level README uses `init_chat_model`, and that's the right place to start:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5.4")
result = model.invoke("Hello, world!")
```

This step is boring, and that's why it's useful. It tells you whether your package install, provider package, API key, and model naming are all correct before you add prompts or output parsing.

There are two sane ways to initialize models in the current codebase. `init_chat_model(...)` is the simpler on-ramp because it gives you one factory across providers. Direct imports like `from langchain_openai import ChatOpenAI` are a bit more verbose, but they expose provider-specific knobs more directly. For a first pass, `init_chat_model` is simpler. For a production service where you care about parameters like `timeout`, `max_retries`, `base_url`, or `use_responses_api`, the direct provider class gives you finer control.

And if you're pointing at an OpenAI-compatible endpoint that isn't actually OpenAI, don't fake it with `ChatOpenAI` just because the wire format looks similar. The OpenAI integration code is explicit that it targets official OpenAI API behavior, and it tells you to use provider-specific packages for services like OpenRouter or DeepSeek. That's a good rule to adopt early.

Now for the part that actually feels like LangChain: building a chain. The modern pattern is not `LLMChain`. The codebase marks `LLMChain` as deprecated since `0.1.17` and points users to `RunnableSequence`, written as `prompt | llm`. That pipe syntax is not decorative. In the tests, LangChain literally asserts that `prompt | model` produces a `RunnableSequence`.

Here's a clean first chain using the current building blocks:

```python
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

model = init_chat_model("openai:gpt-5.4")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You answer like a concise backend engineer."),
        ("human", "Explain {topic} in two short paragraphs."),
    ]
)

chain = prompt | model | StrOutputParser()

result = chain.invoke({"topic": "connection pooling"})
print(result)
```

This is the first chain worth learning because each piece is obvious. `ChatPromptTemplate` formats the input messages. The model produces an `AIMessage`. `StrOutputParser()` converts that message into plain text. If you stop at `prompt | model`, you still have a valid chain, and that's the simplest composition. But `prompt | model | StrOutputParser()` gives you a string, which is usually easier to log, assert on in tests, store, or feed into the next step. Simpler chain shape versus cleaner downstream data is a real trade-off. For most application code, I’d take the parser.

The other reason this style matters is operational, not aesthetic. The Runnable and LCEL docs in the repo say these composed programs inherently support synchronous, asynchronous, batch, and streaming execution. That means the exact same composition model can start as a toy example and still grow into something a service can use. You don't have to rewrite the core abstraction just because you went from one request at a time to batches or streaming tokens.

If you've been reading old blog posts, this is where most confusion starts. Community discussions in the bundled snapshot repeatedly mention how easy it is to find tutorials with deprecated LangChain syntax. The issue tracker says the same thing more formally. On January 17, 2025, maintainers opened a docs cleanup issue to replace `initialize_agent` examples with newer patterns. Different feature area, same moral: copy code from current docs and source, not from random 2023-era tutorials that still rank well in search.

So the practical getting-started path is short. Install `langchain`. Install the provider package you really need. Verify the model with a one-line `invoke`. Then build one LCEL chain with `ChatPromptTemplate`, a chat model, and `StrOutputParser`. That's enough to understand the library's center of gravity.

Use LangChain when you want to get moving quickly with a standard composition model. Move down to LangGraph when you need tighter control over deterministic workflow steps, latency, or orchestration. The repo says that plainly, and the community discussions reinforce it. LangChain is the faster start. LangGraph gives you more control. For a first chain, start high-level and keep it boring.
