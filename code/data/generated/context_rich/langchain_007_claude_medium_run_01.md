# Building Composable LLM Pipelines with LangChain Expression Language

When you first wire up an LLM call, the code is deceptively simple: send a prompt, get a response, maybe parse it. The trouble starts once you need that call to sit inside a larger workflow — one that retrieves documents, reformats context, fans out to multiple models, and streams partial results to a user interface. Gluing those steps together with ad-hoc Python quickly produces a tangle of callbacks, threading hacks, and duplicated error handling. LangChain Expression Language (LCEL) is an attempt to replace that glue with a small, declarative composition system built around one central abstraction: the Runnable.

## The Runnable Protocol

Every component in an LCEL pipeline — a prompt template, a chat model, an output parser, a custom function — implements the same interface. A Runnable accepts an input, produces an output, and exposes a uniform set of methods: `invoke` for a single call, `batch` for processing multiple inputs, `stream` for incremental output, and async counterparts (`ainvoke`, `abatch`, `astream`) for all three. Because the interface is consistent across every building block, you can swap components freely without rewriting the orchestration code that surrounds them.

This uniformity is the real design insight behind LCEL. Rather than defining separate abstractions for "a thing that calls an LLM" and "a thing that formats a prompt," LangChain treats them as instances of the same generic type, parameterized by input and output. The benefit compounds as pipelines grow: any chain you build automatically inherits synchronous, asynchronous, batched, and streaming execution modes from its constituent parts.

## Composition with the Pipe Operator

The most visible feature of LCEL is the `|` operator, which chains Runnables into a `RunnableSequence`. The output of one step becomes the input to the next:


from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

chain = (
    ChatPromptTemplate.from_template("Summarize this text: {text}")
    | ChatOpenAI(model="gpt-4o")
    | StrOutputParser()
)

result = chain.invoke({"text": "Long document content here..."})


Under the hood, `RunnableSequence` orchestrates execution, threading callbacks and configuration through each step. Streaming propagates end-to-end: if every component in the sequence supports a `transform` method that maps streaming input to streaming output, the full chain can stream tokens to the caller as they arrive. When a component lacks streaming support — a `RunnableLambda` wrapping a plain function, for instance — the framework accumulates that step's input before continuing, so partial streaming still works for the rest of the pipeline.

## Parallel Execution with RunnableParallel

Not every workflow is linear. Sometimes you need to fan the same input out to several branches and merge the results. `RunnableParallel` handles this by running a dictionary of Runnables concurrently and returning a dictionary of their outputs:


from langchain_core.runnables import RunnableParallel, RunnablePassthrough

analysis = RunnableParallel(
    summary=summary_chain,
    sentiment=sentiment_chain,
    keywords=keyword_chain,
)

results = analysis.invoke({"text": article})
# {"summary": "...", "sentiment": "positive", "keywords": [...]}


A dict literal appearing inside a `|` expression is automatically coerced into a `RunnableParallel`, so you can embed fan-out points inline without additional ceremony. `RunnablePassthrough` complements this by forwarding inputs unchanged — useful when one branch needs the raw input while another branch transforms it.

## Branching, Fallbacks, and Retry

LCEL provides primitives for conditional logic and resilience. `RunnableBranch` evaluates a series of condition-runnable pairs and executes the first branch whose condition returns true, falling back to a default if none match. This is useful for routing queries to specialized sub-chains based on classification.

For fault tolerance, any Runnable can be wrapped with `.with_fallbacks()` to specify alternative Runnables to try when the primary one raises an exception — a practical necessity when depending on external APIs that occasionally go down. Similarly, `.with_retry()` decorates a Runnable with configurable retry logic backed by exponential backoff and jitter, targeting specific exception types.

These modifiers are not special-cased; they return new Runnables that compose just like anything else. You can attach retries to a single model call within a longer chain without affecting the rest of the pipeline.

## The @chain Decorator and RunnableLambda

Not everything fits neatly into operator syntax. When you need arbitrary Python logic inside a pipeline, `RunnableLambda` wraps any callable into a Runnable. The `@chain` decorator goes a step further: it converts a function into a named Runnable, which means any Runnables invoked inside that function are automatically traced as dependencies. This bridges the gap between LCEL's declarative style and imperative code, letting you drop into regular Python for complex transformations while retaining observability.


from langchain_core.runnables import chain

@chain
def enrich_query(query: str) -> dict:
    expanded = synonym_expander.invoke(query)
    documents = retriever.invoke(expanded)
    return {"query": query, "context": documents}


## Trade-offs and Practical Considerations

LCEL is not without friction. The pipe-operator syntax can become hard to read for deeply nested or heavily branching workflows — at a certain complexity threshold, LangGraph's explicit state-machine model may be a better fit. Debugging can be challenging: when a chain fails, the stack trace passes through several layers of Runnable internals before reaching your code. Community discussions frequently mention this pain point, with some teams choosing to strip back to raw Python loops for tighter control over prompt flow.

There are also subtleties around resource management. For example, wrapping a bound method in a `RunnableLambda` inside a `RunnableSequence` can create reference cycles that prevent garbage collection — an issue documented in the LangChain issue tracker and traced back to internal caching of function metadata. These are solvable problems, but they surface the cost of the abstraction layer when operating at scale.

Performance-sensitive deployments should also be aware that the default batch implementation parallelizes via thread pools (or `asyncio.gather` for async), which works well for IO-bound tasks but does not magically speed up CPU-bound transformations.

## When LCEL Shines

The sweet spot for LCEL is moderate-complexity chains where you want streaming, async support, and tracing without writing boilerplate for each. A retrieval-augmented generation pipeline that fetches documents, formats a prompt, calls a model, and parses the output is a natural fit. So is a multi-provider setup where fallback logic routes between model providers transparently.

For teams already working within the LangChain ecosystem, LCEL offers a genuine productivity gain: you define the pipeline once and get sync, async, batch, and streaming variants for free. For teams that have outgrown its declarative model — or that need fine-grained control over execution, retry budgets, and observability — it may serve better as a reference design than as production infrastructure.

The underlying principle, though, is worth internalizing regardless of framework choice: treat each step of your LLM pipeline as a typed, composable unit with a uniform interface, and the orchestration problems around streaming, concurrency, and fault tolerance become dramatically simpler to reason about.
