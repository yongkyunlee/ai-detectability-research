# Query Performance Optimization in DuckDB

DuckDB has earned its reputation as the go-to embedded analytical database, regularly outperforming cloud warehouses on single-machine workloads. But raw speed at small scale only tells part of the story. What actually makes it interesting from a tuning standpoint is the depth of its query optimizer: a 35-stage pipeline that transforms naively written SQL into surprisingly efficient physical plans. Honestly, the thing is deeper than I expected. Understanding how that pipeline works, and where it falls apart, can mean the difference between a sub-second query and one that takes minutes.

## The Optimizer Pipeline

When a query enters the optimizer, it passes through a carefully ordered sequence of transformations. Early stages handle expression simplification, CTE inlining, and aggregate rewriting (converting `AVG(x)` into `SUM(x)/COUNT(x)`, for instance). The heavy lifting happens in the middle: filter pushdown, join order optimization, column pruning, and common subexpression elimination. Toward the end, the focus shifts to physical plan refinement, choosing build versus probe sides for hash joins, applying late materialization, propagating statistics, and reordering filter expressions based on cost heuristics.

Here's what I find most useful: each stage can be individually disabled through the `disabled_optimizers` setting. That's invaluable for figuring out whether a particular transformation is helping or hurting. No single optimization is universally beneficial, and DuckDB's design acknowledges that.

## Filter Pushdown and Its Limits

Filter pushdown is arguably the most impactful optimization in any analytical engine. DuckDB's implementation walks the logical plan top-down, collecting filter predicates and pushing them as close to table scans as possible. It handles the full spectrum of join types with different strategies; inner joins allow pushdown to both sides, left joins restrict it to the left, and outer joins get handled conservatively.

The boundaries are where things get tricky.

Filters involving expressions that can throw runtime errors (say, `sqrt()` on a column that might contain negatives) can't be pushed down safely. The optimizer has to assume the filter could fail, so it leaves it above the scan. In practice, this causes full-table scans on wide tables where only a tiny fraction of rows match. Switching to error-safe function variants or restructuring the query with a subquery often yields dramatic speedups.

Scalar macros create a similar problem. When a filter references the output of a macro, DuckDB sometimes can't trace it through the macro boundary. You end up scanning all files, then filtering after the fact. A fix that works: replace the macro with a materialized variable or temporary table to restore pushdown behavior and cut query time by orders of magnitude.

## Column Pruning and Late Materialization

Analytical tables with dozens or hundreds of columns are common. Scanning unnecessary ones wastes both I/O and memory, and DuckDB tackles this through a two-phase approach. The `remove_unused_columns` pass traces column references bottom-up through the plan, eliminating projections that no downstream operator actually needs. After that, the `column_lifetime_analyzer` creates projection maps dictating exactly which columns are alive at each operator, enabling early elimination.

Late materialization takes this further. For queries with selective filters on a small subset of columns, the engine can split the scan into two phases: an initial pass that reads only the filter columns and row IDs, then a second pass that fetches remaining columns only for surviving rows. On wide Parquet files, this saves a ton of I/O.

CTE materialization can mess this up, though. When DuckDB materializes a CTE (computes it once and stores the result), it creates a barrier that prevents column pruning from propagating into the definition. A simple pass-through CTE over a wide table selecting only two columns might end up scanning all fifty if it gets materialized rather than inlined. Total performance killer. I've seen queries go from under a second with inlining to over thirty seconds without it.

## Parallel Execution

DuckDB's execution model is pipeline-based and vectorized. Data flows through operators in chunks rather than individual rows, which improves CPU cache utilization and enables SIMD operations. The task scheduler distributes work across threads using a lock-free concurrent queue, and each thread maintains local state to keep synchronization overhead minimal.

Pipelines are organized into meta-pipelines with explicit dependency edges. The build side of a hash join must complete before the probe side begins; within each pipeline, parallelism is straightforward since multiple threads process different chunks simultaneously. For aggregations and joins, work gets partitioned by hash to avoid contention.

One thing that surprised me: not all operators parallelize as you'd expect. Bernoulli and system sampling have been found to run single-threaded even when multiple threads are available, due to internal seed handling that inadvertently marks them as non-parallelizable. These edge cases only surface under profiling.

## Remote Data Access Patterns

Performance characteristics shift significantly when you're querying data on S3 or other remote storage. Locally, scanning extra columns or reading additional row groups adds microseconds. Over HTTP, each unnecessary request adds tens of milliseconds of latency. Costs compound fast.

Hive partition pruning illustrates this well. On local storage, enumerating all files and filtering by partition values is fast enough to be invisible. On S3, the same strategy can issue hundreds of extra HTTP requests for Parquet metadata of files that'll ultimately be discarded. Version 1.5.0 introduced hierarchical glob expansion that changed this behavior, and users with large partitioned datasets noticed immediate regressions: queries that made 80 requests suddenly made over 4,000. That's not a typo.

The `top_n_window_elimination` rule presents a related trade-off. It rewrites `ROW_NUMBER() OVER (...) = 1` patterns into aggregate-based plans, which is faster for in-memory data. But for wide Parquet files on S3, the rewritten plan can require scanning files twice (once for aggregate key columns, once for everything else), multiplying HTTP requests by the number of columns. Disabling this single rule, or materializing intermediate results with a CTE, can restore the original request count.

## What Actually Helps

From what I can tell, the most effective performance tuning comes from understanding the optimizer's behavior rather than fighting it. Use `EXPLAIN` and `EXPLAIN ANALYZE` liberally. CTE materialization barriers are a common culprit; prefer error-safe functions in filter predicates too. On remote storage, be deliberate about partition layouts and consider disabling optimizations that trade I/O for CPU savings. When a query behaves unexpectedly, remember that each of those 35 stages can be toggled independently. The answer is often a single `SET` statement away.
