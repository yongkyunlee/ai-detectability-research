# Show HN: Kalibr – Autonomous Routing for AI Agents

**HN** | Points: 3 | Comments: 13 | Date: 2026-01-27
**Author:** devonkelley
**HN URL:** https://news.ycombinator.com/item?id=46782579

Hey HN, we’re Devon and Alex from Kalibr (https:&#x2F;&#x2F;kalibr.systems).Kalibr is an autonomous routing system for AI agents. It replaces human debugging with an outcome-driven learning loop. On every agent run, it decides which execution path to use based on what is actually working in production.An execution path is a full strategy, not just a model: model + tools + parameters.Most agents hardcode one path. When that path degrades or fails, a human has to notice, debug, change configs, and redeploy. Even then, the fix often doesn’t stick because models and tools keep changing.I got tired of being the reliability layer for my own agents. Kalibr replaces that.With Kalibr, you register multiple paths for a task. You define what success means. After each run, your code reports the outcome. Kalibr captures telemetry on every run, learns from outcomes, and routes traffic to the path that’s working best while continuously canarying your alternative paths. When one path degrades or fails, traffic shifts immediately. No alerts, no dashboards and no incident response.How is this different from other routers or observability tools?Most routers choose between models using static rules or offline benchmarks. Observability tools show traces and metrics but still require humans to act. Kalibr is outcome-aware and autonomous. It learns directly from production success and changes runtime behavior automatically. It answers not “what happened?” but “what should my agent do next?”We’re not a proxy. Calls go directly to OpenAI, Anthropic, or Google. We’re not a retry loop. Failed paths are routed away from, not retried blindly. Success rate always dominates; cost and latency only matter when success rates are close.Python and TypeScript SDKs. Works with LangChain, CrewAI, and the OpenAI Agents SDK. Decision latency is ~50ms. If Kalibr is unavailable, the Router falls back to your first path.Think of it as if&#x2F;else logic for agents that rewrites itself based on real production outcomes.We’ve been running this with design partners and would love feedback. Always curious how others are handling agent reliability in production.GitHub: https:&#x2F;&#x2F;github.com&#x2F;kalibr-ai&#x2F;kalibr-sdk-pythonDocs & benchmarks: https:&#x2F;&#x2F;kalibr.systems&#x2F;docs

## Top Comments

**Antonioromero10:**
Awesome tool been using for a month or so now.

**neilmagnuson:**
awesome tool for observation, been using it for a while !

**adeebvaliulla:**
This resonates with a pain I see repeatedly in production agent systems: humans acting as the reliability layer.Most teams I work with hardcode a single “golden path” for agents, then rely on dashboards, alerts, and tribal knowledge to notice when behavior degrades. By the time someone debugs model choice, tool params, or prompt drift, the environment has already changed again. The feedback loop is slow and brittle.What’s interesting here is the explicit shift from observability to outcome-driven control. Routing based on actual production success rather than static benchmarks or offline evals aligns with how reliability engineering evolved in other domains. We moved from “what happened?” to “what should the system do next?” years ago.A couple of questions I’m curious about:- How do you define and normalize “success” across heterogeneous tasks without overfitting to short-term signals?- How do you prevent oscillation or path thrashing when outcomes are noisy or sparse?- Is there a notion of confidence or regret baked into the routing decisions over time?Overall, this feels less like a router and more like an autonomous control plane for agents. If it holds up under real-world variance, this is a meaningful step toward agents that are self-healing rather than constantly babysat.

**roan-we:**
I had developed a side project with AI agents to help me summarize the research papers and extract key citations, and I was repeatedly hitting the same annoying pattern. I would finetune everything with GPT4 to perfection, and then in a couple of weeks, it would start hallucinating references or missing citations. I used to waste my Saturday mornings changing prompts and switching models instead of really using the thing.Kalibr pretty much freed me from that loop.I basically arranged GPT-4 and Claude as two different routes, explained that success means accurate citations that I can verify, and now it just works.Last week, GPT-4 oddly started being very slow on longer papers, and by the time I realized it, the traffic was already automatically diverted to Claude.It's like the difference between caretaking an agent and actually having a tool that remains functional without constant supervision.Honestly, I wish I had discovered this a few months ago hehe

**0to1ton:**
Congrats on the launch !!!

**curranadvani:**
Amazing work! This will change AI

**ashishforai:**
Amazing tool, much needed. For last two years 80% of yaps were about reliability , reproducibility and observability! Glad this is being addressed here.

**deaux:**
Comment section needs a look at @ tomhow
