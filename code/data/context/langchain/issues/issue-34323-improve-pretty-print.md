# Improve `pretty_print`

**Issue #34323** | State: open | Created: 2025-12-12 | Updated: 2026-03-16
**Author:** mdrxy
**Labels:** feature request, internal

### Privileged issue

- [x] I am a LangChain maintainer, or was asked directly by a LangChain maintainer to create an issue here.

### Issue Content

## Description

`pretty_print()` does not format non-string message content properly. When `AIMessage.content` is a list of content block dictionaries (rather than a plain string), the method simply dumps the raw Python representation of the list, making the output difficult to read.

## Current Behavior

When a message contains structured content blocks (e.g., server-side tool calls, tool results, text with citations), `pretty_print()` outputs the raw dictionary representation:

```python
================================== Ai Message ==================================

[{'text': "I'll search for information...", 'type': 'text'}, {'id': 'toolu_123', 'input': {'query': 'search query'}, 'name': 'web_search', 'type': 'server_tool_use'}, {'content': [{'encrypted_content': 'EoAlCioIChgC...', 'title': 'Page Title', 'type': 'web_search_result', 'url': 'https://example.com'}], 'tool_use_id': 'toolu_123', 'type': 'web_search_tool_result'}, {'citations': [{'cited_text': '...', 'encrypted_index': '...', 'title': '...', 'type': 'web_search_result_location', 'url': '...'}], 'text': 'Here is the answer...', 'type': 'text'}]
```

## Expected Behavior

Content blocks should be formatted in a human-readable way:

```
================================== Ai Message ==================================

I'll search for information...

Server Tool Use: web_search (toolu_123)
  Args:
    query: search query

[Web Search Results]
  - Page Title (https://example.com)

Here is the answer...
```

## Root Cause

In `langchain_core/messages/base.py`, the `pretty_repr` method has a TODO comment acknowledging this limitation:

```python
def pretty_repr(self, html: bool = False) -> str:
    title = get_msg_title_repr(self.type.title() + " Message", bold=html)
    # TODO: handle non-string content.
    if self.name is not None:
        title += f"\nName: {self.name}"
    return f"{title}\n\n{self.content}"
```

While `AIMessage.pretty_repr()` extends this to handle `tool_calls` and `invalid_tool_calls`, it does not handle:
- `server_tool_call` / `server_tool_use` blocks
- `server_tool_result` blocks
- Text blocks with `annotations` / `citations`
- Other non-standard content block types

## Suggested Approach

1. Iterate over content blocks when `content` is a list
2. Format each block type appropriately:
   - **Text blocks**: Display the `text` field directly
   - **Server tool calls**: Show tool name, ID, and formatted arguments
   - **Server tool results**: Summarize results (e.g., count, titles/URLs) without dumping encrypted/binary data
   - **Citations/annotations**: Optionally display inline or as footnotes
   - **Non-standard blocks**: Fall back to a condensed representation or skip
3. Consider a `verbose` parameter to control level of detail

## Reproduction

```python
from langchain_core.messages import AIMessage

# Message with structured content blocks
msg = AIMessage(content=[
    {"type": "text", "text": "Here is some text"},
    {"type": "server_tool_call", "id": "123", "name": "my_tool", "args": {"key": "value"}},
    {"type": "server_tool_result", "tool_call_id": "123", "status": "success", "output": {"data": "..."}},
])

msg.pretty_print()  # Outputs raw list representation
```

## Related

- The `content_blocks` property provides typed access to content, which could be leveraged for formatting
- `KNOWN_BLOCK_TYPES` in `langchain_core/messages/content.py` defines the standard block types that should be handled

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
- [ ] langchain-cli
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

## Comments

**isatyamks:**
Hi! I've worked on fixing the pretty_print() formatting issue (#34323). I've implemented support for formatting non-string message content blocks (server tool calls, tool results, citations, etc.) in a readable way.
PR-->https://github.com/langchain-ai/langchain/pull/34339

**bitloi:**
@mdrxy Can you assign me the issue? I can implement the issue immediately.
