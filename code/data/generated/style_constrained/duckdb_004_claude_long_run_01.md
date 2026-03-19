# Query Performance Optimization in DuckDB

DuckDB is fast. That part isn't controversial anymore. But "fast" hides a lot of nuance, and if you're running DuckDB on anything beyond a toy dataset, the default behavior won't always be the right behavior. We've been watching the project closely as it matures - version 1.5.0 shipped on March 9, 2026 - and the optimizer has become both more powerful and more surprising. The performance wins are real, but so are the regressions and sharp edges. This post covers what matters for squeezing the most out of DuckDB queries, and where the engine can bite you.

## The Execution Model

DuckDB uses a vectorized, push-based execution engine. Data flows through operators in batches rather than row-by-row, which keeps CPU caches warm and avoids per-row function call overhead. That's the foundation of its speed advantage over row-oriented engines like PostgreSQL for analytical workloads.

The pipeline is straightforward: SQL text goes through a parser (based on libpg_query, the same parser PostgreSQL uses), then a planner converts tokens into a tree of `LogicalOperator` nodes, the optimizer rewrites that tree, and finally the execution layer converts it into `PhysicalOperator` nodes for actual data processing. Both cost-based and rule-based optimizations run during the optimizer phase. The key optimizations are predicate pushdown, column pruning, join ordering, and expression rewriting.

So if you're writing queries, the most important thing to understand is that the optimizer is doing a lot of work behind the scenes - and sometimes that work can go wrong.

## Benchmarks: Where DuckDB Sits

A community benchmark published in January 2026 tested DuckDB against BigQuery and Athena on 20GB of ZSTD-compressed Parquet data - 57 queries covering scans, aggregations, joins, and window functions. The results are striking.

DuckDB on local SSD with a medium config (8 threads, 16GB RAM) delivered an 881ms median warm query time. Scale that up to 32 threads and 64GB RAM, and the median dropped to 284ms. BigQuery came in at 2,775ms. Athena at 4,211ms. That's a 3-10x advantage for DuckDB on local storage, which shouldn't shock anyone - there's no network hop, no multi-tenant scheduling, no query compilation step in a remote service.

The breakdown by query type tells a more useful story. Table scans on the XL config hit 208ms. Aggregations landed at 382ms. Joins at 361ms. Window functions were the outlier at 947ms, and things got dramatically worse when running window functions over remote storage on Cloudflare R2 - 12,187ms, because window operations require multiple passes over data that isn't local.

Thread scaling was roughly linear but not perfectly so. Going from 4 threads to 32 threads (an 8x increase) yielded about a 5x speedup on wide scans. That's decent for capacity planning, but don't expect miracles from throwing more cores at a query.

## Configuration Levers That Matter

DuckDB exposes a few pragmas that directly affect query performance. The obvious ones: `SET threads = N` controls parallelism (auto-detected by default), and `SET memory_limit = '16GiB'` caps RAM usage. There's also `SET temp_directory` for disk spill, which becomes critical when working close to memory limits.

A less obvious setting is `SET preserve_insertion_order = false`. If you don't need output rows in insertion order, turning this off lets the engine skip sorting overhead during materialization. And `PRAGMA enable_object_cache = false` can matter if you're profiling and want to eliminate caching effects.

These are blunt instruments. The subtler optimization decisions happen inside the query planner, and that's where the real trouble starts.

## CTE Materialization: A 100x Regression

