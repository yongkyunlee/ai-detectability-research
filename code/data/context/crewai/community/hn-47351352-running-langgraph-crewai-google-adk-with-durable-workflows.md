# Running LangGraph, CrewAI, Google ADK with Durable Workflows

**HN** | Points: 1 | Comments: 2 | Date: 2026-03-12
**Author:** yaronsc
**HN URL:** https://news.ycombinator.com/item?id=47351352
**Link:** https://docs.diagrid.io/getting-started/quickstarts/ai-agents/

## Top Comments

**yaronsc:**
One pattern we've seen while building AI agents is that developers often have to make a frustrating choice between agent frameworks and workflow engines.Frameworks like LangGraph, Strands, CrewAI, ADK, etc. already implement reasoning loops, tool execution, retries, and memory. But they typically don't provide durable execution—if the process crashes, the agent will restart from scratch. Some have very basic checkpoint systems that leave failure detection and resumption to the user, which is essentially the hard problem workflow engines solve.The problem with workflow engines is they handle durability well but require developers to rewrite their agent logic inside the workflow system, which means rebuilding the agent framework from scratch.This work aims to remove that tradeoff by allowing existing agent frameworks to get all the benefits of a durable workflow orchestrator without rewriting any part of their code.

**yaronsc:**
I'm the creator of the Dapr CNCF project, happy to answer any questions.
