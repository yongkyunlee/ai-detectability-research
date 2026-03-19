# Memory and Context Management in CrewAI: What Actually Works

Agent memory sounds straightforward until you're debugging a crew that crashes at task five because the context window exploded. I've spent enough time in CrewAI's internals to have opinions about what the framework gets right, where it falls short, and what you should watch for before pushing a crew to production.

## The Unified Memory System

CrewAI replaced its older collection of separate memory types-short-term, long-term, entity, and external-with a single `Memory` class. This was a good call. The old approach forced you to reason about which memory bucket a fact belonged in, and it rarely matched how agents actually needed to retrieve information. The unified system treats all memories the same way: text goes in, vectors come out, and a composite scoring function ranks them on recall.

The simplest usage is dead simple:


from crewai import Memory

memory = Memory()
memory.remember("We decided to use PostgreSQL for the user database.")
matches = memory.recall("What database did we choose?")


Behind that two-liner, though, there's a surprisingly deep pipeline. On save, an LLM (gpt-4o-mini by default) analyzes the content to infer a scope path, categories, and an importance score between 0 and 1. On recall, results come back ranked by a composite formula that blends semantic similarity, recency decay, and importance. The weights default to 0.5 semantic, 0.3 recency, and 0.2 importance, with a recency half-life of 30 days.

That composite scoring is where things get interesting. The recency decay follows an exponential curve: `0.5^(age_days / half_life_days)`. So a memory is worth half its recency score after 30 days by default, a quarter after 60. You can tune this aggressively for fast-moving projects-set `recency_half_life_days=7` for sprint retros-or stretch it out to 180 days for an architecture knowledge base. The trade-off is clear: a short half-life keeps results fresh but forgets older context fast. A long half-life retains history but risks drowning fresh decisions in stale noise.

## Scopes and Slices: Organizing What Agents Know

Memories live in a hierarchical scope tree, structured like a filesystem. Paths like `/project/alpha`, `/agent/researcher`, or `/company/engineering` partition the memory space. When you recall within a scope, the search only covers that branch. This matters for both precision and performance-fewer records to scan means faster results.

You don't have to design the scope tree upfront. If you call `remember()` without specifying a scope, the LLM picks one based on existing structure and content. Over time, the tree grows organically. I'd still recommend using explicit scopes for anything you know the placement of, and letting the LLM infer only for freeform agent output.

Slices are the multi-scope complement. A `MemorySlice` lets you recall across several disjoint branches simultaneously-useful when an agent needs both its private findings and shared company knowledge. The most common pattern is a read-only slice:


agent_view = memory.slice(
    scopes=["/agent/researcher", "/company/knowledge"],
    read_only=True,
)


This gives the agent visibility into shared docs without letting it pollute the shared space with its own intermediate thoughts. That `read_only=True` flag is load-bearing in multi-agent setups.

## The Encoding Pipeline

What happens between `remember()` and the data hitting LanceDB (the default storage backend) is a five-step encoding flow. The pipeline batches embedding calls into a single `embed_texts()` invocation, runs intra-batch deduplication using cosine similarity (threshold 0.98 by default), then checks storage for similar existing records. If similarity exceeds the consolidation threshold of 0.85, the LLM decides whether to keep, update, or delete the existing record.

The routing is efficient. Records where all fields are provided and no similar records exist in storage take the fast path-zero LLM calls, straight to insert. Records missing fields or needing consolidation trigger one or two LLM calls. This means you can bypass the analysis overhead entirely by passing `scope`, `categories`, and `importance` explicitly when you know them.

`remember_many()` is non-blocking. It submits the encoding pipeline to a background thread and returns immediately. Every subsequent `recall()` call automatically drains pending writes before searching-a read barrier that's transparent to the caller. When a crew finishes, `kickoff()` drains in its `finally` block so nothing is lost. If you're using memory standalone in a script, call `memory.close()` yourself.

## Context Window Management: The Part That Bites You

Memory is only half the context story. The other half is the raw message history that accumulates in the agent executor as an agent works through tasks. This is where I've seen the most production issues.

CrewAI has a `respect_context_window` parameter on agents, defaulting to `True`. When the conversation exceeds the LLM's token limit, the framework summarizes the history and continues. Set it to `False` and you get a hard stop instead. The summarization approach is simpler to operate, but it silently drops detail. The hard-stop approach preserves accuracy but requires you to design tasks that stay within bounds.

There's a real bug here that bit multiple teams. Issue #4381 documented that Anthropic's error format-`"prompt is too long: 210094 tokens > 200000 maximum"`-wasn't in the `CONTEXT_LIMIT_ERRORS` pattern list. The list only matched OpenAI-style messages. So `respect_context_window=True` silently failed to trigger for Claude models, and the agent just crashed. The fix was a one-liner to add the pattern, but the failure mode was invisible until you hit it.

