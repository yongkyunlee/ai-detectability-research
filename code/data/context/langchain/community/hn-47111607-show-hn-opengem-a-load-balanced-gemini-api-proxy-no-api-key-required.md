# Show HN: OpenGem – A Load-Balanced Gemini API Proxy (No API Key Required)

**HN** | Points: 7 | Comments: 3 | Date: 2026-02-22
**Author:** ariozgun
**HN URL:** https://news.ycombinator.com/item?id=47111607
**Link:** https://github.com/arifozgun/OpenGem

Hi HN! I built OpenGem, an open-source, load-balanced proxy for the Gemini API that requires absolutely no paid API keys.GitHub: https:&#x2F;&#x2F;github.com&#x2F;arifozgun&#x2F;OpenGemThe Context:
Like many developers, I was constantly hitting "429 Quota Exceeded" errors while building AI agents and processing large payloads on free tiers. I wanted to build freely without calculating API costs for every test request.How it works:
I reverse-engineered the official Gemini CLI authentication to get standard API access. However, a single free Google account quota depletes quickly. To solve this, I built a Smart Load Balancer at the core of OpenGem.What it does:
- You connect multiple idle&#x2F;free Google accounts to the dashboard via OAuth.
- OpenGem acts as a standard endpoint (`POST &#x2F;v1beta&#x2F;models&#x2F;{model}`).
- It routes traffic to the least-used account. If an account hits a real 429 quota limit, OpenGem instantly detects it, puts that account on a 60-minute cooldown, and seamlessly retries with the next available account. It differentiates between simple RPM bursts and actual limits.Tech specs:
- Fully compatible with official Google SDKs (`@google&#x2F;genai`), LangChain, and standard SSE streaming (no broken [DONE] chunks).
- Supports native "tools" (Function Calling) for agentic workflows.
- Raised payload limit to 50MB for massive contexts.
- AES-256-GCM encryption for all sensitive configs and OAuth tokens at rest.
- Toggle between Firebase Firestore or a fully offline Local JSON database.It’s strictly for educational purposes and personal research to bypass the friction of testing&#x2F;prototyping. The entire project is MIT licensed.I’m currently running it with my own side projects and it handles heavy agent tasks flawlessly. I would love any feedback on the load balancing logic, security implementations, or just general thoughts!

## Top Comments

**yuuu661:**
That's a really nice project, i’ll definitely use it!

**betty001:**
o m g! looks nice!

**frigosk:**
The core challenge of managing multiple free-tier quotas is real, especially when building agents that need consistent uptime. A reliable fallback layer is essential once you move beyond prototyping.We built https:&#x2F;&#x2F;simplio.dev to handle this exact problem at the gateway level, providing smart fallback across paid providers to avoid single points of failure.