Between DuckDB 1.3.2 and 1.4.0, the project switched CTE handling from inlining to materialization by default (PR #17459). The change makes sense in theory - if a CTE is referenced multiple times, materializing it avoids redundant computation. But the implementation introduced a painful regression for a common pattern.

Consider a wide table with 50 columns. You define a CTE that selects everything from it, then reference that CTE twice but only pull two columns each time. With inlining, the optimizer pushes column pruning through the CTE boundary and only scans 2 columns. With materialization, the CTE gets fully materialized with all 50 columns before any downstream pruning happens. On a table of 50 million rows, this difference turned a 0.3-second query into a 31-second query - a 100x slowdown reported by a developer from the UK Ministry of Justice who hit it in production with the Splink record-linkage library (issue #20958).

The fix was merged, and the issue is closed. But the lesson here matters: CTEs that look like simple pass-throughs (`WITH base AS (SELECT * FROM big_table)`) can silently change behavior across DuckDB versions. If you're using CTEs as organizational tools in complex queries, watch your `EXPLAIN` output closely after upgrades. And when performance matters, consider whether a view or a subquery would give the optimizer more room to work.

## Top-N Window Elimination: Optimization Gone Sideways

DuckDB has an optimization called top-N window elimination. When you write a `QUALIFY rn <= 50` on a `ROW_NUMBER()` window function, the optimizer can rewrite this into an `arg_min_max_n` aggregation instead of computing the full window. Clever. But commit `5f9e4101c164d7` opened this up for broader use, and it exposed a memory allocation problem.

The `arg_min_max_n` function pre-allocates all N slots up front. If you ask for the top 50 per group but most groups only have 3 rows, you're allocating 50 slots per group for almost entirely empty storage. On a query with 400,000 rows and a 1GB memory limit, this tripled memory usage and caused an OOM (issue #21431). The workaround is surgical:


SET disabled_optimizers = 'top_n_window_elimination';


DuckDB maintainer Mark Raasveldt confirmed the root cause and noted that the proper fix is to change the heap allocation strategy so it doesn't pre-allocate all slots. The optimization is simpler to disable than to fix, but disabling it means your window queries fall back to the full computation path.

## Sampling: Watch Your Threads

A bug reported in version 1.4.4 revealed that `BERNOULLI` and `SYSTEM` sampling methods don't scale with thread count, while `RESERVOIR` sampling does (issue #21086). The root cause was in `PhysicalStreamingSample::ParallelOperator()`, which returns `false` whenever a seed is set - and the planner always sets a seed internally. So the streaming sample operators were effectively single-threaded regardless of your `SET threads` value.

This matters if you're using sampling to speed up exploratory queries on large datasets. If you need parallelism, use `RESERVOIR` sampling until the fix lands. RESERVOIR is heavier in memory but actually scales across cores.

## Storage: The File Size Problem

DuckDB's on-disk format has a well-known issue with space reclamation. When you delete rows or drop tables, the database file doesn't shrink. Freed blocks go onto a free list and should be reused, but with ART (Adaptive Radix Tree) indexes - which are automatically created for any column with a PRIMARY KEY or UNIQUE constraint - the blocks aren't properly reclaimed.

One user reported a table with just 1,500 rows growing to 1.2GB after 24 hours of INSERT OR REPLACE operations. Removing the UNIQUE constraint dropped steady-state file size to 2.3MB. Exporting the bloated 1.2GB database to Parquet produced a 400KB file (issue #17778). Another user saw a 1.26GB database compact to 256MB via `COPY FROM DATABASE source TO target`.

VACUUM doesn't help. CHECKPOINT doesn't help. The only reliable workaround today is to periodically export and reimport the database, which is the kind of offline maintenance you'd rather not need. This has been under review since September 2024 (issue #14124), and it's the single biggest operational concern for anyone running DuckDB as a persistent store with frequent mutations.

The trade-off judgment here is clear: DuckDB is simpler to deploy and operate than a traditional analytical database, but that simplicity comes at the cost of missing a working VACUUM implementation for indexed tables. If your workload is append-only or read-heavy, this won't matter. If you're doing continuous upserts against indexed columns, plan for periodic compaction or rethink your schema to avoid ART indexes.

## Remote Storage: Cold Starts Dominate

Running DuckDB against Parquet files on Cloudflare R2 or S3 is viable for warm queries - the benchmark showed a 496ms median on the XL config, which is still faster than BigQuery or Athena. But cold start times ranged from 14 to 20 seconds because the first query has to fetch Parquet metadata (file footers, schemas, row group statistics) over the network. That's a 2,778% overhead on the XL config.

Subsequent queries benefit from metadata caching and run close to local speeds. So if your access pattern involves repeated queries against the same files, the cold start is a one-time cost. But for sporadic, ad-hoc workloads against remote data, BigQuery's near-zero cold start overhead (about 2%) makes it a better fit despite being slower in steady state.

## Prepared Statements and Stale Plans

A subtle bug reported in issue #21207 deserves attention if you're using DuckDB in a server context. Prepared statements can embed optimizer decisions that depend on table statistics at prepare time - specifically, the statistics propagation pass can prune filters as "always true" or "always false" based on min/max values in existing row groups. But the rebind check that decides whether to recompile a prepared plan only looks at catalog identity, not data identity. So a plan prepared in one transaction can be reused in a later transaction after inserts have changed the data distribution, returning wrong results.

This is a correctness bug, not just a performance issue. It's most likely to surface in Flight SQL or other contexts where prepare and execute happen in separate transactions. The mitigation is to use parameterized queries (which force rebind) instead of literal values in filters.

## Practical Advice

If you're optimizing DuckDB queries for a production workload, here's what to focus on. Keep your Parquet files sorted on common filter columns - row group statistics based on min/max values let the engine skip entire groups during scans. Use ZSTD compression; it's a solid default. Watch your `EXPLAIN` output after version upgrades, especially around CTEs and window functions. Avoid PRIMARY KEY and UNIQUE constraints on tables that see frequent mutations unless you're prepared to manage file size growth. And test thread scaling for your specific query patterns - not everything scales linearly, and some operations are silently single-threaded due to implementation bugs.

DuckDB has earned its reputation as a fast, embeddable analytical engine. The WASM version clocks in at just 2MB, and the CLI at 16MB - it runs on a $4 VPS with 50MB of idle RAM for web analytics use cases. But the optimizer is complex enough that default behavior isn't always optimal behavior, and the storage layer still has gaps that matter for long-running services. Know the sharp edges, and you'll get a lot out of it.
