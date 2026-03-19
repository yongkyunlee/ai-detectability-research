# Query Performance Optimization in DuckDB

DuckDB is fast out of the box. Its vectorized, push-based execution engine processes data in column batches that play well with modern CPU caches, and for many analytical workloads you won't need to think about tuning at all. But once your tables grow wide, your partitions multiply, or you start reading Parquet over S3, the optimizer's choices start to matter a lot. We've hit enough sharp edges on our team that I wanted to write down what we've learned about where DuckDB's optimizer helps, where it stumbles, and what knobs you can turn.

## The Optimizer Pipeline

DuckDB runs over thirty optimization passes on every query. The chain starts with expression rewriting—constant folding, arithmetic simplification, regex optimization—and moves through filter pushdown, join ordering, column pruning, limit pushdown, and statistics propagation. A late pass called top-N window elimination rewrites patterns like `ROW_NUMBER() OVER (...) = 1` into more efficient aggregate plans using `arg_max`. The final pass pushes join filters down after everything else has settled. Each pass can be individually disabled with `SET disabled_optimizers = '<name>';`, which turns out to be genuinely useful when a specific rewrite backfires.

The ordering of these passes isn't arbitrary. Filter pushdown runs early so that downstream passes operate on smaller intermediate results. Column lifetime analysis runs twice—once in the middle and once near the end—because earlier passes can expose new pruning opportunities. CTE inlining also runs twice, bookending the core optimization block. The whole design reflects an assumption that analytical queries benefit most from reducing I/O as early as possible, and that's usually correct.

## Filter Pushdown: The Most Important Optimization You Can Break

Filter pushdown is where DuckDB earns most of its speed on Parquet and Hive-partitioned data. The optimizer takes your `WHERE` clauses and shoves them as close to the scan operator as possible, skipping entire row groups or partition files that can't match. On a benchmark of 20 GB of Parquet data across 57 queries, DuckDB local with 8 threads delivered a warm median latency of 881 ms—roughly 3x faster than BigQuery at 2,775 ms and nearly 5x faster than Athena at 4,211 ms. Column pruning and predicate pushdown are doing most of that heavy lifting.

But pushdown has limits. Until v1.5.0, DuckDB couldn't push down filter expressions that might throw runtime errors. A query like `WHERE sqrt(column_0) < 0.001` on an 800-column Parquet file would bypass pushdown entirely, scanning all columns and taking 8.35 seconds where Polars finished the same single-threaded query in 500 ms. PR #20744 fixed this, but it's a good reminder that seemingly innocent filter expressions can silently disable the most valuable optimization in the engine.

Hive partition filters from JOIN conditions also didn't push down to file-level pruning until v1.5.0. Before that fix, a join that logically needed one partition file out of 455 would still scan 47 of them. Static literal filters always worked, but dynamically derived ones from joins did not. The fix via PR #19888 introduced file-level dynamic partition pruning for local filesystems—a significant improvement that dramatically reduces I/O for join-heavy pipelines over partitioned data.

## The v1.5.0 S3 Regression

So v1.5.0 brought real gains in partition pruning. It also introduced a painful regression for anyone reading Hive-partitioned Parquet from S3. The new hierarchical glob expansion discovers all files before applying partition filters. A setup that scanned 39 files in v1.4.4 now scans 122 in v1.5.0, issuing extra HTTP GET requests for Parquet footers of files it will ultimately discard. Creating a view over S3 hive-partitioned data went from under a second to over three minutes.

And the top-N window elimination pass made things worse for wide schemas on remote storage. A `QUALIFY ROW_NUMBER() OVER (...) = 1` query that took 81 GET requests and 11.6 seconds in v1.4.4 ballooned to 4,214 GETs and 31.5 seconds in v1.5.0. The rewrite creates a double-scan plan: one lightweight scan to identify winning rows, then a full-column scan to materialize them. On local disk that's fine. Over S3 with 90 columns, it means thousands of individual HTTP requests per column chunk per file.

The workaround is a combination of two settings: `SET disabled_optimizers = 'top_n_window_elimination';` and `SET s3_allow_recursive_globbing = false;`. Together they restore v1.4.4 performance almost exactly—82 GETs, 11.5 seconds. This is the kind of thing that doesn't show up in TPC-H benchmarks but absolutely burns you in production.

## CTE Materialization and Column Pruning

DuckDB switched CTE materialization to the default behavior in v1.4.0 via PR #17459. That's a reasonable default—materializing a CTE that's referenced multiple times avoids redundant computation. The problem is that materialization creates a barrier that prevents column pruning from reaching through. A CTE selecting all 50 columns from a table, referenced twice but needing only 2 columns each time, will materialize all 50. On a 50-million-row table, this caused a 100x slowdown: 0.3 seconds in v1.3.2 ballooned to 31.6 seconds in v1.4.4. Narrow your CTE projections explicitly. Don't rely on the optimizer to prune through materialization boundaries.

## Memory and Disk Space

DuckDB's memory allocator—jemalloc on Linux, mimalloc elsewhere—keeps freed memory in a pool for reuse rather than returning it to the OS immediately. This isn't a leak, but it looks like one in long-running processes. You can cap the budget with `SET memory_limit = 'XGB';` and enable disk spill with `PRAGMA temp_directory = '/tmp/duckdb';`.

Disk space reclamation is a genuine gap. `VACUUM FULL` isn't implemented. `DROP TABLE` doesn't shrink the file. `CHECKPOINT` doesn't reclaim dead blocks. A database with 26% dead space just stays that size. The workaround is `COPY FROM DATABASE source TO target`, which can reduce a 1.26 GB file to 256 MB—but it's a full rewrite, not an in-place compaction. This is simpler than a proper vacuum implementation, but it requires downtime and enough disk for two copies of your data.

## Practical Takeaways

Keep your CTE projections narrow. Watch for filter pushdown failures on expressions that can throw errors. If you're on v1.5.0 reading from S3, test with `s3_allow_recursive_globbing = false` and consider disabling `top_n_window_elimination` for wide tables. And profile with `EXPLAIN ANALYZE`—the number of files scanned and row groups touched tells you more about real-world performance than wall-clock time alone.
