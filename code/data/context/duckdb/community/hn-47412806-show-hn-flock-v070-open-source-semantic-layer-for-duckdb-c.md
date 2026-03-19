# Show HN: Flock v0.7.0 – Open Source Semantic Layer for DuckDB (C++)

**HN** | Points: 2 | Comments: 1 | Date: 2026-03-17
**Author:** dorbanianas
**HN URL:** https://news.ycombinator.com/item?id=47412806

Hi HN, I’m part of the DAIS Lab at Polytechnique Montréal, and we just released v0.7.0 of Flock, our open-source DuckDB extension.
If you want semantic and analytical processing in one place, Flock lets you do it all in SQL. Instead of moving data out of your database into a Python script to run AI workflows, Flock allows you to execute LLM operators and RAG pipelines natively inside DuckDB.In this new release, we've added a few major updates:- Anthropic (Claude) & Multi-Provider Support: We now support OpenAI, Azure, Ollama, and Anthropic. You can define a model once with CREATE MODEL, then swap providers on the admin side without changing the downstream SQL queries.- WASM Support: Flock now compiles and runs entirely inside DuckDB-WASM.- LLM Metrics Tracking: We added end-to-end observability so you can track token usage, latency, and call counts for all LLM invocations directly within a query.- Audio Transcription: We expanded our multimodal capabilities to include audio transcription, alongside our existing image support.You can try it out via the community extension catalog: INSTALL flock FROM community;.We'd love your feedback and contributions! Let us know what you think of the architecture or if you run into any edge cases.Docs: https:&#x2F;&#x2F;dais-polymtl.github.io&#x2F;flock&#x2F; 
Paper: https:&#x2F;&#x2F;dl.acm.org&#x2F;doi&#x2F;10.14778&#x2F;3750601.3750685

## Top Comments

**suyas:**
Looks really promising!
