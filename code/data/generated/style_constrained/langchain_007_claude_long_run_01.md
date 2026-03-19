# LCEL: The Pipe Operator That Replaced Our Glue Code

LangChain Expression Language doesn't look like much at first glance. It's a pipe operator. You chain callables together with `|`, and the framework handles the rest. But that surface simplicity hides a surprisingly well-designed composition system - one that we've been leaning on heavily as our LLM pipelines grow more complex.

I want to walk through what LCEL actually is under the hood, where it shines, and where you'll want to reach for something else instead.

## What LCEL Actually Does

LCEL is built on top of one core abstraction: the `Runnable`. Every component in `langchain-core` - prompts, models, output parsers, retrievers - implements the `Runnable` interface. That interface gives you `invoke`, `batch`, `stream`, and their async counterparts (`ainvoke`, `abatch`, `astream`) for free. Any object that subclasses `Runnable` immediately supports all six execution modes without extra work.

The `|` operator creates a `RunnableSequence`. So when you write `prompt | model | parser`, you're constructing a sequence where the output of each step feeds into the next. That's it. No class hierarchy to memorize, no special chain classes. Just pipes.

Here's the simplest possible example from the source:


from langchain_core.runnables import RunnableLambda

sequence = RunnableLambda(lambda x: x + 1) | RunnableLambda(lambda x: x * 2)
sequence.invoke(1)  # 4
sequence.batch([1, 2, 3])  # [4, 6, 8]


We get batch and async support without writing any additional code. The `RunnableSequence` calls `batch` on each component sequentially, and each component's batch implementation uses a thread pool by default for IO-bound work. This matters more than you'd think once you start hitting external APIs at scale.

## The Two Composition Primitives

LCEL really only has two core building blocks. `RunnableSequence` handles serial execution, and `RunnableParallel` handles concurrent execution. Everything else is a variation or convenience wrapper.

`RunnableParallel` accepts a dict of named runnables and runs them all concurrently with the same input. You can construct one explicitly or just drop a dict literal into a sequence - LangChain coerces it automatically:


sequence = RunnableLambda(lambda x: x + 1) | {
    "mul_2": RunnableLambda(lambda x: x * 2),
    "mul_5": RunnableLambda(lambda x: x * 5),
}
sequence.invoke(1)  # {'mul_2': 4, 'mul_5': 10}


That automatic coercion is one of those small design decisions that makes real pipelines cleaner. You don't need to import and instantiate `RunnableParallel` every time you want to fan out. A plain dict works. And the concurrency is real - both branches run simultaneously, which is exactly what you want when you're making parallel LLM calls.

## RunnablePassthrough and Data Routing

Most real pipelines need to pass data through unchanged alongside transformed data. `RunnablePassthrough` handles this. It's essentially the identity function wrapped in the `Runnable` interface.

Where it gets useful is with `RunnablePassthrough.assign()`. This lets you augment a dict input with additional computed keys while preserving everything that was already there. So if your retriever gives you documents and you need to format them into a prompt alongside the original question, you don't need to write a custom function to merge everything together. The `assign` method handles the plumbing.

`RunnablePick` is the counterpart - it extracts specific keys from a dict. Together, these two cover most of the data routing you'd otherwise write by hand in utility functions.

## Streaming That Actually Works

One of the stronger arguments for LCEL is streaming. A `RunnableSequence` preserves the streaming properties of its components. If every component in the chain implements a `transform` method (the method that maps streaming input to streaming output), the entire chain streams end-to-end. Tokens come out as the model produces them, passed through each downstream step incrementally.

But here's where you need to pay attention. `RunnableLambda` doesn't support `transform` by default. If you stick a lambda in the middle of your chain, streaming will block at that point until the lambda receives its full input. The pipeline won't crash - it just silently degrades from true streaming to buffered-then-stream.

If you need custom streaming logic, use `RunnableGenerator` instead. It takes a function with signature `Iterator[A] -> Iterator[B]`, letting you process and emit chunks incrementally:


from langchain_core.runnables import RunnableGenerator

def gen(input: Iterator[Any]) -> Iterator[str]:
    for token in ["Have", " a", " nice", " day"]:
        yield token

runnable = RunnableGenerator(gen)
list(runnable.stream(None))  # ["Have", " a", " nice", " day"]


`RunnableLambda` is simpler to use but `RunnableGenerator` gives you true streaming capabilities. That's a trade-off worth understanding before you design your chain, because retrofitting streaming later means rewriting your intermediate steps.

## The Standard Methods

Every `Runnable` comes with a set of standard modifier methods that compose cleanly with LCEL chains. These aren't just convenience - they solve real production problems.

