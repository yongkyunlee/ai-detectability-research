# [FEATURE] [FEATURE] Add opt in context_strategy="summarized" to reduce inter task context pollution

**Issue #4661** | State: open | Created: 2026-03-01 | Updated: 2026-03-01
**Author:** Ameysr
**Labels:** feature-request

## Opt-in Context Summarization for Inter-Task Context

### Problem (traced through codebase)

In `Crew._execute_tasks()`, each task receives context via [_get_context()](cci:1://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/crew.py:1489:4-1498:9) → [aggregate_raw_outputs_from_task_outputs()](cci:1://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/utilities/formatter.py:15:0-25:63) in `formatter.py:26`. This concatenates ALL prior task raw outputs verbatim. In a 5-task crew, Task 5's prompt contains ~8,000+ tokens of unfiltered prior output, causing ContextLengthExceeded errors or degraded LLM quality.

### Proposed Solution

Add an opt-in `context_strategy` field:

- [Crew(context_strategy="summarized")](cci:2://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/crew.py:128:0-2039:28) — crew-level, default is `"full"` (existing behavior unchanged)
- [Task(context_strategy="full")](cci:2://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/task.py:84:0-1312:26) — per-task override for tasks needing full output

When `"summarized"`:
- After each task completes, a small LLM call (~100 tokens) using the task's existing `agent.llm` compresses the output into a 2-3 sentence summary
- Summary stored in a new `TaskOutput.context_summary` field
- [_get_context()](cci:1://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/crew.py:1489:4-1498:9) uses summaries instead of raw outputs
- Falls back to truncation if LLM call fails (never crashes)
- Works with both sequential and async task execution

### Files Changed (~100 lines total)

| File | Change |
|------|--------|
| [tasks/task_output.py](cci:7://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/tasks/task_output.py:0:0-0:0) | Add `context_summary` field |
| [utilities/formatter.py](cci:7://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/utilities/formatter.py:0:0-0:0) | Add `aggregate_summarized_outputs_*` functions (existing untouched) |
| [crew.py](cci:7://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/crew.py:0:0-0:0) | Add `context_strategy` field, summary generation, update [_get_context()](cci:1://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/crew.py:1489:4-1498:9) |
| [task.py](cci:7://file:///C:/Users/amey/OneDrive/Desktop/Crewai/crewAI/lib/crewai/src/crewai/task.py:0:0-0:0) | Add per-task `context_strategy` override |
| `tests/test_context_strategy.py` | New test file |

### What This Does NOT Change
- Default behavior is `"full"` — zero breaking changes
- Existing `aggregate_raw_outputs_*` functions untouched
- No new dependencies

1. **Token-budget truncation** — Simply truncating raw outputs to a fixed character limit. Simpler but loses important information that may appear at the end of an output.
2. **Inline summary generation** — Telling the task's own LLM to produce a summary alongside its output. Unreliable because LLMs don't always follow formatting instructions, and it breaks structured outputs (output_json, output_pydantic).
3. **Pass both summary and full output** — Let the downstream LLM choose. Doesn't solve the problem because tokens are still consumed in the context window regardless.

Willingness to Contribute
Yes, I'd be happy to submit a pull request
