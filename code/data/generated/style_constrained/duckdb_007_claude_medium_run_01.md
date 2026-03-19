# Window Functions in DuckDB: What You Actually Need to Know

DuckDB handles window functions differently than most databases you've probably worked with. The engine doesn't just bolt on window evaluation as an afterthought - it treats analytical queries as first-class citizens in its optimizer and execution pipeline. I want to walk through the features that matter and the optimizations worth understanding if you're doing any serious analytical work.

## The Basics, Quickly

Window functions let you compute values across sets of rows related to the current row without collapsing them into groups. DuckDB supports the full SQL standard here: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LEAD()`, `LAG()`, `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, and all the usual aggregate functions - `SUM()`, `COUNT()`, `AVG()`, `MIN()`, `MAX()` - used in a windowed context.

The syntax is standard SQL. You get `PARTITION BY` for splitting data into groups, `ORDER BY` for defining row ordering within those groups, and frame specifications with `ROWS`, `RANGE`, or `GROUPS` modes. All three frame types work. That sounds obvious, but some engines still don't fully support `GROUPS` mode frames, which let you define boundaries by peer groups rather than individual rows or value ranges.

DuckDB also supports the `EXCLUDE` clause in frame specifications - `EXCLUDE NO OTHERS`, `EXCLUDE CURRENT ROW`, `EXCLUDE GROUP`, and `EXCLUDE TIES`. We don't see this used often, but it's there when you need precise control over which rows participate in the window calculation.

## QUALIFY: The Clause You Should Be Using

If you're still wrapping window functions in subqueries just to filter on their results, stop. DuckDB supports `QUALIFY`, which filters rows after window function evaluation. This eliminates a whole layer of nesting.

Instead of this:


SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY student ORDER BY mark DESC) AS rn
  FROM exam
) WHERE rn = 1


You write:


SELECT * FROM exam
QUALIFY ROW_NUMBER() OVER (PARTITION BY student ORDER BY mark DESC) = 1


Same result, less noise. And you can combine `QUALIFY` with named windows - `WINDOW w AS (ORDER BY mark)` - then reference `w` in both the select list and the qualify clause. This keeps complex analytical queries readable when you're stacking multiple window functions on the same frame.

## Streaming Windows

DuckDB recognizes when a window function doesn't actually require sorting or partitioning the full dataset. An unpartitioned cumulative sum - `SUM(x) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` - gets executed as a streaming operation. The engine's physical plan shows `STREAMING_WINDOW` for these cases instead of the full sort-based window operator.

This matters for performance. Streaming evaluation avoids materializing sorted partitions entirely. It processes rows as they arrive. We've seen this apply to `DISTINCT` aggregates in window context too. A query like `SUM(DISTINCT i % 3) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` still gets the streaming treatment. So does `DISTINCT` combined with `FILTER` clauses.

## Optimizer Tricks That Actually Help

Three optimizations stand out in DuckDB's handling of window functions.

**Common subexpression elimination.** If you reference `SUM(cnt_trace) OVER ()` three times in a query, DuckDB computes it once. The test suite explicitly verifies that duplicate window expressions collapse into a single window operator. But the optimizer is smart enough not to merge functions that look similar but aren't - `QUANTILE(x, 0.3) OVER ()` and `QUANTILE(x, 0.7) OVER ()` stay separate because the parameters differ.

**Top-N window elimination.** The classic pattern of `ROW_NUMBER() OVER (PARTITION BY k ORDER BY v DESC) AS rn ... QUALIFY rn <= 3` gets rewritten. Instead of computing row numbers across all partitions and then filtering, DuckDB can rewrite this into an equivalent lateral join or an aggregate using `ARG_MIN`/`ARG_MAX`. The benchmark file `topn_window_elimination.benchmark` tests this with 10 million rows across 100 partitions - a realistic scenario for time-series "latest N per group" queries.

**Filter pushdown through window partitions.** When you filter on a column that matches a window's `PARTITION BY` column, DuckDB pushes the filter below the window operator. A query that computes `SUM(quantity) OVER (PARTITION BY shipmode)` and then filters `WHERE shipmode = 'SHIP'` won't compute windows for every shipmode first - it prunes early. But the optimizer correctly avoids pushing filters when a different window function in the same query doesn't partition on that column, since doing so would change rank or row-number computations.

## Window Sort Fusion

Queries that use multiple window functions often require different sort orders. DuckDB's prefix sort fusion detects when window functions share a sort prefix and combines them into a single sort pass. If one window needs `ORDER BY l_partkey` and another needs `ORDER BY l_partkey, l_orderkey`, DuckDB recognizes the common prefix and avoids redundant sorting. The `test_window_fusion.test` file in the codebase validates this across partitioned and unpartitioned combinations.

## Parallel Execution

Window functions in DuckDB run in parallel across partitions. With `PRAGMA threads=4`, the engine distributes independent partitions across worker threads. The partition hashing and parallel execution tests validate this against a million-row table with 1,024 partitions. This is where DuckDB's architecture as an in-process analytical engine pays off - there's no network overhead between coordinators and workers.

## The Trade-Off Worth Knowing

DuckDB's `STREAMING_WINDOW` path is simpler and faster for cumulative aggregations without partitioning, but it doesn't work for arbitrary frame specifications or partitioned windows. Those fall back to the full sort-based window operator, which needs to materialize partitions in memory. For datasets that fit in RAM, this is rarely a concern. But if you're processing tables with billions of rows and thousands of large partitions, you'll hit memory pressure. DuckDB can spill window state to disk, yet the sort-based path is inherently more expensive than the streaming one. Structuring your queries to use cumulative frames when possible - `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` rather than `ROWS BETWEEN N PRECEDING AND N FOLLOWING` - keeps you on the faster path.

## A Few Functions Worth Knowing

Beyond the standard set, DuckDB supports `MODE()` as a window function for computing the most frequent value in a sliding frame, `MEDIAN()` and `QUANTILE_CONT()` for moving quantile calculations, and `LIST()` for collecting values into arrays within a window. The `fill()` function handles gap-filling over ordered partitions - useful for time-series data where readings are missing.

DuckDB version 1.5.0, released on March 9, 2026, continues to refine these capabilities. The engine keeps getting faster at the workloads that window functions are built for. If you're still reaching for pandas or writing multi-pass scripts for ranked filtering, cumulative aggregations, or moving statistics, it's worth reconsidering your approach.
