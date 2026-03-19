# DuckDB Window Functions: What's Fast, What's Broken, and What You Need to Know

Window functions are one of the best reasons to pick SQL over imperative code for analytical work. They let you compute rankings, running totals, and comparisons across rows without collapsing your result set into aggregates. DuckDB handles them well - most of the time. But the v1.5.0 release introduced an optimizer rewrite that has caused real production headaches, and there are a few semantic traps that catch even experienced SQL writers off guard.

Here's what we've learned running DuckDB window functions against real-world datasets.

## The Basics: Why Window Functions Matter

If you've ever written a self-join to get the previous row's value, or grouped a query just to rank rows and then un-grouped it, you already know the pain window functions solve. DuckDB supports the full standard set: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, and aggregate functions like `SUM()`, `COUNT()`, and `MIN()` used with `OVER` clauses. You get `ROWS BETWEEN`, `RANGE BETWEEN`, and interval-based frames for timestamp columns. DuckDB also supports the `QUALIFY` clause, which is a huge ergonomic win - it lets you filter directly on window function results without needing a subquery or CTE wrapper.

A quick example of the `QUALIFY` pattern that's become extremely common in deduplication workflows:

```sql
SELECT *
FROM events
QUALIFY row_number() OVER (PARTITION BY user_id ORDER BY event_time DESC) = 1;
```

One line replaces what would otherwise be a CTE plus a `WHERE rn = 1` filter. It's clean. We use it everywhere.

## The TopN Optimizer: Clever Until It Isn't

DuckDB v1.5.0 shipped a new optimizer rule called `top_n_window_elimination`. The idea is smart: when the engine sees a `QUALIFY row_number() OVER (...) = 1` pattern, it rewrites the query plan to avoid materializing the full window computation. Instead of scanning, sorting, assigning row numbers, and then filtering, it converts the logic into an `arg_max` aggregate plus a `HASH_GROUP_BY` with a `SEMI JOIN`. For local data, this is often faster.

But the rewrite makes an assumption that doesn't hold for remote storage.

One user reported that a `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY max_date DESC) = 1` query on hive-partitioned Parquet files in S3 went from 81 HTTP GET requests in v1.4.4 to over 4,200 in v1.5.0. Wall-clock time nearly tripled - from 11.6 seconds to 31.5 seconds. The root cause: the rewritten plan scans the remote files twice. The first scan identifies winning rows using a lightweight column projection. The second scan fetches all columns for those rows. Each column chunk in each file triggers a separate HTTP range request.

For local SSDs, two scans is cheap. For S3, where every request carries TLS overhead, auth signing, and a network round-trip, it's catastrophic. With a 90-column schema across 39 Parquet files, those small range requests add up fast.

The workaround involves two settings:

```sql
SET disabled_optimizers = 'top_n_window_elimination';
```

Or, if you don't want to disable the optimizer globally, force a single scan with a `MATERIALIZED` CTE:

```sql
SET s3_allow_recursive_globbing = false;

WITH scanned AS MATERIALIZED (
    SELECT * FROM read_parquet('s3://bucket/data/*/*/data.parquet')
    WHERE last_day(make_date(year, month, 1)) >= DATE '2023-01-01'
)
SELECT *
FROM scanned
QUALIFY row_number() OVER (PARTITION BY id ORDER BY max_date DESC) = 1;
```

The optimizer implementation in `src/optimizer/topn_window_elimination.cpp` triggers its rewrite based purely on the logical pattern - `ROW_NUMBER` with a filter - without considering whether the underlying scan targets remote storage or a wide schema. This is the kind of optimization that's simpler to implement as a universal rewrite, but accounting for storage characteristics would give you a plan that doesn't regress by 50x on remote reads.

## Memory Pre-allocation and OOM

The same optimizer has a second problem. When you write `QUALIFY rn <= 50`, the rewrite converts the query to use `arg_min_max_n(..., 50)`, which pre-allocates 50 slots per group up front. If your data has 200,000 groups but each group only has 3 rows, you've pre-allocated 47 empty slots per group. On a 400,000-row dataset, this more than triples memory usage and can blow past a 1GB memory limit.

DuckDB's lead developer confirmed the fix: the `BinaryAggregateHeap` needs dynamic allocation instead of pre-allocation. That's a cleaner solution than limiting the optimization to small N values, since it reduces `arg_min_max_n` memory usage in general.

## The LAG/LEAD Frame Trap

Here's something that trips up even people who've written SQL for years. `LAG()` and `LEAD()` don't respect window frame specifications. This is actually per the SQL standard, and PostgreSQL behaves the same way - but it's surprising if you haven't hit it before.

Consider this query:

```sql
SELECT ts,
       lag(ts) OVER w AS ts_lag,
       array_agg(ts) OVER w AS window_values
FROM unnest(['2026-01-01T12:00:00Z', '2026-01-01T12:30:00Z',
             '2026-01-01T13:00:00Z']) t(ts)
WINDOW w AS (ORDER BY ts::timestamp
             RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW);
```

