# Bug: `_dict_int_op` raises ValueError for float values in UsageMetadata during streaming aggregation

**Issue #36015** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** nevanwang
**Labels:** external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.

### Example Code

```python
import operator
from langchain_core.utils.usage import _dict_int_op
from langchain_core.messages.ai import add_usage, UsageMetadata

# int values work fine
_dict_int_op({"a": 1}, {"a": 2}, operator.add)  # ✅ {"a": 3}

# float values crash
_dict_int_op({"tokens": 10, "cost": 0.05}, {"tokens": 20, "cost": 0.03}, operator.add)
# ❌ ValueError: Unknown value types: []. Only dict and int values are supported.

# Real-world scenario: UsageMetadata with float total_cost
left = UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150)
left["total_cost"] = 0.005
right = UsageMetadata(input_tokens=200, output_tokens=100, total_tokens=300)
right["total_cost"] = 0.010
add_usage(left, right)  # ❌ ValueError
```

### Error Message and Stack Trace

```
ValueError: Unknown value types: []. Only dict and int values are supported.
```

### Description

`_dict_int_op()` in `libs/core/langchain_core/utils/usage.py` only handles `int` and `dict` types but **not `float`**. When two dictionaries contain the same key with `float` values, the function raises a `ValueError`.

This affects streaming scenarios where LLM providers include float fields in `UsageMetadata` (e.g., `total_cost`, pricing fields, or any custom float metric). During chunk aggregation via `add_usage()` → `_dict_int_op()`, these float fields cause the aggregation to crash.

This is the same class of bug as #36011 (`merge_dicts` missing float support), but in a different function. The `_dict_int_op` function was designed to handle numeric operations on dictionaries but only checked for `int`, missing `float`.

**All 4 float scenarios crash:**
- Direct float values in dicts
- UsageMetadata with float `total_cost` on both sides
- Float field present on only one side (default=0 is int, other side is float)
- Mixed int (from cache init `total_cost=0`) + float (from provider `total_cost=0.005`)

### Root Cause

In `usage.py`, the type check is:
```python
if isinstance(left.get(k, default), int) and isinstance(right.get(k, default), int):
```

This should be:
```python
if isinstance(left.get(k, default), (int, float)) and isinstance(right.get(k, default), (int, float)):
```

### Proposed Fix

1. Change `isinstance(..., int)` to `isinstance(..., (int, float))` in `_dict_int_op()`
2. Update docstring and error message to reflect float support
3. Add regression tests for float values

### System Info

```
langchain-core: 0.3.x (latest main)
Python: 3.10+
OS: macOS / Linux
```

## Comments

**nevanwang:**
I have a fix ready for this bug in PR #36016. Could a maintainer please assign this issue to me so the PR can be properly linked? The fix is minimal and focused:

1. Change `isinstance(..., int)` to `isinstance(..., (int, float))` in `_dict_int_op()`
2. Updated docstring and error message
3. Added 5 regression tests covering float add, subtract, mixed int/float, nested, and one-sided scenarios

All existing tests pass.

**weiguangli-io:**
**Root cause:** `_dict_int_op` in `langchain_core/utils/usage.py` (lines 43-45) checks `isinstance(..., int)` for leaf values. Since Python's `isinstance(1.0, int)` is `False`, any float value in usage metadata (e.g., from providers returning fractional token costs or timing data) hits the `else` branch and raises `ValueError: Unknown value types ... Only dict and int values are supported.`

**Fix:** Extend the type check from `int` to `(int, float)`:

```python
if isinstance(left.get(k, default), (int, float)) and isinstance(
    right.get(k, default), (int, float)
):
```

The `default` parameter type hint and the op callable signature should also be widened to `int | float` for consistency.

I see PR #36016 already addresses this — happy to help review or submit a separate PR if needed.

**nevanwang:**
Hi 👋

This issue is now addressed as part of the comprehensive fix in PR #36053 , which covers all three affected functions:

- `merge_dicts()` and `merge_obj()` in `_merge.py` (fixes #36011)
- **`_dict_int_op()` in `usage.py`** (fixes this issue)

The change expands `isinstance(..., int)` to `isinstance(..., (int, float))` in `_dict_int_op()`, along with updated type annotations, docstrings, and error messages. Regression tests for pure float addition, mixed int/float, and nested dicts with float values are included.

All tests pass ✅ and lint is clean ✅.

**maxsnow651-dev:**
Thanks I texted it and it worked

On Wed, Mar 18, 2026, 2:06 AM nevanwang ***@***.***> wrote:

> *nevanwang* left a comment (langchain-ai/langchain#36015)
> 
>
> Hi 👋
>
> This issue is now addressed as part of the comprehensive fix in PR #36012
> , which covers all
> three affected functions:
>
>    - merge_dicts() and merge_obj() in _merge.py (fixes #36011
>    )
>    - *_dict_int_op() in usage.py* (fixes this issue)
>
> The change expands isinstance(..., int) to isinstance(..., (int, float))
> in _dict_int_op(), along with updated type annotations, docstrings, and
> error messages. Regression tests for pure float addition, mixed int/float,
> and nested dicts with float values are included.
>
> All tests pass ✅ and lint is clean ✅.
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
