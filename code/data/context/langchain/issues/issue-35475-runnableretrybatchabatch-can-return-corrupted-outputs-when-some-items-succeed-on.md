# RunnableRetry.batch/abatch can return corrupted outputs when some items succeed on retry and others still fail

**Issue #35475** | State: open | Created: 2026-02-28 | Updated: 2026-03-11
**Author:** yangbaechu
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
from langchain_core.runnables import RunnableLambda

failed_once = False

def process_item(name: str) -> str:
    global failed_once

    if name == "ok":
        return "ok-result"
    if name == "retry_then_ok":
        if not failed_once:
            failed_once = True
            raise ValueError()
        return "retry-result"
    raise ValueError()

runnable = RunnableLambda(process_item).with_retry(
    stop_after_attempt=2,
    retry_if_exception_type=(ValueError,),
    wait_exponential_jitter=False,
)

result = runnable.batch(
    ["ok", "retry_then_ok", "always_fail"],
    return_exceptions=True,
)

# Expected: the third item is an exception
print(result)
assert isinstance(result[2], Exception)
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

* I'm using `RunnableLambda(...).with_retry(...).batch(...)` with `return_exceptions=True`.
* I expect an input that still fails after all retry attempts to remain an exception in the matching output position.
* Instead, if one item succeeds on retry while another still fails, the failing item can be replaced by the successful item's output.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025
> Python Version:  3.10.12 (main, Jan 26 2026, 14:55:28) [GCC 11.4.0]

Package Information
-------------------
> langchain_core: 1.2.16
> langchain: 1.2.10
> langsmith: 0.7.9
> langchain_openai: 1.1.10
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.10
> openai: 2.24.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**yangbaechu:**
I’d like to work on this. My intended approach would be to add regression tests next to the existing retry batch tests `test_runnable.py`, then fix the final result assembly for this case. Does this align with maintainer expectations?

**JiwaniZakir:**
I'd like to work on this issue. I'll submit a PR shortly.

**JiwaniZakir:**
I've submitted a PR to address this issue: https://github.com/langchain-ai/langchain/pull/35556

**giulio-leone:**
I have opened a fix for this in #35622.

**Root cause:** After retries, the final assembly used `result.pop(0)` to fill positions not in `results_map`. But `result` still contained successfully-retried values alongside exceptions, so the pop consumed the wrong elements — replacing exceptions with stale success values.

**Fix:** Replace the pop-based assembly with an index-mapped lookup using `last_remaining_indices` to correctly associate each original position with its result from the last batch call.

Both sync (`_batch`) and async (`_abatch`) paths are fixed. Regression tests added for both.

**mvanhorn:**
Submitted a fix in #35744. The bug is in the output assembly: `result.pop(0)` on the shortened last-retry result list misaligns outputs when some inputs succeeded on earlier attempts. The fix uses the caught `RetryError` for any index not in `results_map` instead of popping from the stale result list. Applied to both `_batch` and `_abatch`.

**mvanhorn:**
I'd like to work on this issue. Could I be assigned?
