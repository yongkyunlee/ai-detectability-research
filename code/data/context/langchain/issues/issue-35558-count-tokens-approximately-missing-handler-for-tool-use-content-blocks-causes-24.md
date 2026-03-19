# count_tokens_approximately: missing handler for tool_use content blocks causes ~2.4x overcounting

**Issue #35558** | State: open | Created: 2026-03-04 | Updated: 2026-03-09
**Author:** fbiebl
**Labels:** external

## Bug Description

`count_tokens_approximately()` in `langchain_core/messages/utils.py` has no handler for `tool_use` content blocks (Anthropic format). These blocks fall through to the `else` branch which calls `repr(block)` — producing a Python object representation like `"{'type': 'tool_use', 'id': '...', 'name': '...', 'input': {...}}"` that is **much longer** than the actual JSON content.

## Affected Version

`langchain-core>=0.1.x` (confirmed on `1.2.17`)

## Reproducer

```python
from langchain_core.messages import AIMessage
from langchain_core.messages.utils import count_tokens_approximately

# Message with tool_use content block (Anthropic format)
msg = AIMessage(content=[
    {
        "type": "tool_use",
        "id": "toolu_01AbCdEf",
        "name": "search_memories",
        "input": {"query": "recent events"},
    }
])

# Actual compact JSON would be ~90 chars ≈ ~23 tokens
# repr() produces: "{'type': 'tool_use', 'id': 'toolu_01AbCdEf', 'name': 'search_memories', 'input': {'query': 'recent events'}}"
# That's ~115 chars from repr vs ~90 for compact JSON — already worse, and scales badly with large inputs

approx = count_tokens_approximately(msg)
print(f"Approximated tokens: {approx}")
# Returns significantly more tokens than the actual content warrants
```

## Root Cause

In `langchain_core/messages/utils.py` around line 2281, the content block handler has cases for `text`, `image_url`, etc. but no case for `tool_use` / `tool_result`:

```python
# Current behavior (simplified):
for item in content:
    if isinstance(item, str):
        ...
    elif item.get("type") == "text":
        total_chars += len(item.get("text", ""))
    else:
        total_chars += len(repr(item))  # ← tool_use falls here!
```

`repr({"type": "tool_use", "id": "...", "name": "...", "input": {...}})` produces a Python dict repr with single quotes, `True`/`False` booleans, etc. — typically **~2.4x longer** than the equivalent compact JSON for nested tool inputs.

## Impact

In production (weside.ai), we measured **4.6x overcounting** for real Anthropic conversation threads containing tool calls. The tiktoken `cl100k_base` approximation already overcounts Claude tokens (~1.9x), and the `repr()` fallback compounds the error to ~2.4x on top of that for tool_use blocks specifically.

This caused **premature summarization** — the system believed the context was full when only ~40% of the actual token budget was consumed.

## Expected Behavior

`tool_use` and `tool_result` blocks should be normalized to compact JSON (or at minimum use `json.dumps(item)`) before measuring character length:

```python
import json

elif item.get("type") in ("tool_use", "tool_result"):
    # Normalize to compact JSON to avoid repr() inflation
    total_chars += len(json.dumps(item, separators=(",", ":")))
```

## Workaround

We implemented a normalization function in our codebase (`_normalize_for_counting()`) that pre-processes messages to extract only text content and normalize tool blocks to compact JSON before passing to any token counter. This prevents the repr() inflation.

## Additional Notes

- This issue also affects `tool_result` content blocks (which can contain nested `content` arrays with `text` and `image` items)
- The fix should be consistent with how `text` blocks are handled — only count meaningful content, not Python object repr overhead

## Comments

**nightcityblade:**
Hi, I'd like to work on this. I'll submit a PR shortly.

**ccurme:**
Hello, thanks for this. [count_tokens_approximately](https://reference.langchain.com/python/langchain-core/messages/utils/count_tokens_approximately) has a `use_usage_metadata_scaling` feature that is used in SummarizationMiddleware in the latest versions of `langchain`. It uses reported usage metadata to scale token counts. We've found success using that as a lightweight way to improve accuracy.

Can you confirm whether this resolves your issue? There will be any number of discrepancies with the approximate counts across providers. I appreciate the issue highlighted here and am not opposed to patching, but if `use_usage_metadata_scaling` solves your issue, that may be sufficient (and generalize better across content block types, from Anthropic and other providers).
