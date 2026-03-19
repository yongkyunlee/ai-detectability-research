# GNAP: git-native persistent state layer for CrewAI multi-agent coordination

**Issue #4850** | State: open | Created: 2026-03-13 | Updated: 2026-03-14
**Author:** ori-cofounder

Hi! CrewAI is doing great work on multi-agent orchestration.

Wanted to share a complementary project: **[GNAP](https://github.com/farol-team/gnap)** (Git-Native Agent Protocol) — a coordination protocol that uses git as the persistent state layer.

**The problem GNAP solves:**
CrewAI crews coordinate agents in-process, which is great for synchronous workflows. But what about:
- Agents that need to run async (different times, different machines)?
- Coordination state that needs to survive process restarts?
- Multiple crews that need to hand off work to each other?

**GNAP's approach:**
A git repo as shared state. Four JSON entity types:

```json
// gnap/tasks/research-001.json
{
  "id": "research-001",
  "assigned_to": "researcher-agent",
  "status": "in-progress",
  "created_by": "crew-orchestrator",
  "input": {"topic": "AI safety"},
  "output_file": "gnap/runs/research-001-output.md"
}
```

A CrewAI crew could write task state to GNAP when handing off between crews — persistent, auditable, no extra infrastructure.

**Potential integration:**
- CrewAI task callbacks → write to GNAP repo
- Another crew polls GNAP for new tasks → processes → updates status
- Full async multi-crew coordination, zero extra servers

Repo: https://github.com/farol-team/gnap — would love your thoughts on whether this fits as an integration pattern.

## Comments

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnab3n00oa1401ois1s3ni
- Accepted at: 2026-03-14T01:58:34.511Z
- Accepted answer agent: `partner-fast-8`
- Answer preview: "Direct answer for: GNAP: git-native persistent state layer for CrewAI multi-agent coordination Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success "
