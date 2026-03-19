# DuckDB Window Functions and Analytical Queries: What Works, What Breaks, and Why It Matters

Window functions sit at the heart of analytical SQL. They let you compute rankings, running totals, and inter-row comparisons without collapsing your result set into grouped summaries, something `GROUP BY` simply can't do. DuckDB, the embedded columnar database that's been picking up steam for local data analysis, ships with a full suite of them plus several performance tricks that go beyond what most embedded databases even attempt. But those tricks come with sharp edges. This post walks through DuckDB's window function machinery, explores the `QUALIFY` clause, and digs into real performance pitfalls I've seen users hit in production.

## The Basics: Partitions, Ordering, and Frames

A window function operates over a set of rows related to the current row. `PARTITION BY` splits rows into groups, `ORDER BY` sequences them within each group, and the frame specification (e.g., `ROWS BETWEEN 3 PRECEDING AND CURRENT ROW`) constrains which rows contribute to each computation.

DuckDB supports the standard set you'd expect: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, and aggregate functions like `SUM()`, `AVG()`, and `COUNT()` used in a windowed context. There's also a `FILL()` executor for null-gap interpolation within partitions, a less common extension that makes time-series cleanup much simpler.

One semantic detail trips up newcomers: `LAG()` and `LEAD()` don't respect window frame specifications. If you write:

```sql
SELECT ts,
       lag(ts) OVER w AS ts_lag,
       array_agg(ts) OVER w AS window_values
FROM events
WINDOW w AS (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW);
```

The `array_agg` correctly restricts its input to rows within 15 minutes, but `lag` ignores the range entirely and just returns the previous row in partition order. This matches the SQL standard (navigation functions operate on partition ordering, not on the frame), but it diverges from what most analysts intuitively expect. The docs don't make this obvious. If you need frame-aware lookups, you can specify an explicit secondary ordering within the function call itself, or work around it using `FIRST_VALUE` with the appropriate frame.

## QUALIFY: Filtering on Window Results

DuckDB supports `QUALIFY`, borrowed from Teradata's SQL dialect, which lets you filter rows based on window function results without nesting subqueries. Instead of writing:

```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS rn
    FROM orders
) sub
WHERE rn = 1;
```

You can write:

```sql
SELECT *
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;
```

Cleaner. For simple deduplication, it reads almost like plain English. But there's a subtlety in evaluation order that catches people off guard.

The functions inside `QUALIFY` are evaluated against the full dataset *before* the predicate kicks in. When you chain multiple conditions with `AND`, the intersection can produce surprising results. Say you're filtering rows that have at least five distinct prices within both their `item_id` and `product_id` partitions. Each condition independently computes its count over the full input. After the predicate removes rows that fail either check, the surviving rows might no longer satisfy the count threshold if you were to re-examine them, because some contributing rows got eliminated by the other condition. Not a bug; it follows directly from the evaluation model. But if you need post-filter guarantees, you'll want to apply conditions in stages using CTEs.

## Under the Hood: Segment Trees and How Queries Get Rewritten

Internally, DuckDB evaluates window aggregates using a segment tree data structure. The segment tree pre-computes partial aggregates over contiguous blocks of rows, which enables sub-linear computation of sliding window aggregates. A naive approach would recompute the entire aggregate from scratch for every output row. The segment tree gets this down to logarithmic time per row by combining cached partial results. DuckDB picks the right evaluation strategy based on function type and frame specification: constant aggregators for fixed frames, segment trees for variable frames, and specialized executors for value functions like `FIRST_VALUE` and `NTH_VALUE`.

The more aggressive trick is the TopN Window Elimination pass, introduced in version 1.5.0.

When the query planner detects a pattern like `QUALIFY ROW_NUMBER() OVER (PARTITION BY x ORDER BY y DESC) = 1`, it rewrites the window computation into a grouped aggregate using `arg_max` (or `arg_min` for ascending order). Instead of sorting every partition to assign row numbers and then discarding all but the first, it computes the extremal value directly via a hash aggregate. For single-row lookups this can be way faster because it skips the full sort.

There's a cost, though. For data on remote filesystems like S3, the rewritten plan may require two scans of the underlying data: one lightweight scan to identify winning rows per group, and a second to retrieve all requested columns for those rows. Users querying wide Parquet files on S3 discovered that what was an 80-request, 12-second query in version 1.4 turned into a 4,200-request, 32-second query after upgrading. Each column chunk in each row group of each file triggered a separate HTTP range request, and TLS handshake plus authentication overhead per request dominated the runtime. Honestly, that kind of regression surprised me.

There's also a memory problem with `QUALIFY rn <= N` where N is larger than the typical group size. The rewritten aggregate pre-allocates N slots per group upfront. If most groups contain only three rows but N is 50, those remaining 47 slots per group waste memory. On large datasets this can cause out-of-memory failures that the original window-based plan wouldn't trigger.

Both issues have the same workaround: `SET disabled_optimizers = 'top_n_window_elimination';`. If you rely on remote storage or filter with generous limits, test with this flag after upgrading.

## CTE Materialization and Column Pruning

Another query planner interaction worth knowing about involves Common Table Expressions. Starting in version 1.4.0, DuckDB began materializing CTEs by default. That means the CTE result is computed once and stored, then referenced wherever it appears. Good when a CTE shows up multiple times in a query. Bad because it introduces a barrier: the materializer captures all columns from the CTE definition, even if downstream references only need a subset.

For wide tables, this gets ugly fast. A query that selects two columns from a 50-column CTE may scan and store all 50, when inlining it would've let the planner prune the unneeded 48. One user reported a 100x regression (31 seconds vs. 0.3 seconds) on a 50-million-row table after upgrading. The fix is to explicitly select only the columns you need within the CTE definition, or mark the CTE as not materialized using DuckDB's syntax extensions when it's only referenced once.

## Practical Guidance

Window functions in DuckDB are strong enough for serious analytical work on a single machine, but a few things will keep you out of trouble.

Navigation functions like `LAG`, `LEAD`, and `FIRST_VALUE` don't all interact with frames the same way ranking functions do. Check the SQL standard semantics, not your intuition, when combining these with `RANGE` or `ROWS` frame specifications. I think this is the single most common source of confusion I've seen in DuckDB questions online.

If you're querying remote storage (S3, GCS, HTTP endpoints), be deliberate about query planner settings after major version upgrades. The TopN elimination rewrite can multiply your request count by orders of magnitude on wide datasets; profile your S3 request logs before and after upgrading. Keep your CTEs narrow, too. Select only the columns you need inside the CTE body, and this goes double when it feeds into a window function because the materialization barrier prevents the downstream operator from signaling which columns it actually requires.

Test `QUALIFY` conditions independently before combining them. The single-pass evaluation model means intersecting multiple window predicates can produce results that look wrong but are semantically correct. If your filtering logic depends on post-filter counts, restructure into sequential CTE stages where each stage materializes and re-evaluates.

DuckDB evolves fast, and its window function implementation shows both ambition and the inevitable rough edges of aggressive query rewrites. Knowing what's happening beneath the SQL surface is what separates a query that finishes in seconds from one that times out.
