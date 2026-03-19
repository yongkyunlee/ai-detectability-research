# Show HN: AxonFlow, governing LLM and agent workflows

**HN** | Points: 11 | Comments: 14 | Date: 2026-01-20
**Author:** saurabhjain1592
**HN URL:** https://news.ycombinator.com/item?id=46692499

Hi HN, we’re building AxonFlow for teams running LLMs or agents in real production systems.Once agent workflows move past demos, failures are rarely model issues. They tend to show up as execution problems during real runs.Short 2-minute technical demo showing execution control and auditability in practice:
https:&#x2F;&#x2F;youtu.be&#x2F;FNgnESo9RtIAxonFlow is a self-hosted, source-available (BSL 1.1) control plane that sits inline in the execution path and governs LLM calls, tool calls, retries, approvals, and policy enforcement step by step. It does not replace your orchestrator and can run alongside LangChain, CrewAI, or custom systems.The problems we focus on are usually discovered only after going to production:
- retries that accidentally repeat side effects
- partial failures mid-workflow
- permissions that differ per step
- limited ability to inspect or intervene during executionThis is not aimed at early demos or hobby projects. It’s for teams already operating under real production constraints.GitHub:
https:&#x2F;&#x2F;github.com&#x2F;getaxonflow&#x2F;axonflowDocs:
https:&#x2F;&#x2F;docs.getaxonflow.comI’d value feedback from folks running LLM or agent workflows in production.

## Top Comments

**HappyPablo:**
When you speak about deterministic policy enforcement, so are these policy regex based or there are some policies based on hard limit business logics. Do you provide ways to track llm api cost on a user basis. It has been a constant headache for us to efficiently track api usages per user in our team ?

**fpierfed:**
Nice project! Quick question: how do you handle LLM access control in practice? For example, can different steps in a workflow run under different credentials or provider accounts, and is that enforced centrally by AxonFlow or delegated to the underlying orchestrator? Thanks!

**widow-maker:**
Does axonflow support redaction on images ? We have noticed it multiple times that people in our org share images containing critical information with the public apis.

**patthar:**
Nice work, Saurabh. It think you have tackled a deeper problem with llm and agents governance. The small to midsize companies are racing ahead with agentic integrations where security generally comes as after though, your product gives a no-fluff approach to bolt the security early on and not as an after thought. I'd like take a critical view and curious to hear your and others thoughts about the same.1) Axonflow offers dual mode architecture - as a gateway or a full blown governance via proxy mode. In my experience, projects(in enterprise) start small but quickly find themselves amidst requiring deeper fine grained control than just as a gateway check. What migration paths do you give for users for a seamless transition ? The last thing a project wants at a certain stage is to rewrite all the llm invocations to go through axonflow.execute_query(). This migration cliff exists and good have an early insight in your architecture.2) The static (sub-10 ms, in-memory) + dynamic (sub-30 ms, cached) split is good for performance, but the documentation shows policies as a central construct loaded into Postgres&#x2F;Redis.
There is little visibility into how complex&#x2F;custom&#x2F;conditional policies (e.g., business-rule-dependent, ML-based anomaly scoring, or external IdP-attribute checks) are authored, versioned, tested, or rolled out safely.  AxonFlow risks becoming a bottleneck if policy logic grows beyond simple PII&#x2F;SQLi&#x2F;rate-limit rules — especially since dynamic policies still incur DB&#x2F;cache round-trips. Something that you find in enterprise environments.3) With complex rules come the performance expectations. As a suggestion, you could try and publish more standard performance benchmarks with sufficiently complex rules both in structure and count. Real world production scenarios, think of - overlapping policies, cold cache, expensive dynamic lookups could significantly push up the tail latencies.4) Finally, the multi agent planning seems to break the guiding principle of "control plane, not orchestration" boundary. I have no knowledge of the internals and perhaps its documentation that is giving me this perspective but the proxy mode seems to inch towards direct competition with langchain&#x2F;crewAI.Much of my observations are what I got from the documentation. Please excuse any errors in my understanding and correct them, where required.Wishing you the best.

**mansi_mittal:**
This resonates with real pain I’ve seen once agent systems leave the demo phase. Most failures aren’t model quality issues — they are retries with side effects, partial execution failures, and lack of visibility&#x2F;control once things are running live. The idea of a lightweight, inline control plane that doesn’t replace the orchestrator but governs execution step-by-step feels like a pragmatic way to tackle that.I especially liked the ability to start in observe-only mode and progressively enforce policies, and the focus on auditability and permissions per step. That’s the kind of thing teams usually end up building ad-hoc once compliance or reliability becomes non-optional.A couple of things I’m curious about (and would love your thoughts on):
1. How you think about debugging or replay for long-running&#x2F;stateful workflows when enforcement decisions affect downstream steps2. What you’re seeing in practice around latency overhead at scale when AxonFlow is fully in the hot pathOverall, this feels like it’s aimed at the right stage of maturity — not early demos, but teams already feeling production constraints.

**dhruvghulati:**
This is massively needed. I know large corporations are building their own frameworks but a new business looking to go agentic can’t do it without this - Langchain just doesn’t scale. Came across this too https:&#x2F;&#x2F;github.com&#x2F;axsaucedo&#x2F;kaosThere is the security layer on top to be built too.Excited to see where this space would go. I think early users will be really innovative scale ups who are looking to code red around agents, top down mandate, maybe looking to reinvent themselves.
