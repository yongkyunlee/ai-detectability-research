# Importing CSV and Parquet Files in DuckDB

Data ingestion is the unglamorous first step of every analytics workflow, and it's where an uncomfortable amount of time gets lost. Malformed headers. Inconsistent quoting. Schema mismatches between partitions, mysterious type coercions that turn a simple "load my data" task into a debugging session. DuckDB's CSV and Parquet readers are designed to handle messy real-world files with minimal configuration, while still exposing enough knobs for when automatic detection falls short.

This post covers the practical details of getting CSV and Parquet data into DuckDB: core syntax, auto-detection machinery, the parameters you're most likely to need, and the edge cases that trip people up.

## Reading CSV Files

The entry point is the `read_csv` function. Point it at a file, get a table back:

```sql
SELECT * FROM read_csv('sales_2024.csv');
```

It can also read from remote locations (HTTP URLs, S3 buckets, other cloud storage) using the same function. For S3 access you need the `httpfs` extension loaded and your credentials configured.

```sql
SELECT * FROM read_csv('s3://my-bucket/data/sales_2024.csv');
```

Glob patterns work for multi-file reads. If your data is split across monthly exports, you can pull them all in at once:

```sql
SELECT * FROM read_csv('exports/sales_*.csv');
```

### The CSV Sniffer

One of DuckDB's most useful features is its automatic CSV dialect detection. When you call `read_csv` without specifying parsing parameters, the sniffer examines the first chunk of the file to figure out the delimiter, quote character, escape character, whether a header row exists, and the newline format. Column types get inferred from the values it observes.

By default, it inspects 20,480 rows. The `sample_size` parameter controls this. For most well-formed files, the default works fine. But here's the thing: if a particular CSV feature (say, quoted fields) doesn't appear within the sample window, the sniffer won't detect it. A file where quoted fields first show up on row 25,000 will parse incorrectly, because the sniffer will have decided the file doesn't use quoting at all.

You'll usually see a cryptic column-count error:

```
Invalid Input Error: CSV Error on Line: 25013
Expected Number of Columns: 8 Found: 9
```

The fix is simple. Either increase the sample size or explicitly specify the quote character:

```sql
SELECT * FROM read_csv('data.csv', sample_size=-1);
-- or
SELECT * FROM read_csv('data.csv', quote='"');
```

Setting `sample_size` to -1 scans the entire file for dialect detection. Slower, but it eliminates the guessing.

### Key Parameters

Beyond auto-detection, you've got granular control over parsing.

The `delimiter` parameter sets the column separator. It's detected automatically, but you can override it for tab-separated files (`delimiter='\t'`) or other non-standard formats. `header` controls whether the first row contains column names; also auto-detected, but worth setting explicitly for files with unusual header patterns. Got metadata preambles? `skip_rows` lets you jump past them. The `comment` parameter specifies a character that marks lines to be ignored, which comes up a lot in scientific data formats. `null_padding`, when set to true, pads short rows with NULL values instead of throwing an error (honestly, a lifesaver for ragged CSVs), and `all_varchar` reads every column as VARCHAR, bypassing type inference entirely when you want full control over casting.

Two parameters deserve a warning. `ignore_errors` silently skips rows that don't conform to the detected schema, which is handy for exploration but dangerous in production where you actually want to know about quality issues. `strict_mode` enforces CSV standard compliance and is on by default; disabling it alongside `ignore_errors` can help with severely malformed files, ones with footer lines or inconsistent row structures.

For dates and timestamps, `date_format` and `timestamp_format` override automatic detection. If your file uses `DD/MM/YYYY` but the sniffer guesses `MM/DD/YYYY` (as tends to happen with ambiguous dates in the first few rows), these let you specify the correct interpretation.

### CSV Gotchas

Files with footer lines (summary rows appended below the actual data) can crash the parser when combined with `union_by_name`. The footer gets interpreted as data with the wrong schema, and the fix of disabling `strict_mode` plus enabling `ignore_errors` is a blunt instrument.

Remote CSVs aren't cached. Every query re-downloads the entire file. If you're iterating on queries against a remote CSV, download it locally or convert to Parquet first.

I've found DuckDB's sniffer to be less forgiving than pandas, polars, or R's readr with edge cases, particularly around quote detection outside the sample window. When working with files you haven't inspected manually, explicit parameter specification is the safest bet.

## Reading Parquet Files

Parquet is where DuckDB really shines. The columnar format aligns naturally with its vectorized execution engine, and the reader takes full advantage of Parquet's built-in metadata to speed up queries.

Basic usage mirrors the CSV reader:

```sql
SELECT * FROM read_parquet('analytics.parquet');
```

Multiple files work with glob patterns or explicit lists:

```sql
SELECT * FROM read_parquet('data/year=*/month=*/*.parquet');
SELECT * FROM read_parquet(['q1.parquet', 'q2.parquet', 'q3.parquet']);
```

### Column Pruning and Predicate Pushdown

