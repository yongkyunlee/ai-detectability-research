# Query Performance Optimization in DuckDB: What Works, What Breaks, and What to Watch Out For

DuckDB has earned its reputation as the go-to embedded analytical database. On standard benchmarks against cloud platforms like BigQuery and Athena, it regularly delivers sub-second results on datasets where those services take multiple seconds. In one community benchmark on 20 GB of Parquet data, DuckDB clocked an 881 ms median query time locally, compared to nearly 3 seconds on BigQuery and over 4 seconds on Athena. Those numbers are compelling, but they conceal a more nuanced reality. Getting peak performance out of DuckDB requires understanding how its optimizer reasons about your queries — and where that reasoning falls short.

## The Optimizer Pipeline

DuckDB processes queries through a multi-stage optimizer that applies a series of rewrite rules to the logical plan before generating a physical execution plan. The key stages relevant to performance are filter pushdown, column pruning, join ordering, common subexpression elimination, and several specialized rewrites for patterns like top-N window functions. Each of these stages operates on the plan tree independently, and their interactions create both powerful optimizations and surprising regressions.

The vectorized execution engine sits at the bottom of this stack, processing data in batches that fit within CPU cache lines rather than one row at a time. This design means that the optimizer's primary job is not just choosing a good join order — it is minimizing how much data ever reaches the execution engine in the first place.

## Filter Pushdown: Power and Limitations

The most impactful optimization DuckDB performs is filter pushdown. When you write a WHERE clause, the optimizer attempts to move that predicate as close to the data source as possible. For Parquet files, this means the filter can prune entire row groups based on min/max statistics stored in the file metadata. For hive-partitioned datasets on S3, it means skipping files entirely based on partition key values embedded in directory paths.

This works beautifully for straightforward predicates. A query filtering on a partition column with a literal value gets resolved at planning time, and only the relevant files are ever opened. But the optimizer draws a hard line at expressions that could throw runtime errors. A filter like `WHERE sqrt(column_0) < 0.001` will not be pushed down, because `sqrt` could fail on negative inputs. DuckDB prioritizes correctness over speed here — it refuses to evaluate a function that might error before confirming the row should be processed at all.

The practical cost of this conservatism is steep on wide tables. On a dataset with 780 columns and 800,000 rows, a query filtering on a single column through an error-prone expression can scan every column in the file, taking over 8 seconds where a tool like Polars finishes in 500 ms. The fix is straightforward once you know the pattern: restructure the query to separate the filter from any potentially-throwing function, or pre-filter in a subquery using safe predicates.

Scalar macros introduce another blind spot. A filter defined through a user macro does not get recognized as a pushdown candidate during partition pruning. A query using `WHERE [year, month] IN get_hives()` will scan every row in the dataset, while the equivalent query using a pre-computed variable or temporary table completes after touching only a handful of files. The optimizer cannot evaluate the macro early enough to apply dynamic partition pruning, so the filter only takes effect after the data has already been read.

## Column Pruning and the CTE Materialization Trade-Off

DuckDB's unused column elimination pass walks the plan tree and removes references to columns that no downstream operator needs. This is essential for Parquet workloads, where each column is stored independently — reading 2 columns out of 50 means touching a fraction of the data on disk.

But column pruning interacts poorly with common table expression materialization. In recent versions, DuckDB made CTE materialization the default behavior. When a CTE is materialized, its entire result set is computed and stored before any downstream operators access it. This prevents column pruning from propagating through the CTE boundary. If your CTE selects 50 columns but the outer query only needs 2, the engine still materializes all 50.

The performance impact is dramatic. On a table with 50 million rows and 50 columns, a materialized CTE that passes through all columns before the outer query selects two of them can run 100 times slower than the equivalent inlined version. The optimizer treats the materialized CTE as an opaque block — it cannot look inside to determine which columns will actually be used downstream.

The trade-off is real: materialization prevents redundant computation when a CTE is referenced multiple times. But for single-reference CTEs that serve purely as organizational constructs, the cost is significant. The workaround is to explicitly limit the columns selected within the CTE definition, or to avoid CTEs altogether for pass-through queries on wide tables.

This issue compounds across UNION ALL boundaries. When materialized CTEs feed into a UNION ALL, column pruning breaks down further, and the optimizer cannot eliminate unused columns from any branch of the union. The slowdown scales linearly with table width — five extra unused columns might cost you a 2x penalty, while 80 extra columns can push it past 20x.

## Remote Storage: Where Optimizations Meet Reality

