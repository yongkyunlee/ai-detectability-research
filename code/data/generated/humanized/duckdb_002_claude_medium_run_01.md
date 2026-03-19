# Importing CSV and Parquet Files in DuckDB

Getting data into an analytical database is usually the first thing that goes sideways in a data project. DuckDB handles this part well, with built-in support for both CSV and Parquet that needs zero configuration for common cases but gives you plenty of knobs when things get weird.

## Reading CSV Files

The `read_csv()` function is your main entry point for CSV ingestion, but DuckDB also recognizes file extensions directly. You can write `FROM 'sales.csv'` in the FROM clause and start querying; no function call needed. Compressed files ending in `.gz` or `.zst` work transparently too.

### The Sniffer

What makes DuckDB's CSV support interesting is its multi-phase auto-detection system, internally called the "sniffer." When you query a CSV file without specifying formatting details, DuckDB samples the first 20,480 rows and works through five stages: it identifies the dialect (delimiter, quote character, escape character, newline style), detects column types, refines those types against additional sample chunks, figures out whether the first row is a header, and applies any type overrides you've specified.

The dialect detector evaluates candidate delimiters (comma, pipe, tab, semicolon, and others), scoring them based on how consistently they produce the same column count across sampled rows. For type detection, columns are tested against a hierarchy from most specific (BOOLEAN, DATE, TIMESTAMP) down to most general (VARCHAR). Each type gets promoted upward when values don't fit.

This works well most of the time. But the sample-based approach has a known limitation: if the first 20,480 rows all have unquoted fields and a quoted field with an embedded comma shows up later, the sniffer concludes quoting isn't in use and chokes on that row. Easy fix. Specify `quote='"'` explicitly, or set `sample_size=-1` to force a full file scan.

### Parameters Worth Knowing

Beyond `sep`, `header`, and `quote`, the CSV reader has several parameters that matter for real-world data.

The `ignore_errors` and `store_rejects` options let you skip malformed rows and optionally route them to a separate table for inspection, rather than aborting the entire read. If your files have inconsistent column counts, `null_padding` fills in NULL for shorter rows, which I've found useful when combining exports from different time periods. European-style number formatting (where commas and periods swap roles) is handled through `decimal_separator` and `thousands`. A `comment` character can be set to skip full-line comments, and `parallel` is on by default so DuckDB scans even a single large CSV across multiple threads.

For multi-file reads (a directory of monthly exports, say), DuckDB sniffs the first file fully and then does a minimal two-row check on each subsequent file to verify schema compatibility. The `union_by_name` option handles schema evolution across files by aligning columns by name rather than position.

## Reading Parquet Files

Parquet is where DuckDB's analytical architecture really pays off. Because the format is columnar and self-describing, DuckDB can pull tricks with it that aren't possible with CSV.

### Column Pruning and Predicate Pushdown

When you write `SELECT revenue, region FROM read_parquet('data/*.parquet') WHERE year = 2024`, DuckDB reads only the `revenue` and `region` columns from disk. Everything else gets ignored entirely. On wide tables, this column pruning can reduce I/O by orders of magnitude.

DuckDB also pushes filter predicates down into the Parquet reader. Each file is divided into row groups, and each row group stores min/max statistics for its columns. If a row group's max value for `year` is 2023, it gets skipped without reading a single data page. Combine that with hive-style partitioning (where directory names like `year=2024/month=03/` encode filter values) and whole files can be eliminated before any data is touched.

### Remote File Handling

DuckDB reads Parquet directly from S3, GCS, or HTTP endpoints. For remote files, it uses a prefetching strategy to cut down on network round trips: it estimates the footer size as roughly 1/1000th of the total file size and fetches between 16KB and 256KB in a single request to capture both the footer metadata and the initial data pages.

Community benchmarks tell an interesting story here. On 20GB of ZSTD-compressed Parquet spread across 161 files, local DuckDB hit a median query time around 280ms on a 32-thread machine. That same data on Cloudflare R2 yielded 500ms to 1,100ms medians for warm queries, but cold starts (dominated by metadata fetching) took 14 to 20 seconds. BigQuery clocked in around 2,800ms and Athena around 4,200ms per query on the same dataset.

### Hive Partitioning Details

Setting `hive_partitioning=true` tells DuckDB to interpret directory structures as partition columns. Works well in general, but there's a regression in version 1.5.0 worth knowing about: the engine now discovers all files matching a glob pattern before applying partition filters, rather than pruning during discovery. On an S3 bucket with 122 partition files where only 39 match your filter, all 122 get HTTP requests for footer reads. Not great. Setting `s3_allow_recursive_globbing=false` restores the older, more efficient behavior.

## CSV vs. Parquet: When to Use Which

The format choice usually comes down to pipeline stage. CSV is universal; every tool reads it, every system exports it, and DuckDB's sniffer makes ad-hoc querying almost frictionless. But CSV files carry costs. They must be scanned row by row, there's no way to skip columns or row groups, and types have to be inferred rather than read from metadata.

Parquet files carry their schema, compression, and statistics along for the ride. For repeated analytical queries, the difference is real: column pruning alone can cut the data read by 10x or more on a table with dozens of columns. Writing results out with `COPY ... TO ... (FORMAT parquet, COMPRESSION zstd)` also tends to produce files 3-5x smaller than gzipped CSV.

One gotcha: DuckDB writes HUGEINT values as DOUBLE when producing Parquet, which loses precision for very large integers. Casting to `DECIMAL(38,0)` before the write preserves full values.

For most analytical work, the pattern is straightforward: ingest raw CSV once, convert to Parquet for ongoing analysis. Honestly, the conversion step is fast enough that it rarely feels like extra work.
