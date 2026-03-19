# Mastering Window Functions in DuckDB: What the SQL Standard Promises and Where Things Get Interesting

Window functions are one of the most powerful features in analytical SQL. They let you compute rankings, running totals, and row-level comparisons without collapsing your result set the way GROUP BY does. DuckDB, the embedded analytical database that has been steadily gaining traction among data engineers and analysts, implements a rich set of window functions with some interesting internal design choices and a few sharp edges worth understanding.

## The Basics: Partitions, Ordering, and Frames

A window function operates over a "window" of rows related to the current row. You define that window with three components: PARTITION BY splits the data into independent groups, ORDER BY determines the sequence within each partition, and the frame clause controls exactly which rows in the partition contribute to the computation.

DuckDB supports all three frame modes from the SQL standard: ROWS (physical row offsets), RANGE (logical value ranges), and GROUPS (peer group offsets). It also implements all four EXCLUDE options — CURRENT ROW, GROUP, TIES, and NO OTHERS — which let you remove specific rows near the current position from the frame. This is a level of completeness that not every database offers.

Here is a straightforward example that computes a seven-day rolling average of daily sales:


SELECT
    date,
    revenue,
    AVG(revenue) OVER (
        ORDER BY date
        RANGE BETWEEN INTERVAL 7 DAY PRECEDING AND CURRENT ROW
    ) AS rolling_7d_avg
FROM daily_sales;


The RANGE mode here means the frame includes all rows whose date falls within seven days before the current row's date, regardless of how many physical rows that spans. That distinction between ROWS and RANGE trips people up regularly.

## The QUALIFY Clause: Filtering on Window Results

One of DuckDB's conveniences is the QUALIFY clause, borrowed from Teradata's SQL dialect. Instead of wrapping your window function in a subquery just to filter on it, you can write:


SELECT *
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;


This returns the most recent order per customer. Without QUALIFY, you would need a CTE or subquery with a WHERE clause on the window result. It is syntactic sugar, but the kind that meaningfully reduces query nesting in analytical work.

One subtlety: QUALIFY filters are applied after the window functions compute their results over the full dataset. If you combine multiple window conditions — say, filtering on count(distinct price) partitioned by two different columns — the filtering can remove rows that were counted in the original window computation. The post-filtering count for a group might end up lower than the threshold you specified. This is correct behavior per the SQL semantics, but it surprises people who expect the conditions to interact as a single pass.

## Under the Hood: Segment Trees and Merge Sort Trees

DuckDB does not compute window aggregates naively. For standard aggregates like SUM or AVG over sliding frames, it uses a segment tree structure with a fanout of 16. The segment tree pre-computes partial aggregations over blocks of rows, so evaluating an aggregate over any contiguous range requires combining only O(log n) partial states rather than scanning every row in the frame. This matters enormously when the frame slides one row at a time across millions of records.

For ranking functions — ROW_NUMBER, RANK, DENSE_RANK — DuckDB takes a different approach. These functions track partition boundaries and peer group boundaries using validity masks, incrementally updating rank counters as they scan through each partition. The DENSE_RANK implementation, for instance, counts set bits in the order mask between partition start and the current row to determine how many distinct peer groups precede it. This bit-counting approach is cache-friendly and avoids the overhead of maintaining a separate data structure.

DuckDB also supports secondary ordering within window functions through an ORDER BY clause on the function arguments themselves. For example, `FIRST_VALUE(price ORDER BY timestamp)` lets you specify an ordering independent of the frame ordering. Internally, this is implemented using token trees — merge sort trees that can efficiently map between the frame ordering and the argument ordering.

## The TopN Window Elimination Optimizer

DuckDB v1.5.0 introduced an optimization called "top_n_window_elimination" that rewrites certain common patterns. When the optimizer detects a ROW_NUMBER() filtered to equal 1 via QUALIFY or a WHERE clause on a subquery, it can rewrite the query to use an aggregate-based plan with arg_max instead of materializing the full window computation. In theory, this avoids sorting and scanning the entire dataset.

In practice, this optimization has created some interesting trade-offs. For queries against remote storage like S3, the rewritten plan can result in two separate scans of the underlying files — one lightweight scan to identify the "winning" rows and a second scan to fetch all their columns. On local disk, the double scan is nearly free. On S3, each scan translates to HTTP range requests, and for wide tables with many columns, the request count can explode. One user reported going from 80 HTTP requests to over 4,200 after upgrading, with query time nearly tripling.

The workaround is straightforward — either disable the specific optimization with `SET disabled_optimizers='top_n_window_elimination'` or force a single scan by wrapping the source in a MATERIALIZED CTE. The DuckDB team is working on making the optimizer more aware of storage characteristics so it can make better decisions about when the rewrite is profitable.

A related memory issue surfaced with the same optimizer. When `QUALIFY rn <= 50` is rewritten to use `arg_min_max_n`, the internal heap pre-allocates all 50 slots per group upfront. If the actual maximum rank per group is much smaller — say 3 — most of those slots sit empty, wasting memory. At scale, this can cause out-of-memory failures that did not occur with the original window-based plan.

## Gotchas: LAG, LEAD, and Frame Semantics

A common source of confusion is that LAG and LEAD do not respect the window frame specification. This matches the SQL standard and PostgreSQL's behavior: these navigation functions always look backward or forward by a fixed number of rows within the partition, ignoring any ROWS or RANGE frame you define. If you write `LAG(ts) OVER (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW)`, the RANGE clause affects aggregate functions evaluated over the same window but has no effect on LAG.

The workaround, if you need LAG-like behavior constrained to a value range, is to use a secondary ordering on the function argument: `LAG(ts ORDER BY ts)`. This leverages DuckDB's argument-level ORDER BY support to control which rows LAG considers.

## Window Functions and Performance at Scale

Independent benchmarks on 20GB of financial time-series data show that DuckDB's window function performance on local storage is strong — roughly 3x faster than BigQuery and 5x faster than Athena for window-heavy queries. However, window functions over remote storage (like Parquet files on S3 or R2) are a weak point, since they often require multiple passes over the data. One benchmark showed window function queries taking over 12 seconds against remote storage compared to under 1 second locally, a far larger gap than for simple scans or aggregations.

The takeaway for practitioners: if your analytical pipeline is window-function-heavy, keeping the data on local or attached storage pays dividends. If remote storage is unavoidable, materializing intermediate results before applying window functions can dramatically reduce network round-trips.

## Wrapping Up

DuckDB's window function implementation is mature and largely standards-compliant, with segment trees and merge sort trees doing the heavy lifting behind clean SQL syntax. The QUALIFY clause and argument-level ORDER BY are genuine ergonomic improvements over what most databases offer. The newer optimizer rewrites are ambitious, and while they have introduced some rough edges in the v1.5.0 release — particularly around remote storage and memory allocation — the underlying issues are well-understood and being actively addressed. For anyone doing analytical work on datasets that fit on a single machine, DuckDB's window functions remain one of its strongest selling points.