DuckDB's optimizer was designed for local data. When queries target S3 or other remote storage, every optimization decision carries network cost. A single unnecessary file access that takes microseconds locally translates to a full HTTP round-trip over the network.

The top-N window elimination optimization illustrates this tension perfectly. When DuckDB detects a `ROW_NUMBER() OVER (...) <= 1` pattern, it rewrites the plan into an aggregate-based approach using `arg_max` with a hash group-by and semi join. This rewrite is clever — it avoids sorting the entire dataset. But it requires scanning the data source twice: once to identify the winning rows, and once to fetch all their columns.

On local storage, the second scan is effectively free since the data is already in the OS page cache. On remote storage with wide Parquet files, each column chunk in each row group of each file generates a separate HTTP range request. For a dataset with 39 files and 90 columns, this second pass alone can generate over 4,000 GET requests. One community report documented query time jumping from 11 seconds to over 31 seconds between versions, with HTTP request counts increasing from 80 to 4,200.

Disabling the optimization with `SET disabled_optimizers = 'top_n_window_elimination'` reverts to a single-pass window scan plan that is dramatically faster for remote data. Alternatively, wrapping the scan in a materialized CTE forces the engine to read the data once and reuse it, sidestepping the double-scan behavior.

Hive partition discovery introduces another remote storage pitfall. DuckDB's file discovery mechanism can enumerate all files in a partitioned dataset before applying partition filters. On a dataset with hundreds of partitions, this means issuing LIST requests for every partition directory before pruning to the handful of directories that match the filter. Setting `s3_allow_recursive_globbing` to false constrains the discovery to match the partition structure hierarchically, avoiding the enumeration overhead.

## Memory Pressure Points

DuckDB's memory management generally works well for analytical workloads, but specific patterns can cause unexpected pressure.

Partitioned writes to remote storage hold all partition writers open simultaneously, each buffering uncompressed data in memory. Writing a modestly-sized table with 30 partitions to S3 can exhaust a 2 GB memory limit even when the raw data is small. The memory cost is proportional to the number of active partitions multiplied by the buffer size per writer, not the total data volume. Processing partitions sequentially — writing one partition at a time in a loop — trades speed for memory stability.

The top-N window rewrite also creates memory issues through its aggregation strategy. The `arg_min_max_n` aggregate pre-allocates slots based on the N value in the QUALIFY clause. A `QUALIFY rn <= 50` pre-allocates 50 slots per group regardless of actual cardinality. When most groups have only 1 or 2 rows, the wasted allocation compounds across hundreds of thousands of groups and can trigger out-of-memory errors under tight limits.

## Storage Compaction: The Missing Piece

DuckDB currently lacks a built-in mechanism for reclaiming disk space after deletions. Dropping a table marks its storage blocks as reusable internally, but the database file does not shrink. Repeated INSERT OR REPLACE and DELETE cycles can leave 25-30% of the file as dead space. The VACUUM command exists but performs no compaction, and VACUUM FULL is not implemented.

The community workaround is to export the entire database through an in-memory connection using COPY FROM DATABASE, producing a fresh file without any dead blocks. This approach works — one report showed an 80% size reduction — but requires enough free disk space to hold the complete copy during the operation.

## Practical Guidance

Knowing where DuckDB's optimizer excels and where it stumbles translates directly into faster queries.

For local analytical work, DuckDB's defaults are generally excellent. The vectorized engine, automatic parallelism, and aggressive filter pushdown handle most workloads without tuning. The main thing to watch is CTE materialization on wide tables — prefer explicit column lists within CTE definitions or use subqueries when only a few columns are needed downstream.

For remote storage, the picture changes considerably. Evaluate whether advanced rewrites like top-N window elimination help or hurt by checking the query plan with EXPLAIN ANALYZE. Use partition-aware query patterns that let the optimizer apply filters before file discovery. And keep an eye on file counts — DuckDB's per-file overhead is low locally but significant over HTTP.

For memory-constrained environments, be cautious with partitioned writes and large window operations. Both can create allocation patterns that scale with factors other than data volume, catching users off guard when workloads that fit comfortably in RAM on one axis exceed limits on another.

DuckDB is fast, often remarkably so. But its speed comes from an optimizer that makes strong assumptions about storage locality and data access patterns. When those assumptions hold, it is difficult to beat. When they do not, understanding the specific optimization that is working against you — and knowing how to disable or work around it — is the difference between a query that finishes in seconds and one that never completes at all.
