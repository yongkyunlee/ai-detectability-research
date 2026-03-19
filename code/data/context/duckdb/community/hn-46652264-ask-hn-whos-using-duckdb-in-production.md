# Ask HN: Who's using DuckDB in production?

**HN** | Points: 7 | Comments: 4 | Date: 2026-01-16
**Author:** yakkomajuri
**HN URL:** https://news.ycombinator.com/item?id=46652264

Inspired by the post that's on the front page as I write this [1] I'm interested to hear about who's using DuckDB in production and how.We have a tool live that uses it and I'm quite happy so I'm both looking for interesting use cases from others but also to be honest I'm reasonably sure I've just identified today that DuckDB is leaking memory quite seriously [2] so I'm curious to hear if other people have noticed this or if it's maybe something that's not as relevant to others since people might be running DuckDB pipelines in ephemeral envs like lambdas etc. where a memory leak might not matter as much.[1] https:&#x2F;&#x2F;news.ycombinator.com&#x2F;item?id=46645176[2] https:&#x2F;&#x2F;github.com&#x2F;duckdb&#x2F;duckdb&#x2F;issues&#x2F;20569

## Top Comments

**delaminator:**
This is expected behaviour, not a bug.DuckDB (like most database systems and many applications using memory allocators like jemalloc or mimalloc) doesn't immediately release memory back to the OS after freeing it internally.Memory allocator strategy - DuckDB uses an allocator that keeps freed memory in a pool for reuse. Returning memory to the OS is expensive (system calls, page table updates), so allocators hold onto it anticipating future allocations.
