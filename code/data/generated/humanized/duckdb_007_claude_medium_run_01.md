# Window Functions in DuckDB: What the SQL Standard Promises and Where Things Get Interesting

Window functions changed how I think about analytical SQL. They let you compute rankings, running totals, and row-level comparisons without collapsing your result set the way GROUP BY does; DuckDB implements a rich set of them with some interesting internal design choices and a few sharp edges worth knowing about.

## Partitions, Ordering, and Frames

Three components define a window. PARTITION BY splits data into independent groups, ORDER BY sets the sequence within each partition, and the frame clause controls exactly which rows contribute to the computation. DuckDB supports all three frame modes from the SQL standard (ROWS for physical row offsets, RANGE for logical value ranges, and GROUPS for peer group offsets) along with all four EXCLUDE options: CURRENT ROW, GROUP, TIES, and NO OTHERS. Not every database goes this far with spec compliance.

Here's an example computing a seven-day rolling average of daily sales:


SELECT
    date,
    revenue,
    AVG(revenue) OVER (
        ORDER BY date
        RANGE BETWEEN INTERVAL 7 DAY PRECEDING AND CURRENT ROW
    ) AS rolling_7d_avg
FROM daily_sales;


RANGE mode means the frame includes all rows whose date falls within seven days before the current row's date, regardless of how many physical rows that spans. The distinction between ROWS and RANGE trips people up constantly.

## QUALIFY: Filtering Without the Nesting

DuckDB borrows the QUALIFY clause from Teradata's SQL dialect, and honestly it's one of my favorite features. Instead of wrapping a window function in a subquery just to filter on it:


SELECT *
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1;


That returns the most recent order per customer. Without it, you'd need a CTE or subquery with a WHERE clause on the window result. Syntactic sugar, sure, but the kind that meaningfully reduces nesting in real analytical work.

One subtlety worth calling out: QUALIFY filters apply after window functions compute their results over the full dataset. Combining multiple conditions (say, filtering on count(distinct price) partitioned by two different columns) means the filtering can remove rows that were counted in the original computation. The post-filtering count for a group might end up lower than your threshold. Correct per SQL semantics. But I've seen it surprise people who expect the conditions to interact as a single pass.

## Under the Hood: Segment Trees and Merge Sort Trees

DuckDB doesn't compute window aggregates the naive way. For standard aggregates like SUM or AVG over sliding frames, it uses a segment tree with a fanout of 16 that pre-computes partial aggregations over blocks of rows, so evaluating an aggregate over any contiguous range means combining only O(log n) partial states instead of scanning every row in the frame. When the frame slides one row at a time across millions of records, that efficiency gain is enormous.

For ranking functions, the approach differs. ROW_NUMBER, RANK, and DENSE_RANK track partition and peer group boundaries using validity masks, incrementally updating rank counters as they scan each partition. Specifically, DENSE_RANK counts set bits in the order mask between partition start and the current row to figure out how many distinct peer groups precede it. Cache-friendly, and no separate data structure required.

There's also support for secondary ordering within window functions through an ORDER BY clause on the function arguments themselves. `FIRST_VALUE(price ORDER BY timestamp)` lets you specify an ordering independent of the frame ordering. Internally, this relies on token trees (merge sort trees) that efficiently map between the two orderings.

## The TopN Window Elimination Optimizer

Version 1.5.0 introduced an optimization called "top_n_window_elimination." When DuckDB detects a ROW_NUMBER() filtered to equal 1 via QUALIFY or a WHERE clause on a subquery, it can rewrite the query to use an aggregate-based plan with arg_max instead of materializing the full window computation. In theory, this skips sorting and scanning the entire dataset.

Practice tells a different story for remote storage. The rewritten plan can produce two separate scans of the underlying files: one lightweight scan to identify the "winning" rows, then a second to fetch all their columns. Locally, the double scan is nearly free. Over S3, each scan translates to HTTP range requests, and for wide tables the request count can explode; one user reported going from 80 HTTP requests to over 4,200 after upgrading, with query time nearly tripling.

The fix is simple enough: disable the optimization with `SET disabled_optimizers='top_n_window_elimination'` or force a single scan by wrapping the source in a MATERIALIZED CTE. From what I can tell, the team is making the optimizer more aware of storage characteristics so it can decide when the rewrite actually helps.

A related memory problem surfaced too. When `QUALIFY rn <= 50` gets rewritten to use `arg_min_max_n`, the internal heap pre-allocates all 50 slots per group upfront. Most of those slots sit empty if the actual max rank per group is much smaller (say 3). At scale, this causes out-of-memory failures that didn't happen with the original window-based plan.

## LAG, LEAD, and Frame Semantics

This one catches people.

LAG and LEAD don't respect the window frame specification, which matches the SQL standard and PostgreSQL's behavior. These navigation functions always look backward or forward by a fixed number of rows within the partition, ignoring any ROWS or RANGE frame you define. So writing `LAG(ts) OVER (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW)` means the RANGE clause affects aggregate functions evaluated over the same window but does nothing to LAG itself.

If you need LAG-like behavior constrained to a value range, try a secondary ordering on the function argument: `LAG(ts ORDER BY ts)`. DuckDB's argument-level ORDER BY support controls which rows the function considers.

## Performance at Scale

Independent benchmarks on 20GB of financial time-series data show strong local performance, roughly 3x faster than BigQuery and 5x faster than Athena for window-heavy queries. But remote storage? Another story entirely. Parquet files on S3 or R2 are a weak point since window functions often require multiple passes over the data; one benchmark showed these queries taking over 12 seconds remotely compared to under 1 second locally, a much larger gap than for simple scans or aggregations.

Keep data on local or attached storage if your pipeline leans heavily on window functions. When that's not possible, materializing intermediate results before applying the computations can cut network round-trips significantly.

## Where Things Stand

DuckDB's window function implementation is largely standards-compliant, with segment trees and merge sort trees doing the real work behind clean SQL syntax. Honestly, QUALIFY and argument-level ORDER BY are genuine ergonomic wins over what most databases offer. The v1.5.0 optimizer rewrites introduced some rough edges around remote storage and memory allocation, but those issues are well-understood and being actively addressed. For analytical work on datasets that fit on a single machine, I think these are some of DuckDB's best capabilities.
