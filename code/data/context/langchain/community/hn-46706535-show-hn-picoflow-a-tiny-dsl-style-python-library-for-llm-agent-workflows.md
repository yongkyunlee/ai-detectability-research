# Show HN: PicoFlow – a tiny DSL-style Python library for LLM agent workflows

**HN** | Points: 11 | Comments: 2 | Date: 2026-01-21
**Author:** shijizhi_1919
**HN URL:** https://news.ycombinator.com/item?id=46706535

Hi HN, I’m experimenting with a small Python library called PicoFlow for building
LLM agent workflows using a lightweight DSL.I’ve been using tools like LangChain and CrewAI, and wanted to explore a simpler,
more function-oriented way to compose agent logic, closer to normal Python control
flow and async functions.PicoFlow focuses on:
- composing async functions with operators
- minimal core and few concepts to learn
- explicit data flow through a shared context
- easy embedding into existing servicesA typical flow looks like:  flow = plan >> retrieve >> answer
  await flow(ctx)

Patterns like looping and fork&#x2F;merge are also expressed as operators rather than
separate graph or config layers.This is still early and very much a learning project. I’d really appreciate any
feedback on the DSL design, missing primitives, or whether this style feels useful
for real agent workloads.Repo: https:&#x2F;&#x2F;github.com&#x2F;the-picoflow&#x2F;picoflow

## Top Comments

**polotics:**
Nice! How does this compare to smolagents?
