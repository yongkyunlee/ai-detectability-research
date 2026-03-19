# `abatch_as_completed` does not cancel pending tasks on exception or early exit

**Issue #35419** | State: open | Created: 2026-02-24 | Updated: 2026-03-14
**Author:** gautamvarmadatla
**Labels:** bug, core, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
import asyncio
from langchain_core.runnables import RunnableLambda

async def llm_call(prompt: str) -> str:
    if prompt == "bad":
        await asyncio.sleep(0.05)           
        raise RuntimeError("429 rate limit")
    await asyncio.sleep(0.25)               
    print(f"CHARGED: {prompt}")              
    return f"ok:{prompt}"

r = RunnableLambda(llm_call)

async def main():
    try:
        async for _, out in r.abatch_as_completed(
            ["bad", "a", "b"],
            config={"max_concurrency": 3},
        ):
            print("got:", out)
    except Exception as e:
        print("caught:", repr(e))
    await asyncio.sleep(0.6)

await main()
```

### Error Message and Stack Trace (if applicable)

```shell
Expected output:
caught: RuntimeError('429 rate limit')

Actual output:
caught: RuntimeError('429 rate limit')
CHARGED: a
CHARGED: b
```

### Description

I'm using `Runnable.abatch_as_completed` to run multiple LLM calls concurrently and process results as they complete. I expect that if one task raises (default `return_exceptions=False`) or if I break out of the `async for` loop early, any remaining pending work is cancelled, consistent with the sync `batch_as_completed`, which cancels pending futures in a `finally` block. Instead, the remaining tasks continue running in the background and can still complete API calls, incurring me extra cost even though their results will never be consumed.

### System Info

     System Information
     ------------------
     > OS:  Windows
     > OS Version:  10.0.26100
     > Python Version:  3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)]

     Package Information
     -------------------
     > langchain_core: 1.2.12
     > langsmith: 0.7.1
     > langchain_tests: 1.1.5

     Optional packages not installed
     -------------------------------
     > langserve

     Other Dependencies
     ------------------
     > httpx: 0.28.1
     > jsonpatch: 1.33
     > numpy: 2.3.5
     > orjson: 3.11.5
     > packaging: 26.0
     > pydantic: 2.12.5
     > pytest: 9.0.2
     > pytest-asyncio: 1.3.0
     > pytest-benchmark: 5.2.3
     > pytest-codspeed: 4.3.0
     > pytest-recording: 0.13.4
     > pytest-socket: 0.7.0
     > pyyaml: 6.0.3
     > requests: 2.32.5
     > requests-toolbelt: 1.0.0
     > rich: 14.2.0
     > syrupy: 5.1.0
     > tenacity: 9.1.4
     > typing-extensions: 4.15.0
     > uuid-utils: 0.14.0
     > vcrpy: 8.1.1
     > xxhash: 3.6.0
     > zstandard: 0.25.0

## Comments

**xXMrNidaXx:**
This is a real issue - thanks for the detailed repro. The async version is indeed missing the cancellation logic that exists in the sync `batch_as_completed`.

Looking at the implementation, the fix should be relatively straightforward:

```python
# In the async generator, wrap in try/finally
async def abatch_as_completed(...):
    tasks = [...]  # spawned tasks
    try:
        async for idx, result in ...:
            yield idx, result
    finally:
        # Cancel any remaining tasks on exit (exception or break)
        for task in tasks:
            if not task.done():
                task.cancel()
        # Optionally await cancellation to ensure cleanup
        await asyncio.gather(*tasks, return_exceptions=True)
```

The sync version uses `executor.shutdown(cancel_futures=True)` in its finally block, but the async version lacks equivalent cleanup.

**Additional consideration**: You may want to use `asyncio.TaskGroup` (Python 3.11+) which has structured concurrency semantics and automatic cancellation built-in. Though that would be a bigger refactor and might change some edge-case behavior.

For now, adding a `finally` block with task cancellation should fix the billing leak issue you're experiencing.

**xXMrNidaXx:**
This is a significant issue for production systems where cost control matters. I've hit similar problems with async batching.

**Workaround that's worked for me:**

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, TypeVar

T = TypeVar('T')

@asynccontextmanager
async def cancellable_batch(coros: list) -> AsyncIterator[list[asyncio.Task]]:
    """Context manager that ensures all tasks are cancelled on exit."""
    tasks = [asyncio.create_task(c) for c in coros]
    try:
        yield tasks
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for cancellation to complete
        await asyncio.gather(*tasks, return_exceptions=True)

# Usage
async def safe_batch_as_completed(runnable, inputs, config=None):
    async def run_one(inp):
        return await runnable.ainvoke(inp, config)
    
    async with cancellable_batch([run_one(i) for i in inputs]) as tasks:
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                yield result
            except Exception as e:
                # Re-raise after cleanup happens in finally
                raise
```

This ensures that on exception or early exit, all pending tasks get cancelled before the function returns. The key insight is wrapping the tasks in a context manager with a proper `finally` block.

**Why this matters at scale:**
- With 100 concurrent requests and a 1% failure rate, you could be paying for 99 extra API calls that you never use
- With retries, this compounds quickly

Would be happy to contribute a PR if this approach aligns with the team's vision. The fix should probably be in `_abatch_as_completed_unbounded` in `langchain-core/src/langchain_core/runnables/base.py`.

**gautamvarmadatla:**
Hi @eyurtsev,
There are several AI-generated duplicate PRs being opened for this issue, even though I pushed the PR last week when i created the issue. Could you please take a look?

**gautamvarmadatla:**
hi @giulio-leone, thanks for working on this. please try to avoid spamming duplicate AI-generated PRs with the exact same fix.  You already created one and I did try mentioning this to you on your previous PR for this same issue

**alvinttang:**
Hi, I'd like to be assigned to this issue. I have a fix ready in PR #35877 that wraps the async yield loop in try/finally with task cancellation. Happy to address any feedback.

**gautamvarmadatla:**
> Hi, I'd like to be assigned to this issue. I have a fix ready in PR [#35877](https://github.com/langchain-ai/langchain/pull/35877) that wraps the async yield loop in try/finally with task cancellation. Happy to address any feedback.

Hi! We already have multiple duplicate PRs please avoid creating new ones :)
