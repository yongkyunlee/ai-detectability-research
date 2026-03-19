# Show HN: OneRingAI – Single TypeScript library for multi-vendor AI agents

**HN** | Points: 4 | Comments: 1 | Date: 2026-02-17
**Author:** jhoxray
**HN URL:** https://news.ycombinator.com/item?id=47046494
**Link:** https://oneringai.io

OneRingAI started as the internal engine of an enterprise agentic platform we've been building for 2+ years. After watching customers hit the same walls with auth, vendor lock-in, and context management over and over, we extracted the core into a standalone open-source library.
The two main alternatives didn't fit what we needed in production:- LangChain: Great ecosystem, but the abstraction layers kept growing. By the time you wire up chains, runnables, callbacks, and agents across 50+ packages, you're fighting the framework
  more than building your product.
- CrewAI: Clean API, but Python-only and the role-based metaphor breaks down when you need fine-grained control over auth, context windows, or tool failures.OneRingAI is a single TypeScript library (~62K LOC, 20 deps) that treats the boring production problems as first-class concerns:Auth as architecture, not afterthought. A centralized connector registry with built-in OAuth (4 flows, AES-256-GCM storage, 43 vendor templates). This came directly from dealing with
enterprise SSO and multi-tenant token isolation — no more scattered env vars or rolling your own token refresh.Per-tool circuit breakers. One flaky Jira API shouldn't crash your entire agent loop. Each tool and connector gets independent failure isolation with retry&#x2F;backoff. We learned this the
hard way running agents against dozens of customer SaaS integrations simultaneously.Context that doesn't blow up. Plugin-based context management with token budgeting. InContextMemory puts frequently-accessed state directly in the prompt instead of requiring a retrieval
call. Compaction removes tool call&#x2F;result pairs together so the LLM never sees orphaned context.Actually multi-vendor. 12 LLM providers native, 36 models in a typed registry with pricing and feature flags. Switch vendors by changing a connector name. Run openai-prod and
openai-backup side by side. Enterprise customers kept asking for this — nobody wants to be locked into one provider.Multi-modal built in. Image gen (DALL-E 3, gpt-image-1, Imagen 4), video gen (Sora 2, Veo 3), TTS, STT — all in the same library. No extra packages.Native MCP support with a registry pattern for managing multiple servers, health checks, and auto tool format conversion.What it's not: it's not a no-code agent builder, and it's not trying to be a framework for every possible AI use case. It's an opinionated library for people building production agent
systems in TypeScript who want auth, resilience, and multi-vendor support without duct-taping 15 packages together.2,285 tests, strict TypeScript throughout. The API surface is small on purpose — Connector.create(), Agent.create(), agent.run().We also built Hosea, an open-source Electron desktop app on top of OneRingAI, if you want to see what a full agent system looks like in practice rather than just reading docs.GitHub: https:&#x2F;&#x2F;github.com&#x2F;Integrail&#x2F;oneringainpm: npm i @everworker&#x2F;oneringaiComparison with alternatives: https:&#x2F;&#x2F;oneringai.io&#x2F;#comparisonHosea: https:&#x2F;&#x2F;github.com&#x2F;Integrail&#x2F;oneringai&#x2F;blob&#x2F;main&#x2F;apps&#x2F;hosea&#x2F;...Happy to answer questions about the architecture decisions.

## Top Comments

**aantich23:**
Has anyone tried it? Any thoughts?
