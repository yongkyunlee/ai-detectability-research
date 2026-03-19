# Query Performance Optimization in DuckDB: What Actually Matters

DuckDB has quietly become the go-to analytical engine for data engineers who need fast local queries without the overhead of a distributed system. It routinely delivers sub-second latency on datasets that take cloud platforms like BigQuery and Athena multiple seconds to process. Impressive on a benchmark chart. But raw speed in controlled conditions tells you nothing about the performance pitfalls lurking inside a real workload. This post digs into the engine's internals: how it achieves its speed, where the optimizer trips over itself, and what you should watch for when pushing things toward their limits.

## The Execution Model: Vectors, Not Rows

Traditional row-oriented databases process one tuple at a time through a tree of operators. DuckDB takes a different path. Its execution engine operates on vectors of 2,048 rows, passing these fixed-size batches through a pipeline of physical operators. Each operator (whether it performs a filter, a hash join, or an aggregation) consumes and produces columnar vectors, keeping data in a format that plays well with modern CPU cache hierarchies and SIMD instructions.

This vectorized model means that tight loops over homogeneous data replace the pointer-chasing and virtual function dispatch that plague row-at-a-time engines. A filter operator evaluates its predicate across the entire vector and produces a selection bitmap rather than branching on each individual row. The result: computational operations spend their time doing arithmetic instead of waiting on memory.

The engine decomposes queries into pipelines, which are linear chains of operators that can stream data without materializing intermediate results to disk. These run in parallel across available threads, with event-based synchronization managing dependencies between stages. Thread-local state buffers minimize lock contention, and a work-stealing scheduler keeps cores busy even when pipeline stages have uneven workloads.

## The Optimizer Pipeline: Rewriting Queries Before They Run

Before any vector touches a CPU register, DuckDB's optimizer applies a sequence of transformation passes to the logical query plan. The pipeline is extensive. Expression rewriting handles constant folding and arithmetic simplification; a filter pushdown pass shoves predicates as deep into the plan tree as possible. Join ordering uses cardinality estimates to find efficient join sequences, and specialized rewrites handle everything from regex range extraction to aggregate function decomposition.

Filter pushdown is probably the single most impactful optimization for analytical workloads. When a query filters on a column that also serves as a hive partition key, pushing that predicate down to the file-discovery layer means the engine never opens files it doesn't need. On a dataset partitioned across hundreds of Parquet files on S3, the difference between scanning 39 files and all 455 is the difference between a two-second query and a thirty-second one. That's huge.

Pushdown has boundaries that aren't always obvious, though. Expressions containing functions that can throw runtime errors (`sqrt()` on a potentially negative value, for example) can't be safely pushed below a scan operator. The reasoning is straightforward: if the filter were evaluated during scanning, it might encounter a value that triggers an error, even though the original query plan would have filtered that row out first. This safety-first stance is defensible. Still, it means a query filtering on `sqrt(column) < 0.01` over a wide Parquet file with hundreds of columns will read every row and every column before applying the filter; a system willing to return NaN instead of an error could push the predicate and skip most of the data.

## CTE Materialization: A Double-Edged Optimization

Common Table Expressions got a significant behavioral change in DuckDB 1.4 when the default switched from CTE inlining to CTE materialization. The motivation was sound: if a CTE is referenced multiple times, materializing it once avoids redundant computation. But materialization introduces a barrier that blocks optimizer passes from reaching through to the underlying scan.

Here's where it gets interesting. Consider a CTE that selects all columns from a wide table, but the outer query only uses two of them. With inlining, the optimizer sees through the CTE and prunes the unused columns at scan time. Materialization forces all fifty columns to be built first, and column pruning can't cross that boundary. On a table with fifty million rows and fifty columns, I've seen this produce a slowdown from 0.3 seconds to over 30 seconds. Two full orders of magnitude for what looks like an innocuous query pattern.

The practical takeaway: if your CTE is referenced only once and acts as a simple pass-through, materialization is pure overhead. Knowing when to add the `NOT MATERIALIZED` hint (or restructuring the query to avoid it entirely) matters more than most people expect.

## Hive Partitioning: The File Discovery Problem

DuckDB supports reading hive-partitioned datasets directly from S3, and it's one of the most popular features for data lake workflows. The engine parses the directory structure, identifies partition keys, and ideally uses query filters to prune the file list before opening any Parquet metadata.

The reality is messier than that.

