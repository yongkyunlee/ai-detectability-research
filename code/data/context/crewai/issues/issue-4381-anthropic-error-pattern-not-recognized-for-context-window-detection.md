# Anthropic error pattern not recognized for context window detection

**Issue #4381** | State: closed | Created: 2026-02-05 | Updated: 2026-03-13
**Author:** npkanaka
**Labels:** no-issue-activity

## Problem
When using Anthropic/Claude models with `respect_context_window=True`, context window errors are not detected because CrewAI's error pattern matching doesn't recognize Anthropic's error message format.

**Anthropic error:** `"prompt is too long: 210094 tokens > 200000 maximum"`

## Impact
The `respect_context_window=True` flag enables automatic summarization when context limits are exceeded, but this feature doesn't work for Anthropic models because the error detection fails.

## Root Cause
**File:** `crewai/utilities/exceptions/context_window_exceeding_exception.py`

The `CONTEXT_LIMIT_ERRORS` list only includes OpenAI-style error patterns:
```python
CONTEXT_LIMIT_ERRORS: Final[list[str]] = [
    "expected a string with maximum length",
    "maximum context length",
    "context length exceeded",
    "context_length_exceeded",
    "context window full",
    "too many tokens",
    "input is too long",
    "exceeds token limit",
]
```

But Anthropic returns: `"prompt is too long: 210094 tokens > 200000 maximum"`

## Related
- PR #4371 - Implements this fix

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