Unlike CSV, Parquet stores data in a columnar layout with rich metadata. DuckDB exploits this in two important ways.

**Column pruning** means that if your query only references three columns out of ninety, only those three get read from disk. For wide tables, the difference in I/O and memory consumption is massive.

**Predicate pushdown** lets DuckDB apply WHERE clause filters at the storage layer using row group statistics. Each row group stores min and max values for every column; if your filter falls outside a group's range, it gets skipped entirely without decompressing anything. For time-series data partitioned by date, this can reduce scan times by orders of magnitude.

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

With it enabled, the directory structure shows up as additional columns (`year`, `month` in this example), and filters on those columns can prune entire directories from the scan.

There's a catch in version 1.5.0. The engine switched to a hierarchical glob expansion strategy for S3 paths, which discovers all files before applying partition filters. Previous versions only traversed matching directories. For datasets with thousands of partitions on S3, this regression can dramatically increase API requests and slow down query planning. The workaround:

```sql
SET s3_allow_recursive_globbing = false;
```

This restores the older behavior of pruning directories during traversal rather than after.

### Schema Evolution with union_by_name

Real datasets evolve. New columns get added. Old ones get dropped. Types change. When reading multiple Parquet files that don't share an identical schema, `union_by_name` reconciles the differences:

```sql
SELECT * FROM read_parquet('data/*.parquet', union_by_name=true);
```

Columns are matched by name rather than position, and missing ones get filled with NULLs. You can combine this with `hive_partitioning` for flexibility when your data spans schema migrations.

### Other Useful Parameters

Setting `filename=true` adds a column containing the source file path for each row. I've found it really useful for debugging multi-file reads. The `hive_types` parameter lets you explicitly set data types for Hive partition columns, overriding automatic inference; useful when partition values are ambiguous (e.g., `region=01` could be read as an integer or a string).

### Parquet Performance on Remote Storage

Reading Parquet from S3 introduces latency patterns that differ from local reads. Expect a cold start of roughly 14-20 seconds on the first query as DuckDB fetches and caches file metadata. After that, queries in the same session are much faster, often sub-second for filtered reads on moderately sized datasets.

For wide schemas, the default prefetching behavior can generate a large number of individual HTTP GET requests, one per column chunk per row group. With 90+ columns, a single query can trigger thousands of S3 requests. If that becomes a bottleneck, disable prefetching:

```sql
SELECT * FROM read_parquet('s3://bucket/wide_table.parquet', disable_parquet_prefetching=true);
```

There's a related performance trap in version 1.5.0 involving the `QUALIFY ROW_NUMBER() OVER (...) = 1` pattern, commonly used for deduplication. An optimizer change can cause this to scan the data twice, sending S3 request counts through the roof. Wrapping the base query in a `MATERIALIZED` CTE avoids the double scan:

```sql
WITH base AS MATERIALIZED (
    SELECT * FROM read_parquet('s3://bucket/data/*.parquet')
)
SELECT * FROM base
QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) = 1;
```

### Parquet Type Considerations

DuckDB handles most Parquet logical types correctly, but a few edge cases are worth knowing about.

**HUGEINT precision loss.** The native 128-bit integer type doesn't map cleanly to a Parquet physical type. When writing HUGEINT values to Parquet, they may get stored as DOUBLE, losing precision for values exceeding the 53-bit mantissa of a double-precision float. If you need lossless round-tripping of large integers, cast to `DECIMAL(38,0)` before writing.

**GeoParquet.** As of version 1.5.0, DuckDB correctly handles GeoParquet files that specify a null CRS (coordinate reference system). Earlier versions rejected these, even though the spec explicitly allows null CRS to indicate an undefined spatial reference.

**File locking.** On some platforms and language bindings, reading a Parquet file holds a lock that prevents subsequent writes to the same path. In the Julia binding, for example, you need to close the connection that performed the read before opening a new one to write.

## CSV vs. Parquet: When to Use Which

If you control the data format, Parquet is almost always the better choice for analytical workloads. Column pruning, predicate pushdown, built-in compression, and embedded schemas eliminate entire categories of problems. The performance gap isn't marginal; filtered queries on Parquet can be orders of magnitude faster than equivalent scans over CSV, especially for wide tables.

CSV still has its place. It's human-readable, universally supported, and trivial to produce from any system. For data exchange with non-technical stakeholders, one-off imports, or files under a few megabytes, it works just fine. Converting between the two is easy:

```sql
COPY (SELECT * FROM read_csv('input.csv')) TO 'output.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

That single statement reads a CSV, infers its schema, and writes a compressed Parquet file. Often the first thing I do when I get a new dataset.

## Wrapping Up

The main traps to remember: the CSV sniffer's limited sample window, Hive partition discovery on S3 in recent versions, and a handful of type-mapping quirks when writing Parquet. If you're coming from pandas or a similar dataframe library, the shift is less about syntax and more about trusting the engine, then knowing which knobs to turn when it gets something wrong.
