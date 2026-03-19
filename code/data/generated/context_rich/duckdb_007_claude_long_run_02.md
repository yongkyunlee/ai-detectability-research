# Beneath the OVER Clause: How DuckDB Implements Window Functions

Window functions sit at the intersection of expressiveness and computational difficulty in SQL. They let you rank rows, compute running totals, look ahead and behind in ordered sequences, and perform aggregations across sliding frames — all without collapsing rows the way GROUP BY does. DuckDB has invested considerable engineering effort into making these operations fast, correct, and memory-efficient on a single machine. This post walks through how DuckDB handles window functions internally, what SQL patterns you can write with them, and where the real-world rough edges still show up.

## The SQL Surface: What You Can Express

DuckDB supports the full SQL:2003 window function specification, and then some. The OVER clause can include PARTITION BY, ORDER BY, and frame specifications using ROWS, RANGE, or GROUPS modes. The supported built-in window functions span several categories:

**Ranking functions** — `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `PERCENT_RANK()`, `CUME_DIST()`, and `NTILE()`. These assign positional or statistical labels to each row within its partition.

**Value functions** — `FIRST_VALUE()`, `LAST_VALUE()`, `NTH_VALUE()`, `LEAD()`, and `LAG()`. These retrieve values from specific positions relative to the current row or frame boundary.

**Aggregate window functions** — Any standard aggregate (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, and so on) can be used as a window function with an OVER clause, computing the aggregate across a moving frame rather than the entire partition.

DuckDB also supports the EXCLUDE clause (EXCLUDE CURRENT ROW, EXCLUDE GROUP, EXCLUDE TIES), the FILTER clause for conditional aggregation within windows, IGNORE NULLS for value functions, DISTINCT aggregates in window context, and the QUALIFY clause for filtering on window function results without wrapping in a subquery.

A particularly useful feature is the ability to specify a secondary ordering for value functions separate from the frame ordering. For example, `FIRST_VALUE(price ORDER BY timestamp)` lets you pick the first value according to one sort while the frame itself is ordered differently. This is distinct from the frame's own ORDER BY and is handled via a separate `arg_orders` mechanism in the parser and executor.

## Under the Hood: Execution Strategies

DuckDB does not treat all window functions the same way at execution time. The engine selects from several evaluation strategies depending on the function type, frame specification, and partition structure.

### Streaming Evaluation

When a window function has no PARTITION BY and no ORDER BY — essentially operating over the entire input as a single unordered partition — DuckDB can sometimes use a streaming approach. The `PhysicalStreamingWindow` operator processes input in a single pass without buffering the entire partition. This works for ROW_NUMBER (which just increments a counter), unpartitioned running aggregates with an `UNBOUNDED PRECEDING` to `CURRENT ROW` frame, and LEAD/LAG with constant offsets small enough to fit in a fixed-size ring buffer. The streaming operator avoids the overhead of sorting, partitioning, and building tree structures, making it substantially faster for these common cases.

There is one critical constraint: the function must have no partitions, no ordering clauses, and no EXCLUDE mode. If any of those are present, the engine falls back to the full window operator.

### The Segment Tree

For aggregate window functions with sliding frames (like `SUM(x) OVER (ORDER BY ts ROWS BETWEEN 10 PRECEDING AND CURRENT ROW)`), DuckDB builds a segment tree over the partition data. This is a classic data structures approach: the tree pre-computes partial aggregates at different granularity levels, so that any contiguous range can be answered by combining O(log n) pre-computed nodes instead of scanning the entire frame from scratch.

The implementation uses a fanout of 16 (meaning each internal node covers 16 children), and the tree is built in parallel across threads. Each thread claims chunks of work at each level using atomic counters, and a thread that finishes its level early waits briefly for others before the next level starts.

An important optimization handles order-sensitive vs. order-insensitive aggregates differently. For aggregates where the combination order does not matter (like SUM or COUNT), the left and right ragged leaf portions and the tree levels can be combined in any order. For order-sensitive aggregates (like `STRING_AGG`), the engine evaluates left leaves first, then the tree levels, then right leaves, preserving the input ordering.

The segment tree also handles the EXCLUDE clause by splitting evaluation into left-of-exclusion and right-of-exclusion parts, computing each independently, then combining the results.

### Rank and Peer Tracking

Ranking functions take a different path entirely. Rather than aggregating values, they need to identify partition boundaries and peer groups (rows with equal ORDER BY values). The executor maintains running state for the current rank, dense rank, and equality count, resetting at partition boundaries and incrementing at peer boundaries.

For DENSE_RANK specifically, catching up after a seek requires counting the number of order-mask bits between the partition start and the current row — essentially counting how many distinct peer groups exist in that range. The implementation walks the validity mask entry by entry, using bulk counting for aligned entries and bit-by-bit counting for ragged edges.

PERCENT_RANK and CUME_DIST are computed from the rank values and partition sizes using straightforward formulas: `(rank - 1) / (partition_size - 1)` for percent rank and `peer_end / partition_size` for cumulative distribution.

### Value Functions and Index Trees

FIRST_VALUE, LAST_VALUE, NTH_VALUE, LEAD, and LAG need to locate specific rows within frames or partitions. When a secondary ordering is specified (the `arg_orders` feature), DuckDB constructs an index tree — a merge sort tree that maps between the secondary sort order and physical row positions. This allows O(n log n) lookups for operations like "find the k-th element in this frame according to a different sort order."

The LEAD/LAG implementation with secondary ordering follows a specific algorithm: first compute the ROW_NUMBER of the current row in the secondary sort order, then adjust by the offset, then use the index tree to find the physical row at that adjusted position. Both the rank computation and the position lookup run in O(n log n), keeping the overall complexity manageable.

## The QUALIFY Clause and Top-N Optimization

One of the more interesting optimizations in DuckDB's window function pipeline is the top-N window elimination. The extremely common pattern of ranking rows and then filtering to the top N per group — `ROW_NUMBER() OVER (PARTITION BY group ORDER BY value DESC) <= K` — gets rewritten by the optimizer into a grouped aggregate using `arg_min` or `arg_max` with an N parameter.

Instead of sorting each partition and numbering every row only to discard most of them, the optimizer replaces the entire window + filter construct with a single aggregate that keeps only the top K values per group. For K > 1, the aggregate result is then unnested back into individual rows.

This transformation can produce dramatic speedups. However, it recently revealed an interesting trade-off: the `arg_min_max_n` aggregate pre-allocates all K slots upfront. When the actual number of rows per group is much smaller than K (say, groups of 3 but K = 50), those nearly-empty allocations across many groups can consume far more memory than the original window + filter approach would have. A reported issue showed memory usage tripling and blowing past configured limits. The fix being discussed involves either capping the optimization for large K values or changing the heap allocation strategy to grow lazily.

## Gotchas and Surprising Behaviors

Working through DuckDB's issue tracker reveals several patterns that trip up users of window functions:

**LAG/LEAD ignore frame specifications.** This follows the SQL standard and matches PostgreSQL behavior, but it catches people off guard. If you write `LAG(ts) OVER (ORDER BY ts RANGE BETWEEN INTERVAL 15 MINUTES PRECEDING AND CURRENT ROW)`, the LAG function will still look at the previous row in partition order, not constrained to the frame. The workaround is to use a secondary ordering: `LAG(ts ORDER BY ts)` respects the frame.

**QUALIFY filters after window computation.** When you use multiple windowed conditions in QUALIFY (like filtering on `COUNT(DISTINCT x) OVER (PARTITION BY a)` AND `COUNT(DISTINCT x) OVER (PARTITION BY b)`), both conditions are evaluated before the filter. The intersection can then reduce the distinct count below the threshold for rows that individually passed each filter — not a bug, but confusing if you expect the counts to hold after filtering.

**The window self-join optimization** rewrites certain patterns involving multiple window functions over the same data into a single pass with a self-join. This requires the subtrees to be rebindable (essentially, simple chains of scans, projections, and filters), so complex source expressions may prevent the optimization from kicking in.

## Practical Patterns

Here are a few patterns that take advantage of DuckDB's window function capabilities effectively:

For deduplication, prefer `QUALIFY ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1` over self-joins or correlated subqueries. The top-N optimizer will rewrite this into an efficient grouped `arg_max`.

For gap-and-island problems, combine `LAG` with conditional logic to detect partition boundaries, then use `SUM` as a window function to assign group identifiers. DuckDB's streaming evaluation handles the simple LAG efficiently, and the segment tree handles the running SUM.

For running distinct counts, use `COUNT(DISTINCT x) OVER (ORDER BY ts ROWS UNBOUNDED PRECEDING)`. DuckDB handles DISTINCT in window aggregates using a hash table that tracks seen values.

For time-based windows, use RANGE mode with interval expressions: `AVG(value) OVER (ORDER BY timestamp RANGE BETWEEN INTERVAL '1 HOUR' PRECEDING AND CURRENT ROW)`. This computes the average over all rows within the preceding hour, regardless of how many rows that includes.

## The Broader Picture

DuckDB's window function implementation reflects a broader philosophy: invest in sophisticated data structures (segment trees, merge sort trees, token trees) and aggressive optimization (streaming evaluation, top-N elimination, self-join rewriting) to make analytical SQL fast on a single machine without requiring distributed infrastructure. The community discussions around DuckDB consistently highlight its ability to handle analytical workloads that previously demanded Spark or a cloud data warehouse, and window functions are a big part of that story.

The system is not without its edge cases — the interaction between frame specifications and navigation functions remains a source of confusion, and the memory characteristics of certain optimizations still need tuning. But the depth of the implementation, from the parallel segment tree construction to the secondary sort order support, represents a level of engineering care that makes window functions in DuckDB both powerful and surprisingly practical for everyday analytical work.
