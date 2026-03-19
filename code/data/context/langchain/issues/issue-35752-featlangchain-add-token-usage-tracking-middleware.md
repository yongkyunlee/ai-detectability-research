# feat(langchain): add token usage tracking middleware

**Issue #35752** | State: closed | Created: 2026-03-11 | Updated: 2026-03-11
**Author:** prakhar-srivastavaa
**Labels:** langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

### Feature Request

**Problem:**
The middleware system has call-count tracking (`ModelCallLimitMiddleware`) but no 
built-in way to track actual token consumption across agent runs. Users currently 
need custom code to aggregate `usage_metadata` from `AIMessage` responses for cost 
monitoring and budget enforcement.

**Proposed Solution:**
A `TokenUsageTrackingMiddleware` that:
- Extracts `usage_metadata` from `AIMessage` responses after each model call
- Accumulates `input_tokens`, `output_tokens`, `total_tokens` at thread and run levels
- Optionally enforces `thread_budget` / `run_budget` with configurable exit behavior
- Follows the same patterns as `ModelCallLimitMiddleware`

**Use Case:**
Production agents need token-level cost monitoring and budget caps. This is the 
most common observability gap in the current middleware offerings.

I have a working implementation with 21 passing unit tests and would like to 
contribute this.

### Use Case

Production AI agents need token-level cost monitoring and budget enforcement. 

Currently, users must write custom wrapper code to extract `usage_metadata` from 
every `AIMessage`, accumulate counts manually, and implement their own budget-check 
logic — even though the middleware system already supports this pattern for call 
counts (`ModelCallLimitMiddleware`).

This feature would let users:
- Monitor token consumption across agent runs with zero custom code
- Set hard token budgets to prevent runaway costs in agentic loops
- Get thread-level (persistent) and run-level (per-invocation) breakdowns

### Proposed Solution

A new `TokenUsageTrackingMiddleware` class following existing middleware patterns:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import TokenUsageTrackingMiddleware

# Tracking only (observability, no limits)
agent = create_agent("openai:gpt-4o", middleware=[TokenUsageTrackingMiddleware()])

# With budget enforcement
agent = create_agent(
    "openai:gpt-4o",
    tools=[search],
    middleware=[TokenUsageTrackingMiddleware(run_budget=50000, exit_behavior="end")],
)
```

Implementation details:
- Uses `after_model` hook to extract `usage_metadata` from the latest `AIMessage`
- Accumulates `input_tokens`, `output_tokens`, `total_tokens` at thread and run levels
- Uses `before_model` hook to check budgets before each model call
- Supports `exit_behavior="end"` (graceful) and `"error"` (raises `TokenBudgetExceededError`)
- State uses `UntrackedValue` for run-level fields (same pattern as `ModelCallLimitMiddleware`)
- Both sync and async variants implemented

I have a working implementation with 21 passing unit tests ready to contribute.

### Alternatives Considered

1. Using callbacks/tracing (e.g. LangSmith) — tracks usage externally but cannot 
   enforce budgets or stop agent execution mid-run.

2. Wrapping the model with a custom class — works but doesn't integrate with the 
   middleware system and requires per-project boilerplate.

3. Extending `ModelCallLimitMiddleware` to also track tokens — possible but conflates 
   two concerns (call counting vs. token tracking) and makes the API less clean.

A dedicated middleware is the cleanest approach since it follows the single-responsibility 
pattern of existing middleware (e.g. `ModelRetryMiddleware`, `ModelFallbackMiddleware`).

### Additional Context

Related patterns in the codebase:
- `ModelCallLimitMiddleware` (libs/langchain_v1/langchain/agents/middleware/model_call_limit.py) 
  — same state tracking pattern with thread/run levels
- `SummarizationMiddleware` — already reads `usage_metadata` for token-based triggers
- `langchain_core.messages.ai.UsageMetadata` — the standard token usage TypedDict

This middleware fills the gap between call-count limiting and full observability 
platforms, giving users a lightweight built-in option for token budget enforcement.

## Comments

**prakhar-srivastavaa:**
Hi, I have a complete working implementation ready (21 passing unit tests, follows existing middleware patterns). 
Please assign me so I can proceed with the PR. Ready to merge immediately.
