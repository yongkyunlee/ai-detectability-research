# LangChain is powerful, but running it in production isn't

**HN** | Points: 3 | Comments: 1 | Date: 2026-03-18
**Author:** vishaal_007
**HN URL:** https://news.ycombinator.com/item?id=47426670
**Link:** https://modelriver.com/langchain-alternative

## Top Comments

**vishaal_007:**
We kept running into the same wall. The prototype worked great: chain a few calls together, get a response and it felt like we were basically done. Then real traffic showed up and we were spending more time on the stuff around the LLM call than the call itself.Retries, failover when a provider went down, figuring out why latency quietly doubled over a week, parsing responses that were slightly different between models, paying full token cost for the same request hitting us over and over. Each one felt like a small fix. A few months later it was a pile of glue code nobody wanted to touch.At one point we had a Slack bot that pinged us when latency crossed 5 seconds. It mostly taught us how often latency crosses 5 seconds.This page is basically about where that led us. Not saying LangChain is the wrong tool, if you want maximum flexibility, it still makes a lot of sense. This is more for teams that got something working quickly and then realised prod was a completely different problem.Curious to hear from anyone else who’s gone through the same thing. What did you end up building or buying to deal with it?
