# `trim_messages` breaks when `token_counter` is a per-message callable (lambda, subclass annotation, or postponed annotations)

**Issue #35629** | State: open | Created: 2026-03-07 | Updated: 2026-03-14
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
from __future__ import annotations
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.messages.utils import trim_messages

messages = [
    HumanMessage("What is 2 + 2?"),
    AIMessage("It is 4."),
    HumanMessage("What about 3 + 3?"),
]

def run_case(name, counter):
    try:
        result = trim_messages(messages, max_tokens=5, token_counter=counter)
        print(f"{name}: UNEXPECTED SUCCESS — returned {result}")
    except Exception as e:
        print(f"{name}: FAIL — {type(e).__name__}: {e}")

# Case 1: lambda — lambdas cannot be annotated
run_case("lambda", lambda msg: len(msg.content.split()))

# Case 2: no annotation
def counter_no_annotation(msg):
    return len(msg.content.split())

run_case("no annotation", counter_no_annotation)

# Case 3: string annotation
def counter_string_annotation(msg: "BaseMessage") -> int:
    return len(msg.content.split())

run_case("string annotation", counter_string_annotation)

# Case 4: subclass annotation
def counter_subclass(msg: HumanMessage) -> int:
    return len(msg.content.split())

run_case("subclass annotation", counter_subclass)

# Case 5: postponed annotations via `from __future__ import annotations`
def counter_postponed(msg: BaseMessage) -> int:
    return len(msg.content.split())

run_case("postponed annotations", counter_postponed)
```

### Error Message and Stack Trace (if applicable)

```shell
lambda: FAIL — AttributeError: 'list' object has no attribute 'content'
no annotation: FAIL — AttributeError: 'list' object has no attribute 'content'
string annotation: FAIL — AttributeError: 'list' object has no attribute 'content'
subclass annotation: FAIL — AttributeError: 'list' object has no attribute 'content'
postponed annotations: FAIL — AttributeError: 'list' object has no attribute 'content'
```

### Description

`trim_messages` accepts `token_counter` as either a per-list `(messages: list[BaseMessage]) -> int` or per-message `(msg: BaseMessage) -> int` callable, but the per-message form is misdetected in many natural cases.

The current detection logic relies on a raw annotation identity check against `BaseMessage`, which fails for common cases such as lambdas, unannotated functions, string annotations, subclass annotations, and postponed annotations. In these cases, the callable is misclassified as a list counter and called with a list of messages, which commonly causes runtime errors such as `AttributeError: 'list' object has no attribute 'content'`.

### System Info

System Information
------------------
> OS:  Windows
> OS Version:  10.0.26100
> Python Version:  3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 1.2.17
> langsmith: 0.7.9
> langchain_tests: 1.1.5

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

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
> uuid-utils: 0.14.1
> vcrpy: 8.1.1
> wrapt: 2.0.1
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**srinuk9570:**
I’d like to work on this issue.

**xXMrNidaXx:**
The root cause is in how `trim_messages` inspects the `token_counter` callable's type annotations to determine whether it accepts a single message or a list of messages. It uses `get_type_hints()` to inspect annotations, which fails for:

1. **Lambdas** — can't be annotated at all, so there are no hints to inspect
2. **String annotations** (`msg: "BaseMessage"`) — `get_type_hints()` resolves string annotations in the function's defining module's namespace; if `BaseMessage` isn't importable from there, it raises `NameError`
3. **Subclass annotations** — the inspection logic likely checks for exact `BaseMessage` type match rather than `issubclass()`
4. **Postponed annotations** (`from __future__ import annotations`) — all annotations become strings automatically, same issue as #2

**Workarounds while waiting for the fix:**

Option 1 — wrap your counter in a properly annotated function:
```python
from langchain_core.messages import BaseMessage
from langchain_core.messages.utils import trim_messages

def my_counter(msg: BaseMessage) -> int:
    return len(msg.content.split())

