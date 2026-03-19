# Query Performance Optimization in DuckDB

DuckDB query tuning is mostly about helping the engine do less work. The optimizer already applies many rewrites, including filter pushdown, join reordering, limit pushdown, row-group pruning, TopN conversion, late materialization, and statistics propagation. When a query is fast, it is usually because those rules reduce scanned columns, files, row groups, or full-table passes. When a query is slow, the query shape often blocked those reductions.

## 1. Optimize for less data movement, not clever SQL

DuckDB’s execution engine is vectorized, but vectorization alone does not save a query that reads too much data. The biggest wins come from three mechanisms:

- projection pushdown, so scans only read referenced columns
- filter pushdown and file pruning, so irrelevant files and row groups never enter the pipeline
- rewrites that avoid full sorts or unnecessary rescans

You can see those capabilities in the engine itself. Core table scans advertise projection pushdown, filter pushdown, filter pruning, sampling pushdown, and late materialization. Parquet scans expose the same broad shape.

The easiest mistake is to write a query that logically asks for a small result but physically forces a wide scan. A recent regression report showed exactly that pattern: a simple pass-through CTE over a 50-column table, referenced twice, turned from a narrow scan into a materialized 50-column scan and made the query roughly 100x slower. The lesson is straightforward: if a CTE becomes a materialization barrier, it can block column pruning even when the final query only needs two columns.

## 2. Write queries that preserve pushdown opportunities

In DuckDB, the best-performing query is often the one whose filters remain visible as literals or simple comparisons for as long as possible.

For example, TopN is a major optimization. If DuckDB sees `ORDER BY ... LIMIT`, it can replace a full sort with a `LogicalTopN` plan. The implementation even decides not to apply this rewrite when the limit is large relative to estimated cardinality, because a complete sort can be cheaper beyond that threshold. That is a good example of DuckDB’s pragmatism: it does not blindly apply “fancy” operators; it tries to pick the cheaper physical shape.

The same principle applies to file pruning over Parquet and hive-style partitions. Static filters on partition columns are especially valuable because they can shrink the file set before execution gets expensive. A useful pattern is:

```sql
SELECT *
FROM read_parquet('s3://bucket/data/year=*/month=*/*.parquet', hive_partitioning = true)
WHERE year = 2025 AND month IN (1, 2, 3);
```

That shape is optimizer-friendly. By contrast, if the partition filter is hidden behind a scalar macro or a subquery result, DuckDB may lose the chance to treat it as a file filter. One reported case scanned more than 309 million rows because a macro-produced list was evaluated too late; materializing the list first restored pruning.

Another subtle limit is semantic safety. DuckDB currently avoids pushing down filters built from expressions that can throw errors. A filter like `sqrt(column_0) < 0.001` may therefore force a much wider read than expected, even on Parquet, because `sqrt` can fail for negative values. If pushdown matters, prefer predicates whose semantics are safe to move into the scan.

## 3. Be careful with remote Parquet, especially on S3

Remote storage changes the cost model. On local SSD, an extra scan may be tolerable. On S3, thousands of extra HTTP requests can dominate runtime even when the total bytes read barely change.

One regression around `QUALIFY ROW_NUMBER() OVER (...) = 1` rewrote the query into an aggregate-plus-semi-join plan that scanned S3-hosted Parquet twice: once to identify winning rows and again to fetch the full row payload. On a wide schema, that led to more than 4,200 GET requests instead of about 80.

Hive partition handling showed a similar trade-off. In one 1.5.0 regression, DuckDB discovered all files under an S3 glob and only pruned afterward, so `EXPLAIN ANALYZE` reported `Scanning Files: 39/122` instead of `39/39`. The temporary workaround was to disable recursive globbing.

The practical guidance is:

- keep partition predicates explicit
- include partition keys in join conditions when they are logically part of the join
- be suspicious of rewrites that turn one remote scan into two
- treat `SELECT *` on wide remote Parquet as a cost amplifier

Community benchmark discussions in the context bundle reinforce the same point: DuckDB stays very competitive on Parquet, but cold remote queries pay a noticeable metadata and request overhead.

## 4. Use profiling as part of query development

DuckDB exposes profiling directly in the engine. `EXPLAIN ANALYZE` is the fastest way to inspect operator timing, while `PRAGMA enable_profiling` enables richer profiler output. In practice, the most useful signals are the plain plan annotations:

- `Projections`
- `Filters`
- `File Filters`
- `Scanning Files`
- `Total Files Read`

If a scan shows dozens of projected columns when you expected three, projection pruning failed. If `Scanning Files` barely drops after a partition predicate, file pruning failed. If a window query suddenly becomes a semi join plus a second scan, a rewrite changed the I/O pattern.

This is also the right way to decide whether an index will help. DuckDB can use ART indexes for selective lookups, but the current table-scan logic is intentionally conservative: it only supports limited index-scan shapes and explicitly notes missing support for compound ART scans and multi-filter intersection.

## 5. The practical checklist

For most DuckDB workloads, performance optimization reduces to a short checklist:

1. Project only the columns you need.
2. Keep predicates simple and visible to the optimizer.
3. Avoid unnecessary materialization barriers, especially wide CTEs.
4. Prefer static partition filters over derived ones when querying remote files.
5. Inspect `EXPLAIN ANALYZE` before and after every rewrite.

DuckDB is already packed with smart optimizations. The real skill is writing queries that let those optimizations fire. When that happens, DuckDB does not just run SQL correctly. It runs the cheaper physical plan.
