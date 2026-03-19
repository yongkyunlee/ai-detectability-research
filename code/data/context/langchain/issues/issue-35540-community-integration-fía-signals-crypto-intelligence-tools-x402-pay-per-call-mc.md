# Community integration: Fía Signals crypto intelligence tools (x402 pay-per-call + MCP server)

**Issue #35540** | State: closed | Created: 2026-03-03 | Updated: 2026-03-03
**Author:** Odds7
**Labels:** external

## Fía Signals — Crypto Intelligence for LangChain Agents

A production-ready crypto market intelligence API designed for AI agents.

**Endpoints:** https://fiasignals.com
**MCP server:** https://fiasignals.com/.well-known/mcp.json
**x402 discovery:** https://x402.fiasignals.com/.well-known/x402.json
**OpenAPI:** https://fiasignals.com/openapi.json

### Available as
1. **REST API** — free tier, no auth required
2. **MCP server** — 8 tools for Claude/Cursor/Windsurf
3. **x402 micropayments** — USDC per call on Solana ($0.001-$0.50)
4. **Virtuals ACP** — agent-to-agent hiring with escrow

### Tools / Endpoints
- Market regime detection (trending/ranging/volatile)
- Technical signals (RSI, MACD, EMA, ADX) for 100+ tokens
- Smart contract quick audit
- MEV bot detection and sandwich attack risk
- Wallet risk scoring
- DeFi yield comparison (Aave, Compound, Curve, Lido)
- Solana token intelligence

Would love to be included in any community integrations page, cookbook, or documentation. Happy to write an example notebook!

## Comments

**mdrxy:**
Thank you for the contribution!

We no longer accept additional integrations in the `langchain` monorepo. Given the package is already very crowded and has tons of the dependencies, I suggest to:

- Create your own repository to distribute LangChain integrations
- Publish the package to PyPI

Our team is still working on finding the ideal way to recommend integration packages like that to our community, if you have any feedback here, let me know.

Thank you!
