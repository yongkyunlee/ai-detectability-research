# [FEATURE] GuardrailProvider interface for pre-tool-call authorization

**Issue #4877** | State: open | Created: 2026-03-14 | Updated: 2026-03-17
**Author:** uchibeke

## Feature Area

Core functionality

## Is your feature request related to an existing bug?

Not a bug, but multiple open issues and PRs request tool-level authorization:

- **#4502** - "Proposal: Governance Guardrails Plugin for CrewAI" (closed as completed, but no interface was standardized)
- **#4596** - PR proposing fail-closed defaults for unsafe code execution (unresolved safety gap in confirmation timing)
- **#4682** - Feature request for Agent Loop Detection Middleware (proposes a `middleware` parameter on agents)
- **#4840** - Suggestion for pre-install security scanning of tools
- **#4810** - Feature request for Wasm-based sandboxed code execution

CrewAI's existing guardrail system (`Task.guardrail` / `Task.guardrails`) validates *output* after task completion. The `BeforeToolCallHook` protocol in `crewai.hooks.types` can block tool execution by returning `False`. What's missing is a **standard provider contract** that sits between the hook system and authorization logic, so users can plug in any policy engine without writing raw hooks.

## Describe the solution you'd like

A `GuardrailProvider` protocol that any authorization provider can implement. It plugs into the existing `BeforeToolCallHook` system - no changes to the tool execution pipeline.

### Interface (~40 lines)

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

@dataclass
class GuardrailRequest:
    """Context passed to the provider for each tool call."""
    tool_name: str
    tool_input: dict
    agent_role: str | None = None
    task_description: str | None = None
    crew_id: str | None = None
    timestamp: str = ""  # ISO 8601

@dataclass
class GuardrailDecision:
    """Provider's allow/deny verdict."""
    allow: bool
    reason: str | None = None
    metadata: dict = field(default_factory=dict)

@runtime_checkable
class GuardrailProvider(Protocol):
    """Contract for pluggable tool-call authorization."""

    name: str

    def evaluate(self, request: GuardrailRequest) -> GuardrailDecision:
        """Evaluate whether a tool call should proceed.

        Returns a GuardrailDecision. If allow is False, the tool call
        is blocked and `reason` is surfaced to the agent.
        """
        ...

    def health_check(self) -> bool:
        """Optional readiness probe. Default: True."""
        ...
```

### How it plugs in

The provider registers itself as a `BeforeToolCallHook`. A thin adapter bridges the protocol:

```python
from crewai.hooks.tool_hooks import register_before_tool_call_hook

def enable_guardrail(provider: GuardrailProvider, *, fail_closed: bool = True):
    """Wire a GuardrailProvider into CrewAI's hook system."""

    def _hook(context) -> bool | None:
        request = GuardrailRequest(
            tool_name=context.tool_name,
            tool_input=context.tool_input,
            agent_role=getattr(context.agent, "role", None),
            task_description=getattr(context.task, "description", None),
        )
        try:
            decision = provider.evaluate(request)
        except Exception:
            return False if fail_closed else None
        if not decision.allow:
            return False  # blocks tool execution
        return None  # allow

    register_before_tool_call_hook(_hook)
```

### Configuration (optional, for YAML-based crews)

```yaml
# crew.yaml or crewai config
guardrail_provider:
  enabled: true
  fail_closed: true
  provider: "my_package.MyGuardrailProvider"
  config:
    # provider-specific settings
    policy_file: "./policies/default.yaml"
