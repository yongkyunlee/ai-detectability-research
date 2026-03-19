# Query Performance Optimization in DuckDB

DuckDB occupies an unusual spot in the database landscape. It runs inside your application process, requires no server, and yet routinely outperforms cloud data warehouses on analytical queries against datasets in the tens-of-gigabytes range. A local DuckDB instance with 32 threads can return aggregation queries in under 400 milliseconds on 20 GB of Parquet data—an order of magnitude faster than BigQuery or Athena running the same workload. Those results are not magic. They follow from a set of deliberate architectural choices in the optimizer and execution engine that reward careful understanding.

## The Optimizer Pipeline

Every SQL statement that enters DuckDB passes through a parser derived from PostgreSQL's libpg_query, then through a planner that builds a logical operator tree, and finally through a multi-pass optimizer that rewrites that tree before handing it off to the execution engine. The optimizer itself contains over twenty expression-rewriting rules and a dozen structural transformation passes, totaling roughly eleven thousand lines of C++. The passes fall into two broad categories: rule-based rewrites that always apply and cost-based decisions that depend on cardinality estimates.

Rule-based passes include constant folding, arithmetic simplification, LIKE-to-prefix conversion, CASE expression pruning, and IN-clause optimization. These are cheap transformations that fire unconditionally. The cost-based side is anchored by a join order optimizer modeled after the System R dynamic-programming approach. It builds a hypergraph of relations and join predicates, enumerates candidate orderings, and scores each one using a cardinality estimator backed by column statistics and HyperLogLog distinct-count sketches. The result is a join plan that minimizes intermediate result sizes, which matters enormously once tables grow past a few million rows.

## Filter Pushdown and Its Limits

Filter pushdown is one of the highest-impact optimizations DuckDB applies. The idea is straightforward: move WHERE predicates as close to the data source as possible so that fewer rows flow through the rest of the plan. DuckDB pushes filters through projections, aggregations, inner joins, outer joins, semi-joins, and set operations, each with its own specialized handler.

For Parquet and Hive-partitioned datasets, pushdown interacts with row-group statistics. If a predicate references a column whose min/max metadata proves no matching rows exist in a given row group, that group is skipped entirely. On S3-backed datasets where every byte read costs money and latency, this can eliminate most of the I/O.

Pushdown has real limitations, though. Expressions that can throw runtime errors—such as calling `sqrt` on a column that might contain negative values—are deliberately not pushed down, because doing so could surface an error on rows that the original plan would never have evaluated. Scalar macros that return non-constant results also resist pushdown. And filters derived through CTEs may not propagate if the CTE has been materialized rather than inlined, a distinction that became painfully visible when DuckDB changed its default CTE behavior from inlining to materialization in version 1.4.0.

## The CTE Materialization Trade-Off

Before 1.4.0, CTEs were inlined by default, meaning the optimizer treated them as syntactic sugar and applied all downstream optimizations—column pruning, filter pushdown—through the CTE boundary. The switch to materialization aimed to prevent redundant computation when a CTE is referenced multiple times, but it introduced an unintended side effect: materialized CTEs block column pruning. A query selecting two columns from a CTE defined as `SELECT * FROM wide_table` would previously scan only those two columns. After the change, all fifty columns get materialized first. Users reported 100x slowdowns on wide tables with tens of millions of rows. The workaround is to mark CTEs as `NOT MATERIALIZED` explicitly, but the episode illustrates how optimizer defaults carry real performance consequences.

## Column Pruning and Late Materialization

Column pruning removes unreferenced columns from every operator in the plan, reducing both I/O and memory pressure. DuckDB pairs this with late materialization, which delays assembling full result tuples until the last possible moment. During a filtered scan, the engine first evaluates predicates using only the columns they reference, then fetches the remaining output columns only for rows that survive. This approach is especially effective on columnar storage formats like Parquet, where each column lives in a separate chunk and reading fewer columns translates directly into fewer bytes off disk or network.

## Vectorized Execution

At the execution layer, DuckDB processes data in vectors—typically batches of 1,024 to 4,096 rows stored in columnar layout. Every physical operator, from hash joins to window functions to aggregations, operates on these batches rather than individual tuples. This amortizes per-row overhead and allows tight loops that stay in CPU cache. Selection vectors let the engine represent filtered subsets without physically copying data, and an adaptive filter component learns which conjuncts are most selective and reorders them accordingly.

The push-based pipeline model means operators push data downstream rather than pulling it, which simplifies parallelism. Pipelines run across multiple threads, and doubling the thread count roughly halves query latency up to a point—going from four to thirty-two threads on a benchmark suite showed approximately a 5x improvement, reflecting diminishing returns from memory bandwidth and synchronization overhead.

## Partition and Row-Group Pruning for Remote Storage

When querying Hive-partitioned data on S3 or similar object stores, DuckDB prunes at two levels: partitions (entire directories) and row groups within Parquet files. The partition pruner uses the directory structure to avoid listing or opening files that cannot match the predicate. The row-group pruner uses Parquet footer metadata. Together, they can reduce S3 GET requests from thousands to dozens.

Version 1.5.0 introduced a regression in this area: the glob expansion code began discovering all files before applying partition filters, causing unnecessary S3 LIST requests. Setting `s3_allow_recursive_globbing` to false restored the previous behavior. A related issue involved the top-N window elimination optimizer rewriting `ROW_NUMBER() OVER (...) = 1` into a semi-join that doubled the number of file scans, inflating HTTP requests by 50x on remote data. Disabling that specific optimizer pass was the recommended workaround.

## Practical Takeaways

Tuning DuckDB performance comes down to ensuring the optimizer can do its job. Write predicates that reference base columns directly rather than wrapping them in error-prone expressions. Avoid `SELECT *` in CTEs over wide tables, or mark them `NOT MATERIALIZED`. Profile with `EXPLAIN ANALYZE` to verify that filters push down to the scan level. For remote storage, monitor HTTP request counts—an unexpected spike usually signals a pruning regression. And keep an eye on the `disabled_optimizers` setting: sometimes the fastest path forward is telling DuckDB which shortcut not to take.
