# Feature: Work Ledger integration — regression testing & diff for LangChain runs

**Issue #35725** | State: open | Created: 2026-03-10 | Updated: 2026-03-10
**Author:** metawake
**Labels:** core, external

### Checked other resources

- [X] This is a feature request, not a bug report or usage question.
- [X] I added a clear and descriptive title that summarizes the feature request.
- [X] I used the GitHub search to find a similar feature request and didn't find it.
- [X] I checked the LangChain documentation and API reference to see if this feature already exists.
- [X] This is not related to the langchain-community package.

### Package (Required)

- [X] langchain-core

### Feature Description

[Work Ledger](https://github.com/metawake/work-ledger) is an open-source library (MIT) for recording, replaying, and comparing LLM agent runs. It already ships a `WorkLedgerCallbackHandler` that inherits from `langchain_core.callbacks.BaseCallbackHandler` and captures:

- LLM/chat model calls with token usage
- Tool invocations with inputs/outputs
- Retriever queries with documents
- Chain-level inputs/outputs
- Causal links between steps

```python
from work_ledger import WorkLedger, WorkLedgerCallbackHandler
from langchain_openai import ChatOpenAI

ledger = WorkLedger(store="./runs")
handler = WorkLedgerCallbackHandler(ledger, run_name="my-chain")

chain.invoke({"question": "hi"}, config={"callbacks": [handler]})
run = handler.get_run()  # structured Run with steps, metrics, causal links
```

After recording runs, you can diff them:

```python
from work_ledger.testing.diff import RunDiff

diff = RunDiff(run_v1, run_v2)
print(f"Similarity: {diff.similarity:.0%}")
print(f"Token delta: {diff.token_diff:+d}")
print(f"Steps added: {diff.steps_added}")
```

### Use Case

When developing LangChain applications, prompt changes, model swaps, or tool modifications can silently alter behavior. Currently there's no standard way to:

1. Record a chain/agent execution as a structured artifact
2. Compare two runs to see exactly what changed (steps, outputs, tokens, cost)
3. Set up golden-file regression tests for CI

Work Ledger fills this gap. It's not an observability platform — it's a testing/debugging tool that complements LangSmith.

Typical workflow:
- Record a "known good" run
- Make changes (prompt, model, tools)
- Record the new run
- `RunDiff` shows exactly what changed
- CLI: `work-ledger diff  `

### Proposed Solution

I'd like to propose adding Work Ledger to LangChain's community integrations documentation, so users can discover it as a testing tool.

The integration is already working — the `WorkLedgerCallbackHandler` properly inherits from `BaseCallbackHandler`, passes `isinstance` checks, and works with LCEL chains via `RunnableConfig`.

Tested with real OpenAI API calls through `langchain-openai`:
- Simple LLM calls ✓
- LCEL chains (prompt | llm | parser) ✓
- Tool-calling LLMs ✓
- Cross-run diff ✓

### Alternatives Considered

- **LangSmith**: Great for observability/monitoring but focuses on tracing, not structured regression testing with diffs
- **Manual scripts**: Every team builds their own — no standard approach
- **agent-vcr / agentgraph**: Similar tools but single-framework; Work Ledger supports LangChain, LangGraph, PydanticAI, CrewAI, LlamaIndex, OpenAI SDK, Anthropic SDK

### Additional Context

- Repository: https://github.com/metawake/work-ledger
- License: MIT
- 276 tests passing
- Also integrates with LangGraph via `wrap_graph()`
- No heavy dependencies — langchain-core is optional (handler falls back to plain class)

## Comments

**miguelmanlyx:**
Yo, might be a openai outage thing on their end. Might be worth trying npx ai-doctor for a fallback.
