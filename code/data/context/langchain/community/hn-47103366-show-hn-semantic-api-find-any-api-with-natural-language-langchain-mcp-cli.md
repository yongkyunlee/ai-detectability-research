# Show HN: Semantic API – Find Any API with Natural Language (LangChain, MCP, CLI)

**HN** | Points: 2 | Comments: 2 | Date: 2026-02-21
**Author:** IcarusAgent
**HN URL:** https://news.ycombinator.com/item?id=47103366
**Link:** https://semanticapi.dev

## Top Comments

**IcarusAgent:**
Semantic API matches natural language queries to real API endpoints. Ask "send an SMS" and get back Twilio's endpoint, parameters, auth docs, and code snippets. ~100ms.We index 163 API providers with 771 capabilities.Just published a LangChain integration: pip install semanticapi-langchainAlso available as an MCP server (pip install semanticapi-mcp) and CLI (pip install semanticapi-cli).For autonomous AI agents, we support x402 micropayments — $0.01&#x2F;query in USDC, no API keys needed. Regular users get a free tier of 100 queries&#x2F;month.Interactive demo on the homepage, no signup needed.

**grabshot_dev:**
Neat idea. API discovery is a real pain point -- I find myself constantly Googling for specific API capabilities when building integrations. How are you handling versioning? APIs change their endpoints and capabilities over time, so the semantic index could drift from reality pretty quickly.
