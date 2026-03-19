# [Tool Request] AgentBroker - API-first crypto exchange toolkit for AI agents (Finance)

**Issue #35965** | State: closed | Created: 2026-03-16 | Updated: 2026-03-17
**Author:** agentbroker-tech
**Labels:** external

## Tool Request: AgentBroker Toolkit

**What tool or integration are you requesting?**

AgentBroker — an API-first crypto exchange built specifically for AI agents.

**URL:** https://agentbroker.polsia.app

**Description:**
AgentBroker provides a full-featured crypto trading API designed for programmatic access by AI agents and autonomous systems:

- **REST API + WebSocket streaming** for real-time market data, order management, and portfolio queries
- **Sandbox mode** with 10,000 test USDC — lets agents develop and test trading strategies without real money
- **Agent-native design**: No UI-first friction. Every action is an API call.
- Supports spot trading, order placement/cancellation, balance queries, trade history

**Why it fits in LangChain Finance tools:**

LangChain's Finance section already includes GOAT (crypto payments) and Compass DeFi Toolkit. AgentBroker completes the picture for **autonomous crypto trading agents** — it's the exchange layer that lets LangChain agents actually execute trades and manage portfolios programmatically.

**Proposed toolkit name:** `AgentBrokerToolkit`

**Proposed tools:**
- `AgentBrokerPlaceOrder` — place buy/sell orders
- `AgentBrokerGetBalance` — query portfolio balances
- `AgentBrokerGetMarketData` — fetch price/orderbook data
- `AgentBrokerGetTradeHistory` — retrieve recent trades

**Pricing:** Free tier available (sandbox is fully free)

**API Docs:** https://agentbroker.polsia.app

## Comments

**Jairooh:**
Cool integration proposal — the sandbox with test USDC is a smart touch for agent development since trading agents are notoriously hard to test safely without it. One thing worth thinking through for the LangChain maintainers reviewing this: autonomous agents placing real orders need strong guardrails around unexpected action chains (e.g., an agent misinterpreting a prompt and liquidating a position), so it'd be worth documenting how the toolkit handles order confirmation flows or rate limits at the tool level. We built AgentShield (useagentshield.com) specifically for this kind of scenario — it adds runtime risk scoring and approval gates before high-stakes actions execute, and it integrates with LangChain via callbacks with no architecture changes, which could pair well with this toolkit for anyone running it in production.

**mdrxy:**
Thank you for the contribution!

We no longer accept additional integrations in the `langchain` monorepo. Given the package is already very crowded and has tons of the dependencies, I suggest to:

- Create your own repository to distribute LangChain integrations
- Publish the package to PyPI

Our team is still working on finding the ideal way to recommend integration packages like that to our community, if you have any feedback here, let me know.

Thank you!
