# Show HN: Flakestorm – Chaos engineering for AI agents (local-first, open source)

**HN** | Points: 6 | Comments: 0 | Date: 2026-01-05
**Author:** frankhumarang
**HN URL:** https://news.ycombinator.com/item?id=46495434

Hi everyone,I’ve been working on an open-source tool called Flakestorm to test the reliability of AI agents before they hit production.Most agent testing today focuses on eval scores or happy-path prompts. In practice, agents tend to fail in more mundane ways: typos, tone shifts, long context, malformed input, or simple prompt injections — especially when running on smaller or local models.
Flakestorm applies chaos-engineering ideas to agents. Instead of testing one prompt, it takes a “golden prompt”, generates adversarial mutations (semantic variations, noise, injections, encoding edge cases), runs them against your agent, and produces a robustness score plus a detailed HTML report showing what broke.Key points:
Local-first (uses Ollama for mutation generation)Tested with Qwen &#x2F; Gemma &#x2F; other small models
Works against HTTP agents, LangChain chains, or Python callables
No cloud or API keys required
This started as a way to debug my own agents after seeing them behave unpredictably under real user input. I’m still early and trying to understand how useful this is outside my own workflow.I’d really appreciate feedback on:
Whether this overlaps with how you test agents today
Failure modes you’ve seen that aren’t covered
Whether “chaos testing for agents” is a useful framing, or if this should be thought of differently
Repo: https:&#x2F;&#x2F;github.com&#x2F;flakestorm&#x2F;flakestorm
Docs are admittedly long.Thanks for taking a look.
