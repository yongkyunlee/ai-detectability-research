# Importing CSV and Parquet Files in DuckDB

Data ingestion is the unglamorous first step of every analytics workflow—and it is where an uncomfortable amount of time gets lost. Malformed headers, inconsistent quoting, schema mismatches between partitions, and mysterious type coercions can turn a simple "load my data" task into a debugging session. DuckDB, the in-process analytical database engine, has invested heavily in making this step as frictionless as possible. Its CSV and Parquet readers are designed to handle messy real-world files with minimal configuration, while still exposing enough knobs for the cases where automatic detection falls short.

This post covers the practical details of getting CSV and Parquet data into DuckDB: the core syntax, the auto-detection machinery, the parameters you are most likely to need, and the edge cases that trip people up.

## Reading CSV Files

The entry point is the `read_csv` function. At its simplest, you point it at a file and get a table back:

```sql
SELECT * FROM read_csv('sales_2024.csv');
```

DuckDB can also read from remote locations—HTTP URLs, S3 buckets, and other cloud storage—using the same function. For S3 access, you need the `httpfs` extension loaded and your credentials configured.

```sql
SELECT * FROM read_csv('s3://my-bucket/data/sales_2024.csv');
```

Glob patterns work for multi-file reads. If your data is split across monthly exports, you can pull them all in at once:

```sql
SELECT * FROM read_csv('exports/sales_*.csv');
```

### The CSV Sniffer

One of DuckDB's most useful features is its automatic CSV dialect detection. When you call `read_csv` without specifying parsing parameters, DuckDB's sniffer examines the first chunk of the file to determine the delimiter, quote character, escape character, whether a header row exists, and the newline format. It then infers column types based on the values it observes.

The sniffer inspects 20,480 rows by default. This is controlled by the `sample_size` parameter. For most well-formed files, the default works fine. But there is an important subtlety here: if a particular CSV feature—say, quoted fields—does not appear within the sample window, the sniffer will not detect it. A file where quoted fields first appear on row 25,000 will parse incorrectly with the default sample size, because the sniffer will have concluded that the file does not use quoting at all.

The result is usually a cryptic column-count error when the parser encounters a quoted field containing a delimiter:

```
Invalid Input Error: CSV Error on Line: 25013
Expected Number of Columns: 8 Found: 9
```

The fix is straightforward—either increase the sample size or explicitly specify the quote character:

```sql
SELECT * FROM read_csv('data.csv', sample_size=-1);
-- or
SELECT * FROM read_csv('data.csv', quote='"');
```

Setting `sample_size` to -1 scans the entire file for dialect detection. This is slower but eliminates the guessing.

### Key Parameters

Beyond auto-detection, you have granular control over parsing behavior:

- **`delimiter`** — The column separator. Detected automatically, but you can override it for tab-separated files (`delimiter='\t'`) or other non-standard formats.
- **`header`** — Whether the first row contains column names. Auto-detected, but worth setting explicitly when working with files that have unusual header patterns.
- **`skip_rows`** — Number of rows to skip before reading. Useful for files with metadata preambles.
- **`comment`** — A character that marks lines to be ignored. Common in scientific data formats.
- **`null_padding`** — When set to true, rows with fewer columns than expected get padded with NULL values instead of triggering an error. This is a lifesaver for ragged CSVs.
- **`all_varchar`** — Reads every column as VARCHAR, bypassing type inference. Useful when you want full control over type casting downstream.
- **`ignore_errors`** — Silently skips rows that do not conform to the detected schema. Handy for exploratory work on dirty data, but dangerous for production pipelines where you want to know about data quality issues.
- **`strict_mode`** — Enforces CSV standard compliance. Enabled by default. Disabling it, along with `ignore_errors`, can help when dealing with severely malformed files—ones with footer lines or inconsistent row structures.
- **`date_format` and `timestamp_format`** — Override the automatic detection of date and timestamp formats. If your file uses `DD/MM/YYYY` but the sniffer guesses `MM/DD/YYYY` (as tends to happen with ambiguous dates in the first few rows), these parameters let you specify the correct interpretation.

### CSV Gotchas

A few things to watch out for in practice:

Files with footer lines—summary rows appended below the actual data—can crash the parser when combined with `union_by_name`. The footer row gets interpreted as data with the wrong schema. Disabling `strict_mode` and enabling `ignore_errors` together is the workaround, though it is a blunt instrument.

Remote CSVs are not currently cached in DuckDB's external file cache. Every query re-downloads the entire file. If you are iterating on queries against a remote CSV, it is worth downloading the file locally or converting it to Parquet first.

Compared to some other CSV readers like pandas, polars, or R's readr, DuckDB's sniffer can be less forgiving with edge cases—particularly around quote detection outside the sample window. Explicit parameter specification is the most reliable path when working with files you have not inspected manually.

## Reading Parquet Files

Parquet is where DuckDB really shines. The columnar format aligns naturally with DuckDB's vectorized execution engine, and the reader takes full advantage of Parquet's built-in metadata to optimize query performance.

Basic usage mirrors the CSV reader:

```sql
SELECT * FROM read_parquet('analytics.parquet');
```

Multiple files can be read with glob patterns or explicit lists:

```sql
SELECT * FROM read_parquet('data/year=*/month=*/*.parquet');
SELECT * FROM read_parquet(['q1.parquet', 'q2.parquet', 'q3.parquet']);
```

### Column Pruning and Predicate Pushdown

Unlike CSV, Parquet stores data in a columnar layout with rich metadata. DuckDB exploits this in two important ways.

**Column pruning** means that if your query only references three columns out of ninety, DuckDB reads only those three columns from disk. This makes a dramatic difference for wide tables—both in I/O and memory consumption.

