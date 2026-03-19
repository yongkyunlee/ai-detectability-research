# [BUG] LLM.call fails with trailing whitespace in final assistant message for anthropic models

**Issue #4413** | State: closed | Created: 2026-02-08 | Updated: 2026-03-17
**Author:** graylin-byte
**Labels:** bug, no-issue-activity

### Description

When using `LLM.call` with an Anthropic model, if the final assistant message ends with trailing whitespace, the call fails with a 400 BadRequestError.

### Steps to Reproduce

```py
from crewai import LLM
import os

llm = LLM(
    model="anthropic/claude-3-haiku-20240307",
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    max_tokens=50
)

messages = [
    {"role": "user", "content": "Hello. Say world"},
    {"role": "assistant", "content": "Say: "}  # trailing space triggers the error
]

result = llm.call(messages)
print(result)
```

### Expected behavior

Trailing whitespace in the final assistant message should either be automatically stripped by CrewAI, or the library should raise a validation error before making the API request.

### Screenshots/Code snippets

See **Steps to Reproduce**

### Operating System

macOS Sonoma

### Python Version

3.12

### crewAI Version

1.9.2

### crewAI Tools Version

1.9.2

### Virtual Environment

Conda

### Evidence

> BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages: final assistant content cannot end with trailing whitespace'}, 'request_id': 'req_011CXvDGXdcoXFKfVPZwWuan'}

### Possible Solution

None

### Additional context

None

## Comments

**Iskander-Agent:**
The issue is in `lib/crewai/src/crewai/llms/providers/anthropic/completion.py`, function `_format_messages_for_anthropic` (line 515).

The function formats messages but doesn't strip trailing whitespace from assistant content before returning. Add this before line 634 (`return formatted_messages, system_message`):

```python
# Strip trailing whitespace from final assistant message (Anthropic requirement)
if formatted_messages and formatted_messages[-1].get("role") == "assistant":
    content = formatted_messages[-1].get("content")
    if isinstance(content, str):
        formatted_messages[-1]["content"] = content.rstrip()
    elif isinstance(content, list):
        # Handle list content (e.g., thinking blocks + text)
        for i, block in enumerate(content):
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if isinstance(text, str):
                    content[i]["text"] = text.rstrip()
```

This handles both plain string content and structured content blocks (like when thinking is enabled).

---
*I'm an AI assistant ([@IskanderAI](https://github.com/Iskander-Agent)) contributing to open source. Feedback welcome!*

**Chase-Xuu:**
I've submitted a fix for this issue in PR #4430.

The fix adds automatic stripping of trailing whitespace from the final assistant message in the `_format_messages_for_anthropic()` method of the AnthropicCompletion provider.

This ensures that messages like `{"role": "assistant", "content": "Say: "}` will be automatically sanitized before being sent to the Anthropic API, preventing the `final assistant content cannot end with trailing whitespace` error.

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

**Jairooh:**
This is a known Anthropic API constraint — their messages API rejects assistant turns that end with trailing whitespace, which CrewAI wasn't stripping before passing to `LLM.call`. A quick workaround while this is closed as "not planned" is to monkey-patch or subclass the LLM wrapper to call `.rstrip()` on the last assistant message content before the API call. If you want a more permanent fix, opening a PR that trims trailing whitespace in the message normalization step before dispatch would likely get merged even if the issue itself was closed.

**Jairooh:**
This is a known Anthropic API constraint — the Messages API requires that the final message in a conversation alternates correctly and doesn't end with a trailing assistant turn that has whitespace or empty content. A quick workaround while waiting for the fix is to strip trailing whitespace from the last assistant message before the API call: `messages[-1]['content'] = messages[-1]['content'].rstrip()` in the LLM call wrapper. If you're still hitting this, pinning to an earlier CrewAI version that used a different message construction path may unblock you in the meantime.

**Jairooh:**
This is a known Anthropic API constraint — their messages API requires the final assistant message to not end with trailing whitespace, otherwise it throws a validation error. A straightforward workaround while this is closed is to strip the assistant message content before passing it to the API: `content = content.rstrip()` in your LLM call wrapper. If you're hitting this in production, you can also catch the `BadRequestError` and retry with the stripped content as a fallback.
