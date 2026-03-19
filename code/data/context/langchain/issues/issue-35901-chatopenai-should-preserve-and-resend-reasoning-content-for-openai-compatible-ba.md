# ChatOpenAI should preserve and resend reasoning_content for OpenAI-compatible backends such as vLLM

**Issue #35901** | State: closed | Created: 2026-03-15 | Updated: 2026-03-16
**Author:** Shaunak00
**Labels:** external

### Issue
When using `langchain_openai.ChatOpenAI` against an OpenAI-compatible backend such as vLLM, some reasoning models return a non-standard assistant field named `reasoning_content`. `ChatOpenAI` currently does not preserve this field on the incoming assistant message and does not resend it on subsequent turns, which breaks multi-turn tool-calling flows for models/backends that expect the field to round-trip.

### Current behavior
- Turn 1 returns an assistant message with both a tool call and `reasoning_content`.
- LangChain parses the tool call, but `reasoning_content` is not surfaced in a reusable way by default.
- On Turn 2, after appending the tool result and invoking the model again, the earlier `reasoning_content` is not included in the outgoing assistant message payload.
- For some vLLM-served reasoning models, this leads to degraded or empty final responses in the tool-result summarization step.

### Expected behavior
If an OpenAI-compatible backend returns extra assistant message fields such as `reasoning_content`, there should be an opt-in or compatibility mechanism to:
1. Preserve the field on the `AIMessage` (for example in `additional_kwargs`).
2. Resend that field when serializing the prior assistant message for the next request.

### Minimal workaround
A local workaround is to subclass `ChatOpenAI` and patch both directions:
- override `_create_chat_result(...)` to capture `reasoning_content` from the raw response and store it in `AIMessage.additional_kwargs`
- override `_convert_message_to_dict(...)` to include `reasoning_content` when serializing prior `AIMessage` instances

That workaround resolves the issue for my vLLM setup and restores correct multi-turn tool-calling behavior.

### Why this seems upstream-relevant
This is not specific to one prompt or one model family; it is a compatibility gap between `ChatOpenAI` and OpenAI-compatible backends that extend the message schema with assistant-side reasoning fields. I am not suggesting this should be enabled unconditionally for OpenAI itself, but an explicit compatibility hook, passthrough mechanism, or backend-specific integration point would make sense.

### Suggested direction
One of these seems reasonable:
- an opt-in passthrough list for extra assistant message fields
- a more generic preservation of unknown assistant message attributes returned by compatible backends
- a dedicated vLLM/OpenAI-compatible chat integration if this is considered too backend-specific for `langchain_openai`

### Repro outline
1. Use `ChatOpenAI(base_url=, ...)` with a reasoning model served by vLLM.
2. Bind a simple tool and invoke the model with a prompt that triggers tool use.
3. Observe that the first assistant response includes a tool call and backend-specific `reasoning_content`.
4. Append the `ToolMessage` result and invoke the model again.
5. Observe that the prior assistant message sent by LangChain does not include `reasoning_content`, and the backend/model may return an empty or degraded final answer.

### Offer
I already have a local subclass-based patch that demonstrates the behavior and can convert it into a PR if maintainers can confirm the preferred repository and shape.

## Comments

**mdrxy:**
#34328

**fairchildadrian9-create:**
Stale

On Sun, Mar 15, 2026, 10:08 PM Mason Daugherty ***@***.***>
wrote:

> *mdrxy* left a comment (langchain-ai/langchain#35901)
> 
>
> #34328 
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
