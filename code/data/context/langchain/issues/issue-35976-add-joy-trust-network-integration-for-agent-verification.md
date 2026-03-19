# Add Joy trust network integration for agent verification

**Issue #35976** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** tlkc888-Jenkins
**Labels:** external

## Feature Request

**Problem:**
When LangChain agents delegate tasks to other agents or tools, there's no standard way to verify trustworthiness. Malicious or unreliable agents could be delegated sensitive tasks.

**Solution:**
Integrate with [Joy](https://choosejoy.com.au), an open trust network for AI agents. Joy provides:
- Trust scores based on vouches from other trusted agents
- Verified badges for agents that prove endpoint ownership
- Discovery of trusted agents by capability

**Proposed Components:**
- `langchain-joy` partner package
- `JoyTrustVerifier` - Programmatic trust verification
- `JoyTrustTool` - LangChain tool for trust checks in agent workflows
- `JoyDiscoverTool` - Tool for discovering trusted agents

**Why This Matters:**
As AI agents collaborate more, trust becomes critical. Joy provides a decentralized reputation layer where agents build trust through vouches. 6,000+ agents are already registered.

**Existing PR:**
PR #35902 was auto-closed due to missing issue link. Happy to reopen once this issue is approved.

**References:**
- Joy API: https://joy-connect.fly.dev
- Documentation: https://choosejoy.com.au
- Similar integrations: AutoGPT #12423, CrewAI #4886

## Comments

**Jairooh:**
Interesting proposal — agent-to-agent trust is a real gap as multi-agent workflows become more common. One thing worth thinking through carefully here: a reputation network based on vouches is useful for discovery, but it doesn't help you at runtime when a trusted agent's endpoint gets compromised or starts behaving outside its declared capabilities — a high trust score doesn't prevent prompt injection or scope creep mid-execution. It might be worth pairing something like Joy for pre-flight discovery/verification with runtime behavioral monitoring that actually watches what the delegated agent *does* once invoked, which is the layer where things tend to go wrong in practice.

**fairchildadrian9-create:**
Thanks for reporting this I'll take a look

On Tue, Mar 17, 2026, 7:27 AM Jairooh ***@***.***> wrote:

> *Jairooh* left a comment (langchain-ai/langchain#35976)
> 
>
> Interesting proposal — agent-to-agent trust is a real gap as multi-agent
> workflows become more common. One thing worth thinking through carefully
> here: a reputation network based on vouches is useful for discovery, but it
> doesn't help you at runtime when a trusted agent's endpoint gets
> compromised or starts behaving outside its declared capabilities — a high
> trust score doesn't prevent prompt injection or scope creep mid-execution.
> It might be worth pairing something like Joy for pre-flight
> discovery/verification with runtime behavioral monitoring that actually
> watches what the delegated agent *does* once invoked, which is the layer
> where things tend to go wrong in practice.
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

**tlkc888-Jenkins:**
Thanks @Jairooh - this is a really insightful point and exactly the kind of feedback we need.

You're right that Joy currently focuses on **pre-flight trust** (discovery + verification before delegation). Runtime behavioral monitoring is a different layer that we don't currently address.

**What Joy does today:**
- Trust scores based on vouches from other trusted agents
- Verified badges (proof of endpoint ownership)
- Capability declarations
- Network-wide reputation that persists across interactions

**The gap you identified:**
A high trust score doesn't prevent a trusted endpoint from being compromised, experiencing prompt injection, or drifting outside declared capabilities mid-execution.

**Potential complementary approach:**
Joy could evolve to include runtime signals:
1. **Interaction outcomes** - did the delegated task succeed/fail?
2. **Capability drift detection** - flag agents behaving outside declared scope
3. **Anomaly reporting** - other agents can report suspicious behavior, affecting trust scores retroactively
4. **Session-scoped trust** - trust verified at runtime, not just at discovery

This would pair pre-flight reputation with post-execution feedback loops, making trust scores dynamic rather than static.

Thanks for engaging with this - runtime monitoring is definitely on the roadmap as Joy matures. Would love to continue this conversation as we build out the integration.

cc @fairchildadrian9-create

**tlkc888-Jenkins:**
Following up on the runtime monitoring discussion with @Jairooh —

We've been speccing out how to address the gap between pre-flight trust (Joy) and runtime behavioral monitoring. Rather than building a custom solution, we're planning to integrate with **LangSmith** for the runtime layer.

**Proposed architecture:**

```
Pre-flight (Joy)              Runtime (LangSmith)           Feedback
      │                              │                          │
  JTS check ───► Delegate ───► Trace execution ───► Anomaly? ───► Update JTS
```

**How it would work:**
- Joy handles discovery + trust verification before delegation
- LangSmith traces the actual execution (latency, token usage, tool calls, anomalies)
- Anomaly signals from LangSmith feed back into Joy to adjust trust scores retroactively

This keeps Joy focused on what it does well (trust network) while leveraging LangSmith's production-grade observability for runtime monitoring. It also means the `langchain-joy` integration would pair naturally with existing LangSmith setups.

Keen to hear if this direction makes sense to the maintainers. Happy to adjust the integration proposal accordingly.
