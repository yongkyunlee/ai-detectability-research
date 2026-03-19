# Window Functions in DuckDB: What You Actually Need to Know

Aggregations only get you so far. The moment you need running totals, rankings within groups, or comparisons between neighboring rows, you're reaching for window functions. DuckDB has a really solid implementation of these, and it throws in some syntax sugar that makes analytical SQL genuinely nicer to write. I've been using them heavily and wanted to share what I've learned about the different frame types, where DuckDB goes beyond standard SQL, and a few performance gotchas.

## Anatomy of a Window Call

Every window function follows the same pattern. You call a function and tack on an `OVER` clause that sets up the computational context:

```sql
function_name(arguments) OVER (
    PARTITION BY grouping_columns
    ORDER BY sorting_columns
    frame_specification
)
```

`PARTITION BY` splits your dataset into independent groups, sort of like defining boundaries for where the function does its work. `ORDER BY` determines row sequence inside each partition. The frame specification narrows things even further, pinpointing which rows around the current one actually participate in the calculation.

All three are optional. Most real queries include at least one, though. If you leave everything out, the frame covers the entire result set, which can be handy when you need global statistics next to row-level detail.

## Ranking Functions

DuckDB gives you the full set of SQL ranking functions, and the differences between them come down to how they handle ties. `ROW_NUMBER()` produces a sequential integer for every row, breaking ties arbitrarily; it's your go-to for deduplication and top-N selection. `RANK()` assigns the same number to tied rows but leaves gaps in the sequence, so if two rows tie at position 2, the next row jumps to 4. `DENSE_RANK()` handles ties too, but without gaps, keeping the sequence contiguous. Then there's `PERCENT_RANK()` and `CUME_DIST()`, which express position as a fraction for percentile calculations.

A typical top-N query:

```sql
SELECT product_name, category, revenue,
       ROW_NUMBER() OVER (
           PARTITION BY category
           ORDER BY revenue DESC
       ) AS rank_in_category
FROM product_sales
```

This assigns a revenue rank within each category. Filtering down to the top 3 per category would traditionally mean wrapping it in a subquery. DuckDB has a cleaner approach, which I'll get to shortly.

## Looking Across Rows with Value Access Functions

Sometimes you need to compare a row with its neighbors or grab values from specific positions in an ordered set. `LAG(expr, offset, default)` reaches backward by `offset` rows, while `LEAD(expr, offset, default)` reaches forward. `FIRST_VALUE(expr)` and `LAST_VALUE(expr)` pull from the edges of the frame, and `NTH_VALUE(expr, n)` retrieves from any arbitrary position.

These are great for row-over-row changes. Daily price movement, for instance:

```sql
SELECT trading_date, close_price,
       close_price - LAG(close_price) OVER (ORDER BY trading_date) AS daily_change
FROM stock_prices
```

DuckDB also has a `FILL()` function for forward-filling missing values across a partition. Anyone working with time series will appreciate this one, since it kills the need for self-joins or correlated subqueries just to carry forward the last known value.

## Frame Specifications: Where Things Get Subtle

The frame specification is where window functions get really flexible. It's also where I've seen people trip up the most. DuckDB supports three modes.

**ROWS** defines boundaries by physical row count. "Give me the average of the current row plus the two preceding rows" translates directly:

```sql
AVG(value) OVER (ORDER BY ts ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
```

**RANGE** defines boundaries by logical value distance. This matters a lot for time-based windows where rows aren't evenly spaced. Here's a 30-day moving average that handles irregular timestamps:

```sql
AVG(price) OVER (
    ORDER BY trade_date
    RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
) AS moving_avg_30d
```

**GROUPS** operates on peer groups (sets of rows sharing the same `ORDER BY` value). I don't see it used as often, but it's valuable when you want to include all ties naturally.

Each mode lets you set boundaries as `UNBOUNDED PRECEDING`, `UNBOUNDED FOLLOWING`, `CURRENT ROW`, or an explicit offset in either direction. There's also an `EXCLUDE` clause for finer control: you can exclude the current row, the current group, ties, or nothing.

One thing the docs don't make super obvious: the default frame when you specify `ORDER BY` is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, giving you cumulative aggregations. Without `ORDER BY`, the default covers the entire partition, which is constant aggregation and actually the fastest mode internally.

## The QUALIFY Clause