```

### What this enables

**Simple (no external dependencies):**
- Block tools by name (e.g., deny `ShellTool` in production)
- Restrict file paths per agent role
- Rate-limit tool calls per crew run

**Advanced (via provider packages):**
- Policy-as-code with declarative YAML rules
- Per-agent capability scoping in multi-agent crews
- Audit trails with signed decisions
- Remote policy evaluation for enterprise deployments

## Describe alternatives you've considered

**1. Raw `BeforeToolCallHook` only (status quo)**
Works today - any function returning `False` blocks a tool. But there's no contract for what context the hook receives, no standard for deny reasons, no `fail_closed` behavior, and no way to swap providers without rewriting hook logic. Each implementation is ad-hoc.

**2. Extend Task guardrails to cover tool calls**
Task guardrails (`Task.guardrail`) validate *output* after completion - a different concern. Tool-call authorization must happen *before* execution, per-call, across all tasks. Mixing the two conflates output validation with access control.

**3. Middleware parameter on Agent (like #4682 proposes)**
The loop detection middleware proposal (#4682) adds a `middleware` parameter to agents. A guardrail provider could be expressed as middleware, but tool authorization is cross-cutting - it should apply to all agents in a crew, not be configured per-agent. The hook system is the right level.

## Additional context

**Existing hook infrastructure is sufficient.** The `BeforeToolCallHook` protocol in `crewai.hooks.types` already supports returning `False` to block execution. The `ToolCallHookContext` provides `tool_name`, `tool_input`, `agent`, `task`, and `crew`. The `GuardrailProvider` protocol is a standardization layer on top of this - not a new execution path.

**Proven pattern.** [APort Agent Guardrails](https://github.com/APortHQ/aport-agent-guardrails) implements this provider pattern for multiple agent frameworks, demonstrating that a thin protocol over existing hooks is viable without core changes.

**Scope boundary.** This proposal covers: the `GuardrailProvider` protocol, the `enable_guardrail()` adapter, and documentation. It does NOT propose: RBAC, multi-tenant policies, bundled providers, changes to the agent loop, or modifications to existing task guardrails.

## Willingness to Contribute

Yes, I'd be happy to submit a pull request.

## Comments

**Jairooh:**
Pre-tool-call authorization is a critical gap. Static guardrails help but don't catch issues from autonomous agent behavior — unexpected tool call chains, escalating permissions, or actions that are technically allowed but contextually wrong.
We built AgentShield (useagentshield.com) for real-time risk scoring on every agent action. It integrates via CrewAI callbacks, catches behavioral anomalies as they happen, and supports approval gates for high-risk decisions.
Happy to share more if relevant to your use case.

**uchibeke:**
So we can’t have actual architectural discussions these days? Everyone trying to use AI to push their slop?

My proposal is for a provider agnostic way to do to offer guardrails. Please let’s read it and understand it before commenting or spamming

**Jairooh:**
sorry, I read the proposal again more carefully. The GuardrailProvider protocol with BeforeToolCallHook is exactly the right abstraction layer. What I should have asked: how do you envision the provider contract handling async authorization decisions, where the guardrail needs to wait on an external approval before returning?

That's the gap we ran into building AgentShield's approval workflow — i want know how your design addresses it.

**uchibeke:**
Hi @Jairooh, fair enough - I was too quick to react. AgentShield's approval workflow is actually exactly the kind of use case the provider contract needs to handle well.

On async: the current design has the provider's `before_tool_call` return a GuardrailDecision - allow, deny, or **_suspend_**. The suspend path is where async authorization lives. The framework holds execution and polls (or awaits a callback) until the provider resolves. The provider contract exposes a resolve(decision_id, outcome) endpoint for push-based resolution - so a human approval UI or an external policy engine can unblock it without the hook sitting in a busy-wait.

Timeout is configurable per provider, with a default-deny on expiry for irreversible actions. For reversible ones you can default-allow + register for audit.

This is the part I haven't fully specified in the proposal yet 0 - happy to work through it here if you want to share how AgentShield's approval workflow is structured. Might be useful to spec against a real implementation.

**Jairooh:**
That suspend + resolve(decision_id, outcome) pattern is exactly right. The busy-wait problem was the first thing we hit too.

In AgentShield's approval workflow: when a high-risk action is flagged, execution suspends and a pending approval record is created with a unique decision_id. The human approval UI calls a resolve endpoint (POST /approvals/{id}/decision) which unblocks the agent via a callback. Default-deny on configurable timeout for irreversible actions, default-allow + audit for reversible ones — same logic you described.

The main thing we haven't solved cleanly yet: what happens when the agent has downstream dependencies waiting on the suspended action.

**uchibeke:**
Yes. I dont know how this will fit cleanly into Crew tbh. We're pushing for more autonomy and if an action needs a human, then it should be handled by a Human and `done` or `allowed` should gate what the agent can do and the action, from an Agent and guardrail perspective should be complete. Then a Human can take on from there as a separate step/process.

Having the process pause will work if you control the end to end flow (Model, UI, Guardrail etc) but not sure how it works here.

If you have a clean way for adding this to the architecture I have proposed, happy to hear it.
