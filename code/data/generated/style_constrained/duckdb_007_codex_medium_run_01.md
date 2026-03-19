# DuckDB Window Functions Are the Real Analytical Interface

DuckDB describes itself as a high-performance analytical database, and the interesting part is how directly that shows up in SQL. You can point a query at a file with `SELECT * FROM 'myfile.parquet';` and then layer ranking, running aggregates, and partition-aware calculations on top without switching tools. That's the core analytical path.

I don't think window functions are an advanced corner of SQL anymore. In DuckDB, they're the normal way to express stateful analytics while keeping row-level detail alive. `GROUP BY` collapses. Windows annotate.

DuckDB also leans into the ergonomics. The repo's `test/sql/aggregate/qualify/test_qualify.test` uses `QUALIFY` heavily, which means you can filter on window output without burying the query inside another `SELECT`. So the common top-per-group pattern stays compact:

```sql
SELECT *
FROM qt
QUALIFY row_number() OVER (PARTITION BY b ORDER BY c) = 1;
```

That reads the way analysts actually think. Compute the ranking, keep the first row, move on. The same test file uses aliases in `QUALIFY`, shared `WINDOW` clauses, and value functions like `first_value()` and `last_value()`. DuckDB isn't treating window SQL as a special mode.

But `QUALIFY` has a semantic edge that trips people up. In issue `#21198`, a report about combined `count(distinct)` filters turned out to be expected behavior, not a bug. The windowed counts are computed before the `QUALIFY` predicate is applied, so filtering rows afterward can shrink the set that survives each partition. If you expect the filter to change the window's input, you want a different query shape.

Ranking functions are where this becomes practical. `row_number()` is the blunt instrument. It gives you one winner per partition, full stop. `rank()` and `dense_rank()` are the business-safe tools when ties matter. DuckDB's test cases show that clearly: a global `rank() OVER (ORDER BY mark DESC) = 4` returns two rows because two students share the same mark. `row_number() = 1` is simpler, but `rank() = 1` gives you tie preservation, which is often the real requirement in reporting and pricing systems.

And DuckDB's window support goes well past ranking. The same `QUALIFY` tests use a moving average over power generation data with a frame defined as `RANGE BETWEEN INTERVAL 3 DAYS PRECEDING AND INTERVAL 3 DAYS FOLLOWING`. The `test/sql/window/test_window_distinct.test` coverage goes further with `COUNT(DISTINCT ...) OVER (...)`, including both `ROWS` and `RANGE` frames, plus nested types.

Still, window frames are not a universal control plane. Issue `#21330` is a good reminder. A user expected `lag(ts)` to respect a `RANGE` frame of 15 minutes and return `NULL` outside that bound. DuckDB returned the same result as Postgres, and the issue was closed as expected behavior: `lag` doesn't use window framing in that way. That's a subtle rule, and it's exactly the kind of thing engineers forget six months later. So if a query mixes framed aggregates with navigation functions like `lag` or `lead`, don't assume the frame means the same thing to every function.

Under the hood, DuckDB is not executing all windows the same way either. `test/sql/window/test_streaming_window.test` asserts that `EXPLAIN` produces a `STREAMING_WINDOW` physical operator for cases like `row_number() OVER ()`, `lag`, `lead`, and running aggregates with `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. That means some analytical queries can stay incremental instead of forcing a fully materialized plan.

The repo also makes performance work visible. There is a dedicated microbenchmark, `benchmark/micro/window/window_rownumber_orderbys.benchmark`, that builds a 10,000,000-row table and exercises `row_number` with partitioning, ordering, and a `RANGE` frame. And there is a separate optimizer benchmark, `benchmark/micro/optimizer/topn_window_elimination.benchmark`, that compares lateral top-N patterns with `row_number() ... QUALIFY rn <= 1` and `rn <= 3`. DuckDB is benchmarking the real analytical idioms, not just toy aggregates.

That brings us to the most useful trade-off in the current sources. DuckDB 1.5.0, released on March 9, 2026, added a `top_n_window_elimination` optimizer rule implemented in `src/optimizer/topn_window_elimination.cpp`. The idea is sensible: rewrite patterns like `QUALIFY row_number() OVER (...) = 1` into a more direct Top-N style plan. On local data, that can be the right call. But remote storage changes the math.

Issue `#21348` shows why. On hive-partitioned Parquet in S3, the same query went from about 81 HTTP GET requests in v1.4.4 to 4,214 in v1.5.0, and wall-clock time rose from 11.6s to 31.5s. The reported plan shifted from a single scan plus `WINDOW` to a shape involving aggregate and join operators that effectively scanned remote data twice. The rewrite is cleverer, but the plain window plan can be cheaper when the storage layer charges latency per request instead of giving you local bandwidth.

And the edge cases didn't stop there. Issue `#21431` reports an out-of-memory failure for `QUALIFY rn <= 50`, where the rewrite used `arg_min_max_n(..., 50)` and preallocated slots aggressively even though the real maximum rank was only 3. DuckDB exposes a practical escape hatch here. You can disable the rule with:

```sql
SET disabled_optimizers='top_n_window_elimination';
```

For remote scans, the issue discussion also showed that a `MATERIALIZED` CTE and `SET s3_allow_recursive_globbing = false;` could restore a much saner access pattern. That is a very backend-engineering lesson. Analytical SQL is only half the story. The storage topology and optimizer rewrite determine whether elegant SQL stays fast.

A January 27, 2026 community benchmark on roughly 20 GB of Parquet data tells the same story from the outside. Across 57 queries, the reported DuckDB Local XL median for window functions was 947 ms, while DuckDB plus remote R2 storage was 12,187 ms. DuckDB window queries can be extremely fast, but they are fastest when the execution model and storage model agree.

We should read DuckDB window functions as first-class infrastructure, not decoration. They are wired into parser tests, physical operators, optimizer rules, and dedicated benchmarks. That's why the right engineering move is usually to write the direct analytical query first, inspect `EXPLAIN`, and only get fancy if the plan proves it deserves the complexity. Short SQL is good. Predictable SQL is better. In DuckDB, the best queries usually give you both.
