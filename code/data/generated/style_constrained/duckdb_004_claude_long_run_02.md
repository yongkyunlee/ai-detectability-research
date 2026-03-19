# Query Performance Optimization in DuckDB: What Actually Matters

DuckDB is fast. Impressively fast. On a benchmark of 57 queries against 20 GB of ZSTD-compressed Parquet data, a mid-range DuckDB configuration (8 threads, 16 GB RAM) delivered a warm median latency of 881 ms per query. BigQuery clocked in at 2,775 ms. Athena managed 4,211 ms. That's a 3–10x advantage running on commodity hardware against fully managed cloud services. But raw engine speed only gets you so far. The optimizer decisions that DuckDB makes-and sometimes gets wrong-determine whether your query takes half a second or seven minutes.

I've spent enough time reading through DuckDB's issue tracker and community benchmarks to have strong opinions about where the performance cliffs hide. This post covers the optimizations that matter most and the traps that will cost you.

## Filter Pushdown Is Everything

The single most impactful thing DuckDB does for performance is pushing filters down to the scan level. For Parquet files, this means skipping entire row groups based on column statistics, and for hive-partitioned datasets, it means skipping files entirely. When it works, it's spectacular. When it doesn't, you'll wonder why your query is scanning 309 million rows instead of a few thousand.

There are several well-documented cases where pushdown silently fails. Expressions that can throw errors-like `sqrt()`-don't get pushed down into scans. The optimizer can't guarantee that the function won't throw on some row it would have otherwise skipped. On a Parquet file with 800,000 rows and 780 columns, a query filtering with `sqrt(column_0) < 0.001` took 8.55 seconds because DuckDB read every row of every column before applying the filter. Polars handled the same query in 500 ms. That's a 17x difference, and the root cause was purely about pushdown behavior, not engine throughput. A fix landed in PR #20744, but the lesson stands: watch your query plans for filters that sit above the scan operator rather than inside it.

Scalar macros create a similar blind spot. If you define a macro that returns a list of partition values and use it in a `WHERE` clause, DuckDB won't push that filter into the file scan. One user reported their query scanning all 309 million rows in 409 seconds. The workaround was to materialize the macro result into a session variable first:

```sql
SET VARIABLE hives = get_hives();
SELECT * FROM my_data WHERE [year, month] IN getvariable('hives');
```

That dropped the scan from all files to 12 out of 28, bringing runtime to 4.33 seconds. Same data. Same logic. Completely different execution path. This is the kind of thing `EXPLAIN` will reveal immediately, so make it a habit.

## CTE Materialization: A Quiet 100x Regression

DuckDB changed its default CTE behavior between versions 1.3.2 and 1.4.0. CTEs went from being inlined (essentially copy-pasted into the query plan) to being materialized (computed once and stored). This sounds reasonable-materialization prevents redundant computation when a CTE is referenced multiple times. But it has a critical side effect: it blocks column pruning.

Consider a wide table with 50 columns. You write a CTE with `SELECT *` and then only use two columns downstream. With inlining, the optimizer sees through the CTE and only scans those two columns. With materialization, all 50 columns get read and stored before the downstream query picks the two it needs.

On a table with 50 million rows and 50 columns, this pushed execution time from 0.3 seconds to 31.64 seconds. That's a 100x slowdown from an optimizer default change. The fix was eventually merged, but the takeaway is practical: don't write `SELECT *` in CTEs unless you actually need every column. And if you're upgrading across major versions, re-benchmark your CTE-heavy queries.

## Top-N Window Elimination: The Optimizer That Gives and Takes

DuckDB has an optimization called `top_n_window_elimination`. It rewrites patterns like `QUALIFY ROW_NUMBER() OVER (PARTITION BY x ORDER BY y) = 1` into an `arg_max` aggregation, which is theoretically cheaper than a full window sort. The problem is that this rewrite doesn't always account for the physical reality of how data gets accessed.

The worst case shows up with remote storage. On S3-hosted hive-partitioned Parquet data, the rewrite turned a query that issued 81 HTTP GET requests (v1.4.4) into one that issued 4,214 GETs (v1.5.0). Wall-clock time went from 11.6 seconds to 31.5 seconds. The rewritten plan forces a second scan of the data-fine for local SSD, catastrophic when each column chunk in each file triggers a separate HTTP request.

And there's a memory problem too. When the `QUALIFY` threshold is large-say `rn <= 50`-the `arg_min_max_n` function pre-allocates all 50 slots per group upfront. If most groups only have 3 rows, you're wasting memory on 47 empty slots per group, which can trigger OOM with a 1 GB memory limit on a 400,000-row dataset. The optimizer doesn't consider the actual data distribution.

You can disable this optimization explicitly:

```sql
SET disabled_optimizers = 'top_n_window_elimination';
```

That's a blunt instrument but an effective one. The trade-off is simple: the rewrite is faster for local, moderately sized data with low cardinality groups, but it's worse for remote storage or when the top-N value is large relative to actual group sizes.

