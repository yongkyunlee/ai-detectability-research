# Support Immediate Streaming for Server-Side Tool Invocations

**Issue #33810** | State: open | Created: 2025-11-04 | Updated: 2026-03-11
**Author:** Christian-Browne
**Labels:** feature request, openai, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Feature Description

I would like LangChain to support **immediate streaming emission of server-side tool calls** when using OpenAI's server-side tools (`web_search_preview`, `code_interpreter`, `file_search`, etc.) with the Responses API.

Currently, when streaming with server-side tools, the `server_tool_call` content block is not emitted when the model decides to call the tool. Instead, it's buffered and emitted together with `server_tool_result` after the tool execution completes.

**What I'm requesting:**

This feature would allow LangChain to emit server-side tool calls immediately (when execution begins) by handling OpenAI's `.in_progress` status events, similar to how `function_call` and `reasoning` blocks already emit on `.added` events.

**Specific functionality:**

- Emit `server_tool_call` content blocks when tool execution begins (via `.in_progress` status events)
- Emit `server_tool_result` content blocks when tool execution completes (via `.done` events)
- Provide proper separation between tool call and result in the streaming timeline
- Match the existing streaming pattern for `function_call` and `reasoning` blocks

### Use Case

I'm building a RAG application with web search integration and code execution capabilities. My users need real-time feedback about what the AI agent is doing during streaming responses.

**Current problem:**

When the model decides to search the web or execute code, there's ~3 seconds with no feedback to the user. Then once the tool is finished executing it sends both the `server_tool_call` AND the `server_tool_result`. Ideally, I would like for the `server_tool_call` to be yielded immediately when the model decides to call it.

### Proposed Solution

I believe this could be implemented by adding handlers for OpenAI's `.in_progress` status events in the `_convert_responses_chunk_to_generation_chunk` function.

**Current implementation** (line 4265-4278 in `langchain_openai/chat_models/base.py` file):

```python
# Currently only handles .done events
elif chunk.type == "response.output_item.done" and chunk.item.type in (
    "web_search_call",
    "code_interpreter_call",
    "file_search_call",
    "computer_call",
    "mcp_call",
    "image_generation_call",
):
    _advance(chunk.output_index)
    tool_output = chunk.item.model_dump(exclude_none=True, mode="json")
    tool_output["index"] = current_index
    content.append(tool_output)
```

**Proposed enhancement:**

According to OpenAI's Responses API documentation, server-side tools emit status events during execution:

- `code_interpreter`: `.added` → **`.in_progress`** → `.interpreting` → `.completed` → `.done`
- `web_search`: `.added` → `.done` (no intermediate events)
- `mcp`: `.added` → **`.in_progress`** → `.completed`/`.failed` → `.done`
- `file_search`: `.added` → **`.in_progress`** → `.searching` → `.completed` → `.done`

The solution could emit tool calls on `.in_progress` events:

```python
# Handle .in_progress status events to emit tool calls immediately
elif chunk.type in (
    "response.code_interpreter_call.in_progress",
    "response.mcp_call.in_progress",
    "response.file_search_call.in_progress",
    "response.image_generation_call.in_progress",
):
    _advance(chunk.output_index)
    content.append({
        "type": chunk.item.type,
        "id": chunk.item_id,
        "index": current_index,
        "status": "in_progress",
    })

# Special case: web_search has no .in_progress event, use .added
elif (
    chunk.type == "response.output_item.added"
    and chunk.item.type == "web_search_call"
):
    _advance(chunk.output_index)
    content.append({
        "type": "web_search_call",
        "id": chunk.item_id,
        "index": current_index,
        "status": "started",
    })

# Keep existing .done handler for results
elif chunk.type == "response.output_item.done" and chunk.item.type in (...):
    # Existing implementation for tool results
    ...
```

### Alternatives Considered

_No response_

### Additional Context

### Related Documentation

- [OpenAI Code Interpreter Streaming](https://platform.openai.com/docs/api-reference/responses-streaming/response/code_interpreter_call)
- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- [OpenAI Server-Side Tools](https://platform.openai.com/docs/guides/function-calling#server-side-tools)

## Comments

**keenborder786:**
@Christian-Browne , The response.output_item.added event already fires with status: "in_progress", which gives users the immediate feedback they need.
So wouldn't a single update in if condition will be enough:
```python
 elif (
        chunk.type in ("response.output_item.added", "response.output_item.done")
        and chunk.item.type
        in (
            "web_search_call",
            "file_search_call",
            "computer_call",
            "code_interpreter_call",
            "mcp_call",
            "mcp_list_tools",
            "mcp_approval_request",
            "image_generation_call",
        )
    ):
        _advance(chunk.output_index)
        tool_output = chunk.item.model_dump(exclude_none=True, mode="json")
        tool_output["index"] = current_index
        content.append(tool_output)

```
Doc Reference: https://platform.openai.com/docs/api-reference/responses-streaming/response/output_item/added

**keenborder786:**
https://github.com/langchain-ai/langchain/pull/35080
Check the above Draft PR @Christian-Browne

**Christian-Browne:**
Thanks! Just left a comment on your PR

**passionworkeer:**
Immediate streaming for tool invocations would be a game-changer for real-time applications! This is a highly requested feature. Any implementation details or a rough timeline?
