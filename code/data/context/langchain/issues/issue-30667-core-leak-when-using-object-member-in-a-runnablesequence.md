# core: leak when using object member in a `RunnableSequence`

**Issue #30667** | State: open | Created: 2025-04-04 | Updated: 2026-03-14
**Author:** maxfriedrich
**Labels:** help wanted, bug, investigate, core, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
import gc

from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
)

def log_memory_usage():
    gc.collect()
    objs = gc.get_objects()
    print(f"Total objects: {len(objs)}")

class ThingWithRunnable:
    def __init__(self, func):
        self.func = func
        self.runnable_lambda = RunnableLambda(func)
        self.expensive = {i: [i] for i in range(1000000)}

    def call(self, inputs):
        return self.runnable_lambda.invoke(inputs)

    def __del__(self):
        print(">>>> Cleaning up")

def func(inp):
    return {"result": "ok"}

def works():
    thing = ThingWithRunnable(func)
    thing.call({})

def works2():
    thing = ThingWithRunnable(func)
    (RunnableLambda(thing.func) | RunnablePassthrough()).invoke({})

def broken():
    thing = ThingWithRunnable(func)
    (thing.call | RunnablePassthrough()).invoke({})

def broken2():
    thing = ThingWithRunnable(func)
    (RunnableLambda(thing.call) | RunnablePassthrough()).invoke({})

if __name__ == "__main__":
    gc.freeze()
    print("Works:")
    for _ in range(2):
        works()
        log_memory_usage()

    print("Works 2:")
    for _ in range(2):
        works2()
        log_memory_usage()

    print("Broken:")
    for _ in range(2):
        broken()
        log_memory_usage()

    print("Broken 2:")
    for _ in range(2):
        broken2()
        log_memory_usage()
```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

(I created this first as a discussion but after giving it some more thought, I'm pretty sure it's a bug in langchain-core so I'm opening this issue)

Hi, we encountered a memory leak in our app and simplified it down to this. When creating a new RunnableSequence where a member of an object (thing.call) that invokes a Runnable is followed by something else like a RunnablePassthrough, the memory is not cleaned up.

There seems to be a reference to thing still held somewhere which is why the GC doesn't remove the object from memory.

Output:

```
Works:
>>>> Cleaning up
Total objects: 24670
>>>> Cleaning up
Total objects: 24658
Works 2:
>>>> Cleaning up
Total objects: 24936
>>>> Cleaning up
Total objects: 24936
Broken:
Total objects: 1024999
Total objects: 2025005
Broken 2:
Total objects: 3025011
Total objects: 4025017
```

What I would expect: "Cleaning up" logged also in the "broken" versions, object counts don't increase by a lot

In our real app, we were able to work around it by creating two Runnables, the first with the object member and the second with further steps, and invoking them one after the other.

### System Info

```
uv run python -m langchain_core.sys_info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.3.0: Thu Jan  2 20:24:24 PST 2025; root:xnu-11215.81.4~3/RELEASE_ARM64_T6030
> Python Version:  3.13.1 (main, Jan  5 2025, 06:22:40) [Clang 19.1.6 ]

Package Information
-------------------
> langchain_core: 0.3.50
> langsmith: 0.3.24

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch=1.33: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith=0.1.125: Installed. No version info available.
> openai-agents: Installed. No version info available.
> opentelemetry-api: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http: Installed. No version info available.
> opentelemetry-sdk: Installed. No version info available.
> orjson: 3.10.16
> packaging: 24.2
> packaging=23.2: Installed. No version info available.
> pydantic: 2.11.2
> pydantic=2.5.2;: Installed. No version info available.
> pydantic=2.7.4;: Installed. No version info available.
> pytest: Installed. No version info available.
> PyYAML>=5.3: Installed. No version info available.
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> rich: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: 0.23.0
```

## Comments

**eyurtsev:**
cc @sydney-runkle / @ccurme

**maxfriedrich:**
I dug around a bit more, the cause for this is the `@lru_cache` on `get_function_nonlocals` https://github.com/langchain-ai/langchain/pull/28131 https://github.com/langchain-ai/langchain/blob/30af9b8166fa5a28aa91fe77a15ba42c82d9b9e2/libs/core/langchain_core/runnables/utils.py#L412-L413

`@lru_cache` holds on to the `Callable` argument forever like here: https://discuss.python.org/t/memoizing-methods-considered-harmful/24691.

If I comment out that decorator, my demo script works as expected. I would still consider this a bug, the cache should not strongly reference objects and keep them alive forever (or until 256 are created), what do you think?

**Allyyi:**
Hi team, I have read relavent discussions. My idea is we can try to use weak references like `weakref` for function caching. If there's no one actively working on this, I'd be happy to take this one. Could you please assign it to me?

**yaowubarbara:**
Hi, I'd like to work on this if no one else is actively on it. The root cause is clear @lru_cache on get_function_nonlocals holds strong references to Callable keys, so bound methods (and their associated objects) are kept alive until the cache evicts them. My plan is to replace the @lru_cache with a weakref-based cache that doesn't prevent GC. The tricky part is that bound methods can't be weakly referenced directly, so I'll need to handle that case, likely by skipping the cache for bound methods or keying on (id(func), ...) with a weak reference callback to clean up entries when the underlying object is collected.The change only affects caching strategy, the return value of get_function_nonlocals stays exactly the same, so wort case is a cache miss leading to recomputation, not incorrect results. Happy to open a draft PR for discussion.

**antonio-mello-ai:**
Hi — I see the root cause has been identified (`@lru_cache` on `get_function_nonlocals` holding strong refs to callables) and a couple of people expressed interest but no PR has been submitted.

I'd like to take a crack at this. My plan is to replace the `@lru_cache` with a `WeakValueDictionary`-based cache (or skip caching for bound methods entirely, since they can't be weakly referenced directly). Will look at the code and submit a PR shortly.

**antonio-mello-ai:**
Could you assign me to this issue? I have a fix ready (replaced `@lru_cache` with `WeakKeyDictionary`), but the CI bot requires the PR author to be assigned to the linked issue. My PRs #35797 and #35798 were auto-closed by the bot for this reason.

**antonio-mello-ai:**
Hi, I'd like to work on this issue. I've already submitted a fix (PR #35797) that replaces the `@lru_cache` on `get_function_nonlocals` with a `WeakKeyDictionary`-based cache, which was auto-closed due to missing assignment. The fix showed a 30% performance improvement on CodSpeed benchmarks. Happy to resubmit once assigned. Thanks\!