## Remote Storage Has Different Rules

DuckDB's performance story changes substantially when your data lives on S3 rather than local disk. The benchmark numbers illustrate this clearly. Window functions on local storage averaged 947 ms in the XL configuration (32 threads, 64 GB). The same queries against R2 (Cloudflare's S3-compatible store) took 12,187 ms-nearly 13x slower-because window functions require multiple passes over the data, and each pass means more network round trips.

Cold starts are the other killer. Local DuckDB showed about 5–8% overhead on cold queries. DuckDB reading from R2 showed 1,679–2,778% cold-start overhead because the first query must fetch all Parquet metadata (footers, schemas, row group info) over the network before execution begins.

Version 1.5.0 introduced a regression in how S3 file discovery works for hive-partitioned data. The new hierarchical glob expansion caused DuckDB to discover all files in a partition tree before pruning, rather than pruning during discovery. A `CREATE VIEW` statement that took about 1 second in v1.4.4 ballooned to 3.5 minutes in v1.5.0. The workaround is straightforward:

```sql
SET s3_allow_recursive_globbing = false;
```

This restores the old behavior. A permanent fix is expected in v1.5.1. But the broader point is worth internalizing: optimizations designed for local file access can backfire badly over the network. Dynamic partition pruning through joins reads Parquet footers from every partition file to check row-group statistics, even when the hive directory path alone could have excluded the file. One comparison showed join-derived dynamic pruning reading 6,717 GETs and 1.3 GiB over 407 seconds, while a static `WHERE` literal with the same filter value used 546 GETs, 109 MiB, and finished in 27 seconds. That's 15x faster. If you can express your partition filter as a literal rather than deriving it from a join, do it.

## Memory and Disk Space: The Operational Gaps

DuckDB doesn't have a working `VACUUM FULL`. Running `VACUUM`, `VACUUM ANALYZE`, or `CHECKPOINT` won't reclaim disk space after deletes or table drops. `VACUUM FULL` raises a `Not implemented Error`. One user observed a database file at 1.26 GB with 26% dead space-1,354 free blocks out of 5,169 total. The only recourse is to copy the database to a fresh file:

```python
with duckdb.connect(":memory:") as conn:
    conn.execute(f"ATTACH '{source_path}' AS source (READ_ONLY)")
    conn.execute(f"ATTACH '{compact_path}' AS target")
    conn.execute("COPY FROM DATABASE source TO target")
```

This reduced the file from 1.26 GB to 256 MB-an 80% reduction-in under 5 seconds. But it requires a maintenance window, enough free disk for a full copy, and manual file management afterward. Databases with heavy write churn accumulate bloat that you have to deal with operationally. It's been an open issue since 2019.

Partitioned writes to S3 have their own memory problem. `COPY ... TO` with hive partitioning keeps all partition writers buffered in memory simultaneously. A tiny dataset-2 integer columns, 30 partitions of 1,000 rows each-can OOM with a 2 GB memory limit. The Parquet writers don't flush until row group thresholds are met, and with many partitions open at once, the uncompressed buffers add up fast. Settings like `SET threads = 1` or configuring temp directories don't help. The only reliable workaround is iterating partitions one at a time with filtered `COPY` statements, which is slower but bounded in memory.

## Scaling and Thread Behavior

DuckDB scales well with threads for most operations. The benchmark data shows near-linear scaling on wide scans: 4,971 ms at 4 threads dropping to 995 ms at 32 threads. That's a 5x improvement from an 8x increase in threads-not perfectly linear, but solid.

There are exceptions. Bernoulli and system sampling methods don't scale with thread count at all. The implementation forces single-threaded execution whenever a seed is set, and the optimizer always sets one. Only reservoir sampling scales across threads. If you're sampling large tables and wondering why adding cores doesn't help, that's why.

And concurrency is a known constraint. DuckDB uses single-writer MVCC, which makes it excellent for analytical read-heavy workloads but poorly suited for applications with concurrent writers hitting the same records. This isn't a bug-it's a design choice that trades write concurrency for read performance and operational simplicity.

## Practical Advice

After going through all of this, my recommendations boil down to a short list. Run `EXPLAIN ANALYZE` on any query that matters. Check that filters appear inside the scan operator, not above it. Avoid `SELECT *` in CTEs on wide tables. For S3 data, prefer static `WHERE` literals over join-derived filters when possible, and test with `s3_allow_recursive_globbing` set to false if you're on v1.5.0. Disable `top_n_window_elimination` if your `QUALIFY` queries touch remote data or have large thresholds. And if you're running DuckDB as a persistent store with writes and deletes, budget time for periodic compaction via the copy-to-new-file workaround.

DuckDB's default behavior is excellent for 90% of analytical workloads. The remaining 10% is where understanding the optimizer-its assumptions, its edge cases, and its version-to-version changes-separates a query that finishes in a second from one that never does.