An even nastier problem surfaced in issues #4319 and #4389: when agents are reused across sequential tasks (the common pattern with `@listen` decorators in Flows), the executor doesn't clear its message history between tasks. Messages accumulate-1 system message becomes 2, then 3-until the LLM receives conflicting system prompts and starts returning empty responses. The error you'd eventually see is `ValueError: Invalid response from LLM call - None or empty`, which tells you nothing about the root cause. The fix is straightforward: reset `self.messages` and `self.iterations` at the start of each `invoke()` call. But as of version 1.9.3, the legacy executor still had this bug. The experimental executor already handled it correctly.

## The Context Pollution Problem

There's a subtler issue that the memory system doesn't solve on its own. In `Crew._execute_tasks()`, each task receives context from prior tasks via `_get_context()`, which concatenates all previous task raw outputs verbatim. In a five-task crew, that means task five's prompt contains the full uncompressed output of tasks one through four. Issue #4661 describes this well: roughly 8,000+ tokens of unfiltered prior output accumulating before the current task even starts.

The proposed solution is an opt-in `context_strategy="summarized"` flag. With it enabled, a small LLM call after each task compresses the output to two or three sentences for downstream consumption. The default stays `"full"` for backward compatibility. This is a sensible trade-off: you lose some fidelity in inter-task context, but you keep the context window from exploding in longer pipelines.

Until that lands, the practical workaround is to be deliberate about task `context` dependencies. Don't let every task depend on every prior task's output-explicitly specify which upstream tasks a given task actually needs. Pair that with `respect_context_window=True` and RAG tools for large documents, and you can keep things under control.

## Recall Depth: Shallow vs. Deep

The `recall()` method supports two modes. Shallow recall is a direct vector search with composite scoring-fast (roughly 200ms according to the docs) and requires no LLM calls. Deep recall runs a multi-step `RecallFlow`: the LLM analyzes the query, selects scopes, searches in parallel, evaluates confidence, and optionally runs recursive exploration rounds when confidence is low.

There's a smart optimization here: queries shorter than 200 characters (the `query_analysis_threshold` default) skip LLM analysis entirely, even in deep mode. Short queries like "What database do we use?" don't benefit from being rewritten into sub-queries. Only longer queries-full task descriptions, paragraphs of context-get the LLM distillation treatment.

For routine agent context injection, shallow recall is the right default. Reserve deep recall for complex, cross-scope queries where you need the framework to figure out where the relevant memories live.

## Storage and Privacy

LanceDB is the default storage, writing to `./.crewai/memory` or whatever `$CREWAI_STORAGE_DIR` points at. It handles concurrent access through a shared lock with retry logic-up to 5 retries with exponential backoff on commit conflicts. The storage layer caps scans at 50,000 rows, which is a reasonable guard against unbounded memory consumption.

The privacy model is source-based. Records marked `private=True` are only visible to recall requests that pass the matching `source` parameter. An `include_private=True` flag gives admin access. It's a simple model, but it covers the common case: isolating per-user or per-session memories in a multi-tenant deployment.

One thing to be aware of: memory content gets sent to whatever LLM you configure for analysis. If you're handling sensitive data, use a local model for both the LLM and embedder. The Ollama provider works for this-`Memory(llm="ollama/llama3.2", embedder={"provider": "ollama", "config": {"model_name": "mxbai-embed-large"}})`.

## What the Community Is Building Around It

The community reaction to CrewAI's memory tells you something. A developer built `crewai-soul`, a markdown-based alternative that stores memories in readable `.md` files instead of a vector database. The motivation was debuggability-you can `cat` the file and see exactly what your agent remembers. Another project, Mnemora, took the opposite approach: a serverless database-first architecture where reads hit DynamoDB at sub-10ms and the LLM only runs at write time for embedding generation.

Both projects are reacting to the same tension. CrewAI's unified memory is capable, but it's opaque. When something goes wrong-a stale memory keeps surfacing, or consolidation ate a record you needed-you're digging through LanceDB internals to figure out what happened. The `memory.tree()` and `memory.list_records()` methods help, and the `crewai memory` TUI browser is a step in the right direction, but production-grade observability for agent memory is still an unsolved problem across the ecosystem.

## Practical Recommendations

We've been using memory long enough to have a short list of rules. Keep scope depth to two or three levels. Scope by concern, not by data type-`/project/alpha/decisions` rather than `/decisions/project/alpha`. Use `remember_many()` for batch operations to get the non-blocking behavior and intra-batch dedup. If you're reusing agents across tasks, verify that your CrewAI version resets executor state properly between invocations. And test your context window behavior with the specific LLM provider you're deploying to-don't assume the error detection patterns cover your model's format.

Memory in agent frameworks is still young. CrewAI's unified approach with composite scoring and LLM-powered analysis is more sophisticated than most alternatives. But sophistication creates failure modes, and the gap between the framework's ambitions and its production reliability is where most debugging time goes. The defaults are reasonable. The architecture is sound. Just don't trust the happy path until you've tested the edges.
