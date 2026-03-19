# DuckDB Window Functions and Analytical Queries: What Works, What Breaks, and Why It Matters

Window functions sit at the heart of analytical SQL. They let you compute rankings, running totals, and inter-row comparisons without collapsing your result set—something that `GROUP BY` cannot do. DuckDB, the embedded columnar database that has been gaining traction for local data analysis, ships with a full suite of window functions and several optimizations that push them beyond what most embedded databases attempt. But those optimizations come with sharp edges. This post walks through DuckDB's window function machinery, explores the `QUALIFY` clause as a filtering tool, and digs into real performance pitfalls that users have encountered in production.

## The Basics: Partitions, Ordering, and Frames

A window function operates over a set of rows related to the current row. The `PARTITION BY` clause splits rows into groups, `ORDER BY` sequences them within each group, and the frame specification (e.g., `ROWS BETWEEN 3 PRECEDING AND CURRENT ROW`) constrains which rows contribute to each computation.

DuckDB supports the standard window functions you would expect: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`, `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, and aggregate functions like `SUM()`, `AVG()`, and `COUNT()` used in a windowed context. It also offers a `FILL()` executor for null-gap interpolation within partitions—a less common extension that simplifies time-series cleanup.

One important semantic detail trips up newcomers: `LAG()` and `LEAD()` do not respect window frame specifications. If you write:

```sql
SELECT ts,
       lag(ts) OVER w AS ts_lag,
       array_agg(ts) OVER w AS window_values
FROM events
WINDOW w AS (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW);
```

The `array_agg` correctly restricts its input to rows within 15 minutes, but `lag` ignores the range entirely and simply returns the previous row in partition order. This matches the SQL standard—navigation functions like `LAG` and `LEAD` operate on partition ordering, not on the frame—but it diverges from what many analysts intuitively expect. If you need frame-aware lookups, you can specify an explicit secondary ordering within the function call itself, or use a workaround involving `FIRST_VALUE` with the appropriate frame.

## QUALIFY: Filtering on Window Results

DuckDB supports the `QUALIFY` clause, borrowed from Teradata's SQL dialect, which lets you filter rows based on window function results without nesting subqueries. Instead of writing:

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

The syntax is cleaner, and for simple deduplication tasks, it reads almost like plain English. But there is a subtlety in evaluation order that catches people off guard. Window functions inside `QUALIFY` are evaluated against the full dataset *before* the predicate is applied. When you chain multiple window conditions with `AND`, the intersection of those conditions can produce surprising results.

Consider filtering rows that have at least five distinct prices within both their `item_id` and `product_id` partitions. Each window function independently computes its count over the full input. After the `QUALIFY` predicate removes rows that fail either condition, the surviving rows might no longer satisfy the count threshold when you re-examine them—because some contributing rows were eliminated by the other condition. This is not a bug; it follows directly from the evaluation model. But if you need post-filter guarantees, you may need to apply the conditions in stages using CTEs.

## Under the Hood: Segment Trees and Optimization

Internally, DuckDB evaluates window aggregates using a segment tree data structure. The segment tree pre-computes partial aggregates over contiguous blocks of rows, enabling sub-linear computation of sliding window aggregates. For a frame that shifts one row at a time, a naive approach recomputes the entire aggregate from scratch for every output row. The segment tree reduces this to logarithmic time per row by combining cached partial results. DuckDB selects the appropriate evaluation strategy based on the function type and frame specification—constant aggregators for fixed frames, segment trees for variable frames, and specialized executors for value functions like `FIRST_VALUE` and `NTH_VALUE`.

The more aggressive optimization is the TopN Window Elimination pass, introduced in version 1.5.0. When the optimizer detects a pattern like `QUALIFY ROW_NUMBER() OVER (PARTITION BY x ORDER BY y DESC) = 1`, it rewrites the window computation into a grouped aggregate using `arg_max` (or `arg_min` for ascending order). Instead of sorting every partition to assign row numbers and then discarding all but the first, it computes the extremal value directly via a hash aggregate. For single-row lookups, this can be substantially faster because it avoids the full sort.

However, this rewrite has a cost. For data stored on remote filesystems like S3, the rewritten plan may require two scans of the underlying data: one lightweight scan to identify the winning rows per group, and a second scan to retrieve all requested columns for those rows. Users querying wide Parquet files on S3 discovered that what was an 80-request, 12-second query in version 1.4 became a 4,200-request, 32-second query after upgrading. Each column chunk in each row group of each file triggered a separate HTTP range request, and the TLS handshake and authentication overhead per request dominated the runtime.

For queries with `QUALIFY rn <= N` where N is larger than the typical group size, the optimization also introduces a memory allocation problem. The rewritten aggregate pre-allocates N slots per group upfront. If most groups contain only three rows but N is 50, the remaining 47 slots per group waste memory. On large datasets, this can cause out-of-memory failures that the original window-based plan would not trigger.

Both issues can be worked around with a single setting: `SET disabled_optimizers = 'top_n_window_elimination';`. Users who rely on remote storage or who filter with generous limits should test with this flag after upgrading.

## CTE Materialization and Column Pruning

Another optimizer interaction worth understanding involves Common Table Expressions. Starting in version 1.4.0, DuckDB began materializing CTEs by default. Materialization means the CTE result is computed once and stored, then referenced wherever the CTE appears. This is beneficial when a CTE is used multiple times in a query, but it introduces an optimization barrier: the materializer captures all columns from the CTE definition, even if downstream references only need a subset.

For wide tables, this can cause dramatic slowdowns. A query that selects two columns from a 50-column CTE may scan and materialize all 50 columns, when inlining the CTE would have allowed the optimizer to prune the unneeded 48. One user reported a 100x regression—31 seconds versus 0.3 seconds—on a 50-million-row table after upgrading. The fix is to explicitly select only needed columns within the CTE definition, or to mark the CTE as not materialized using DuckDB's syntax extensions when your CTE is referenced only once.

## Practical Guidance

Window functions in DuckDB are powerful enough for serious analytical workloads running on a single machine. A few principles will keep you out of trouble.

First, remember that navigation functions (`LAG`, `LEAD`, `FIRST_VALUE`) and ranking functions (`ROW_NUMBER`, `RANK`) do not all interact with frames the same way. Check the SQL standard semantics, not your intuition, when combining these with `RANGE` or `ROWS` frame specifications.

Second, if you are querying remote storage—S3, GCS, or HTTP endpoints—be deliberate about optimizer settings after major version upgrades. The TopN elimination rewrite can multiply your request count by orders of magnitude on wide datasets. Profile your S3 request logs before and after upgrading.

Third, keep CTEs narrow. Select only the columns you need inside the CTE body. This applies doubly when the CTE feeds into a window function, because the materialization barrier prevents the downstream window operator from signaling which columns it actually requires.

Finally, test `QUALIFY` conditions independently before combining them. The single-pass evaluation model means that intersecting multiple window predicates can produce results that look wrong but are semantically correct. If your filtering logic depends on post-filter counts, restructure the query into sequential CTE stages where each stage materializes and re-evaluates.

DuckDB continues to evolve rapidly, and its window function implementation reflects both ambition and the inevitable rough edges of aggressive optimization. Understanding the machinery beneath the SQL surface is what separates a query that runs in seconds from one that times out or runs out of memory.
