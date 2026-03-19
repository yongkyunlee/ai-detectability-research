# DuckDB Window Functions for Real Analytical Queries

DuckDB’s appeal in analytics is not just that it supports window functions. DuckDB treats analytical SQL as a first-class workload even when the data lives in files, temporary tables, or embedded application state. The repository README positions it as a high-performance analytical database with a broad SQL dialect, and the test suite makes that concrete: ranking, running aggregates, frame clauses, `QUALIFY`, named windows, filtered aggregates, and value functions all show up as standard engine behavior.

For day-to-day analysis, that means you can write the kinds of queries people normally reach for in warehouse SQL without much ceremony. A running departmental payroll total is just:

```sql
SELECT
  depname,
  empno,
  salary,
  sum(salary) OVER (PARTITION BY depname ORDER BY empno)
FROM empsalary;
```

The same test coverage also shows the usual ranking family working as expected: `row_number`, `rank`, `dense_rank`, `percent_rank`, `cume_dist`, `first_value`, `last_value`, `lag`, and `lead`. DuckDB also supports named window specifications through the `WINDOW` clause, so repeated partitioning and ordering logic can be defined once and reused. That matters in analytical codebases because repeated `OVER (...)` clauses are easy to drift out of sync.

One particularly practical feature is `QUALIFY`. Instead of wrapping a windowed query in a subquery just to filter on the derived ranking, DuckDB lets you keep the logic in one statement:

```sql
SELECT *
FROM exam
QUALIFY rank() OVER (PARTITION BY student ORDER BY mark DESC) = 2;
```

From the binder logic and test coverage, a few rules are worth remembering. `QUALIFY` must be attached to a query that actually uses a window function, either in the select list or in the `QUALIFY` predicate itself. It can reference projection aliases. And if you use a named `WINDOW` clause, it has to appear before `QUALIFY`, not after it.

DuckDB is also fairly strict about window semantics, in ways that are helpful once you understand them. The binder rejects nested window calls, and it does not support correlated columns inside window functions. `RANGE` frames are limited to a single `ORDER BY` expression, which matches the fact that value-based framing needs one sortable axis. The implementation also rewrites range boundaries carefully for descending order and for time types, which hints at how much engine work hides behind a seemingly simple clause like `RANGE BETWEEN INTERVAL 3 DAYS PRECEDING AND CURRENT ROW`.

The more interesting story is what DuckDB does after parsing. In the physical planner, window expressions are grouped when they share equivalent partitions and a compatible ordering prefix. Identical expressions can reuse work, and several windows over the same grain can move through the same planned operator. That is exactly the kind of optimization analytical queries need, because dashboards and notebooks often compute several rankings and moving aggregates over the same keys.

DuckDB also distinguishes between blocking and streaming windows. The general `PhysicalWindow` operator uses a multi-stage pipeline with sorting and materialization, which is the expensive path but necessary for partitioned, ordered, or frame-sensitive analysis. There is also a `PhysicalStreamingWindow` path for simpler cases. The source shows that functions like `row_number() OVER ()`, `rank() OVER ()`, `dense_rank() OVER ()`, some `lead` and `lag` calls, and running aggregates over `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` can stream under the right conditions. In practice, some analytical queries become closer to a single pass than a full window materialization.

That planner flexibility becomes very visible in top-N analytical patterns. In `optimizer.cpp`, DuckDB explicitly runs a `top_n_window_elimination` pass after statistics propagation. The corresponding optimizer source rewrites a pattern such as `row_number() ... QUALIFY rn <= N` into aggregate-based plans built from `min`, `max`, `arg_min`, or `arg_max` variants. The optimizer tests confirm the intent: after rewriting, the logical plan should no longer contain the original `FILTER` over a `WINDOW` node.

This is a smart optimization for many local analytical workloads. It replaces a full ranking step with a grouped aggregate strategy, which is often exactly what a “top row per partition” query means semantically. But the issue tracker shows why window functions remain a trade-off-heavy area. An open issue from March 12, 2026 reports that `QUALIFY row_number() OVER (...) = 1` on hive-partitioned Parquet in S3 triggered a plan that scanned remote files twice and multiplied HTTP requests dramatically on a wide schema. Another open issue from March 17, 2026 shows the same optimizer family causing out-of-memory failures when `rn <= 50` was rewritten to an `arg_min_max_n` strategy that allocated far more state than the actual result cardinality required.

Those reports do not make the optimization wrong. They show that the best plan for a local table is not always the best plan for remote object storage, wide Parquet, or skewed partitions. Community discussion in the context bundle points the same way: users consistently praise DuckDB for embedded analytics and fast local file processing, while also noting that remote storage changes the cost model. One benchmark in the community set found window-heavy queries especially sensitive to remote object storage because they may require additional passes and metadata work.

There is also an important semantic footnote around frames: not every window function obeys frame clauses in the way newcomers expect. A March 12, 2026 issue around `lag()` with a `RANGE` frame was closed as expected behavior after discussion. The key point is that `lag` is defined by row offset semantics, not by the frame in the same way an aggregate like `array_agg` is. If you are reasoning about time windows, that distinction matters.

The practical takeaway is that DuckDB gives you expressive analytical SQL and increasingly aggressive optimization for common window patterns. Use shared window definitions, prefer `QUALIFY` when it clarifies intent, and inspect plans when ranking queries hit remote files or very large partitions. DuckDB is strong at analytical windows because it does not treat them as syntax sugar. It treats them as an optimization problem. That is exactly why it performs so well when the query shape and storage layout line up, and exactly why advanced users should still care about the plan underneath the SQL.
