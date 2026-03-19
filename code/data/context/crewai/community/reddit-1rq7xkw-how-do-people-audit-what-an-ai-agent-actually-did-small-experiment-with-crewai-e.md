# How do people audit what an AI agent actually did?
Small experiment with CrewAI + execution logs

**r/LocalLLaMA** | Score: 1 | Comments: 9 | Date: 2026-03-10
**Author:** DealDesperate7378
**URL:** https://www.reddit.com/r/LocalLLaMA/comments/1rq7xkw/how_do_people_audit_what_an_ai_agent_actually_did/

I've been thinking about a problem with agent systems.

Once an agent starts calling tools and executing tasks,

it becomes surprisingly hard to answer a simple question:

What actually happened?

So I tried building a small experiment.

The pipeline looks like this:

persona (POP)

→ agent execution (CrewAI)

→ execution trace

→ audit evidence

The goal is simply to see if agent actions can produce

a verifiable execution record.

The demo runs locally (no API keys) and outputs

an audit JSON after execution.

Curious if others are experimenting with

observability / governance layers for agents.

Repo if anyone wants to look at the experiment:

[github.com/joy7758/verifiable-agent-demo](http://github.com/joy7758/verifiable-agent-demo)
