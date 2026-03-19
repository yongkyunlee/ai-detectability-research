# openai: malformed tool calls cause all tool calls to be silently dropped

**Issue #35782** | State: open | Created: 2026-03-12 | Updated: 2026-03-13
**Author:** T1mn
**Labels:** openai, external, trusted-contributor

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package

- [x] langchain-openai

### Reproduction Steps / Example Code (Python)

```python
#!/usr/bin/env python3
"""
Minimal reproduction for: malformed tool calls cause all tool calls to be silently dropped

This script demonstrates a bug in _convert_delta_to_message_chunk where a malformed
tool call (missing 'function' key) causes ALL tool calls in the batch to be silently dropped.
"""

from langchain_openai.chat_models.base import _convert_delta_to_message_chunk

# Test case: One malformed tool call in a batch causes ALL to be dropped
mixed_delta = {
    "role": "assistant",
    "content": None,
    "tool_calls": [
        {
            "id": "call_good",
            "type": "function", 
            "function": {"name": "good_func", "arguments": "{}"},
            "index": 0
        },
        {
            "id": "call_bad",
            "type": "function",
            # Missing 'function' key - causes KeyError
            "index": 1
        }
    ]
}

result = _convert_delta_to_message_chunk(mixed_delta, None)
print(f"Tool call chunks count: {len(result.tool_call_chunks)}")
# Expected: 1 valid tool call chunk (the good one)
# Actual: 0 tool call chunks (entire batch lost!)
```

### Error Message and Stack Trace

```
No exception is raised - this is a silent data loss bug.

Output from reproduction script:
✓ Test 1 passed: Normal tool call works correctly
✓ Test 2 passed (bug confirmed): Malformed tool call was silently dropped
Tool call chunks count: 0
✗ BUG CONFIRMED: ALL tool calls were dropped due to one malformed tool call!
  Expected: 1 valid tool call chunk
  Actual: 0 tool call chunks (entire batch lost)
```

### Description

**What I'm doing:**
Processing streaming chat responses that include tool calls from OpenAI-compatible APIs.

**Expected behavior:**
When one tool call in a batch is malformed (missing required 'function' key), the valid tool calls should still be processed. The malformed one should be skipped or logged, but valid tool calls should not be lost.

**Actual behavior:**
A bare `except KeyError: pass` in `_convert_delta_to_message_chunk` causes the entire list comprehension to fail, silently dropping ALL tool calls when ANY single tool call is malformed.

**Root Cause:**
In `libs/partners/openai/langchain_openai/chat_models/base.py`, lines 417-429:

```python
if raw_tool_calls := _dict.get("tool_calls"):
    try:
        tool_call_chunks = [
            tool_call_chunk(
                name=rtc["function"].get("name"),
                args=rtc["function"].get("arguments"),
                id=rtc.get("id"),
                index=rtc["index"],
            )
            for rtc in raw_tool_calls
        ]
    except KeyError:
        pass  # BUG: This silently drops ALL tool calls
```

The `except KeyError: pass` wraps the entire list comprehension. When any single tool call lacks the 'function' or 'index' keys, the entire batch is discarded without warning.

**Impact:**
- Silent data loss in streaming responses
- Difficult to debug since no error is raised
- Affects all OpenAI-compatible integrations

**Suggested Fix:**
Handle errors per-tool-call rather than for the entire batch:

```python
tool_call_chunks = []
for rtc in raw_tool_calls:
    try:
        tool_call_chunks.append(
            tool_call_chunk(
                name=rtc["function"].get("name"),
                args=rtc["function"].get("arguments"),
                id=rtc.get("id"),
                index=rtc["index"],
            )
        )
    except KeyError:
        # Log warning or skip silently per-tool-call
        continue
```

**I am willing to submit a PR to fix this issue.**
Please assign this issue to me. I have already identified the root cause and can implement the fix as suggested above.

### System Info

```
Repository: langchain-ai/langchain
Branch: master
Commit: 1891d414be
Commit Date: 2026-03-11 23:09:17 -0400
langchain-openai version (from pyproject.toml): 1.1.11
langchain-core version (from pyproject.toml): 1.2.18
Python version: 3.10.12
```

**Note:** This issue was discovered using automated static analysis and confirmed through dynamic testing. The reproduction script confirms the bug exists in the current codebase.

## Comments

**T1mn:**
I'd like to work on this issue and submit a PR. Please assign it to me if possible.

**laniakea001:**
Thanks for the detailed reproduction! This is a known issue with OpenAI tool calling when malformed JSON is returned.

Here are some debugging suggestions:

1. **Enable verbose logging** to see raw API responses
2. **Use a validation wrapper** to skip malformed tool calls before execution
3. **Check OpenAI SDK version** - newer versions have better error handling

This helps isolate the malformed call without breaking the entire tool calling chain.

**laniakea001:**
## Potential Solutions

Thanks for the detailed reproduction! This is indeed a critical silent data loss bug. Here are a few approaches to fix it:

### 1. Per-Item Error Handling (Recommended)
Instead of wrapping the entire list comprehension, handle errors per item:

```python
tool_call_chunks = []
for rtc in raw_tool_calls:
    try:
        tool_call_chunks.append(tool_call_chunk(...))
    except KeyError as e:
        # Log only the failed item, continue with valid ones
        logging.warning(f"Skipping malformed tool call: {e}")
        continue
```

### 2. Validate Before Processing
Add validation upfront to filter invalid tool calls:

```python
def is_valid_tool_call(rtc):
    return all(k in rtc for k in ['function', 'index'])

valid_calls = [rtc for rtc in raw_tool_calls if is_valid_tool_call(rtc)]
```

### 3. Use dataclass Validation
Consider using Pydantic or similar for structured validation:

```python
from pydantic import BaseModel, validator

class RawToolCall(BaseModel):
    id: str
    type: str
    function: dict
    index: int
    
    @validator('function')
    def function_must_have_name(cls, v):
        if 'name' not in v:
            raise ValueError('function must have name')
        return v
```

### Additional Recommendations:

1. **Add unit tests** for malformed input scenarios
2. **Consider using  field in the response model** to enforce schema
3. **Add a configuration flag** to choose between strict (fail fast) vs lenient (skip invalid) modes

Hope this helps! The root cause analysis is solid. 👍

**gitbalaji:**
Hi, I've opened PR #35813 with a fix for this. Could a maintainer please assign this issue to me? The fix moves the `try/except KeyError` inside the loop so only the malformed item is skipped rather than dropping the entire batch.