**Predicate pushdown** allows DuckDB to apply WHERE clause filters at the storage layer using Parquet's row group statistics. Each row group stores minimum and maximum values for every column. If your filter condition falls outside a row group's range, DuckDB skips it entirely without decompressing any data. For time-series data partitioned by date, this can reduce scan times by orders of magnitude.

### Hive Partitioning

Production data lakes often organize Parquet files into directory hierarchies that encode partition values in the path:

```
data/
  year=2023/
    month=01/
      part-00000.parquet
    month=02/
      part-00000.parquet
  year=2024/
    ...
```

DuckDB recognizes this convention with the `hive_partitioning` parameter:

```sql
SELECT * FROM read_parquet('data/**/*.parquet', hive_partitioning=true);
```

With Hive partitioning enabled, the directory structure is exposed as additional columns (`year`, `month` in this example), and filters on those columns can prune entire directories from the scan.

There is a catch in version 1.5.0, though. The engine switched to a hierarchical glob expansion strategy for S3 paths, which discovers all files before applying partition filters. In earlier versions, only matching directories were traversed. For datasets with thousands of partitions on S3, this regression can dramatically increase the number of API requests and slow down query planning. The workaround is:

```sql
SET s3_allow_recursive_globbing = false;
```

This restores the older behavior of pruning directories during traversal rather than after.

### Schema Evolution with union_by_name

Real datasets evolve over time. New columns get added, old ones get dropped, types change. When reading multiple Parquet files that do not share an identical schema, `union_by_name` reconciles the differences:

```sql
SELECT * FROM read_parquet('data/*.parquet', union_by_name=true);
```

Columns are matched by name rather than position. Missing columns are filled with NULLs. This can be combined with `hive_partitioning` for maximum flexibility when working with data that spans schema migrations.

### Other Useful Parameters

- **`filename=true`** — Adds a column containing the source file path for each row. Invaluable for debugging multi-file reads.
- **`hive_types`** — Explicitly specifies the data types for Hive partition columns, overriding automatic inference. Useful when partition values are ambiguous (e.g., `region=01` could be interpreted as an integer or a string).

### Parquet Performance on Remote Storage

Reading Parquet from S3 introduces latency patterns that differ from local reads. Expect a cold start of roughly 14-20 seconds on the first query as DuckDB fetches file metadata and caches it. Subsequent queries in the same session are much faster, often sub-second for filtered reads on moderately sized datasets.

For wide schemas (tables with many columns), the default prefetching behavior can generate a large number of individual HTTP GET requests—one per column chunk per row group. With 90+ columns, a single query can trigger thousands of S3 requests. If this becomes a bottleneck, you can disable prefetching:

```sql
SELECT * FROM read_parquet('s3://bucket/wide_table.parquet', disable_parquet_prefetching=true);
```

A related performance trap in version 1.5.0 involves the `QUALIFY ROW_NUMBER() OVER (...) = 1` pattern, which is commonly used for deduplication. An optimizer change can cause this to scan the data twice, dramatically increasing S3 request counts. Wrapping the base query in a `MATERIALIZED` CTE avoids the double scan:

```sql
WITH base AS MATERIALIZED (
    SELECT * FROM read_parquet('s3://bucket/data/*.parquet')
)
SELECT * FROM base
QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) = 1;
```

### Parquet Type Considerations

DuckDB handles most Parquet logical types correctly, but a few edge cases are worth knowing about.

**HUGEINT precision loss.** DuckDB's native 128-bit integer type does not map cleanly to a Parquet physical type. When writing HUGEINT values to Parquet, they may be stored as DOUBLE, losing precision for values that exceed the 53-bit mantissa of a double-precision float. If you need lossless round-tripping of large integers, cast to `DECIMAL(38,0)` before writing.

**GeoParquet.** As of version 1.5.0, DuckDB correctly handles GeoParquet files that specify a null CRS (coordinate reference system). Earlier versions rejected these files, even though the GeoParquet specification explicitly allows null CRS to indicate an undefined spatial reference.

**File locking.** On some platforms and language bindings, reading a Parquet file holds a lock that prevents subsequent writes to the same file. In the Julia binding, for example, you need to close the connection that performed the read before opening a new connection to write to the same path.

## CSV vs. Parquet: When to Use Which

If you control the data format, Parquet is almost always the better choice for analytical workloads. Column pruning, predicate pushdown, built-in compression, and embedded schemas eliminate entire categories of problems. The performance difference is not marginal—filtered queries on Parquet can be orders of magnitude faster than equivalent scans over CSV, especially for wide tables.

CSV still has its place. It is human-readable, universally supported, and trivial to produce from any system. For data exchange with non-technical stakeholders, one-off imports, or files under a few megabytes, CSV is perfectly adequate. DuckDB also makes it easy to convert between the two:

```sql
COPY (SELECT * FROM read_csv('input.csv')) TO 'output.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

This single statement reads a CSV, infers its schema, and writes a compressed Parquet file—often the first thing worth doing when you receive a new dataset.

## Wrapping Up

DuckDB's file readers are designed to get out of your way. The auto-detection machinery handles the common cases, explicit parameters handle the edge cases, and the optimizer ensures that Parquet reads are efficient even at scale. The main traps involve the CSV sniffer's limited sample window, Hive partition discovery on S3 in recent versions, and a handful of type-mapping quirks when writing Parquet.

For anyone moving from pandas or similar dataframe libraries to DuckDB for file processing, the shift is less about learning new syntax and more about trusting the engine to do the right thing—and knowing which knobs to turn when it does not.
