# gpt-5.4+ models not detected as Responses API models, causing tool_choice.function error

**Issue #35584** | State: open | Created: 2026-03-05 | Updated: 2026-03-09
**Author:** rohankub
**Labels:** external

## Description

`_model_prefers_responses_api` doesn't cover `gpt-5.4+` models (e.g. `gpt-5.4-2026-03-05`). This causes `langchain-openai` to route them through Chat Completions (`/v1/chat/completions`) instead of the Responses API, which results in OpenAI rejecting the request with:

```
Unknown parameter: 'tool_choice.function'
```

This happens because Chat Completions sends `tool_choice: {"type": "function", "function": {"name": "..."}}`, but `gpt-5.4+` only accepts the Responses API format (`{"type": "function", "name": "..."}`).

## Reproduction

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def my_tool(x: str) -> str:
    """A test tool."""
    return x

# Fails
llm = ChatOpenAI(model="gpt-5.4-2026-03-05")
llm_with_tools = llm.bind_tools([my_tool], tool_choice="my_tool")
result = await llm_with_tools.ainvoke("hello")
# → openai.BadRequestError: Unknown parameter: 'tool_choice.function'

# Works
llm = ChatOpenAI(model="gpt-5.4-2026-03-05", use_responses_api=True)
llm_with_tools = llm.bind_tools([my_tool], tool_choice="my_tool")
result = await llm_with_tools.ainvoke("hello")
# → SUCCESS: tool called correctly
```

## Expected behavior

`gpt-5.4-2026-03-05` is automatically routed to the Responses API, matching the same logic applied to `gpt-5.2-pro` and `codex` (added in #35058).

## Proposed fix

In `libs/partners/openai/langchain_openai/chat_models/base.py`:

```python
def _model_prefers_responses_api(model_name: str | None) -> bool:
    if not model_name:
        return False
    return "gpt-5.2-pro" in model_name or "gpt-5.4" in model_name or "codex" in model_name
```

## Version

- `langchain-openai==1.1.10` (latest)

## Comments

**AryamanSi17:**
@sbusso @jarib @zeke @deepblue Please assign this issue to me!

**goingforstudying-ctrl:**
Hi! I've submitted a fix for this in PR #35643.

The fix adds gpt-5.4 to the _model_prefers_responses_api detection function, ensuring these models are properly routed to the Responses API.

This should resolve the tool_choice.function error.

**ccurme:**
I can't reproduce the issue on latest and OpenAI's models page [includes chat completions support](https://developers.openai.com/api/docs/models/gpt-5.4) for gpt-5.4.

I'm able to take the payload produced by langchain-openai and get a response using the openai client directly:
```python
import openai

client = openai.OpenAI()

payload = {
  "model": "gpt-5.4-2026-03-05",
  "stream": False,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "my_tool",
        "description": "A test tool.",
        "parameters": {
          "properties": {
            "x": {
              "type": "string"
            }
          },
          "required": [
            "x"
          ],
          "type": "object"
        }
      }
    }
  ],
  "tool_choice": {
    "type": "function",
    "function": {
      "name": "my_tool"
    }
  },
  "messages": [
    {
      "content": "hello",
      "role": "user"
    }
  ]
}

client.chat.completions.create(**payload)
# ChatCompletion(id='chatcmpl-DHUyY6EQYYnxvCc9COi7zlJWOJUqx', choices=[Choice(finish_reason='tool_calls', index=0, logprobs=None, message=ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_LRehKscJSuQf8IymMLPvbe3E', function=Function(arguments='{"x":"hello"}', name='my_tool'), type='function')]))], created=1773063018, model='gpt-5.4-2026-03-05', object='chat.completion', service_tier='default', system_fingerprint=None, usage=CompletionUsage(completion_tokens=17, prompt_tokens=123, total_tokens=140, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
```
