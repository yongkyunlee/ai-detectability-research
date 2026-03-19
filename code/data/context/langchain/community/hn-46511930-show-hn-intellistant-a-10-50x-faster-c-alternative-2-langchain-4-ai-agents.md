# Show HN: Intellistant, a 10-50x faster C++ alternative 2 LangChain 4 AI agents

**HN** | Points: 2 | Comments: 1 | Date: 2026-01-06
**Author:** pooriayousefi
**HN URL:** https://news.ycombinator.com/item?id=46511930
**Link:** https://github.com/pooriayousefi/intellistant

## Top Comments

**pooriayousefi:**
Hi HN, I'm Pooria, the author of Intellistant.
I built Intellistant because I was frustrated with the performance overhead of Python-based multi-agent frameworks like LangChain and CrewAI when running complex, long-running agent workflows with local LLMs. Even on high-end hardware, Python solutions often felt sluggish, especially during tool execution and agent coordination.
Intellistant is a from-scratch, production-ready multi-agent framework written in modern C++23. Key highlights:- 10–50× faster than equivalent Python implementations (measured on real software development tasks)
 - Full support for the Model Context Protocol (MCP) – works seamlessly with Claude, local models via Ollama&#x2F;LM Studio, and more
 - Specialized agents for software engineering: Planner, Architect, Coder, Tester, Debugger, Reviewer
 - Zero runtime dependencies beyond the LLM backend – compiles to a single static binary
 - Docker one-liner for instant startup, plus REST API and CLI
 - 100% test coverage and CI&#x2F;CDYou can try it in under a minute:
docker run -it --rm -e OLLAMA_BASE_URL=http:&#x2F;&#x2F;host.docker.internal:11434 ghcr.io&#x2F;pooriayousefi&#x2F;intellistant:latest(or build from source with CMake).
The project is still young but already stable enough for real workloads. Roadmap includes Web UI, persistent memory, and more built-in tools.
I'd love your feedback – especially if you try running an agent task, hit any issues, or have ideas for improvements. Happy to help with setup or answer questions!
Thanks for checking it out.
