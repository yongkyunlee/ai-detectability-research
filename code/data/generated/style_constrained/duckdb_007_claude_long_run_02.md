# DuckDB Window Functions: What Works, What Breaks, and What the Optimizer Does Behind Your Back

Window functions are the backbone of analytical SQL. They let you compute rankings, running totals, and cross-row comparisons without collapsing your result set into grouped aggregates. DuckDB handles them well. But there are sharp edges you'll hit in production, especially after v1.5.0 introduced aggressive optimizer rewrites that change how your window queries actually execute.

I want to walk through DuckDB's window function support from the perspective of someone writing real queries against real data. We'll cover the execution model, the QUALIFY syntax that saves you a subquery, the new top-N window elimination optimizer, and several gotchas that have caught people off guard in recent releases.

## The Basics: What DuckDB Gives You

DuckDB supports the full SQL standard window function repertoire. Ranking functions like ROW_NUMBER, RANK, DENSE_RANK, NTILE, PERCENT_RANK, and CUME_DIST all work as expected. Value functions include FIRST_VALUE, LAST_VALUE, NTH_VALUE, LAG, and LEAD. And any aggregate function - SUM, AVG, MIN, MAX, COUNT, even QUANTILE and MODE - can be used as a window function by appending an OVER clause.

Frame specifications are flexible. You get ROWS BETWEEN, RANGE BETWEEN, and GROUPS BETWEEN, plus the EXCLUDE clause for fine-grained control over which rows participate in the computation. DuckDB also supports named window definitions through the WINDOW clause, which is underused but genuinely helpful for readability when a query has multiple window functions sharing the same partitioning logic.

Here's what that looks like in practice:


SELECT
    l_extendedprice,
    l_partkey,
    l_orderkey,
    SUM(l_extendedprice) OVER (PARTITION BY l_partkey ORDER BY l_orderkey) AS running_total,
    SUM(l_extendedprice) OVER (PARTITION BY l_partkey ORDER BY l_orderkey DESC) AS reverse_total
FROM lineitem
ORDER BY l_partkey, l_orderkey;


DuckDB's window fusion optimization kicks in here. When multiple window functions share compatible PARTITION BY clauses but differ in ORDER BY, the engine can sort the data once and derive multiple window results from that single pass. The `test_window_fusion.test` in DuckDB's test suite verifies exactly this pattern - combining partitioned and unpartitioned windows over the same data with different orderings, confirming that the engine fuses prefix-compatible sorts rather than re-sorting for each function.

## Streaming Windows: The Fast Path

Not every window function requires materializing the entire partition. DuckDB recognizes a class of "streaming" window functions that can be computed in a single pass without buffering all rows. ROW_NUMBER over an empty OVER() clause is the canonical example. So are RANK, DENSE_RANK, and PERCENT_RANK without ORDER BY. LAG and LEAD with constant offsets also qualify for streaming execution.

The optimizer emits a STREAMING_WINDOW physical operator for these cases instead of the full WINDOW operator. Running aggregates with `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` frames - like a running SUM or COUNT - are also streamable. This matters for performance. A streaming window doesn't need to buffer the entire partition into memory before producing output, which reduces both memory pressure and latency to first row.

There's a subtlety here though. FIRST_VALUE with IGNORE NULLS over a running frame can be streamed. FIRST_VALUE with IGNORE NULLS over a full partition frame cannot, because the engine needs to see all rows before it can determine which non-null value comes first in the frame. The test suite explicitly verifies this distinction - the EXPLAIN output either matches or fails to match the `STREAMING_WINDOW` pattern depending on the frame specification.

## QUALIFY: The Clause You Should Be Using

DuckDB supports the QUALIFY clause, which filters rows after window functions are evaluated. This is a huge ergonomic win. Without it, you'd need a subquery or CTE just to filter on a window function's output.