result = trim_messages(messages, max_tokens=5, token_counter=my_counter)
```

Option 2 — pass a model class as the token counter (the supported path):
```python
from langchain_openai import ChatOpenAI
result = trim_messages(messages, max_tokens=5, token_counter=ChatOpenAI(model='gpt-4o'))
```

Option 3 — pre-count and use `max_tokens` with a simple int counter that explicitly annotates with the exact base class:
```python
import langchain_core.messages as _m
from langchain_core.messages.utils import trim_messages

def counter(msg: _m.BaseMessage) -> int:
    return len(msg.content.split())

result = trim_messages(messages, max_tokens=5, token_counter=counter)
```

The fix in `langchain-core` should use a more robust inspection strategy: try `get_type_hints()` but fall back to treating the function as a single-message counter if inspection fails (which is the less-ambiguous default for simple callables).

**gautamvarmadatla:**
Requesting maintainer triage here because this is getting kind of ridiculous.

I opened a few issues in `langchain-core` and also put up the corresponding fixes:

* #35419 -> #35420
* #35629 -> #35630

I also have a couple of similar issues in `langgraph`:
* [https://github.com/langchain-ai/langgraph/issues/6956](https://github.com/langchain-ai/langgraph/issues/6956)
* [https://github.com/langchain-ai/langgraph/issues/6909](https://github.com/langchain-ai/langgraph/issues/6909)

What’s frustrating is that the issues were already reported and fixed in the original PRs, which included proper regression coverage. Since those PRs have been sitting open without maintainer review, newer PRs for the same bugs have started piling up with the exact same fixes. ( Even for this issue they all use the exact same function name and changes lol ) 

I tried replying to a few of them, but honestly it just keeps happening.

At this point, After looking through these follow-up PRs and the recent activity from some of the same accounts, this honestly looks like AI slop spam more than real independent contribution. It feels like people are just picking up already-reported bugs and existing fixes, repackaging them, and mass-opening duplicate PRs without adding anything meaningful. I have seen some of the same profiles doing similar stuff in other repos too ( Can send few ss ) .

Would really appreciate maintainer triage on the original issues and PRs first, and then closing, redirecting, or consolidating the duplicate follow-up PRs so everything stays in one place instead of turning into five parallel threads for the same bug.

Thanks.

cc @eyurtsev @ccurme @mdrxy

**JiwaniZakir:**
Picked this up -- working on a fix now.

**gautamvarmadatla:**
> Picked this up -- working on a fix now.

hi @JiwaniZakir please read the above comment first. There are already 5 PRs why would you want to create another one? :(

**JiwaniZakir:**
PR is up: https://github.com/langchain-ai/langchain/pull/35669

**gautamvarmadatla:**
Hi, could you please take a look when you get a chance? This doesn’t seem to be stopping.

cc @eyurtsev @ccurme @mdrxy

**ccurme:**
@gautamvarmadatla thank you for flagging the issue and submitting a fix.

We usually prefer PRs submitted by the issue author as there's increased trust that the PR author understands and can replicate the issue they are attempting to fix (and are also typically submitted first).

There has been a noticeable uptick in AI-generated PRs, many of which pile on to issues and ignore (1) previous PRs, and (2) maintainer comments or questions. We are working on a policy to combat this. Thank you for your patience in the meantime.

**gautamvarmadatla:**
> [GAUTAM V DATLA (@gautamvarmadatla)](https://github.com/gautamvarmadatla) thank you for flagging the issue and submitting a fix.
> 
> We usually prefer PRs submitted by the issue author as there's increased trust that the PR author understands and can replicate the issue they are attempting to fix (and are also typically submitted first).
> 
> There has been a noticeable uptick in AI-generated PRs, many of which pile on to issues and ignore (1) previous PRs, and (2) maintainer comments or questions. We are working on a policy to combat this. Thank you for your patience in the meantime.

awesome! tysm for the prompt response :)

**weiguangli-io:**
## Technical Analysis of `trim_messages` token_counter Detection

### Root Cause

The current detection logic at [utils.py L1420-L1424](https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/messages/utils.py#L1420-L1424) uses an identity check on the raw `inspect.Parameter.annotation`:

```python
if (
    next(iter(inspect.signature(actual_token_counter).parameters.values()))
    .annotation is BaseMessage
):
```

This fails in several well-documented scenarios:

1. **`from __future__ import annotations` (PEP 563)** — All annotations become strings at runtime. `param.annotation` is `'BaseMessage'` (a str), not the `BaseMessage` class, so `is BaseMessage` is always `False`. Notably, `utils.py` itself uses `from __future__ import annotations` (line 10), which means any function defined *in that file* with a `BaseMessage` annotation would also fail this check — though this doesn't currently matter since the user-supplied callable is defined elsewhere.

2. **Lambdas and unannotated functions** — `param.annotation` is `inspect.Parameter.empty`, which is not `BaseMessage`.

3. **Subclass annotations** (e.g., `msg: HumanMessage`) — The identity check requires the annotation to be exactly `BaseMessage`, not a subclass.

4. **String/forward-reference annotations** (e.g., `msg: "BaseMessage"`) — Same issue as PEP 563; the annotation is a string.

The net effect is that any per-message callable that isn't explicitly annotated with `msg: BaseMessage` in a module *without* `from __future__ import annotations` gets silently misclassified as a list counter, leading to `AttributeError: 'list' object has no attribute 'content'` at call time.

### Impact of Python's Type System Evolution

PEP 563 (available via `from __future__ import annotations` since Python 3.7, and originally planned to become default in 3.10+) makes all annotations lazy strings. While PEP 649 (deferred evaluation, accepted for Python 3.14) will change the mechanism again, the key takeaway is: **raw `inspect.Parameter.annotation` is unreliable for runtime type dispatch**. Libraries that need runtime annotation introspection must use `typing.get_type_hints()` with appropriate error handling, or avoid annotation-based dispatch entirely.

### Evaluation of PR #35630

[PR #35630](https://github.com/langchain-ai/langchain/pull/35630) by @gautamvarmadatla takes a solid approach:

1. **Uses `get_type_hints()` with a try/except fallback** — This correctly resolves string annotations back to live types in most cases, and gracefully handles `NameError`/`AttributeError`/`TypeError` when resolution fails (e.g., forward references to undefined names).

2. **Uses `issubclass()` instead of `is`** — Correctly handles subclass annotations like `HumanMessage`.

3. **Adds `token_counter_is_per_message` explicit flag** — Provides an escape hatch for lambdas and unannotated callables where auto-detection is fundamentally impossible. This is a clean API addition.

4. **Comprehensive test coverage** — Tests cover all five failure cases from the issue (exact annotation, subclass, string annotation, lambda with flag, unannotated with flag), plus backward compatibility.

The approach is well-considered. A few observations for the maintainers:

- The `token_counter_is_per_message` parameter is a new addition to a public API. Per the project's conventions, this should probably be keyword-only (it already is, given its position after existing keyword args — just worth confirming).
- An alternative design would be to default to treating ambiguous callables as per-message counters (since that's the more common user-facing pattern), but this would be a behavioral change for edge cases where users rely on the current fallback-to-list behavior. The explicit flag avoids this risk.
- One subtle point: `get_type_hints()` itself can be affected by the *caller's* module namespace. Since it's called from within `langchain_core.messages.utils` (which imports `BaseMessage`), string annotations like `"BaseMessage"` resolve correctly *only if* they refer to names importable from the callable's own module. This works for the common case but could theoretically fail for unusual setups. The try/except handles this gracefully.

### Recommendation

PR #35630 appears to be the earliest and most complete fix for this issue. Given that there are now 6+ duplicate PRs (most closed), I'd recommend the maintainers prioritize reviewing #35630. The fix is minimal, backward-compatible, and well-tested.

For anyone hitting this in the meantime: either annotate your counter with `msg: BaseMessage` (without `from __future__ import annotations` in your module), or pass a model object as `token_counter` instead of a callable.
