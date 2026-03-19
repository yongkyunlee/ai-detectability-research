# Does anyone use CrewAI or LangChain anymore?

**HN** | Points: 11 | Comments: 5 | Date: 2026-02-24
**Author:** rakan1
**HN URL:** https://news.ycombinator.com/item?id=47132187

Curious.

## Top Comments

**obiefernandez:**
No. They suck.

**CodeBit26:**
I feel the hype is cooling down. LangChain was great for getting something running in 5 minutes, but the 'abstraction soup' makes debugging a nightmare in production. I'm seeing more people just using the OpenAI&#x2F;Anthropic SDKs directly or very thin wrappers. It’s better to own your prompts than to hide them behind five layers of library code.

**fennu637:**
Sometimes, simple PoC that does not require any "Agentic" features

**kypro:**
Well, what are you building? It's hard to know if its the right tool without understanding what problem you're trying to solve.If you need a multi-model setup, have complex agentic workflows, have observability requirements, need to run evals, etc, then they'll make more sense.The company I work for uses LangChain heavily, but that's because we have fairly complex requirements compared to products which are just incorporating AI as an additional feature for example.It's probably similar to how Next.js is overused and overhyped – it can be great if you have complex requirements, but if you just need a simple website with a little interactivity it's total overkill.LangChain seems to get a lot of hate here and I'm not entirely sure why. There's a lot of frameworks which seem to make a relatively simple problem needless complex, I don't feel that way about LangChain personally.
