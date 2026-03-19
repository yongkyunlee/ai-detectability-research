# Claude 4.6 models fail: consecutive assistant messages treated as prefill

**Issue #4798** | State: open | Created: 2026-03-10 | Updated: 2026-03-12
**Author:** shaul-saitowitz-pango

## Description

Claude 4.6 models (Sonnet 4.6, Opus 4.6) return **400 Bad Request** errors when used with CrewAI agents. Anthropic made a breaking API change: Claude 4.6 no longer supports assistant message prefilling, and any request with a trailing assistant message is rejected.

## Root Cause

`CrewAgentExecutor._append_message()` appends every LLM response as `role: "assistant"` ([crew_agent_executor.py#L273](https://github.com/crewAIInc/crewAI/blob/main/src/crewai/agents/crew_agent_executor.py#L273)):

```python
self._append_message(formatted_answer.text)  # role defaults to "assistant"
```

This builds conversations with **consecutive assistant messages**:

```
user: [system prompt + task]
assistant: [LLM response with tool call]
assistant: [tool result + observation]   ← consecutive assistant
assistant: [next iteration]              ← consecutive assistant
```

Claude 4.6 interprets the trailing assistant message as a prefill attempt and rejects the request. Earlier Claude models (3.5, 4.5) tolerated this, but 4.6 is strict.

## Steps to Reproduce

1. Create a CrewAI agent with `llm=LLM(model="anthropic/claude-sonnet-4-6-20250514")`
2. Give it a task that requires tool use (multiple iterations)
3. The agent fails on the second LLM call with:
   ```
   400 Bad Request: Prefilling assistant messages is no longer supported
   ```

## Expected Behavior

CrewAI should normalize the message history before sending to the LLM — either by:
- Merging consecutive same-role messages
- Inserting a `user` message between consecutive `assistant` messages
- Using `_format_model_specific_messages()` to handle this (it already has Mistral/Ollama handling but not Anthropic)

## Environment

- CrewAI version: 1.6.1 (also reproduced conceptually against 1.10.1 source)
- Python: 3.13
- LLM provider: OpenRouter (LiteLLM path)
- Models affected: `anthropic/claude-sonnet-4-6-20250514`, `anthropic/claude-opus-4-6-20250514`

## Related Issues

- #1454 (alternating messages in instruct mode — fixed via LiteLLM `ensure_alternating_roles`, but that param is no longer available)
- #2063 (Anthropic message formatting — fixed first-message ordering but not consecutive assistant messages)
- #3964 (extended thinking — fixed thinking block preservation)
- External: [livekit/agents#4907](https://github.com/livekit/agents/issues/4907), [strands-agents/sdk-python#1694](https://github.com/strands-agents/sdk-python/issues/1694)

## Suggested Fix

Add Anthropic handling to `_format_model_specific_messages()` in `llm.py` (around line 1508) to merge consecutive assistant messages, similar to the existing Mistral/Ollama handling:

```python
# Handle Anthropic models — merge consecutive same-role messages
if self.is_anthropic:
    merged = [messages[0]]
    for msg in messages[1:]:
        if msg["role"] == merged[-1]["role"]:
            merged[-1]["content"] += "\n\n" + str(msg["content"])
        else:
            merged.append(msg)
    messages = merged
```

## Workaround

Using a LiteLLM input callback to merge consecutive messages before they reach the API:

```python
import litellm

def merge_consecutive_messages(kwargs, **_):
    messages = kwargs.get("messages", [])
    if len(messages) < 2:
        return
    merged = [messages[0]]
    for msg in messages[1:]:
        if msg["role"] == merged[-1]["role"]:
            merged[-1]["content"] += "\n\n" + str(msg["content"])
        else:
            merged.append(msg)
    kwargs["messages"] = merged

litellm.input_callback = [merge_consecutive_messages]
```

## Comments

**ehansis:**
Note: The line number above refers to some previous version of the CrewAI package (before the split into native/react tool calls?).

In the current version, this problem still exists, but only for the react tool calling pattern (`_invoke_loop_react`). 

In the native tool calling pattern (`_invoke_loop_native_tools`) the tool results are appended with role `tool`:
 https://github.com/crewAIInc/crewAI/blob/542afe61a8adfca1b9a0434189b9f339dfb07817/lib/crewai/src/crewai/agents/crew_agent_executor.py#L1084-L1089

An accompanying reasoning prompt is appended with role "user"

https://github.com/crewAIInc/crewAI/blob/542afe61a8adfca1b9a0434189b9f339dfb07817/lib/crewai/src/crewai/agents/crew_agent_executor.py#L789-L793

https://github.com/crewAIInc/crewAI/blob/542afe61a8adfca1b9a0434189b9f339dfb07817/lib/crewai/src/crewai/agents/crew_agent_executor.py#L812-L816

So it looks like the issue should not occur here.
