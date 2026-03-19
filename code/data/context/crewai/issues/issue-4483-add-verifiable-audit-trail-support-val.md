# Add Verifiable Audit Trail Support (VAL)

**Issue #4483** | State: open | Created: 2026-02-14 | Updated: 2026-03-16
**Author:** aite550659-max
**Labels:** no-issue-activity

# Add Verifiable Audit Trail Support (VAL)

**Problem:**
Multi-agent systems need verifiable records of which agent did what. Current CrewAI logging can be modified or deleted - no way to prove agent actions to third parties.

**Proposed Solution:**
Add `VALCrew` wrapper that automatically attests all crew actions to immutable storage (Hedera HCS by default, chain-agnostic spec).

**Example Usage:**
```python
from crewai import Crew, Agent, Task
from crewai_val import VALCrew

researcher = Agent(role="Researcher", ...)
writer = Agent(role="Writer", ...)

# Wrap your crew - all actions attested to HCS
crew = VALCrew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    topic_id="0.0.12345"
)

result = crew.kickoff()
```

**Benefits:**
- **Attribution**: Prove which agent in your crew did what
- **Trust**: Users can verify crew behavior
- **Debugging**: Complete crew interaction history
- **Compliance**: Auditable multi-agent workflows

**Specification:**
https://github.com/aite550659-max/verifiable-agent-log

**Reference Implementation:**
https://github.com/aite550659-max/verifiable-agent-log/tree/main/integrations/crewai

**Cost:** ~$0.0008 per attestation on Hedera HCS

Would CrewAI consider adding this as an optional feature?

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.
