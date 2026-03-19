# Beneath the OVER Clause: How DuckDB Implements Window Functions

Window functions sit right at the spot where SQL gets both powerful and computationally expensive. They let you rank rows, compute running totals, look ahead and behind in ordered sequences, and perform aggregations across sliding frames, all without collapsing rows like GROUP BY does. DuckDB has put serious engineering effort into making these operations fast, correct, and memory-efficient on a single machine.

This post walks through how it handles them internally, what SQL patterns you can write, and where the rough edges still show up.

## The SQL Surface: What You Can Express

DuckDB supports the full SQL:2003 window function specification, and then some. The OVER clause accepts PARTITION BY, ORDER BY, and frame specifications using ROWS, RANGE, or GROUPS modes. On the ranking side, you get `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `PERCENT_RANK()`, `CUME_DIST()`, and `NTILE()` for assigning positional or statistical labels to each row within its partition. Value functions like `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, `LEAD()`, and `LAG()` grab values from specific positions relative to the current row or frame boundary. Any standard aggregate (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, and so on) can also be used with an OVER clause, computing the aggregate across a moving frame rather than the entire partition.

Beyond the basics, there's support for the EXCLUDE clause (EXCLUDE CURRENT ROW, EXCLUDE GROUP, EXCLUDE TIES), the FILTER clause for conditional aggregation within windows, IGNORE NULLS for value functions, DISTINCT aggregates in window context, and the QUALIFY clause for filtering on window function results without wrapping things in a subquery.

One feature I find particularly useful: you can specify a secondary ordering for value functions separate from the frame ordering. Something like `FIRST_VALUE(price ORDER BY timestamp)` lets you pick the first value according to one sort while the frame itself is ordered differently. Under the hood, this is handled via a separate `arg_orders` mechanism in the parser and executor.

## Under the Hood: Execution Strategies

Not all window functions get the same treatment at execution time. The engine picks from several evaluation strategies depending on the function type, frame specification, and partition structure.

### Streaming Evaluation

When a window function has no PARTITION BY and no ORDER BY (essentially operating over the entire input as one unordered partition), DuckDB can sometimes use a streaming approach. The `PhysicalStreamingWindow` operator processes input in a single pass without buffering the entire partition. This works for ROW_NUMBER (which just increments a counter), unpartitioned running aggregates with an `UNBOUNDED PRECEDING` to `CURRENT ROW` frame, and LEAD/LAG with constant offsets small enough to fit in a fixed-size ring buffer. Skipping the overhead of sorting, partitioning, and building tree structures makes it substantially faster for these common cases.

There's one hard constraint though. No partitions, no ordering clauses, no EXCLUDE mode. Any of those present? Falls back to the full window operator.

### The Segment Tree

For aggregate window functions with sliding frames (like `SUM(x) OVER (ORDER BY ts ROWS BETWEEN 10 PRECEDING AND CURRENT ROW)`), DuckDB builds a segment tree over the partition data. Classic data structures approach. The tree pre-computes partial aggregates at different granularity levels so any contiguous range can be answered by combining O(log n) pre-computed nodes instead of scanning the entire frame from scratch.

The implementation uses a fanout of 16, meaning each internal node covers 16 children, and the tree gets built in parallel across threads. Each thread claims chunks of work at each level using atomic counters; a thread that finishes its level early waits briefly for others before the next level starts.

Here's where it gets interesting. Order-insensitive aggregates (like SUM or COUNT) can combine the left and right ragged leaf portions and tree levels in any order. But order-sensitive ones (like `STRING_AGG`) need a specific sequence: left leaves first, then tree levels, then right leaves, preserving input ordering.

The segment tree also handles the EXCLUDE clause by splitting evaluation into left-of-exclusion and right-of-exclusion parts, computing each independently, then combining the results.

### Rank and Peer Tracking

Ranking functions take a completely different path. Instead of aggregating values, they need to identify partition boundaries and peer groups (rows with equal ORDER BY values). The executor maintains running state for the current rank, dense rank, and equality count, resetting at partition boundaries and incrementing at peer boundaries.

DENSE_RANK has a quirk worth mentioning. Catching up after a seek requires counting the number of order-mask bits between the partition start and the current row, which amounts to counting how many distinct peer groups exist in that range. The implementation walks the validity mask entry by entry, using bulk counting for aligned entries and bit-by-bit counting for ragged edges.

PERCENT_RANK and CUME_DIST are simpler: `(rank - 1) / (partition_size - 1)` for percent rank, `peer_end / partition_size` for cumulative distribution.

### Value Functions and Index Trees

