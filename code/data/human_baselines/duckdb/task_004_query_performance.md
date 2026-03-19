---
source_url: https://duckdb.org/2025/09/24/sorting-again.html
author: "Laurens Kuiper"
platform: duckdb.org (official blog)
scope_notes: "Trimmed from a 16-min read on DuckDB's sort redesign. Focused on key normalization, sorting algorithm choices, and benchmark results. Original ~4000 words; trimmed to ~500 words."
---

After four years, the DuckDB team decided to redesign DuckDB's sort implementation, again. DuckDB v1.4.0 includes a complete redesign that integrates a new spillable page layout for larger-than-memory query processing.

## Key Normalization

Database systems that do not compile required types into the query plan suffer from interpretation overhead, especially when comparing tuples while sorting. DuckDB's new implementation uses the `create_sort_key` function:

```sql
SELECT
    s,
    create_sort_key(s, 'asc nulls last') AS k1,
    create_sort_key(s, 'asc nulls first') AS k2
FROM
    (VALUES ('hello'), ('world'), (NULL)) t(s);
```

Because of the binary-comparable nature of the constructed BLOB, `ORDER BY x DESC NULLS LAST, y ASC NULLS FIRST` becomes equivalent to `ORDER BY create_sort_key(x, 'DESC NULLS LAST', y, 'ASC NULLS FIRST')`.

If the resulting BLOB is known to be less than 16 bytes, DuckDB converts it to unsigned integers for static integer comparisons rather than string comparisons, which is significantly faster.

## Sorting Algorithm

DuckDB uses a combination of three sorting algorithms for good performance and high adaptivity to pre-sorted data: **Vergesort** detects and merges runs of nearly sorted data, reducing effort for time-series data stored in sorted order. **Ska Sort** performs an adaptive Most Significant Digit (MSD) radix sort on the first 64-bit integer. **Pattern-defeating quicksort** handles remaining cases.

## Parallel K-Way Merge

Prior to v1.4.0, DuckDB materialized fully-merged data. The new k-way merge outputs chunks of sorted data directly from sorted runs in a streaming fashion, meaning data can be output before the full merge has been computed. For large `ORDER BY ... LIMIT ...` queries, the merge can be stopped at any point, so the cost of fully merging is never incurred.

The team generalized Merge Path to k sorted runs, allowing arbitrary output chunk sizes with skew-resistant parallelism.

## Benchmark Results

Tests run on M1 Max MacBook Pro with 10 threads and 64 GB of memory, median of 5 runs.

### Raw Integer Sorting Performance

| Input        | Rows (M) | Old (s) | New (s) | Speedup |
|-------------|----------|---------|---------|---------|
| Ascending   | 1000     | 15.302  | 1.475   | 10.4x   |
| Descending  | 1000     | 15.789  | 1.712   | 9.2x    |
| Random      | 1000     | 17.554  | 6.493   | 2.7x    |

The new implementation is highly adaptive to pre-sorted data: roughly 10x faster at ascending/descending data and more than 2x faster at sorting randomly ordered data.

### Wide Table Sorting (TPC-H lineitem, 15 columns)

| Scale Factor | Old (s)  | New (s) | Speedup |
|-------------|----------|---------|---------|
| 1           | 0.328    | 0.189   | 1.7x    |
| 10          | 3.353    | 1.520   | 2.2x    |
| 100         | 273.982  | 80.919  | 3.4x    |

At scale factor 100, data no longer fits in memory. The new k-way merge sort reduces data movement and I/O, proving much more efficient for sorting wide tables than the old cascaded 2-way merge sort.

### Thread Scaling (100M random integers)

| Threads | Old Speedup vs. 1T | New Speedup vs. 1T |
|---------|--------------------|--------------------|
| 2       | 1.5x               | 1.9x               |
| 4       | 2.3x               | 3.5x               |
| 8       | 3.5x               | 6.5x               |

The new implementation's parallel scaling is dramatically better than the old implementation.
