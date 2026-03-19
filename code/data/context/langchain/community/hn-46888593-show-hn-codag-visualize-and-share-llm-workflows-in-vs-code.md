# Show HN: Codag – Visualize and share LLM workflows in VS Code

**HN** | Points: 6 | Comments: 1 | Date: 2026-02-04
**Author:** michaelzixizhou
**HN URL:** https://news.ycombinator.com/item?id=46888593
**Link:** https://github.com/michaelzixizhou/codag

I built Codag because I kept getting lost in my own AI code.You're chaining 3 LLM calls across 5 files. A prompt change breaks something downstream. Which call? Which branch? You grep for "openai.chat", open 8 tabs, trace the flow manually.Codag automates this:
- Point it at your codebase and it extracts every LLM call, decision branch, and processing step
- Renders an interactive and shareable DAG with clickable nodes that link back to source     
- Live updates as you edit using tree-sitter — no waiting for re-analysisSupports OpenAI, Anthropic, Gemini, LangChain, LangGraph, CrewAI, and more. Works with Python, TypeScript, Go, Rust, Java, and more.It's a VS Code extension + self-hosted backend (Gemini 2.5 Flash for analysis). Open source, MIT licensed.

## Top Comments

**avi_khazzz123:**
this is fire, use it at work all the time. great stuff!
