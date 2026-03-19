# Show HN: SafeAgent – exactly-once execution guard for AI agent side effects

**HN** | Points: 3 | Comments: 2 | Date: 2026-03-08
**Author:** Lions2026
**HN URL:** https://news.ycombinator.com/item?id=47294291

I built a small Python library called SafeAgent that protects real-world side effects when AI agents retry tool calls.One issue we ran into while experimenting with agent workflows is that retries can trigger irreversible actions multiple times:agent calls tool
↓
network timeout
↓
agent retries
↓
side effect happens twiceExamples:• duplicate payment
• duplicate email
• duplicate ticket
• duplicate tradeMost systems solve this ad-hoc using idempotency keys scattered around different services.SafeAgent centralizes this into a small execution guard.The idea is simple:1. every tool execution gets a request_id
2. SafeAgent records the execution receipt
3. retries return the original receipt instead of running the side effect againExample:FIRST CALL
REAL SIDE EFFECT: sending emailSECOND CALL WITH SAME request_id
SafeAgent returns the original execution receipt
(no second side effect)The project is early but includes examples for:• OpenAI tool calls
• LangChain style tools
• CrewAI actionsPyPI:
https:&#x2F;&#x2F;pypi.org&#x2F;project&#x2F;safeagent-exec-guard&#x2F;GitHub:
https:&#x2F;&#x2F;github.com&#x2F;azender1&#x2F;SafeAgentCurious how other people are handling retry safety for agent side effects.

## Top Comments

**Lions2026:**
A bit more context on why I built this.While experimenting with LLM agents calling tools, I ran into a reliability problem: retries can easily trigger irreversible actions more than once.For example:agent → call tool
network timeout → retry
agent retries tool call
side effect runs twiceThat can mean:duplicate paymentduplicate emailduplicate ticketduplicate tradeMost systems solve this locally with idempotency keys, but in agent workflows the retries can come from multiple layers (agent loops, orchestration frameworks, API retries, etc.).SafeAgent is a small execution guard that sits between the agent and the side effect. Every tool call gets a request_id, and SafeAgent records a durable execution receipt. If the same request is replayed, it returns the original receipt instead of executing again.
