# [BUG] Native tool calls are discarded if LLM returns a text response

**Issue #4788** | State: open | Created: 2026-03-09 | Updated: 2026-03-11
**Author:** ehansis
**Labels:** bug

### Description

The Crew Agent Executor loop for models supporting native tools intentionally passes `available_functions=None` to `get_llm_response` in order to get the tool calls as list for external execution:

https://github.com/crewAIInc/crewAI/blob/cd42bcf035c7e5b50ca6317da712d99394c75b44/lib/crewai/src/crewai/agents/crew_agent_executor.py#L512-L528

However, if the LLM response contains a text response in addition to the tool calls, this text response is returned instead of the tool calls, because of `available_functions` being `None`. The intention probably would be to follow the path `6)` below, but `5)` is executed instead.

https://github.com/crewAIInc/crewAI/blob/cd42bcf035c7e5b50ca6317da712d99394c75b44/lib/crewai/src/crewai/llm.py#L1237-L1251 

Fixing this might be as easy as switching `5)` and `6)`, but I'm not sure if this breaks something else.

The plaintext response is passed back into the agent executor loop and handled as potential final answer, the tool calls are never executed.

https://github.com/crewAIInc/crewAI/blob/cd42bcf035c7e5b50ca6317da712d99394c75b44/lib/crewai/src/crewai/agents/crew_agent_executor.py#L546-L557

### Steps to Reproduce

Sorry, I have no minimal reproduction example available at this time.

I ran a crew with native tool calls against "openrouter/anthropic/claude-haiku-4.5" and "openrouter/anthropic/claude-sonnet-4.6" with some custom tool definitions. This triggered LLM responses with both text response and `ChatCompletionMessageToolCall` definitions, which causes the described issue.

### Expected behavior

Return the tool calls and execute them in the agent executor loop. Discard the text response content (I guess?).

### Screenshots/Code snippets

See above

### Operating System

Ubuntu 22.04

### Python Version

3.12

### crewAI Version

1.10.1

### crewAI Tools Version

?

### Virtual Environment

Venv

### Evidence

LLM response with both text response and tool calls:

```
ModelResponse(id='redacted', created=1773061504, model='anthropic/claude-4.5-haiku-20251001', object='chat.completion', system_fingerprint=None, choices=[Choices(finish_reason='tool_calls', index=0, message=Message(content='I will search for the given query.', role='assistant', tool_calls=[ChatCompletionMessageToolCall(index=0, function=Function(arguments='{"mode": "redacted", "query": "redacted"}', name='code_search'), id='redacted', type='function')], function_call=None, provider_specific_fields={'refusal': None, 'reasoning': None}), provider_specific_fields={'native_finish_reason': 'tool_calls'})], usage=Usage(...), provider='Amazon Bedrock')
```

### Possible Solution

See above

### Additional context

See above

## Comments

**mvanhorn:**
Submitted a fix in #4806. The issue is that the text-return path (step 5) matches before the tool-calls-without-functions path (step 6) because `not available_functions` is True when the executor passes None. The fix reorders these checks so tool calls are returned first.

**saschabuehrle:**
This looks like a merge policy bug between assistant text and tool call payloads.

A robust approach is to parse response parts first, then apply deterministic precedence:

If any valid tool calls exist, preserve all of them.
Keep assistant text as an additional content part, not a replacement.
Only drop a tool call when schema validation fails, and surface that explicitly in logs.

Two regression tests are especially useful:

Single message containing both text and one tool call
Single message containing text and multiple tool calls

Expected result in both cases is that tool calls are executed and text remains available for transcript or UI.
