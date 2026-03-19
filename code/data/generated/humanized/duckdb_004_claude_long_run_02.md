# Query Performance in DuckDB: What Works, What Breaks, and What to Watch Out For

DuckDB has earned its spot as the go-to embedded analytical database. On standard benchmarks against cloud platforms like BigQuery and Athena, it regularly delivers sub-second results on datasets where those services take multiple seconds. One community benchmark on 20 GB of Parquet data had DuckDB clocking an 881 ms median query time locally, compared to nearly 3 seconds on BigQuery and over 4 seconds on Athena. Impressive numbers. But they hide a messier truth: getting peak performance requires understanding how its optimizer reasons about your queries, and where that reasoning falls short.

## The Optimizer Pipeline

DuckDB processes queries through a multi-stage optimizer that applies rewrite rules to the logical plan before generating a physical execution plan. The stages that matter most for performance are filter pushdown, column pruning, join ordering, common subexpression elimination, and a handful of specialized rewrites for patterns like top-N window functions. Each stage operates on the plan tree independently; their interactions create both powerful speedups and surprising regressions.

Underneath all of that sits the vectorized execution engine, processing data in batches sized to fit CPU cache lines rather than one row at a time. So the optimizer's primary job isn't just picking a good join order. It's about keeping as much data as possible from ever reaching the engine in the first place.

## Filter Pushdown: Power and Limitations

The single most impactful thing DuckDB does is filter pushdown. When you write a WHERE clause, the optimizer tries to shove that predicate as close to the data source as it can. For Parquet files, this means pruning entire row groups based on min/max statistics in file metadata. With hive-partitioned datasets on S3, it means skipping files entirely based on partition key values embedded in directory paths.

Straightforward predicates work beautifully. A query filtering on a partition column with a literal value gets resolved at planning time, and only the relevant files are ever opened. But the optimizer draws a hard line at expressions that could throw runtime errors. Something like `WHERE sqrt(column_0) < 0.001` won't be pushed down because `sqrt` could fail on negative inputs. DuckDB prioritizes correctness over speed here; it refuses to evaluate a function that might error before confirming the row should be processed at all.

The practical cost? Steep on wide tables. On a dataset with 780 columns and 800,000 rows, filtering on a single column through an error-prone expression can force a scan of every column in the file, taking over 8 seconds where Polars finishes in 500 ms. The fix is straightforward once you know the pattern: restructure the query to separate the filter from any potentially-throwing function, or pre-filter in a subquery using safe predicates.

Scalar macros are another blind spot. A filter defined through a user macro doesn't get recognized as a pushdown candidate during partition pruning. A query using `WHERE [year, month] IN get_hives()` will scan every row, while the same logic expressed with a pre-computed variable or temporary table completes after touching only a handful of files. The optimizer can't evaluate the macro early enough to prune partitions, so the filter only kicks in after everything has already been read.

## Column Pruning and the CTE Materialization Trade-Off

DuckDB's unused column elimination pass walks the plan tree and removes references to columns that no downstream operator needs. For Parquet workloads this matters a lot, since each column is stored independently; reading 2 columns out of 50 means touching a fraction of the data on disk.

Column pruning interacts poorly with CTE materialization, though. Recent versions made materialization the default behavior. When a CTE is materialized, its entire result set gets computed and stored before any downstream operators touch it. This blocks pruning from propagating through the CTE boundary. Your CTE selects 50 columns but the outer query only needs 2? The engine still materializes all 50.

The performance hit is dramatic. On a table with 50 million rows and 50 columns, a materialized CTE that passes through everything before the outer query picks two columns can run 100x slower than the inlined version. The optimizer treats it as an opaque block; it can't peek inside to figure out which columns actually get used downstream.

There's a genuine trade-off: materialization prevents redundant computation when a CTE is referenced multiple times. For single-reference CTEs that exist purely as organizational constructs, though, the cost is painful. Either limit columns in the CTE definition itself, or skip CTEs altogether for pass-through queries on wide tables.

This compounds across UNION ALL boundaries too. When materialized CTEs feed into a UNION ALL, pruning breaks down further, and unused columns can't be eliminated from any branch. The slowdown scales linearly with table width. Five extra unused columns might cost 2x; eighty can push it past 20x.