Dynamic partition pruning, introduced to handle cases where the filter value comes from a join rather than a literal, works well for local files. On remote storage, though, the timing of file enumeration introduces a gap. If the glob pattern gets expanded during query planning rather than execution, the full file list is locked in before dynamic filters can prune it. A query that should touch 39 files instead discovers all 122 matching the glob, reads their Parquet footers, and only then discards the ones that don't match. Each unnecessary footer read is an HTTP GET request, and on wide schemas with many row groups, those requests add up fast.

Things get worse when combined with optimizer rewrites that transform the query plan in unexpected ways. The top-N window elimination optimization rewrites `QUALIFY ROW_NUMBER() OVER (...) = 1` into an `arg_max` aggregation followed by a semi-join. The rewritten plan scans the data twice: once to identify winning rows using a lightweight projection, and again to fetch all columns for those rows. On local disk, the second scan hits the OS page cache and costs almost nothing. On S3 with a 90-column schema, it generates one HTTP range request per column chunk per file per row group, turning 80 network requests into over 4,000 and nearly tripling wall-clock time. Honestly, that surprised me.

The optimizer makes this transformation based purely on the logical structure of the query, with no awareness of whether the data lives on a local NVMe drive or across an ocean on an S3 endpoint. Storage topology is invisible to the planner; the cost model doesn't currently account for per-request latency on remote storage.

## Memory Management Under Pressure

DuckDB's design as an embedded, single-process engine means it shares its host's memory with everything else running on the machine. It uses jemalloc or mimalloc for allocation, and these allocators intentionally hold onto freed memory in thread-local pools rather than returning it to the OS immediately. Efficient for steady-state workloads, since reusing already-mapped pages avoids expensive system calls. But memory usage as reported by the OS won't drop after a large query completes. The memory is available for reuse by subsequent queries, just not by other processes.

Partitioned writes are where the more serious concern shows up. When exporting a table to hive-partitioned Parquet files, the engine maintains a buffered writer for each active partition. Each writer holds uncompressed row data in memory until it accumulates enough rows to fill a row group, at which point it compresses and flushes. With hundreds or thousands of partitions, the aggregate buffer size can exceed the configured memory limit even when the source data is small. I've seen a thirty-partition export of a table with only thirty thousand rows fail with an out-of-memory error under a two-gigabyte limit. Not because the data is large, but because thirty concurrent writers each holding partial row groups consume memory that scales with partition count rather than data volume.

## Prepared Statements and Plan Staleness

One subtle correctness issue sits at the intersection of optimization and transaction isolation. When a prepared statement is created, the optimizer uses current table statistics (min/max values, row counts) to make pruning decisions. If those statistics indicate that a filter will match zero rows, the optimizer may eliminate the scan entirely. The prepared plan caches this decision.

Here's the problem. Plan invalidation checks only whether the catalog has changed (table schema modifications), not whether the underlying data has changed between transactions. If new rows are inserted that would satisfy the pruned filter, executing the cached prepared plan returns stale results. The pruning was correct at prepare time but wrong at execute time. This mismatch between snapshot-sensitive optimization and catalog-only invalidation creates a window where prepared statements silently return incorrect data. From what I can tell, this isn't widely known.

## What to Do About All This

For practitioners pushing DuckDB on real workloads, a few practical guidelines emerge from these internals.

Profile with `EXPLAIN ANALYZE`, not just `EXPLAIN`. The analyzed plan shows actual row counts, file scan ratios, and operator timings; you'll want to watch for `Scanning Files: 39/122` patterns that reveal incomplete partition pruning.

Keep an eye on CTE materialization when you're working with wide tables. If your CTE is referenced once and selects broadly, consider inlining it or restructuring the query. The performance difference can be staggering.

You can disable specific optimizer rules when they backfire. `SET disabled_optimizers='top_n_window_elimination';` prevents the catastrophic plan rewrites I described on remote storage. It's a scalpel, not a sledgehammer; disable only what causes measurable harm. On the S3 side, setting `s3_allow_recursive_globbing` to false can prevent the file-discovery regression that enumerates entire directory trees before applying partition filters.

Be cautious with prepared statements across transaction boundaries. If you're inserting data between prepare and execute, rebind the statement or use fresh queries.

DuckDB's performance is genuinely impressive for what it is: an embedded analytical engine with no cluster to manage and no network hops between operators. But "fast by default" doesn't mean "fast in every case." Understanding where the optimizer's assumptions break down (around remote storage costs, materialization barriers, and error-safe filter pushdown) is what separates a query that finishes in milliseconds from one that grinds for minutes.
