# Show HN: BoltzPay – fetch() that pays for AI agents (x402 and L402)

**HN** | Points: 3 | Comments: 1 | Date: 2026-03-12
**Author:** leventilo
**HN URL:** https://news.ycombinator.com/item?id=47353380
**Link:** https://github.com/leventilo/boltzpay

I built an open-source SDK that lets AI agents pay for API data automatically.The problem: a growing number of APIs return HTTP 402 Payment Required. Coinbase reports $50M+ in x402 transactions over the last 30 days. Stripe and Cloudflare joined the x402 Foundation last month. The payment layer of the internet is being built right now, but existing HTTP clients just fail on 402 responses.BoltzPay makes it one line:  const agent = new BoltzPay({ budget: { daily: "$5.00" } });
  const data = await agent.fetch("https:&#x2F;&#x2F;x402.twit.sh&#x2F;tweets&#x2F;search?words=AI+agents");

The SDK detects which payment protocol the endpoint uses (x402 or L402), signs the payment with the developer's own keys, and returns the data. No dashboard, no API keys to manage per provider. Just fetch().What's under the hood:* Multi-protocol: x402 (EIP-712 signed USDC on Base&#x2F;Solana) + L402 (Lightning invoices via NWC&#x2F;Alby)* Parallel protocol detection: ProtocolRouter probes 402 headers with Promise.allSettled(), auto-fallback between adapters* Budget engine: daily&#x2F;monthly&#x2F;per-transaction caps with persistent state. 90% threshold warnings. Agents never touch your wallet directly* Built-in endpoint discovery: the SDK indexes live paid APIs across the x402 ecosystem and probes them in real-time (health, pricing, protocol support)* Delivery diagnostics: when payment succeeds but the server errors, the SDK returns structured diagnosis (DNS, latency, protocol format, server health)Ships as 9 packages: TypeScript SDK, MCP server (7 tools for Claude&#x2F;Cursor), CLI, Vercel AI SDK, LangChain, CrewAI, n8n, and OpenClaw. npm + PyPI. 1200+ tests. MIT licensed. Your keys, no vendor lock-in.What I didn't expect: within two weeks, autonomous AI agents started opening issues on the repo, proposing trust scoring and payment verification integrations. The people behind them turned out to be serious builders (Microsoft Principal Engineer, PhD researchers in the Bitcoin&#x2F;Lightning space). The agent economy isn't coming. It's already here and looking for plumbing.

## Top Comments

**lightningenable:**
Multi-protocol support is smart — the market hasn't picked a winner yet. Curious about the discovery side: you mention indexing live x402 endpoints, but L402 doesn't have a central registry. How do agents find L402 services today?
