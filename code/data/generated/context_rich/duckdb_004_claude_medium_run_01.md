# Query Performance Optimization in DuckDB

DuckDB has earned a reputation as the go-to embedded analytical database, routinely outperforming cloud warehouses on single-machine workloads. But raw speed at small scale only tells part of the story. What makes DuckDB genuinely interesting from an optimization standpoint is the depth of its query optimizer — a 35-stage pipeline that transforms naively written SQL into surprisingly efficient physical plans. Understanding how that pipeline works, and where it breaks down, can mean the difference between a sub-second query and one that takes minutes.

## The Optimizer Pipeline

When a query enters the DuckDB optimizer, it passes through a carefully ordered sequence of transformations. Early stages handle expression simplification, CTE inlining, and aggregate rewriting (converting `AVG(x)` into `SUM(x)/COUNT(x)`, for instance). The middle stages do the heavy lifting: filter pushdown, join order optimization, column pruning, and common subexpression elimination. Late stages focus on physical plan refinement — choosing build versus probe sides for hash joins, applying late materialization, propagating statistics, and reordering filter expressions based on cost heuristics.

Each optimizer can be individually disabled through the `disabled_optimizers` setting, which is invaluable for diagnosing whether a particular transformation is helping or hurting a specific query. This granularity reflects a pragmatic philosophy: no single optimization is universally beneficial.

## Filter Pushdown and Its Limits

Filter pushdown is arguably the most impactful optimization in any analytical engine. DuckDB's implementation walks the logical plan top-down, collecting filter predicates and pushing them as close to table scans as possible. It handles the full spectrum of join types with different strategies — inner joins allow pushdown to both sides, left joins restrict it to the left, and outer joins are handled conservatively.

Where things get nuanced is at the boundaries. Filters involving expressions that can throw runtime errors — `sqrt()` on a column that might contain negative values, for example — cannot be pushed down safely. The optimizer must assume the filter could fail, so it leaves it above the scan. In practice, this can cause full-table scans on wide tables where only a tiny fraction of rows match. Users who hit this pattern often find that switching to error-safe function variants or restructuring the query with a subquery yields dramatic speedups.

Another boundary issue surfaces with scalar macros. When a filter references the output of a macro, DuckDB sometimes cannot trace the filter through the macro boundary, resulting in a scan of all files followed by post-scan filtering. Replacing the macro with a materialized variable or temporary table can restore pushdown behavior and cut query time by orders of magnitude.

## Column Pruning and Late Materialization

Analytical tables with dozens or hundreds of columns are common, and scanning unnecessary columns wastes both I/O and memory. DuckDB tackles this through a two-phase approach. First, the `remove_unused_columns` pass traces column references bottom-up through the plan, eliminating any projections that no downstream operator actually needs. Second, the `column_lifetime_analyzer` creates projection maps that dictate exactly which columns are alive at each operator in the pipeline, enabling early elimination.

Late materialization takes this a step further. For queries with selective filters on a small subset of columns, DuckDB can split the scan into two phases: an initial pass that reads only the filter columns and row IDs, followed by a second pass that fetches the remaining columns only for rows that survived filtering. This is especially effective on wide Parquet files where reading all columns upfront would be wasteful.

However, CTE materialization can interfere. When DuckDB materializes a CTE — computing it once and storing the result — it creates a barrier that prevents column pruning from propagating into the CTE definition. A simple pass-through CTE over a wide table that selects only two columns can end up scanning all fifty columns if the CTE is materialized rather than inlined. The performance difference can be staggering: a query that runs in under a second with inlining may take over thirty seconds with materialization.

## Parallel Execution

DuckDB's execution model is pipeline-based and vectorized. Data flows through operators in chunks rather than individual rows, improving CPU cache utilization and enabling SIMD operations. The task scheduler distributes work across threads using a lock-free concurrent queue, and each thread maintains local state to minimize synchronization overhead.

Pipelines are organized into meta-pipelines with explicit dependency edges — the build side of a hash join, for instance, must complete before the probe side begins. Within each pipeline, parallelism is straightforward: multiple threads process different chunks simultaneously. For aggregations and joins, work is partitioned by hash across threads to avoid contention.

One subtlety worth noting: not all operators parallelize as expected. Bernoulli and system sampling, for example, have been found to run single-threaded even when multiple threads are available, due to internal seed handling that inadvertently marks them as non-parallelizable. These are the kinds of edge cases that surface only under profiling.

## Remote Data Access Patterns

DuckDB's performance characteristics shift significantly when querying data on S3 or other remote storage. Locally, scanning a few extra columns or reading additional row groups adds microseconds. Over HTTP, each unnecessary request adds tens of milliseconds of latency, and the costs compound quickly.

Hive partition pruning illustrates this well. On local storage, enumerating all files and then filtering by partition values is fast enough to be invisible. On S3, the same strategy can issue hundreds of extra HTTP requests for Parquet metadata of files that will ultimately be discarded. Version 1.5.0 introduced hierarchical glob expansion that changed this behavior, and users with large partitioned datasets on S3 noticed immediate regressions — queries that made 80 requests suddenly made over 4,000.

The `top_n_window_elimination` optimizer rule presents a related trade-off. It rewrites `ROW_NUMBER() OVER (...) = 1` patterns into aggregate-based plans, which is faster for in-memory data. But for wide Parquet files on S3, the rewritten plan can require scanning the same files twice — once for the aggregate key columns, once for all remaining columns — multiplying HTTP requests by the number of columns. Disabling this single optimization rule, or materializing intermediate results with a CTE, can restore the original request count.

## Practical Takeaways

The most effective DuckDB performance tuning comes from understanding the optimizer's behavior rather than fighting it. Use `EXPLAIN` and `EXPLAIN ANALYZE` liberally. Watch for materialization barriers in CTEs. Prefer error-safe functions in filter predicates. On remote storage, be deliberate about partition layouts and consider disabling optimizations that trade I/O for CPU savings. And when a query behaves unexpectedly, remember that each of those 35 optimizer stages can be toggled independently — the answer is often a single `SET` statement away.
