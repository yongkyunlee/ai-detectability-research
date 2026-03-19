# langchain-openai: `_construct_responses_api_input` omits `type: "message"` on user/system/developer items, breaking OpenAI-compatible endpoints

**Issue #35689** | State: closed | Created: 2026-03-09 | Updated: 2026-03-09
**Author:** santiagxf
**Labels:** external

## Description

`_construct_responses_api_input()` in `libs/partners/openai/langchain_openai/chat_models/base.py` builds Responses API input items **without** explicitly setting `"type": "message"` on `user`, `system`, and `developer` message dicts. OpenAI's native endpoint silently infers the type, but other OpenAI-compatible endpoints (e.g. Azure AI Foundry) enforce the schema strictly and reject the request with a **400 Bad Request**.

## Reproduction

```python
from langchain_openai import ChatOpenAI

# Using any OpenAI-compatible endpoint that strictly enforces the Responses API schema
model = ChatOpenAI(
    base_url="https://.services.ai.azure.com/openai/v1",
    api_key="...",
    model="gpt-4o",
)

model.invoke([
    {"role": "developer", "content": "Translate from English into Italian"},
    {"role": "user", "content": "hi!"},
])
```

## Error

```
BadRequestError: Error code: 400 - {'error': {'message': "Invalid value: ''. Supported values are: 
'apply_patch_call', 'apply_patch_call_output', 'code_interpreter_call', 'compaction', 'computer_call', 
'computer_call_output', 'custom_tool_call', 'custom_tool_call_output', 'file_search_call', 'function_call', 
'function_call_output', 'image_generation_call', 'item_reference', 'local_shell_call', 'local_shell_call_output', 
'mcp_approval_request', 'mcp_approval_response', 'mcp_call', 'mcp_list_tools', 'message', 'reasoning', 
'shell_call', 'shell_call_output', and 'web_search_call'.",
'type': 'invalid_request_error', 'param': 'input[1]', 'code': 'invalid_value'}}
```

The server sees an empty/missing `type` on `input[1]` and rejects it because it does not default to `"message"`.

## Root cause

In `_construct_responses_api_input()`, the `user`/`system`/`developer` code paths append the message dict without a `type` field:

```python
elif msg["role"] in ("user", "system", "developer"):
    if isinstance(msg["content"], list):
        ...
        if msg["content"]:
            input_.append(msg)    # ← no "type": "message"
    else:
        input_.append(msg)        # ← no "type": "message"
else:
    input_.append(msg)            # ← no "type": "message"
```

The OpenAI Python SDK's `EasyInputMessageParam` TypedDict already defines `type: Literal["message"]` as an (optional) field — setting it explicitly is spec-conforming and a no-op for OpenAI's own endpoint.

## Expected behavior

All message-role items in the Responses API `input` array should include `"type": "message"` so the output is valid for any OpenAI-compatible endpoint.

## Suggested fix

Add `msg["type"] = "message"` before each `input_.append(msg)` call for user/system/developer messages (and the else fallthrough) in `_construct_responses_api_input()`.
