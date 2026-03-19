# Show HN: Langasync – Use OpenAI/Anthropic Batch APIs with LangChain Chains

**HN** | Points: 1 | Comments: 0 | Date: 2026-02-14
**Author:** basilwoods256
**HN URL:** https://news.ycombinator.com/item?id=47014708
**Link:** https://github.com/langasync/langasync

OpenAI and Anthropic both offer batch APIs that process requests asynchronously at 50% of the standard token price. The trade-off is latency — results come back within 24 hours instead of seconds.The problem is the batch API interface is completely different from the real-time one. OpenAI requires JSONL file uploads and polling. Anthropic has its own Message Batches format. If you have an existing LangChain pipeline, you'd have to rewrite it.langasync wraps both batch APIs behind LangChain's Runnable interface:batch = batch_chain(prompt | model | parser)
job = await batch.submit(inputs)
results = await job.get_results()It handles file formatting, submission, polling, result parsing, partial failure handling, and job persistence (batch jobs can outlive your process, so metadata is stored to disk and you can resume later).Python, Apache 2.0, on PyPI. Vertex AI and Azure OpenAI on the roadmap.
