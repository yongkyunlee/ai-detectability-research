# Show HN: AgentArmor – open-source 8-layer security framework for AI agents

**HN** | Points: 10 | Comments: 8 | Date: 2026-03-14
**Author:** AgastyaTodi
**HN URL:** https://news.ycombinator.com/item?id=47374958
**Link:** https://github.com/Agastya910/agentarmor

I've been talking to founders building AI agents across fintech, devtools, and 
productivity – and almost none of them have any real security layer. Their agents 
read emails, call APIs, execute code, and write to databases with essentially no 
guardrails beyond "we trust the LLM."So I built AgentArmor: an open-source framework that wraps any agentic 
architecture with 8 independent security layers, each targeting a distinct attack 
surface in the agent's data flow.The 8 layers:
  L1 – Ingestion: prompt injection + jailbreak detection (20+ patterns, DAN, 
       extraction attempts, Unicode steganography)
  L2 – Storage: AES-256-GCM encryption at rest + BLAKE3 integrity for vector DBs
  L3 – Context: instruction-data separation (like parameterized SQL, but for 
       LLM context), canary tokens, prompt hardening
  L4 – Planning: action risk scoring (READ=1 → DELETE=7 → EXECUTE=8 → ADMIN=10),
       chain depth limits, bulk operation detection
  L5 – Execution: network egress control, per-action rate limiting, human 
       approval gates with conditional rules
  L6 – Output: PII redaction via Microsoft Presidio + regex fallback
  L7 – Inter-agent: HMAC-SHA256 mutual auth, trust scoring, delegation depth 
       limits, timestamp-bound replay prevention
  L8 – Identity: agent-native identity, JIT permissions, short-lived credentialsI tested it against all 10 OWASP ASI (Agentic Security Integrity) risks from 
the December 2025 spec. The red team suite is included in the repo.Works as: (a) a Python library you wrap around tool calls, (b) a FastAPI proxy 
server for framework-agnostic deployment, or (c) a CLI for scanning prompts in CI.Integrations included for: LangChain, OpenAI Agents SDK, MCP servers.I ran it live with a local Ollama agent (qwen2:7b) – you can watch it block a 
`database.delete` at L8 (permission check), redact PII from file content at L6, 
and kill a prompt injection at L1 before it ever reaches the model.GitHub: https:&#x2F;&#x2F;github.com&#x2F;Agastya910&#x2F;agentarmor
PyPI:   pip install agentarmor-coreWould love feedback, especially from people who have actually built production 
agents and hit security issues I haven't thought of.TAGS: security, python, llm, ai, agents

## Top Comments

**Gnobu:**
Really thorough coverage of the attack surfaces—especially including identity as a core layer. Curious how you handle cross-agent permissions in dynamic workflows: do you rely solely on deterministic checks at each action, or is there a runtime trust evaluation that can adapt as agents interact?

**ibrahim_h:**
The pipeline ordering is smart — L8 identity running before anything touches the ingestion layer means a rogue agent gets rejected before it even gets to inject anything. I've seen a couple agent wrappers that run input scanning first and only check identity after, which is just asking for trouble.One thing I noticed digging through the code though — L4 risk scoring categorizes actions purely by verb. _categorize_action parses the action string for keywords like "read" or "delete" but never looks at params. So read.file targeting &#x2F;etc&#x2F;shadow gets a risk score of 1, while delete.file on &#x2F;tmp&#x2F;cache.json scores 7. In real agent workloads the target matters as much as the verb — feels like the policy engine could bridge this gap with param-aware rules, since the condition evaluator already supports params.* field resolution.Also noticed TrustScorer takes a decay_rate in __init__ but never actually applies time-based decay anywhere — trust only changes on interactions. So an agent that was trusted six months ago and went dormant still walks back in with the same score. Small thing but could matter in long-running multi-agent setups.The MCP rug-pull detection is the standout feature for me. Cross-referencing tool names against their descriptions to catch things like "safe_search" that actually calls exec — haven't seen that anywhere else. With how fast MCP is getting adopted this could get real traction.

**kwstx:**
This looks fantastic, agent security is definitely under-addressed.
Curious how you handle inter-agent trust scoring when multiple agents collaborate or share state, especially in edge cases like delegated actions or nested calls.
Also, have you run it against more adversarial prompt injection attempts in production, beyond the red team suite?

**Mooshux:**
The layer ordering matters more than people realize, and you got it right with identity running before ingestion. Checking identity after input scanning is a common mistake — you're doing expensive processing on requests you should have rejected immediately.One gap I see in most agent security frameworks: they handle what agents do, but not what agents hold. An agent that's behaviorally constrained by guardrails can still be prompt-injected into exfiltrating a raw API key it was given at startup. The credential layer sits outside the behavioral layer.What actually closes that gap: agents that never hold raw provider keys at all. You broker the credential at request time, scoped to the specific call, and it's gone when the session ends. The agent can't leak what it doesn't have. We're doing exactly this at https:&#x2F;&#x2F;www.apistronghold.com&#x2F;blog&#x2F;securing-openclaw-ai-agen... if it's useful context.

**jovanaccount:**
Interesting approach. One question: how do you handle state coordination when multiple agents are writing to shared context simultaneously?This is the problem we kept hitting — agent A reads state, agent B reads the same state, both process, then B overwrites A's work. Classic race condition but much harder to debug in AI systems because the output looks plausible.We built an open-source coordination layer that adds optimistic concurrency control to any framework: https:&#x2F;&#x2F;github.com&#x2F;Jovancoding&#x2F;Network-AI

**Mooshux:**
The layered approach makes sense. Behavior guardrails sit at the reasoning&#x2F;action layer and have to handle every possible attack vector.Credentials are a separate surface. An agent can pass every behavioral check and still hold a full-access API key that makes a successful injection far more damaging than it needs to be. Defense in depth works better when the credential layer enforces least privilege independently of what the agent is doing.We built the secrets side of this: https:&#x2F;&#x2F;www.apistronghold.com&#x2F;blog&#x2F;stop-giving-ai-agents-you...