`.with_retry()` wraps a runnable in retry logic using `tenacity` under the hood. You configure `stop_after_attempt`, `retry_if_exception_type`, and jitter parameters. This is critical for any chain that calls external APIs. We've all written our own retry wrappers; this one at least integrates with the tracing and callback system.

`.with_fallbacks()` lets you specify alternative runnables to try when the primary fails. The canonical use case is model fallbacks - if your primary provider goes down, automatically route to another. Fallbacks are tried in order until one succeeds or all fail. You can define them at the individual component level or wrap an entire chain.

`.bind()` is for passing additional arguments to a runnable that don't come from the previous step in the chain. This is how you'd attach things like `stop` sequences or `function_call` parameters to a model without modifying the upstream data flow.

`.with_config()` lets you attach tags, metadata, and callback handlers to specific steps in a chain. And `configurable_fields` and `configurable_alternatives` allow runtime swapping of components - useful when you want the same chain to work with different models or parameters depending on the request.

## Branching and Routing

`RunnableBranch` provides conditional logic. You give it a list of `(condition, runnable)` pairs and a default, and it evaluates conditions in order, running the first matching branch:


from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda x: isinstance(x, str), lambda x: x.upper()),
    (lambda x: isinstance(x, int), lambda x: x + 1),
    lambda x: "goodbye",
)
branch.invoke("hello")  # "HELLO"


This covers simple if/else routing within a chain. For anything more complex - cycles, human-in-the-loop, stateful agents - you'll want LangGraph, which sits on top of LCEL but adds a proper graph execution model.

## The @chain Decorator

There's a `@chain` decorator that turns a plain function into a `Runnable`. It sets the name for tracing and ensures any runnables called inside the function are tracked as dependencies:


from langchain_core.runnables import chain

@chain
def my_func(fields):
    prompt = PromptTemplate("Hello, {name}!")
    model = OpenAI()
    formatted = prompt.invoke(**fields)
    for chunk in model.stream(formatted):
        yield chunk


This is handy when you need custom logic that doesn't fit neatly into the pipe syntax but still want to participate in the tracing ecosystem.

## What To Watch Out For

LCEL isn't without sharp edges. The current version of `langchain-core` is 1.2.20, and even at this stage of maturity there are open issues worth knowing about.

There's a documented memory leak (issue #30667) when using bound methods in a `RunnableSequence`. The root cause is an `@lru_cache` on `get_function_nonlocals` that holds strong references to callables. If you're creating runnables from object methods in a loop, you could see memory grow unboundedly. The workaround is to separate the method call and the downstream steps into distinct runnables and invoke them sequentially instead of piping them together.

There's also a bug in `RunnableRetry.batch` (issue #35475) where `return_exceptions=True` can return corrupted outputs when some batch items succeed on retry while others fail. The result assembly uses `result.pop(0)` on a list that no longer matches the original input ordering after retries. Multiple community fixes have been proposed, but it's still open.

These aren't showstoppers, but they're the kind of production gotchas you find only after deploying. Keep them in mind.

## When Not to Use LCEL

Community sentiment is mixed on frameworks in general. We see recurring threads - "Are we still using LangChain in 2026?" and "What are you using instead?" - where engineers express frustration with the weight of the abstraction layer. One common complaint is that prototypes feel great but production deploys require dealing with retries, failover, latency monitoring, and response parsing across models, and the glue code piles up regardless.

And that's a fair criticism. LCEL is a composition primitive, not a production platform. It handles the plumbing of connecting components, but it doesn't solve observability, deployment, or the dozens of operational concerns that come with real traffic. LangSmith addresses some of this, and LangGraph handles more complex orchestration patterns. But if your pipeline is straightforward - a prompt, a model call, maybe a retriever - sometimes raw Python with explicit error handling is genuinely simpler.

The `langchain-core` package description says it plainly: "Building applications with LLMs through composability." That composability is what LCEL delivers. It doesn't try to be more.

## Where It Fits

So where does LCEL actually earn its keep? Three places. First, when you're building chains that need to work both synchronously and asynchronously without duplicating code. The dual-mode support is genuinely useful. Second, when you want streaming from end to end through multiple processing steps. Getting that right by hand is tedious. And third, when you need runtime configurability - swapping models, adjusting parameters, adding fallbacks - without restructuring your pipeline.

For anything involving complex control flow, state management, or multi-agent coordination, start with LangGraph. LCEL is the foundation it builds on, and understanding how runnables compose will make your LangGraph code better. But don't try to force loops or conditional state into pipe operators. That's not what they're for.

The `Runnable` abstraction and the `|` operator are LangChain's strongest design decisions. They've made the framework modular in a way that the early chain classes never were. Whether you use the rest of the ecosystem or not, the idea of composable, protocol-compliant processing steps is worth adopting. We've been doing it in Unix for decades. LCEL just brings that pattern to LLM pipelines.
