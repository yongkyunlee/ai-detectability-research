# DuckDB Window Functions: What Backend Engineers Should Actually Know

DuckDB handles analytical SQL well. Really well. But its window function implementation has depth that most engineers gloss over, and a few sharp edges that'll bite you in production if you don't know where they are. I want to walk through the practical parts: what works, what's subtly broken, and where DuckDB's design choices force you to think differently about analytical queries.

## The Basics, Quickly

Window functions in DuckDB follow the SQL standard closely. You get the full set: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `NTILE()`, `LEAD()`, `LAG()`, plus aggregate functions like `SUM()`, `MIN()`, `MAX()`, and `COUNT()` used in a windowed context. DuckDB also supports `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, and statistical functions like `QUANTILE()` and `MEDIAN()` as window aggregates. Frame specifications support `ROWS`, `RANGE`, and `GROUPS` modes, all with the standard boundary keywords.

Nothing shocking there. The interesting stuff is in the details.

## QUALIFY: The Clause You Should Be Using

DuckDB supports `QUALIFY`, a filtering clause that runs after window function evaluation. This is borrowed from Teradata-style SQL and it eliminates the tedious subquery-wrapping pattern that plagues standard SQL.

Instead of this:

```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY cnt DESC) AS rn
    FROM counts
) sub
WHERE rn = 1
```

You write this:

```sql
SELECT *
FROM counts
QUALIFY ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY cnt DESC) = 1
```

Shorter. Clearer. One less level of nesting. We've adopted it as the default pattern for deduplication and top-N-per-group queries on our team. It works with named windows too, so you can define a window once and reference it in both your SELECT and QUALIFY clauses.

## LAG and LEAD Don't Respect Window Frames

This one catches people. If you define a `RANGE`-based window frame and then use `LAG()` inside it, the frame specification is silently ignored. `LAG` and `LEAD` operate on the entire partition regardless of what frame you've set.

A user reported this as a bug in DuckDB v1.5.0, setting up a window with `RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW` and expecting `LAG(ts)` to return NULL when the previous row fell outside that range. It didn't. The DuckDB maintainers confirmed this is expected behavior -- and Postgres does the same thing.

The workaround is to use the secondary ordering syntax: `LAG(ts ORDER BY ts)`. But honestly, this is one of those SQL standard design decisions that surprises everyone the first time. Other aggregates like `ARRAY_AGG()` do respect the frame, so the inconsistency feels wrong even though it's technically correct.

## Frame Types: ROWS vs RANGE

DuckDB supports three frame types, and picking the right one matters for both correctness and performance.

`ROWS BETWEEN` counts physical rows. It's simple and fast. `RANGE BETWEEN` works on logical value distances -- you can write things like `RANGE BETWEEN INTERVAL 3 DAYS PRECEDING AND CURRENT ROW` for time-series analysis. `GROUPS BETWEEN` operates on peer groups, which is handy when you need to aggregate across tied values.

The default frame depends on whether you specify an `ORDER BY`. With one, you get `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Without one, you get `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`. This default behavior is standard SQL but trips people up because the two defaults are meaningfully different. A `SUM() OVER (PARTITION BY x)` gives you a partition-level total. Add `ORDER BY` and it becomes a running sum. Same function, different semantics.

Under the hood, DuckDB uses segment trees for efficient range queries over window frames. The implementation includes multiple aggregation strategies -- a naive aggregator for small frames and a segment tree aggregator for larger ones. ROWS framing is simpler and generally faster, but RANGE gives you semantic correctness for time-series work. Pick ROWS when physical offsets are what you actually need.

## The TopN Optimization and Its Memory Problem

DuckDB's query optimizer can rewrite `QUALIFY rn <= N` patterns into `arg_min_max_n()` aggregates, skipping the full window computation. This is the TopN window elimination optimization, and it's clever. But as of the main development branch (commit `5f9e4101c1`), it has a memory pre-allocation problem.

The optimizer rewrites `QUALIFY rn <= 50` into an `arg_min_max_n(..., 50)` call. That function pre-allocates all 50 slots per group up front. If you have 200,000 groups but only 3 rows per group, you're allocating 47 empty slots per group for nothing. One user reported that this tripled memory usage past a 1GB limit, causing an OOM on a query that worked fine with the optimization disabled. The workaround is `SET disabled_optimizers = 'top_n_window_elimination'`. The DuckDB team has acknowledged that dynamic allocation in the `BinaryAggregateHeap` is the right fix, since it would reduce `arg_min_max_n` memory usage everywhere, not just in this specific case.

## Watch Out for v1.5.0 Regressions

DuckDB v1.5.0, released on March 9, 2026, introduced several window-related issues worth knowing about.

A `ROW_NUMBER()` bug surfaces when you combine multi-column `PARTITION BY`, an `ORDER BY` on a non-VARCHAR column, and a filter on the window output. The error message reads `INTERNAL Error: Failed to bind column reference "k": inequal types (VARCHAR != TIMESTAMP)`. Swapping to `RANK()` or `DENSE_RANK()` avoids it. So does using a single-column partition. The binder incorrectly resolves a column's type from the `ORDER BY` expression instead of the column's declared type.

There's also a serialization error with windowed `MIN`/`MAX`/`SUM` over CSV or pandas sources when you omit `ORDER BY`. The workaround is adding `ORDER BY NULL` to your window specification. Parquet files aren't affected -- only non-serializable scan functions like `PandasScan` trigger it.

## When to Reach for Window Functions

DuckDB's analytical SQL is strong enough that window functions should be your default tool for ranking, running aggregates, gap-and-island detection, and sessionization. The `QUALIFY` clause makes top-N-per-group patterns concise, and `IGNORE NULLS` support on `LAST_VALUE` and `FIRST_VALUE` handles forward-fill logic cleanly without procedural code.

But don't ignore the edges. Test with your actual data volumes -- the TopN optimization that saves CPU might blow your memory budget. Know that `LAG` and `LEAD` won't respect your carefully crafted `RANGE` frames. And if you're on v1.5.0, double-check any `ROW_NUMBER()` queries with composite partition keys.

DuckDB's window function implementation is mature and capable. It just rewards you for reading the fine print.
