# Show HN: Agint Flow – design software as a graph, then compile the graph to code

**HN** | Points: 5 | Comments: 3 | Date: 2026-01-16
**Author:** AgintAI
**HN URL:** https://news.ycombinator.com/item?id=46650465
**Link:** https://flow.agintai.com

Hi HN — I’m Abhi.We built Agint so PMs and engineers can design and edit software as a graph — architecture first — iterate with fast visual feedback, then generate deployable code from it when it’s ready.We presented underlying approach at NeurIPS (Deep Learning for Codegen) as an Agentic Graph Compiler:The graph (structure + types + semantic annotations) is the source of truth, and code is a compilation&#x2F;export target.Paper:
Agentic Graph Compilation for Software Engineering Agents:https:&#x2F;&#x2F;arxiv.org&#x2F;abs&#x2F;2511.19635Live Demo:https:&#x2F;&#x2F;flow.agintai.com(The demo runs in sandbox mode -- no real external tools&#x2F;data sources wired yet. It creates repos @ github.com&#x2F;AgintHub)CLI:https:&#x2F;&#x2F;github.com&#x2F;AgintAI&#x2F;agint-cliHow it works:Type in the chat to modify the graph (or use the “+” menu for specific actions).1) Create&#x2F;Compose: (chat + live graph feedback) design and modify algorithmic flow + schema graphs:   Add, remove, split, merge, and rename steps, via chat

    "Fetch stock data from the NYSE and NASDAQ"

    "Also include the Toronto Stock Exchange"

    "Add the LSE as well"

2) Refine&#x2F;Upgrade (engineering-facing, GUI + CLI &#x2F; git-friendly graph edits):
   Add types, semantic annotations, restructure, reorganize nodes, transform, execute, and test behavior
    "Break the combine step into storage, normalization, and repartitioning"   On the CLI it can look like:

    dagify refine workflow.yaml \
       "add protocol-level details, latencies, and datacenter info for each feed" --intelligence 5

    dagify resolve workflow.yaml --yaml-display --ascii

3) Save&#x2F;Load&#x2F;Export:
    “Save” exports the graph into ordinary code, pipelines, tool calls, and APIs that can be owned and deployed like any other system.
     The graph is an executable artifact, not just documentation.
     Targets include native Python today, plus exports to frameworks like CrewAI&#x2F;LangGraph.Example output repo:
https:&#x2F;&#x2F;github.com&#x2F;AgintHub&#x2F;dreamy-mirzakhani&#x2F;blob&#x2F;agint&#x2F;out...Would love reactions and feedback — I’ll be around to answer questions.Thanks,
AbhiAbhi@AgintAI.com

## Top Comments

**ritwikpavan15:**
Incredible! Excited to try this out.

**Theguy334:**
This is wild, I have so many uses!

**sunnycali:**
Interesting, would love to learn more!
