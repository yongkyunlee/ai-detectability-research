# [Enhancement] Add debug logging when OutputParserError triggers agent retry

**Issue #4246** | State: open | Created: 2026-01-16 | Updated: 2026-03-10
**Author:** VedantMadane

## Description

When ormat_answer() raises OutputParserError, the agent enters a retry loop. However, the original malformed output and the specific parsing failure are not logged by default, making it difficult to diagnose why agents are retrying or producing slow/inconsistent results.

## Current Behavior

The agent silently retries when parsing fails, with no visibility into:
- What the LLM actually returned
- Why parsing failed
- How many retries occurred

## Proposed Enhancement

Add optional debug logging (controlled by environment variable or log level) that captures:

1. The raw LLM output that failed to parse (truncated for safety)
2. The specific parsing pattern that failed to match
3. Retry count per agent turn
4. Final outcome (success after N retries, or max iterations reached)

Example:
`
DEBUG [crewai.parser] Parse failed for agent 'Researcher': No Final Answer found
DEBUG [crewai.parser] Raw output (truncated): "Let me think about this... The answer is..."
DEBUG [crewai.parser] Retry 2/5 initiated
`

## Use Case

Debugging production crews that are:
- Slower than expected (hidden retry loops)
- Producing inconsistent results
- Hitting max iterations unexpectedly

## Additional Context

This would complement PR #4229 which improved the fail-closed behavior - having visibility into when/why that path triggers would help developers optimize their prompts.

## Comments

**jacobgadek:**
I've been hitting this exact wall with production crews. The silent retries burn tokens and time, and because the framework swallows the OutputParserError internally, you can't see the raw output that caused the failure.

As a workaround until this gets merged, I’m wrapping my agent execution in a separate process (using vallignus) to capture the raw stderr and stdout streams to a local file. It bypasses the CrewAI logger entirely, so you can see the malformed LLM response that triggered the retry loop even if the agent crashes.

It’s not a native fix, but it definitely helps catch those 'hidden' parsing failures: https://github.com/jacobgadek/vallignus

**bmdhodl:**
+1 on this. The silent retry problem is painful — you burn tokens and time with zero visibility into what went wrong.

I built a tracing SDK that captures every step of an agent run, which helps a lot with diagnosing retry loops:

```python
from agentguard import Tracer, LoopGuard
from agentguard.tracing import JsonlFileSink

tracer = Tracer(sink=JsonlFileSink("crew_trace.jsonl"))
loop_guard = LoopGuard(max_repeats=3)

with tracer.trace("crew.task") as span:
    span.event("reasoning.step", data={"thought": "planning research"})

    # Before each tool/LLM call, check for loops
    loop_guard.check(tool_name="llm_call", tool_args={"prompt": prompt})

    with span.span("llm.call", data={"model": "gpt-4", "prompt": prompt}):
        response = llm.call(prompt)

    span.event("llm.result", data={"response": response, "tokens": token_count})
```

Then inspect with: `agentguard report crew_trace.jsonl`

```
AgentGuard report
  Total events: 14
  Reasoning steps: 3
  Tool results: 2
  Loop guard triggered: 1 time(s)
```

It won't solve the CrewAI-native logging gap, but it gives you full visibility into what's happening during retries right now. Zero deps: `pip install agentguard47`

https://github.com/bmdhodl/agent47

**sicmundu:**
This is a great enhancement request. I've been working on a related feature proposal (#4682 — Loop Detection Middleware) and this intersects nicely.

The silent retry on `OutputParserError` is especially problematic because it can compound into the kind of repetitive loops that waste tokens and time. When an agent retries parsing without logging, it's invisible to both developers debugging and to any monitoring middleware.

A few thoughts on implementation:

1. **Structured logging** would be ideal here — not just a debug message but emitting a structured event like `{"event": "output_parse_retry", "attempt": n, "error_type": "OutputParserError", "agent": agent_name}`. This makes it consumable by monitoring tools and loop detectors.

2. **Retry count exposure**: Beyond logging, it would be valuable to expose the retry count to callbacks/middleware so external systems can react (e.g., escalate after N retries).

3. **Backoff visibility**: If there's any backoff logic, logging should include the delay before retry.

Happy to help implement this if it's still on the roadmap. It's a natural complement to the loop detection middleware I proposed.

**utibeokodi:**
The tricky thing about this failure mode is that the agent is not broken. It is doing exactly what it is supposed to do (OutputParserError → retry), just completely invisibly. So from the outside it looks like slowness, not a failure.

A short-term workaround while this is pending upstream. You can patch the retry path to emit structured logs:

```python
from crewai.agents import parser as agent_parser

original_parse = agent_parser.parse
_attempt_counter = {}

def patched_parse(text: str):
    call_id = id(text)
    _attempt_counter[call_id] = _attempt_counter.get(call_id, 0) + 1
    try:
        return original_parse(text)
    except Exception as e:
        print(f"[PARSE_FAIL] attempt={_attempt_counter[call_id]} raw_output={text[:200]} error={e}")
        raise

agent_parser.parse = patched_parse
```

Note: The attempt tracking is a best-effort approximation since crewAI does not expose retry count through the parser. If you want accurate retry counts, you need to hook into the agent loop one level up.
That at least gives you visibility into what the model returned and how many retries are burning before a success or final failure.

The right fix in the framework would be for every retry to emit a structured event with the raw LLM output, the parse error type, and the retry count, making it trivial to detect "this run burned 8 retries before succeeding" after the fact.