The `array_agg` correctly returns only rows within the 15-minute range. But `lag` ignores the frame entirely and returns the globally previous row. If your rows are 30 minutes apart, `lag` still gives you the prior row even though it falls outside the window frame.

The workaround is `lag(ts ORDER BY ts)`, which applies a secondary ordering. This catches people because the frame clause is right there, visually suggesting that all functions in the window respect it. They don't.

## Type Binding Bug in row_number()

Version 1.5.0 introduced a subtle binder bug with `row_number()`. When you combine a multi-column `PARTITION BY` with an `ORDER BY` on a non-VARCHAR column and then filter on the row number output, DuckDB incorrectly binds the selected column's type from the `ORDER BY` column's type instead of its actual declared type.

```sql
CREATE TABLE t (a VARCHAR, ts TIMESTAMP, k VARCHAR);

WITH deduped AS (
    SELECT k,
           row_number() OVER (PARTITION BY a, k ORDER BY ts DESC) AS rn
    FROM t
)
SELECT k FROM deduped WHERE rn = 1;
```

This throws: `INTERNAL Error: Failed to bind column reference "k" [N.1]: inequal types (VARCHAR != TIMESTAMP)`. All four conditions must be present - `row_number()` specifically (not `rank()`), multi-column `PARTITION BY`, non-VARCHAR `ORDER BY`, and a filter on the window output. Remove any one condition and the error disappears.

## Serialization Failures with PARTITION BY

Also in v1.5.0, window aggregate functions with `PARTITION BY` fail on non-Parquet data sources - CSV files and pandas DataFrames both trigger the error. The error message reads: `NotImplementedException: Logical Operator Copy requires serializable operators: PandasScan function cannot be serialized`.

A community-discovered workaround is dead simple: add `ORDER BY NULL` to the window spec.

```sql
-- Fails in 1.5.0
SELECT id, MIN(lastupdatedtime) OVER (PARTITION BY id) FROM base_data;

-- Works
SELECT id, MIN(lastupdatedtime) OVER (PARTITION BY id ORDER BY NULL) FROM base_data;
```

The underlying issue is that the optimizer tries to copy the logical operator tree for the rewrite, but scan functions for CSV and pandas sources don't implement serialization. Adding `ORDER BY NULL` changes the plan path enough to avoid the serialization step.

## Performance: Local vs. Remote

A community benchmark comparing DuckDB against BigQuery and Athena on 20GB of financial time-series Parquet data tells a clear story about where window functions shine and where they struggle. On the XL configuration (32 threads, 64GB RAM), DuckDB local completed window function queries in a median of 947ms. BigQuery took 3,013ms. Athena took 5,389ms.

But DuckDB reading from Cloudflare R2 hit 12,187ms for those same window queries - roughly 13x slower than local. Window functions require multiple passes over the data, and each pass means another round of network I/O. Aggregation queries, by contrast, only degraded from 382ms to 411ms over remote storage.

So the trade-off is this: DuckDB local is dramatically faster for window functions than any cloud warehouse, but DuckDB over remote storage can be slower than BigQuery for window-heavy workloads. If your analytics pipeline relies heavily on ranking and partitioned aggregates, keep the data local. If you can't, consider materializing intermediate results before applying windows.

## Practical Advice

After working through these issues, a few patterns have held up well.

First, test window-heavy queries after any DuckDB version upgrade. The v1.5.0 optimizer changes are a good reminder that optimizer rewrites can change query plans in ways that affect correctness and performance. Running `EXPLAIN ANALYZE` before and after an upgrade takes five minutes and can save you from a 50x regression.

Second, use `QUALIFY` freely for simple deduplication, but be aware that DuckDB evaluates windowed aggregates before applying the `QUALIFY` filter. If you're using `COUNT(DISTINCT ...)` in a `QUALIFY` clause, the distinct count reflects all rows, not the rows that survive the filter. This is expected behavior, but it's a common source of confusion.

Third, if you're querying remote Parquet files with wide schemas, the `top_n_window_elimination` optimizer can hurt. Either disable it or wrap your scan in a `MATERIALIZED` CTE. This forces DuckDB to scan the remote files once and operate on the cached result.

And fourth, remember that `LAG` and `LEAD` are peer-blind - they don't see your frame specification. If you need frame-aware access to adjacent rows, use `FIRST_VALUE` or `LAST_VALUE` with an explicit frame, or use the `ORDER BY` clause directly inside the function call.

DuckDB's window function implementation is architecturally solid - it uses segment trees for efficient range queries, supports streaming execution for simple cases like `LAG` without `PARTITION BY`, and handles distinct aggregates within windows. The v1.5.0 issues are optimizer-level problems, not fundamental engine limitations. They'll get fixed. But until they do, knowing the workarounds is the difference between a sub-second query and an OOM crash.
