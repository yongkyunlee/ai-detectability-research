---
source_url: https://duckdb.org/2024/12/05/csv-files-dethroning-parquet-or-not.html
author: "Pedro Holanda"
platform: duckdb.org (official blog)
scope_notes: "Trimmed from a 13-min read comparing CSV and Parquet formats. Focused on file format differences, DuckDB's CSV reader improvements, and performance benchmarks. Original ~3000 words; trimmed to ~500 words."
---

Data analytics relies on two primary storage formats: human-readable text files like CSV and performance-driven binary files like Parquet.

## CSV Files

Data is commonly stored in human-readable formats including JSON and CSV files. Historically, CSV files earned a reputation for slowness and operational difficulty. Traditional workflows required manual schema discovery via text editor inspection, table creation with discovered schema, manual dialect identification (quote characters, delimiters), file loading using `COPY` statements with dialect configuration, and finally query execution.

Storage efficiency suffers significantly. Data stores as strings throughout; numeric values like `1000000000` consume 10 bytes rather than 4 bytes for int32 storage. Row-wise layout eliminates opportunities for lightweight columnar compression.

## Parquet Files

Parquet files provide columnar data storage, multiple compression techniques, row group partitioning, row group statistical metadata, and embedded schema definitions. Reading becomes straightforward with well-defined schemas. Parallelization works naturally, with threads processing independent row groups.

## Reading CSV Files in DuckDB

Recent DuckDB releases prioritized both usable and performant CSV scanning, featuring a custom CSV sniffer, parallelization algorithm, buffer management, casting mechanisms, and a state machine-based parser. Users now query CSV files directly:

```sql
FROM 'path/to/file.csv';
```

Or create tables without predefined schemas:

```sql
CREATE TABLE t AS FROM 'path/to/file.csv';
```

## Performance Comparison

Testing used Apple M1 Max, 64 GB RAM, TPC-H scale factor 20, median times from 5 runs. Schemas were provided upfront and `preserve_insertion_order = false` was set.

### Creating Tables

| Format           | Time (s) | Size (GB) |
|------------------|----------|-----------|
| CSV              | 11.76    | 15.95     |
| Parquet Snappy   | 5.21     | 3.78      |
| Parquet Zstd     | 5.52     | 3.22      |

Parquet files occupy approximately 5x less space. CSV loading runs roughly 2x slower.

### Directly Querying Files (TPC-H Q01)

```sql
SELECT
    l_returnflag, l_linestatus,
    sum(l_quantity) AS sum_qty,
    sum(l_extendedprice) AS sum_base_price,
    sum(l_extendedprice * (1 - l_discount)) AS sum_disc_price,
    avg(l_quantity) AS avg_qty, avg(l_discount) AS avg_disc,
    count(*) AS count_order
FROM lineitem
WHERE l_shipdate <= CAST('1996-09-02' AS date)
GROUP BY l_returnflag, l_linestatus
ORDER BY l_returnflag, l_linestatus;
```

| Format           | Time (s) |
|------------------|----------|
| CSV              | 6.72     |
| Parquet Snappy   | 0.88     |
| Parquet Zstd     | 0.95     |

Direct file querying reveals approximately 7x performance differential. Parquet skips row groups failing the filter condition and individual non-matching rows. Columnar orientation enables complete column skipping for non-projected fields. CSV readers cannot efficiently skip data sections lacking partitions.

## Conclusion

CSV scanning performance has dramatically improved over the years. Earlier performance gaps would have exceeded one order of magnitude. However, sophisticated CSV readers should not obscure reality: data thrives in self-describing, column-binary compressed formats like Parquet or DuckDB's native format. These maintain substantially smaller sizes and consistent characteristics. Direct Parquet file querying provides significant benefits through efficient projection and filter pushdown and available statistics.