Honestly, this might be my favorite DuckDB feature for analytical work. In standard SQL, filtering on a window function result means nesting:

```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_time DESC) AS rn
    FROM events
) sub
WHERE rn = 1
```

DuckDB collapses this into a single query:

```sql
SELECT *
FROM events
QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_time DESC) = 1
```

`QUALIFY` runs after window functions are computed, similar to how `HAVING` filters after `GROUP BY`. The boilerplate reduction is real, and the intent reads so much more clearly. You can combine multiple window conditions, reference aggregate windows, and build expressive filters without any subquery nesting.

Some common patterns: selecting the top N per group, filtering partitions by size, applying thresholds to running totals.

```sql
-- Keep only categories with at least 10 products
SELECT *
FROM products
QUALIFY COUNT(*) OVER (PARTITION BY category_id) >= 10
```

## Performance Under the Hood

DuckDB's query engine picks between several internal strategies for window computation based on the frame type. Knowing which one fires helps explain why some window queries are dramatically faster than others.

Constant aggregation kicks in when there's no `ORDER BY` and the frame spans the entire partition. The aggregate gets computed once per partition and broadcast to all rows. Essentially free after the initial grouping pass.

Streaming aggregation handles sequential access patterns like `LAG` and `LEAD`, or cumulative frames that grow one row at a time. Single pass, no buffering of the whole partition.

Segment tree aggregation is the strategy for variable-bound `RANGE` frames where arbitrary slices of sorted data need efficient aggregation. The tree structure gives logarithmic lookup per row instead of linear rescanning.

What does this mean in practice? Partitioning strategy matters a lot; huge partitions eat more memory and limit parallelism. Cumulative frames (`UNBOUNDED PRECEDING` to `CURRENT ROW`) are cheaper than symmetric frames that look both forward and backward. And if you're querying remote data on S3, window functions can trigger multiple scans of underlying files. Wrapping the scan in a `MATERIALIZED` CTE forces a single read and keeps subsequent operations local.

## Pitfalls and Known Limitations

A few sharp edges worth knowing about.

`LAG` and `LEAD` don't respect `RANGE` frame specifications. Set a range-based frame, call `LAG()`, and it behaves as if the frame weren't there, always reaching back by the specified offset in physical row terms. Aggregate functions over the same window clause *do* respect the range, so if you need range-aware lookback, restructuring toward an aggregate approach is probably the way to go.

DuckDB's optimizer has a rule called top-N window elimination that rewrites `QUALIFY ROW_NUMBER() ... = 1` patterns into more efficient aggregation strategies. Usually that's a good thing. But it can backfire with remote storage like S3, where the rewritten plan may issue way more HTTP requests than the original because it introduces additional scan passes. The workaround is `SET disabled_optimizers='top_n_window_elimination'` if you notice unexpected slowdowns. Not the most discoverable fix, I'll admit.

There are also edge cases around partition-by clauses without any ordering that can cause failures depending on the input source format. Adding an explicit `ORDER BY NULL` resolves them. Shouldn't be necessary in theory, but there it is.

## Putting It All Together

Here's a more realistic example. Say you're building a customer retention analysis: identify each customer's first purchase, compute their running spend, flag their most recent transactions.

```sql
SELECT
    customer_id,
    order_date,
    order_total,
    FIRST_VALUE(order_date) OVER w AS first_purchase,
    SUM(order_total) OVER (
        PARTITION BY customer_id
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_spend,
    DATEDIFF('day', LAG(order_date) OVER w, order_date) AS days_since_last_order
FROM orders
WINDOW w AS (PARTITION BY customer_id ORDER BY order_date)
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY customer_id ORDER BY order_date DESC
) <= 5
```

One query. First purchase dates, cumulative spending, inter-purchase intervals, and output limited to each customer's five most recent orders. No subqueries, no CTEs, no temp tables.

I think the biggest takeaway from working with window functions in DuckDB is matching your frame type to what you're actually trying to measure: `ROWS` for fixed physical offsets, `RANGE` for logical value distances, and constant frames for partition-wide stats. Get that right and keep an eye on partition sizes, and you can handle surprisingly complex analytical work in a single statement. Features like `QUALIFY` and `FILL()` sand down the rough edges of standard SQL just enough to make the whole experience feel less like a wrestling match.