## Remote Storage: Where Things Get Interesting

DuckDB's optimizer was designed for local data. When queries target S3 or other remote storage, every decision carries network cost. A single unnecessary file access that takes microseconds locally becomes a full HTTP round-trip.

The top-N window elimination rewrite shows this tension well. When DuckDB detects a `ROW_NUMBER() OVER (...) <= 1` pattern, it rewrites the plan into an aggregate approach using `arg_max` with a hash group-by and semi join. Clever move, since it avoids sorting the entire dataset. But it requires scanning the source twice: once to identify the winning rows, once to fetch all their columns.

Locally, that second scan is basically free because the data lives in the OS page cache. Over the network with wide Parquet files, each column chunk in each row group of each file spawns a separate HTTP range request. For a dataset with 39 files and 90 columns, the second pass alone can generate over 4,000 GET requests. One community report documented query time jumping from 11 to 31 seconds between versions, with HTTP requests ballooning from 80 to 4,200. Honestly, that surprised me when I first read it.

You can disable this with `SET disabled_optimizers = 'top_n_window_elimination'`, which reverts to a single-pass window scan that's dramatically faster for remote data. Wrapping the scan in a materialized CTE also works, forcing a single read and sidestepping the double-scan.

Hive partition discovery is another pitfall worth knowing about. DuckDB's file discovery can enumerate all files in a partitioned dataset before applying partition filters. With hundreds of partitions, this means issuing LIST requests for every directory before pruning to the handful that actually match. Setting `s3_allow_recursive_globbing` to false constrains discovery to follow the partition structure hierarchically, which avoids that overhead.

## Memory Pressure Points

Memory management generally works fine for analytical workloads. Specific patterns break it.

Partitioned writes to remote storage hold all partition writers open at once, each buffering uncompressed data. Writing a modestly-sized table with 30 partitions to S3 can exhaust a 2 GB memory limit even when the raw data is small. The cost scales with the number of active partitions multiplied by buffer size per writer, not total data volume. Processing them sequentially (one partition at a time) trades speed for stability.

The top-N window rewrite creates memory issues too, through its aggregation strategy. The `arg_min_max_n` aggregate pre-allocates slots based on the N value in the QUALIFY clause. A `QUALIFY rn <= 50` pre-allocates 50 slots per group regardless of actual cardinality. When most groups have 1 or 2 rows, that wasted allocation compounds across hundreds of thousands of groups and can trigger out-of-memory errors under tight limits.

## Storage Compaction: The Missing Piece

DuckDB currently has no built-in way to reclaim disk space after deletions. Dropping a table marks its storage blocks as reusable internally, but the file itself doesn't shrink. Repeated INSERT OR REPLACE and DELETE cycles can leave 25-30% of the file as dead space. VACUUM exists but does nothing for compaction, and VACUUM FULL isn't implemented.

The workaround is exporting the entire database through an in-memory connection using COPY FROM DATABASE, producing a fresh file without dead blocks. It works (one report showed an 80% size reduction) but you'll need enough free disk space for the complete copy during the operation.

## What I'd Actually Recommend

Here's where all of this turns into practical advice.

For local analytical work, DuckDB's defaults are generally excellent. The vectorized engine, automatic parallelism, and aggressive filter pushdown handle most workloads without tuning. Just watch CTE materialization on wide tables; prefer explicit column lists inside CTE definitions or use subqueries when only a few columns are needed downstream.

Remote storage changes the picture. Check whether advanced rewrites like top-N window elimination help or hurt by inspecting the plan with EXPLAIN ANALYZE. Write partition-aware queries that let filters apply before file discovery, and keep an eye on file counts; per-file overhead is low locally but adds up fast over HTTP.

In memory-constrained environments, be cautious with partitioned writes and large window operations. Both create allocation patterns that scale with factors other than data volume; workloads that fit comfortably in RAM on one dimension can blow past limits on another.

DuckDB is fast. Often startlingly so. But that speed comes from an optimizer making strong assumptions about storage locality and access patterns. When those hold, it's hard to beat. When they don't, I think understanding which specific rewrite is working against you (and knowing how to turn it off) makes all the difference.