SELECT *
FROM metrics m
WHERE m.k = t.k
QUALIFY ROW_NUMBER() OVER (PARTITION BY m.k ORDER BY m.tm DESC) <= 3;


That's equivalent to wrapping the whole thing in a CTE, computing `rn`, and filtering `WHERE rn <= 3`. But it's one query. Less nesting, less noise. The DuckDB benchmark suite uses this pattern extensively - the `topn_window_elimination.benchmark` file tests exactly this with a 10-million-row metrics table and a 100-key tags table.

QUALIFY also works with multiple window conditions. You can write something like `QUALIFY COUNT(DISTINCT price) OVER (PARTITION BY item_id) >= 5 AND COUNT(DISTINCT price) OVER (PARTITION BY product_id) >= 5`. But be aware: both window functions are computed *before* the QUALIFY predicate filters rows. The intersection of two QUALIFY conditions can reduce the distinct count below your threshold for groups that narrowly passed each individual filter. This is correct SQL semantics, not a bug - but it trips people up.

## The Top-N Window Elimination Optimizer: Faster, Except When It Isn't

Here's where things get interesting. DuckDB v1.5.0 introduced the `top_n_window_elimination` optimizer rule. The idea is straightforward: when you write `ROW_NUMBER() OVER (PARTITION BY x ORDER BY y) = 1` and filter on it, the optimizer can rewrite the window function into an `arg_max` aggregate with a GROUP BY. This avoids materializing the full window computation and can be significantly faster.

The rewrite transforms the plan from `TABLE_SCAN -> WINDOW -> FILTER` into `TABLE_SCAN -> HASH_GROUP_BY (arg_max) -> SEMI JOIN`. For local data, this is often a win. The benchmark file confirms the optimization compares favorably with equivalent LATERAL JOIN patterns.

But it has caused real problems for remote storage. One well-documented case (issue #21348) showed that a `QUALIFY ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) = 1` query against ~40 hive-partitioned Parquet files on S3 went from 81 HTTP GET requests in v1.4.4 to over 4,200 in v1.5.0. Wall clock time nearly tripled, from 11.6 seconds to 31.5 seconds. The rewritten plan requires scanning the remote files twice - once to identify the winning rows via the aggregate, and again to fetch all columns for those rows. Each column chunk in the second scan generates a separate HTTP range request. For a wide table with 90 columns, that's devastating.

The workaround is to either disable the optimizer entirely with `SET disabled_optimizers = 'top_n_window_elimination'` or wrap your scan in a `MATERIALIZED` CTE to force a single-pass plan:


WITH scanned AS MATERIALIZED (
    SELECT * FROM read_parquet('s3://bucket/data/*/*/data.parquet')
    WHERE partition_filter_conditions
)
SELECT *
FROM scanned
QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) = 1;


There's a second problem with this optimizer. When `QUALIFY rn <= N` uses a large N but the actual number of groups per partition is small, the rewrite to `arg_min_max_n(..., N)` pre-allocates N slots per group upfront. Issue #21431 demonstrated that with `QUALIFY rn <= 50` on data where the actual max rank per group was 3, memory usage tripled and exceeded the configured 1GB limit. The fix being discussed involves having the internal `BinaryAggregateHeap` allocate slots lazily instead of pre-allocating.

So here's the trade-off: the top-N window elimination is simpler and faster for local queries with narrow tables, but it gives you worse performance - sometimes dramatically worse - on wide schemas over remote storage. Know your data shape before relying on the default optimizer behavior.

## IGNORE NULLS: Powerful but Picky

DuckDB supports the IGNORE NULLS and RESPECT NULLS modifiers on FIRST_VALUE, LAST_VALUE, NTH_VALUE, LAG, and LEAD. This is genuinely useful for forward-filling sparse data. If you have a time series with intermittent NULL readings, `LAST_VALUE(reading IGNORE NULLS) OVER (ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` gives you the most recent non-null observation at each point.

