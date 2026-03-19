# Query Performance Optimization in DuckDB: What Actually Matters

DuckDB is fast. On a 20GB Parquet dataset, a community benchmark clocked it at 284ms median query time (32 threads, 64GB RAM) -- roughly 10x faster than BigQuery and 15x faster than Athena on the same queries. That's the headline number. But raw speed on a clean benchmark doesn't tell you what happens when your queries hit real optimizer behavior, remote storage quirks, and wide tables with dozens of columns.

We've been watching DuckDB's issue tracker closely since the v1.5.0 release, and there's a pattern worth understanding. The engine's optimizer is getting more aggressive, and that aggression sometimes backfires in ways you won't catch until production.

## Filter Pushdown: The Foundation You Can Break

DuckDB's query planner pushes filter predicates down into table scans. This is standard database stuff. On Parquet files, it means the engine can skip entire row groups using min/max statistics and, with hive partitioning, skip entire files based on directory paths. A query that filters on `year=2025 AND month=12` against hive-partitioned S3 data should scan 1 of 26 files instead of all 26. And it does -- when the filter is a literal.

But the pushdown has edges. DuckDB won't push filters containing expressions that can throw runtime errors. The function `sqrt(column_0) < 0.001` looks like a perfectly reasonable scan predicate, but `sqrt` can error on negative inputs. So DuckDB reads every row of every column, then filters afterward. On a table with 780 columns and 800,000 rows, that's 8.5 seconds instead of the 500ms you'd get with an error-safe equivalent. This was reported and confirmed as an expected limitation (issue #19277). The fix that landed in PR #20744 helped with some cases, but the core rule stands: if your filter expression can throw, it won't push down. Use safe alternatives where they exist.

Subquery-derived filters are another gap. If your partition filter comes from a scalar macro or subquery rather than a literal or variable, the optimizer may not recognize it as pushable. One user reported a query scanning 309 million rows in 409 seconds that dropped to 12 files and 4 seconds after materializing the filter value into a variable with `SET VARIABLE hives = get_hives()` and using `getvariable('hives')` instead (issue #21312). The workaround is awkward but effective: pre-compute filter values into temp tables or session variables so the planner sees constants.

## The CTE Materialization Trap

DuckDB 1.4.0 changed CTEs from inlining to materialization by default (PR #17459). The intent was sound -- materialized CTEs prevent redundant computation when a CTE is referenced multiple times. The trade-off is that materialization creates a barrier the optimizer can't see through.

Consider a wide table with 50 columns. You write a CTE that selects all columns, then your outer query only needs two. With inlining, column pruning kicks in and scans just those two columns. With materialization, the CTE reads all 50 columns into a temp result, and the outer query picks two from that. On 50 million rows, that's the difference between 0.3 seconds and 31 seconds -- a 100x regression reported against real Splink workloads at the UK Ministry of Justice (issue #20958). The issue was closed with a fix, but the lesson holds: `SELECT *` in a materialized CTE is expensive when you don't need every column.

## Optimizer Rewrites That Hurt Remote Storage

The `top_n_window_elimination` optimizer, new in v1.5.0, rewrites `ROW_NUMBER() OVER (...) = 1` patterns into an `arg_max`-based plan with a semi-join. Locally, this is often faster. On S3-hosted Parquet with wide schemas, it's a disaster. The rewrite causes two separate scans of the remote files. For 39 files with 90 columns each, that turned 81 HTTP GET requests into 4,214 -- wall clock time nearly tripled from 11.6s to 31.5s (issue #21348).

The workaround is direct: `SET disabled_optimizers='top_n_window_elimination';` restores the old single-scan window plan. You can also wrap your scan in a `MATERIALIZED` CTE to block the rewrite. This is simpler, but the `MATERIALIZED` CTE approach forces all data through memory, while disabling the optimizer rule preserves the streaming window plan that may handle larger datasets more gracefully.

A related issue surfaced with `QUALIFY rn <= 50` on grouped data where the actual max rank was 3 (issue #21431). The `arg_min_max_n` aggregate pre-allocates all N slots up front, and when N is 50 but most groups have 3 entries, the wasted allocations blow past memory limits. The DuckDB team acknowledged the fix should change how the binary aggregate heap allocates, but until that lands, keep `QUALIFY` thresholds tight or disable the optimization.

## S3 Globbing: The v1.5.0 Regression

DuckDB v1.5.0 introduced hierarchical S3 glob expansion. The old behavior discovered only the files matching your hive partition filters. The new behavior discovers all files first, then prunes. On a bucket with 122 partition files, a query needing 39 of them now issues HTTP requests for all 122 Parquet footers before throwing out the extras (issue #21347). That's pure latency overhead on every query.

`SET s3_allow_recursive_globbing = false;` is the recommended workaround from the DuckDB maintainers, and a fix targeting v1.5.1 is in progress. If you upgraded recently and noticed S3 queries getting slower, check this first.

## Practical Takeaways

Write your filters as literals or pre-computed variables, not subqueries. Avoid `SELECT *` in CTEs that get materialized -- list the columns you need. Profile with `EXPLAIN ANALYZE` and look at the `Scanning Files` line to confirm partition pruning is working. And if you're on v1.5.0 querying S3 with hive partitioning, set `s3_allow_recursive_globbing` to false until 1.5.1 ships.

DuckDB's vectorized engine is genuinely excellent at what it does -- the benchmark numbers don't lie. But the optimizer is evolving fast, and each release brings rewrites that assume local disk. If your data lives in S3, you're operating at the edge of what's been tested. Read the changelogs, run your own profiling, and don't assume that an upgrade is free.
