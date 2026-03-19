# Show HN: Agent framework that generates its own topology and evolves at runtime

**HN** | Points: 107 | Comments: 36 | Date: 2026-02-11
**Author:** vincentjiang
**HN URL:** https://news.ycombinator.com/item?id=46979781
**Link:** https://github.com/adenhq/hive/blob/main/README.md

Hi HN,I’m Vincent from Aden. We spent 4 years building ERP automation for construction (PO&#x2F;invoice reconciliation). We had real enterprise customers but hit a technical wall: Chatbots aren't for real work. Accountants don't want to chat; they want the ledger reconciled while they sleep. They want services, not tools.Existing agent frameworks (LangChain, AutoGPT) failed in production - brittle, looping, and unable to handle messy data. General Computer Use (GCU) frameworks were even worse. My reflections:1. The "Toy App" Ceiling & GCU Trap
Most frameworks assume synchronous sessions. If the tab closes, state is lost. You can't fit 2 weeks of asynchronous business state into an ephemeral chat session.The GCU hype (agents "looking" at screens) is skeuomorphic. It’s slow (screenshots), expensive (tokens), and fragile (UI changes = crash). It mimics human constraints rather than leveraging machine speed. Real automation should be headless.2. Inversion of Control: OODA > DAGs
Traditional DAGs are deterministic; if a step fails, the program crashes. In the AI era, the Goal is the law, not the Code. We use an OODA loop to manage stochastic behavior:- Observe: Exceptions are observations (FileNotFound = new state), not crashes.- Orient: Adjust strategy based on Memory and - Traits.- Decide: Generate new code at runtime.- Act: Execute.The topology shouldn't be hardcoded; it should emerge from the task's entropy.3. Reliability: The "Synthetic" SLA
You can't guarantee one inference ($k=1$) is correct, but you can guarantee a System of Inference ($k=n$) converges on correctness. Reliability is now a function of compute budget. By wrapping an 80% accurate model in a "Best-of-3" verification loop, we mathematically force the error rate down—trading Latency&#x2F;Tokens for Certainty.4. Biology & Psychology in Code
"Hard Logic" can't solve "Soft Problems." We map cognition to architectural primitives:
Homeostasis: Solving "Perseveration" (infinite loops) via a "Stress" metric. If an action fails 3x, "neuroplasticity" drops, forcing a strategy shift.
Traits: Personality as a constraint. "High Conscientiousness" increases verification; "High Risk" executes DROP TABLE without asking.For the industry, we need engineers interested in the intersection of biology, psychology, and distributed systems to help us move beyond brittle scripts. It'd be great to have you roasting my codes and sharing feedback.Repo: https:&#x2F;&#x2F;github.com&#x2F;adenhq&#x2F;hive

## Top Comments

**vincentjiang:**
To expand on the "Self-Healing" architecture mentioned in point #2:The hardest mental shift for us was treating Exceptions as Observations. In a standard Python script, a FileNotFoundError is a crash. In Hive, we catch that stack trace, serialize it, and feed it back into the Context Window as a new prompt: "I tried to read the file and failed with this error. Why? And what is the alternative?"The agent then enters a Reflection Step (e.g., "I might be in the wrong directory, let me run ls first"), generates new code, and retries.We found this loop alone solved about 70% of the "brittleness" issues we faced in our ERP production environment. The trade-off, of course, is latency and token cost.I'm curious how others are handling non-deterministic failures in long-running agent pipelines? Are you using simple retries, voting ensembles, or human-in-the-loop?It'd be great to hear your thoughts.

**Multicomp:**
I am of course unqualified to provide useful commentary on it, but I find this concept to be new and interesting, so I will be watching this page carefully.My use case is less so trying to hook this up to be some sort of business workflow ClawdBot alternative, but rather to see if this can be an eventually consistent engine that lets me update state over various documents across the time dimension.could I use it to simulate some tabletop characters and their locations over time?that would perhaps let me remove some bookkeeping how to see where a given NPC would be on a given day after so many days pass between game sessions. Which lets me do game world steps without having to manually do them per character.

**foota:**
I was sort of thinking about a similar idea recently. What if you wrote something like a webserver that was given "goals" for a backend, and then told agents what the application was supposed to be and told it to use the backend for meeting them and then generate feedback based on their experience.Then have an agent collate the feedback, combined with telemetry from the server, and iterate on the code to fix it up.In theory you could have the backend write itself and design new features based on what agents try to do with it.I sort of got the idea from a comparison with JITs, you could have stubbed out methods in the server that would do nothing until the "JIT" agent writes the code.

**Biswabijaya:**
Great work team.

**mhitza:**
3. What, or who, is the judge of correctness (accuracy); regardless of the many solutions run in parallel. If I optimize for max accuracy how close can I get to 100% matemathically and how much would that cost?

**CuriouslyC:**
Failures of workflows signal assumption violations that ultimately should percolate up to humans. Also, static dags are more amenable to human understanding than dynamic task decomposition. Robustness in production is good though, if you can bound agent behavior.Best of 3 (or more) tournaments are a good strategy. You can also use them for RL via GRPO if you're running an open weight model.

**omhome16:**
Strongly agree on the 'Toy App' ceiling with current DAG-based frameworks. I've been wrestling with LangGraph for similar reasons—once the happy path breaks, the graph essentially halts or loops indefinitely because the error handling is too rigid.The concept of mapping 'exceptions as observations' rather than failures is the right mental shift for production.Question on the 'Homeostasis' metric: Does the agent persist this 'stress' state across sessions? i.e., if an agent fails a specific invoice type 5 times on Monday, does it start Tuesday with a higher verification threshold (or 'High Conscientiousness') for that specific task type? Or is it reset per run?Starred the repo, excited to dig into the OODA implementation.

**fwip:**
Yet more LLM word vomit. If you can't be bothered to describe your new project in your own words, it's not worth posting about.

**mubarakar95:**
It forces you to write code that is "strategy-aware" rather than just "procedural." It’s a massive shift from standard DAGs where one failure kills the whole run. Really interesting to see how the community reacts to this "stochastic" approach to automation.

**kkukshtel:**
The comments on this post that congratulate&#x2F;engage with OP all seem to be from hn accounts created in the past three months that have only ever commented on this post, so it seems like there is some astro-turfing going on here.
