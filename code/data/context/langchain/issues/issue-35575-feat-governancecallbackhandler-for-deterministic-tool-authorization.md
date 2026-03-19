# feat: GovernanceCallbackHandler for deterministic tool authorization

**Issue #35575** | State: closed | Created: 2026-03-05 | Updated: 2026-03-05
**Author:** devongenerally-png
**Labels:** external

## Feature request

A callback handler that enforces deterministic governance policies on tool calls via structural authority separation (PROPOSE / DECIDE / PROMOTE).

### Motivation

LangChain agents select and execute tools based on LLM reasoning, but there's no built-in mechanism to enforce per-tool authorization policies without LLM involvement. Current approaches (system prompts, output parsers) are probabilistic — they rely on the model to self-police.

For production deployments, teams need deterministic guarantees: "this agent can use `search` but not `shell`", "shell commands matching `rm -rf` are always denied", "every tool verdict is logged to a tamper-evident audit trail."

### Proposed solution

A `GovernanceCallbackHandler` that interposes between tool selection and tool execution using `on_tool_start` with `raise_error=True`:

- **PROPOSE**: Convert each tool call into a structured intent with SHA-256 content hash
- **DECIDE**: Evaluate the intent against user-defined policy rules — pure function, no LLM, no interpretation ambiguity
- **PROMOTE**: Allow approved calls, raise `ToolExecutionDeniedError` for denied calls, log every verdict to a hash-chained witness file

Policy example:
```python
policy = {
    "default": "deny",
    "rules": [
        {"tools": ["search", "wikipedia"], "verdict": "approve"},
        {
            "tools": ["shell"],
            "verdict": "approve",
            "constraints": {
                "blocked_patterns": ["rm -rf", "sudo"],
                "allowed_patterns": ["--dry-run"],
            },
        },
    ],
}
handler = GovernanceCallbackHandler(policy=policy, witness_path="./witness.jsonl")
agent.invoke(inputs, config={"callbacks": [handler]})
```

### Key properties

- **Fail-closed**: Unknown tools denied by default
- **Deterministic**: No LLM in the authorization path
- **Auditable**: Hash-chained witness log (each entry contains SHA-256 of previous entry) for tamper-evident audit trails
- **Zero core changes**: Uses existing `BaseCallbackHandler` + `raise_error=True`

### Reference implementation

PR #35529 contains a working implementation with 25 unit tests. Happy to iterate on the API surface based on feedback.

Related: [governance-guard](https://github.com/MetaCortex-Dynamics/governance-guard) implements this pattern for TypeScript agent frameworks.

## Comments

**eyurtsev:**
Use middleware for this pattern rather than callbacks. Callbacks usually are non blocking and aren't for this purpose.

**devongenerally-png:**
That makes sense — callbacks are observer-pattern and shouldn't block execution. Middleware is the right structural fit since governance needs to interpose *before* the tool runs and either allow or deny.

I'll rework this as a `RunnableConfig`-based middleware that wraps tool execution. The PROPOSE/DECIDE/PROMOTE pipeline and hash-chained witness log stay the same, but the integration point moves from `on_tool_start` to a proper middleware layer.

Would you prefer this as:
1. A `Runnable` wrapper (e.g. `GovernanceMiddleware` that wraps a `BaseTool`), or
2. Something that hooks into the tool execution path via `RunnableConfig` middleware?

Happy to look at existing middleware patterns in the codebase to match conventions.
