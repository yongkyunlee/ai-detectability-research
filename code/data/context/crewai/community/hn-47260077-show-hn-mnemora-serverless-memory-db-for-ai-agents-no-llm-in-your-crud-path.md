# Show HN: Mnemora – Serverless memory DB for AI agents (no LLM in your CRUD path)

**HN** | Points: 4 | Comments: 4 | Date: 2026-03-05
**Author:** isaacgbc
**HN URL:** https://news.ycombinator.com/item?id=47260077
**Link:** https://github.com/mnemora-db/mnemora

Hi HN,I built Mnemora because every AI agent memory solution I evaluated (Mem0, Zep, Letta) routes data through an LLM on every read and write. At scale, that means 200-500ms latency per operation, token costs on your memory layer, and a runtime dependency you don't control.Mnemora takes the opposite approach: direct database CRUD. State reads hit DynamoDB at sub-10ms. Semantic search uses pgvector with Bedrock Titan embeddings — the LLM only runs at write time to generate the embedding vector. All reads are pure database queries.Four memory types, one API:
1. Working memory: key-value state in DynamoDB (sub-10ms reads)
2. Semantic memory: vector-searchable facts in Aurora pgvector
3. Episodic memory: time-stamped event logs in S3 + DynamoDB
4. Procedural memory: rules and tool definitions (coming v0.2)Architecture: fully serverless on AWS — Aurora Serverless v2, DynamoDB on-demand, Lambda, S3. Idles at ~$1&#x2F;month, scales per-request. Multi-tenant by default: each API key maps to an isolated namespace at the database layer.What I'd love feedback on:
1. Is the "no LLM in CRUD path" differentiator clear and compelling?
2. Would you use this over Mem0&#x2F;Zep for production agents? What's missing?
3. What memory patterns are you solving that don't fit these 4 types?Happy to answer architecture questions.SDK:
pythonpip install mnemorafrom mnemora import MnemoraSyncclient = MnemoraSync(api_key="mnm_...")
client.store_memory("my-agent", "User prefers bullet points over prose")
results = client.search_memory("output format preferences", agent_id="my-agent")
# [0.54] User prefers bullet points over prose
Drop-in LangGraph CheckpointSaver, plus LangChain and CrewAI integrations.Links:
5-min quickstart: https:&#x2F;&#x2F;mnemora.dev&#x2F;docs&#x2F;quickstart
GitHub: https:&#x2F;&#x2F;github.com&#x2F;mnemora-db&#x2F;mnemora
PyPI: https:&#x2F;&#x2F;pypi.org&#x2F;project&#x2F;mnemora&#x2F;
Architecture deep-dive: https:&#x2F;&#x2F;mnemora.dev&#x2F;blog&#x2F;serverless-memory-architecture-for-...

## Top Comments

**isaacgbc:**
All feedback is appreciated :)

**brianwmunz:**
The no-LLM-in-CRUD-path thing makes sense...I've seen teams hit real latency walls routing every memory operation through inference.
What's your thinking around retrieval patterns? Most agent memory systems I've worked with end up needing vector similarity for semantic search but also structured queries for stuff like "all conversations from last week." Are you planning to support both or staying vector-focused?
