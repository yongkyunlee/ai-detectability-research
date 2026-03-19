---
source_url: https://duckdb.org/2025/02/14/window-flying.html
author: "Richard Wesley"
platform: duckdb.org (official blog)
scope_notes: "Trimmed from an 11-min read on window function optimizations. Focused on segment tree vectorization, streaming windows, constant aggregation, and shared expressions. Original ~2500 words; trimmed to ~480 words."
---

This post examines recent performance enhancements to DuckDB's windowing capabilities, focusing on resource optimization. The optimizations presented push the performance of DuckDB's window operator even further.

## Segment Tree Vectorization

A significant 2023 improvement converted segment tree evaluation from single-value to vectorized processing. The original implementation processed one row at a time using aggregate APIs, but the optimized version accumulates vectors of leaf values and tree states and flushes them into each output row's state when reaching the vector capacity of 2048 rows. Performance improvements reached approximately 4x speedup.

## Constant Aggregation

Window computations frequently require comparing partial aggregates against entire partition aggregates. Previously, users employed subquery workarounds to avoid redundant computation. The new optimization identifies partition-wide aggregates and computes them once per partition, returning constant vectors that share values across all chunk rows.

A specific use case involved constructing a constant 100k element list and then computing the median with a list aggregation lambda. By returning a single constant list, DuckDB builds and reduces that list only once instead of once per row.

## Streaming Windows

Window function computation traditionally requires full relation materialization, partitioning, and sorting. However, when partitioning and ordering are absent, the function operates over the entire relation in the natural order, using a frame that starts with the first row and continues to the current row.

Streamable functions include aggregates with frame `BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, plus `first_value`, `percent_rank`, `rank`, `dense_rank`, `row_number`, `lead`, and `lag`.

```sql
SELECT setseed(0.8675309);
CREATE OR REPLACE TABLE df AS
    SELECT random() AS a, random() AS b, random() AS c
    FROM range(10_000_000);

SELECT sum(a_1 + a_2 + b_1 + b_2)
FROM (
    SELECT
        lead(a, 1) OVER () AS a_1,
        lead(a, 2) OVER () AS a_2,
        lead(b, 1) OVER () AS b_1,
        lead(b, 2) OVER () AS b_2
    FROM df
) t;
```

The streaming LEAD implementation achieved dramatic performance improvements over the baseline materialized approach.

## Shared Expressions

Window expressions frequently reference identical expensive-to-evaluate elements. For example:

```sql
SELECT
    x,
    min(x) OVER w AS min_x,
    avg(x) OVER w AS avg_x,
    max(x) OVER w AS max_x
FROM data
WINDOW w AS (
    PARTITION BY p ORDER BY s
    ROWS BETWEEN 1_000_000 PRECEDING AND 1_000_000 FOLLOWING
);
```

Version 1.2 introduced expression sharing between functions, eliminating duplicate evaluation and materialization. This reduces memory consumption and disk paging, particularly beneficial when multiple functions access identical partition values.

## Future Work

The author identifies query rewriting as a promising optimization avenue, noting that certain window functions can be evaluated through alternative techniques such as self-joins and advanced aggregates like `arg_max`. These alternate query plans could yield substantial performance benefits. Windowing represents a complex optimization challenge with limited published research, and the DuckDB team commits to more timely documentation of future enhancements.
