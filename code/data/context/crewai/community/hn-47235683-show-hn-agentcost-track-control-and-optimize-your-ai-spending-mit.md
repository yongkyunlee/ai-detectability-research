# Show HN: AgentCost – Track, control, and optimize your AI spending (MIT)

**HN** | Points: 3 | Comments: 1 | Date: 2026-03-03
**Author:** agentcostin
**HN URL:** https://news.ycombinator.com/item?id=47235683
**Link:** https://github.com/agentcostin/agentcost

Hi HN,
We built AgentCost to solve a problem we kept running into: nobody knows what their AI agents actually cost.
One line wraps your OpenAI&#x2F;Anthropic client:
from agentcost.sdk import trace
client = trace(OpenAI(), project="my-app")
From there you get a dashboard with cost forecasting, model optimization recommendations, and pre-call cost estimation across 42 models.
What's included (MIT):Python + TypeScript SDKs
Real-time dashboard with 6 views
Cost forecasting (linear, EMA, ensemble)
Optimizer: "switch these calls from GPT-4 to GPT-4-mini, save $X&#x2F;day"
Prompt cost estimator for 42 models
LangChain&#x2F;CrewAI&#x2F;AutoGen&#x2F;LlamaIndex integrations
Plugin system
OTel + Prometheus exporters
CLI with model benchmarkingEnterprise features (BSL 1.1): SSO, budgets, policies, approvals, notifications, anomaly detection, AI gateway proxy.
Tech stack: Python&#x2F;FastAPI, SQLite (community) or PostgreSQL (enterprise), React dashboard, TypeScript SDK.
GitHub: https:&#x2F;&#x2F;github.com&#x2F;agentcostin&#x2F;agentcost
Docs: https:&#x2F;&#x2F;docs.agentcost.in
pip install agentcostin
Would love feedback from anyone managing AI costs at scale.

## Top Comments

**gilles_oponono:**
Hey, I love and share your approach. THere is some solution on the market, starting by edgee.ai (I'm biaised of course on this one).
