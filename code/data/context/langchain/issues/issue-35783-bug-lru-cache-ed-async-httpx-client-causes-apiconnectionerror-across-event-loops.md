# Bug: @lru_cache-ed async httpx client causes APIConnectionError across event loops

**Issue #35783** | State: open | Created: 2026-03-12 | Updated: 2026-03-17
**Author:** niilooy
**Labels:** bug, openai, internal

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
- [x] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

errors = []
successes = []
lock = threading.Lock()

def worker(thread_id: int):
    """Each thread runs asyncio.run() which creates a fresh event loop."""
    for cycle in range(5):
        async def call():
            return await llm.ainvoke(f"Reply with only: t{thread_id}c{cycle}")

        try:
            result = asyncio.run(call())
            with lock:
                successes.append((thread_id, cycle))
        except Exception as e:
            with lock:
                errors.append((thread_id, cycle, e))
                print(f"Thread {thread_id} cycle {cycle}: {type(e).__name__}: {e}")

with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(worker, i) for i in range(8)]
    for f in as_completed(futures):
        f.result()

print(f"\nTotal: {len(successes) + len(errors)}, OK: {len(successes)}, FAIL: {len(errors)}")
```

### Error Message and Stack Trace (if applicable)

```shell
Traceback (most recent call last):
  File ".../openai/_base_client.py", line 1604, in request
    response = await self._client.send(...)
  File ".../httpx/_client.py", line 1629, in send
    response = await self._send_handling_auth(...)
  ...
  File ".../httpcore/_async/http11.py", line 135, in handle_async_request
    await self._response_closed()
  File ".../httpcore/_async/http11.py", line 250, in _response_closed
    await self.aclose()
  File ".../httpcore/_async/http11.py", line 258, in aclose
    await self._network_stream.aclose()
  File ".../httpcore/_backends/anyio.py", line 53, in aclose
    await self._stream.aclose()
  File ".../anyio/streams/tls.py", line 241, in aclose
    await self.transport_stream.aclose()
  File ".../anyio/_backends/_asyncio.py", line 1352, in aclose
    self._transport.close()
  File ".../asyncio/selector_events.py", line 875, in close
    self._loop.call_soon(self._call_connection_lost, None)
  File ".../asyncio/base_events.py", line 799, in call_soon
    self._check_closed()
  File ".../asyncio/base_events.py", line 545, in _check_closed
    raise RuntimeError('Event loop is closed')
RuntimeError: Event loop is closed

The above exception was the direct cause of the following exception:

openai.APIConnectionError: Connection error.
```

### Description

### The problem

`_get_default_async_httpx_client()` in `langchain_openai/chat_models/_client_utils.py` uses `@lru_cache` to share a single `httpx.AsyncClient` across all `ChatOpenAI` instances with the same `(base_url, timeout)`. This is unsafe when `ainvoke()` is called from multiple event loops — which happens in:

- **Multi-threaded async evaluation** (each thread runs `asyncio.run()`, creating a new loop)
- **Sequential `asyncio.run()` calls** (each call creates and then closes a new loop)
- **Framework scheduling** (e.g. Celery async workers, multi-process evaluation)

The cached `AsyncClient` opens HTTP connections that are bound to the event loop where the request was first made. When `asyncio.run()` finishes, that loop is **closed**. The next call from a different loop gets the same cached client, which tries to reuse (or close) connections from the dead loop, causing `RuntimeError: Event loop is closed`.

### Root cause

```python
# langchain_openai/chat_models/_client_utils.py

@lru_cache  # ← process-global, not event-loop-aware
def _cached_async_httpx_client(base_url, timeout):
    return _build_async_httpx_client(base_url, timeout)

def _get_default_async_httpx_client(base_url, timeout):
    try:
        hash(timeout)
    except TypeError:
        return _build_async_httpx_client(base_url, timeout)
    else:
        return _cached_async_httpx_client(base_url, timeout)  # ← shared across loops
```

The cache key is `(base_url, timeout)` but should also include the **event loop identity** to prevent cross-loop sharing. The same pattern exists in `langchain-anthropic`.

### Workaround

Pass an explicit `http_async_client` to bypass the cache entirely:

```python
import httpx
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    http_async_client=httpx.AsyncClient(),
    http_client=httpx.Client(),
)
```

Or implement a loop-isolated cache:

```python
import asyncio, httpx

_async_client_cache = {}

def get_loop_isolated_async_client(**kwargs):
    loop_id = id(asyncio.get_running_loop())
    if loop_id not in _async_client_cache:
        _async_client_cache[loop_id] = httpx.AsyncClient(**kwargs)
    return _async_client_cache[loop_id]
