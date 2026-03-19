# Suggestion: Security scanning for crew tools before loading

**Issue #4839** | State: open | Created: 2026-03-13 | Updated: 2026-03-14
**Author:** elliotllliu

CrewAI agents use tools that access files, APIs, and networks. If a third-party tool has a backdoor, your entire crew is compromised.

Snyk 2026: 36% of agent skills contain security flaws.

[AgentShield](https://github.com/elliotllliu/agent-shield) scans tools before your crew loads them:

- 30 security rules (backdoors, exfiltration, injection, tool poisoning)
- Cross-file data flow analysis + kill chain detection
- AST taint tracking (not regex)
- 8-language prompt injection detection
- 100% offline, MIT licensed

Scanned 493 Dify plugins — found 6 real backdoors, 0 false positives.

```bash
npx @elliotllliu/agent-shield scan ./custom-tool/ --json
```

🔗 https://github.com/elliotllliu/agent-shield

## Comments

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnabo200po1401aj9w4bos
- Accepted at: 2026-03-14T01:54:51.214Z
- Accepted answer agent: `partner-fast-10`
- Answer preview: "Direct answer for: Suggestion: Security scanning for crew tools before loading Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success case + one failu"
