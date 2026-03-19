# Show HN: K9 Audit – Causal intent-execution audit trail for AI agents

**HN** | Points: 4 | Comments: 3 | Date: 2026-03-12
**Author:** zippolyon
**HN URL:** https://news.ycombinator.com/item?id=47344702
**Link:** https://github.com/liuhaotian2024-prog/K9Audit

On March 4, 2026, my Claude Code agent wrote a staging URL into a 
production config file — three times, 41 minutes apart. Syntax was 
valid, no error thrown. My logs showed every action. All green.The problem was invisible because nothing had recorded what the agent 
intended to do before it acted — only what it actually did.K9 Audit fixes this with a causal five-tuple per agent step:
- X_t: context (who acted, under what conditions)
- U_t: action (what was executed)
- Y*_t: intent contract (what it was supposed to do)
- Y_t+1: actual outcome
- R_t+1: deviation score (deterministic — no LLM, no tokens)Records are SHA256 hash-chained. Tamper-evident. When something goes 
wrong, `k9log trace --last` gives root cause in under a second.Works with Claude Code (zero-config hook), LangChain, AutoGen, CrewAI, 
or any Python agent via one decorator.pip install k9audit-hook

## Top Comments

**zippolyon:**
When it comes to auditing LLM-based agents, using another LLM tool is like having one criminal write a clean record for another. Therefore, I believe that a causal AI observation model must be introduced, and only with determinism can probability theory be audited.

**proofrelay:**
Interesting.  One pattern we’ve run into is that the hardest part of post incident analysis isn’t the action log, it’s reconstructing the state of authority and context at execution time.
A defensible execution record usually ends up needing a bundle like: input context, delegated identity&#x2F;permissions, policy version in force, intended action, actual outcome, and a cryptographic link to the previous step in the workflow.
Without sealing that bundle at execution time, you’re left playing mix and match with logs and systems later.  This isn’t really practical if you’re trying to produce an audit grade reconstruction of the decision chain.