```

### System Info
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.3.0
> Python Version:  3.12.11

Package Information
-------------------
> langchain_core: 1.2.18
> langchain_openai: 1.1.11
> langsmith: 0.4.49
> openai: 2.26.0
> httpx: 0.28.1
> httpcore: 1.0.9
> anyio: 4.12.0

## Comments

**laniakea001:**
遇到类似问题可以尝试以下解决方案：

1. **避免在异步函数中使用 @lru_cache**：考虑使用自定义缓存或 functools.cache（Python 3.9+）
2. **为每个事件循环创建独立客户端**：使用 contextvars 来隔离客户端实例
3. **检查 httpx.AsyncClient 的生命周期**：确保客户端在事件循环结束前正确关闭

如果需要长期解决方案，建议在 GitHub 上提交 issue 给 httpx 团队，说明异步上下文中的缓存问题。

**anushkapunekar:**
Good find. The loop-aware cache approach is the right direction, but there's a secondary issue worth addressing: dead loop IDs will accumulate in the cache dict indefinitely since there's no cleanup when a loop closes. A more robust fix would use a WeakValueDictionary or register cleanup via loop.call_soon(client.aclose) when the loop is shutting down.
Also worth noting — the same @lru_cache pattern exists in langchain-anthropic's client utils, so any fix should be applied consistently across both packages.
Happy to open a PR if the maintainers agree on the approach.

**indexedakki:**
Root cause is clear — @lru_cache on _cached_async_httpx_client uses (base_url, timeout) as the key but ignores event loop identity. httpx.AsyncClient connections are bound to the loop they were created on, so reusing them across loops causes RuntimeError: Event loop is closed.
Suggested fix: Either make the cache loop-aware by including id(asyncio.get_running_loop()) in the cache key (with cleanup on loop close), or simply don't cache async clients at all since they're lightweight to create and correctness matters more than avoiding a few object creations.
The same issue likely exists in langchain-anthropic for the same reason.
Immediate workaround (already noted in the issue) is passing http_async_client=httpx.AsyncClient() explicitly.

**saiprasanth-git:**
I'd like to work on this issue. I've already identified the root cause and implemented a fix in PR #35794 (now closed due to the assignment requirement). The fix replaces the process-global `@lru_cache` on `_cached_async_httpx_client` with a `WeakValueDictionary` keyed by event loop `id()`, ensuring each event loop gets its own `AsyncClient` instance. Could a maintainer please assign this issue to me so I can reopen the PR?

**Ker102:**
I'd like to work on this. The root cause analysis is excellent — the `@lru_cache` keyed by `(base_url, timeout)` doesn't account for event loop identity, causing the cached `AsyncClient` to bind to a dead loop when `asyncio.run()` closes it.

I'll implement a loop-aware cache (using `id(asyncio.get_running_loop())` as part of the key) and submit a PR shortly.

**shivamtiwari3:**
Hi, I've updated my PR with a revised fix that addresses both the original cross-loop `APIConnectionError` bug and the performance regression from my first attempt.

**Root cause recap:** `_get_default_async_httpx_client` returns a process-global cached `httpx.AsyncClient`. `ChatOpenAI` stores it at `__init__` time. When a second `asyncio.run()` uses the same instance, requests go through a client bound to the now-closed first loop.

**New approach — loop-aware proxy:** Instead of a plain `@lru_cache`'d client, the function now returns a `_LoopAwareAsyncHttpxClientWrapper` — itself `@lru_cache`'d (one per `(base_url, timeout)` pair, so init performance is preserved). The proxy overrides `send()` to dispatch to a per-loop inner `httpx.AsyncClient` stored in a `WeakKeyDictionary`. Each new event loop gets a fresh inner client; GC'd loops are cleaned up automatically.

This avoids the -98.55% `test_init_time` regression because the outer proxy is created once and cached — `ChatOpenAI.__init__` pays no per-loop overhead. The per-loop cost is only on the first `send()` from a new loop.

Could a maintainer please assign this issue to me so the PR can be reopened? Thank you!

**saiprasanth-git:**
Hi maintainers! I opened PR #35794 fixing this issue with a `WeakValueDictionary` per-event-loop cache, but it was auto-closed since I wasn't assigned.

I also noticed the CodSpeed performance regression (-98.55% on `test_init_time`) flagged on my PR. The root cause is that `WeakValueDictionary.__getitem__` is significantly slower than `lru_cache` for the init-time benchmark. The fix Shivam described (a loop-aware proxy wrapper that stays `@lru_cache`d at the outer level) is a cleaner approach and would preserve init performance.

Could a maintainer please assign this issue to me so I can update my PR (#35794) with the proxy-based approach? Happy to implement it right away.

**maxsnow651-dev:**
I'm trying to reproduce this on my side

On Mon, Mar 16, 2026, 3:57 PM saiiiii ***@***.***> wrote:

> *saiprasanth-git* left a comment (langchain-ai/langchain#35783)
> 
>
> Hi maintainers! I opened PR #35794
>  fixing this issue
> with a WeakValueDictionary per-event-loop cache, but it was auto-closed
> since I wasn't assigned.
>
> I also noticed the CodSpeed performance regression (-98.55% on
> test_init_time) flagged on my PR. The root cause is that
> WeakValueDictionary.__getitem__ is significantly slower than lru_cache
> for the init-time benchmark. The fix Shivam described (a loop-aware proxy
> wrapper that stays @lru_cached at the outer level) is a cleaner approach
> and would preserve init performance.
>
> Could a maintainer please assign this issue to me so I can update my PR (
> #35794 ) with the
> proxy-based approach? Happy to implement it right away.
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