FIRST_VALUE, LAST_VALUE, NTH_VALUE, LEAD, and LAG need to locate specific rows within frames or partitions. When a secondary ordering is specified (that `arg_orders` feature I mentioned), DuckDB constructs an index tree, basically a merge sort tree that maps between the secondary sort order and physical row positions. This allows O(n log n) lookups for operations like "find the k-th element in this frame according to a different sort order."

How does LEAD/LAG work with secondary ordering? First compute the ROW_NUMBER of the current row in that secondary sort order, then adjust by the offset, then use the index tree to find the physical row at that adjusted position. Both the rank computation and the position lookup run in O(n log n), which keeps the overall complexity reasonable.

## The QUALIFY Clause and Top-N Optimization

One of the more interesting optimizations here is top-N window elimination. That extremely common pattern where you rank rows then filter to the top N per group, like `ROW_NUMBER() OVER (PARTITION BY group ORDER BY value DESC) <= K`, gets rewritten into a grouped aggregate using `arg_min` or `arg_max` with an N parameter.

Instead of sorting each partition and numbering every row only to throw most of them away, the rewrite replaces the entire window + filter construct with a single aggregate that keeps only the top K values per group. For K > 1, the aggregate result then gets unnested back into individual rows.

This can produce dramatic speedups. But it recently revealed a fun trade-off.

The `arg_min_max_n` aggregate pre-allocates all K slots upfront. When the actual number of rows per group is much smaller than K (say, groups of 3 but K = 50), those nearly-empty allocations across many groups can eat far more memory than the original approach would have. One reported issue showed memory usage tripling and blowing past configured limits. The fix being discussed involves either capping the rewrite for large K values or changing the heap allocation to grow lazily.

Honestly, this surprised me. An optimization that makes things faster but uses 3x the memory is the kind of thing you only discover with real workloads.

## Gotchas and Surprising Behaviors

Working through DuckDB's issue tracker reveals several patterns that trip people up.

LAG and LEAD ignore frame specifications. This follows the SQL standard and matches PostgreSQL behavior, but it catches people off guard. If you write `LAG(ts) OVER (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW)`, the function will still look at the previous row in partition order, not constrained to the frame. The workaround is a secondary ordering: `LAG(ts ORDER BY ts)` respects it.

QUALIFY filters after window computation, which matters when you have multiple windowed conditions. Say you're filtering on `COUNT(DISTINCT x) OVER (PARTITION BY a)` AND `COUNT(DISTINCT x) OVER (PARTITION BY b)`. Both conditions are evaluated before the filter applies. The intersection can then reduce the distinct count below the threshold for rows that individually passed each condition. Not a bug, but confusing if you expect the counts to hold after filtering.

There's also the window self-join rewrite, which collapses certain patterns involving multiple window functions over the same data into a single pass with a self-join. It requires the subtrees to be rebindable (essentially simple chains of scans, projections, and filters), so complex source expressions may prevent it from kicking in. The docs don't make this obvious.

## Practical Patterns

For deduplication, I'd reach for `QUALIFY ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1` over self-joins or correlated subqueries every time. The top-N rewrite turns this into an efficient grouped `arg_max`.

Gap-and-island problems pair well with `LAG` and conditional logic to detect partition boundaries, followed by `SUM` as a window function to assign group identifiers. DuckDB's streaming evaluation handles the simple LAG efficiently; the segment tree handles the running SUM.

Running distinct counts work via `COUNT(DISTINCT x) OVER (ORDER BY ts ROWS UNBOUNDED PRECEDING)`, with DuckDB using a hash table internally to track seen values. For time-based windows, RANGE mode with interval expressions does the job: `AVG(value) OVER (ORDER BY timestamp RANGE BETWEEN INTERVAL '1 HOUR' PRECEDING AND CURRENT ROW)` computes the average over all rows within the preceding hour, regardless of how many rows that includes.

## The Broader Picture

DuckDB's approach here reflects a philosophy of investing in the right data structures (segment trees, merge sort trees, token trees) and aggressive optimizations (streaming evaluation, top-N elimination, self-join rewriting) so analytical SQL runs fast on a single machine. No distributed infrastructure needed. Community discussions consistently point to its ability to handle workloads that previously demanded Spark or a cloud data warehouse; window functions are a big part of why.

It isn't without edge cases. Frame specifications and navigation functions interact in confusing ways, and the memory characteristics of certain optimizations still need tuning. But from what I can tell, the depth of the implementation, from parallel segment tree construction to secondary sort order support, shows a level of care that makes window functions in DuckDB both powerful and, I think, surprisingly practical for everyday analytical work.
