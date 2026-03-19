# Bug: `merge_dicts` raises TypeError for float values during streaming chunk aggregation

**Issue #36011** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** nevanwang
**Labels:** external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.

### Example Code

```python
from langchain_core.utils._merge import merge_dicts

# int values merge correctly (added in #16605)
merge_dicts({"tokens": 10}, {"tokens": 5})  # ✅ {"tokens": 15}

# Equal float values pass (via the equality check)
merge_dicts({"score": 0.5}, {"score": 0.5})  # ✅ {"score": 0.5}

# Unequal float values crash
merge_dicts({"score": 0.5}, {"score": 0.3})  # ❌ TypeError
```

### Error Message and Stack Trace

```
TypeError: Additional kwargs key score already exists in left dict and value has unsupported type .
```

### Description

`merge_dicts()` in `libs/core/langchain_core/utils/_merge.py` handles `str`, `dict`, `list`, equal values, and `int` types — but **not `float`**. When two dicts contain the same key with unequal `float` values, the function falls through to the final `else` branch and raises a `TypeError`.

This affects streaming scenarios where LLM providers return float fields in `generation_info` or `additional_kwargs` (e.g., `logprob`, `score`, safety scores, cost fields, etc.). During chunk aggregation via `ChatGenerationChunk.__add__()` → `merge_dicts()`, these float fields cause the stream to crash.

**History:** Issue #17376 reported the same bug in 2024. PR #16605 added `int` support but omitted `float`. PR #36012 attempted a fix but was closed due to missing issue link and unrelated changes.

### Root Cause

In `_merge.py` line 71, the type check is:
```python
elif isinstance(merged[right_k], int):
```

This should be:
```python
elif isinstance(merged[right_k], (int, float)):
```

### Proposed Fix

1. Change `isinstance(merged[right_k], int)` to `isinstance(merged[right_k], (int, float))` in `merge_dicts()`
2. Apply the same fix to `merge_obj()` for consistency (add `float` to the numeric handling)
3. Add regression tests for float values

### System Info

```
langchain-core: 1.2.19
Python: 3.10+
OS: macOS / Linux
```

## Comments

**nevanwang:**
Hi maintainers 👋

I'd like to work on this issue. I've already prepared a fix in PR #36012 which:

1. Changes `isinstance(merged[right_k], int)` to `isinstance(merged[right_k], (int, float))` in `merge_dicts()`
2. Adds `float` numeric addition support in `merge_obj()` (after the equality check)
3. Includes regression tests for float values in both functions

The PR was auto-closed because I wasn't assigned to this issue yet. Could you please assign this issue to me so the PR can be reopened?

Thank you!

**FocusMode-coder:**
Hey! I may be able to help with this bug.

I build custom fixes for Python projects and automation systems.

If you'd like help resolving this issue quickly feel free to reach out.

Happy to take a look 👍

**Jairooh:**
Good catch on the `isinstance` check — this kind of bug surfaces specifically with streaming responses from models that return `logprobs` or `token_logprob` as floats, so the fix is definitely needed. One small thing worth double-checking in your PR: make sure `merge_obj()` handles the case where `left` is `float` and `right` is `int` (or vice versa) consistently, since Python's `isinstance(x, int)` actually returns `True` for `bool` as well, which could cause unexpected behavior if those ever appear in chunk metadata. Tagging this so maintainers see the PR reference — #36012 looks like a clean, targeted fix that deserves to be reopened.

**Jairooh:**
Good catch — the fix is straightforward: in `_merge.py`, the `int` branch (added in #16605) can simply be expanded to cover `float` as well by changing the `isinstance(left_val, int)` check to `isinstance(left_val, (int, float))`, which will sum the values the same way. One thing worth noting: summing floats across streaming chunks can silently accumulate floating-point precision errors, so if the intent is to track something like a running `logprob` or safety score, you may want to consider whether addition is actually the right aggregation semantic versus taking the last value or the max. A minimal repro PR would probably just be a one-liner change to that isinstance check plus a test case mirroring the ones already in the merge tests.

**Jairooh:**
The actual bug here is that `merge_dicts` doesn't handle `float` types when aggregating streaming chunks — the fix is straightforward: in the type-checking logic where `int` is handled (typically with `+` aggregation), `float` should be included in the same branch, e.g. `if isinstance(v, (int, float))`. You can see this in `langchain_core/utils/utils.py` around the `merge_dicts` implementation — adding `float` to that isinstance check should resolve the TypeError without any broader side effects.

**nevanwang:**
@eyurtsev Hi! Could you please assign this issue to me? 
I already have a fix ready in PR #36012 but it was auto-closed since I wasn't assigned. 
Happy to make any changes needed. Thanks! 🙏

**nevanwang:**
Hi everyone 👋

I've updated PR #36053 with a more comprehensive fix that now covers **all three affected functions**:

1. **`merge_dicts()`** — `isinstance(int)` → `isinstance((int, float))` for value summation
2. **`merge_obj()`** — Added `(int, float)` numeric addition **after** the equality check (this ordering is critical — see below)
3. **`_dict_int_op()`** in `usage.py` — Same `isinstance` expansion for `UsageMetadata` aggregation (also fixes #36015)

### Addressing @Jairooh's feedback

Great points about `bool` being a subclass of `int`. In our implementation, this is safely handled because the `left == right` equality branch comes **before** the numeric addition branch in `merge_obj()`. So `True == True` returns `True` (not `2`), and `42 == 42` returns `42` (not `84`). Only **unequal** numeric values (e.g., `10 + 5`) reach the addition branch.

Regarding float precision concerns: the current approach mirrors the existing `int` addition semantics. For use cases where last-value or max semantics are preferred, that would be a separate feature beyond this bug fix.

### Test coverage

- Regression tests for float in `merge_dicts`, `merge_obj`, and `_dict_int_op`
- Tests for mixed int/float, nested dicts with floats, and preserved special keys (`index`, `created`, `timestamp`)
- All 95 tests pass ✅, lint clean ✅

The PR is currently auto-closed pending issue assignment. @eyurtsev Could you please assign this issue to me so the CI can re-run? Thank you! 🙏
