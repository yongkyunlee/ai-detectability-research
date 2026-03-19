---
source_url: https://crewai.com/blog/how-to-build-agentic-systems-the-missing-architecture-for-production-ai-agents
author: "João (Joe) Moura"
platform: crewai.com (official blog)
scope_notes: "Trimmed to focus on task/workflow architecture: Flows as deterministic backbone, when to use agents vs crews vs plain code, and the DocuSign workflow case study. Removed general industry commentary and conclusion."
---

## The Production Reality Gap

After analyzing 1.7 billion agentic workflows across enterprise customers in healthcare, CPGs, finance, logistics, and professional services, a consistent pattern emerged. Many projects fail not because agents lack capability, but because systems lack proper architectural foundations.

The industry largely approaches agent development in two flawed ways: either building overly rigid scaffolding that cannot adapt, or creating unbounded agency systems that enterprises cannot safely deploy.

## What Are Agentic Systems?

Production systems require observability, governance, cost control, auditability, and maintainability. Agentic Systems address these through two integrated components:

**1. Deterministic Backbone (Flows)**
Flows provide structural control through flexible code layers with minimal abstractions. They manage conditional branching, state management, and custom business logic. Flows ensure predictability through regular code rather than framework configuration, with event-driven architecture and runtime modifiability.

**2. Intelligence Deployed Strategically**
Intelligence exists on a spectrum: from single ad-hoc LLM calls for straightforward tasks, to single agents for tool-using scenarios, to full crews with multiple collaborating agents for complex reasoning. Crews operate within Flow-defined boundaries and return control to the backbone upon completion.

## Building Agentic Systems: The Right Approach

**When to use plain code:** Data validation, formatting, API calls with known parameters, and steps without intelligence requirements belong in the Flow itself, not wrapped in agents.

**When to use single LLM calls:** Simple tasks like document summarization, field extraction, or input classification need only a single completion without agency overhead.

**When to use single agents:** Tasks requiring reasoning and tool use -- researching companies for financial data or verifying credentials across sources -- benefit from a single agent's capabilities.

**When to use crews:** Complex multi-step intelligence involving collaboration, such as conducting comprehensive due diligence across legal, financial, and operational dimensions, justifies multi-agent architectures.

## Common Architecture Mistakes

Placing all logic in agents when much should remain code creates debugging challenges and unpredictable costs. Squeezing too much into single agents increases hallucination rates and context window issues. Building complex workflows without architectural backbones fails to handle real branching and state management. Avoiding model-agnostic design limits flexibility when models change.

## The DocuSign Case Study

DocuSign -- used by 90% of Fortune 500 companies -- faced a challenge: personalizing customer engagement at scale without requiring sales reps to spend hours researching before composing emails.

Their solution implemented an Agentic System where:

- A Flow manages the deterministic backbone and state
- Specialized agents tap into Salesforce and Snowflake data
- Hallucination guardrails ensure quality at runtime
- The Flow routes to manual review when necessary and handles agent failures gracefully

Results were significant: the system matched or exceeded human rep performance on engagement metrics while reducing turnaround time from hours to minutes. Email open rates, reply rates, and conversion rates all improved.

Key success factor: agents remained reusable across multiple use cases because the Flow/Intelligence separation allowed component reuse throughout the organization.

## Why This Architecture Matters

This approach enables predictable costs (control where intelligence operates, budget AI like infrastructure), faster iteration (maintainable systems enable new use cases in weeks rather than quarters), reduced risk (observable, governable systems work in regulated industries), and competitive advantage (systems learning from each execution create advantages competitors cannot copy through prompts alone).