The syntax applies only to window functions, not to regular aggregates or windowed aggregates. If you try `SUM(x IGNORE NULLS) OVER (...)`, DuckDB will reject it with `Parser Error: RESPECT/IGNORE NULLS is not supported for windowed aggregates`. That restriction is explicit in the parser.

One non-obvious behavior: `LAG(x, 0, default IGNORE NULLS)` is always the identity function. It returns the current row's value regardless of the IGNORE NULLS modifier. A LAG offset of zero doesn't look backward, so null-skipping logic doesn't apply. The test suite verifies this edge case.

## LAG, LEAD, and Window Frames: A Common Misconception

LAG and LEAD don't use window frames. This catches people. If you specify `LAG(ts) OVER (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW)`, the RANGE clause has no effect on what LAG returns. LAG always looks at the row that is exactly N positions before the current row in the partition ordering, regardless of the frame specification. The frame only constrains aggregate window functions like SUM, AVG, and ARRAY_AGG.

Issue #21330 documented this confusion clearly. A user expected `LAG(ts)` over a 15-minute range window to return NULL when the previous row was more than 15 minutes away. The `ARRAY_AGG` function over the same window correctly observed the range, but LAG didn't. This matches PostgreSQL's behavior - it's correct per the SQL standard. The workaround, as DuckDB contributor hawkfish suggested, is to use a secondary ordering: `LAG(ts ORDER BY ts)`.

## Performance Characteristics: Local vs. Remote

Community benchmarks provide useful context. One detailed comparison tested DuckDB against BigQuery and Athena across 57 queries on 20GB of financial time-series data in Parquet format. The window function category showed DuckDB Local (32 threads, 64GB RAM) completing in 947ms median, compared to 3,013ms for BigQuery and 5,389ms for Athena. That's roughly a 3-5x advantage.

But switch to remote storage and the picture changes. DuckDB reading from Cloudflare R2 hit 12,187ms median on window functions - an order of magnitude slower than local, and actually slower than BigQuery. Window functions require multiple passes over the data, and each pass over a remote file incurs network round-trip latency. For table scans and simple aggregations, the overhead is manageable (407ms vs. 208ms locally). For windows, it's not.

## Bugs to Watch in v1.5.0

The v1.5.0 release introduced several window-related regressions that are worth knowing about. A `ROW_NUMBER()` with multi-column `PARTITION BY` and a non-VARCHAR `ORDER BY` column can cause an internal error where the binder resolves a selected column's type from the ORDER BY column's type instead of its declared type (issue #21387). All four conditions - ROW_NUMBER specifically, multi-column partition, non-VARCHAR ordering column, and a WHERE filter on the window output - must be present to trigger it. Switching to RANK or DENSE_RANK works around it.

The `MIN`/`MAX` window functions with `PARTITION BY` also broke for PandasScan and CSV inputs in v1.5.0 (issue #21367), throwing a `NotImplementedException` about serialization. The workaround: add `ORDER BY NULL` to your window specification. This forces a different code path that avoids the serialization requirement.

## Practical Advice

Use QUALIFY generously - it's cleaner than nested CTEs for filtering on window results. Prefer named WINDOW clauses when you have three or more window functions sharing the same partition. Be deliberate about frame specifications; remember that LAG and LEAD ignore them entirely. Test with `EXPLAIN ANALYZE` before deploying window-heavy queries against remote Parquet data, especially on wide schemas. And if you're on v1.5.0, know where the `disabled_optimizers` setting lives: `SET disabled_optimizers = 'top_n_window_elimination'` is your escape hatch when the new optimizer makes things worse.

DuckDB's window function implementation is genuinely strong. Streaming execution, window fusion, and QUALIFY put it ahead of most embedded databases in analytical ergonomics. The rough spots are mostly optimizer regressions that the team is actively fixing. But you should understand the execution model well enough to recognize when the optimizer's choices don't suit your workload.
