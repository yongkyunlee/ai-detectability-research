# Importing CSV and Parquet Files in DuckDB

Getting data into an analytical database is often the first obstacle in any data project. DuckDB handles this remarkably well, offering first-class support for both CSV and Parquet through built-in functions that require zero configuration for common cases but expose deep control when you need it.

## Reading CSV Files

The `read_csv()` function is the main entry point for CSV ingestion. DuckDB also recognizes file extensions directly, so a bare `FROM 'sales.csv'` in the FROM clause is enough to start querying a file without any explicit function call. Compressed variants ending in `.gz` or `.zst` are handled transparently as well.

### The Sniffer

What makes DuckDB's CSV support stand out is its multi-phase auto-detection system, internally called the "sniffer." When you run a query against a CSV file without specifying formatting details, DuckDB samples the first 20,480 rows and works through five stages: it identifies the dialect (delimiter, quote character, escape character, newline style), detects column types, refines those types against additional sample chunks, determines whether the first row is a header, and finally applies any user-specified type overrides.

The dialect detector evaluates candidate delimiters — comma, pipe, tab, semicolon, and others — and scores them based on how consistently they produce the same number of columns across sampled rows. For type detection, columns are tested against a hierarchy ranging from the most specific (BOOLEAN, DATE, TIMESTAMP) down to the most general (VARCHAR), with each type promoted upward when values don't fit.

This works well in the vast majority of cases, but the sample-based approach has a known limitation. If the first 20,480 rows contain only unquoted fields and a quoted field with an embedded comma appears later, the sniffer will conclude that no quoting is in use and then choke on that later row. The fix is straightforward: either specify `quote='"'` explicitly or set `sample_size=-1` to force scanning the entire file.

### Parameters Worth Knowing

Beyond the basics like `sep`, `header`, and `quote`, DuckDB's CSV reader exposes several parameters that matter for real-world data:

- **`ignore_errors`** and **`store_rejects`** let you skip malformed rows and optionally route them into a separate table for inspection rather than aborting the entire read.
- **`null_padding`** fills in NULL for rows that have fewer columns than expected, which is useful for appending files with inconsistent structures.
- **`decimal_separator`** and **`thousands`** accommodate European-style number formatting where commas and periods swap roles.
- **`comment`** designates a character that marks full-line comments to skip.
- **`parallel`** is enabled by default, allowing DuckDB to scan even a single large CSV across multiple threads.

For multi-file reads — say, a directory of monthly exports — DuckDB sniffs the first file fully and then performs a minimal two-row check on subsequent files to verify schema compatibility. The `union_by_name` option handles schema evolution across files by aligning columns by name rather than position.

## Reading Parquet Files

Parquet is where DuckDB's analytical architecture really shines. Because Parquet is a columnar, self-describing format, DuckDB can exploit its structure for significant performance gains that simply aren't possible with CSV.

### Column Pruning and Predicate Pushdown

When you write `SELECT revenue, region FROM read_parquet('data/*.parquet') WHERE year = 2024`, DuckDB reads only the `revenue` and `region` columns from disk, ignoring every other column in the file entirely. This column pruning can reduce I/O by orders of magnitude on wide tables.

On top of that, DuckDB pushes filter predicates down into the Parquet reader. Each Parquet file is divided into row groups, and each row group stores min/max statistics for its columns. If a row group's maximum value for `year` is 2023, DuckDB skips that entire group without reading a single data page. Combined with hive-style partitioning — where directory names like `year=2024/month=03/` encode filter values — whole files can be eliminated before any data is touched.

### Remote File Handling

DuckDB can read Parquet directly from S3, GCS, or HTTP endpoints. For remote files, it employs a prefetching strategy to minimize network round trips: it estimates the footer size as roughly 1/1000th of the total file size and fetches between 16KB and 256KB in a single request to capture both the footer metadata and the initial data pages.

Benchmarks from the community tell an interesting story here. On 20GB of ZSTD-compressed Parquet spread across 161 files, local DuckDB achieved a median query time around 280ms on a 32-thread machine. The same data on Cloudflare R2 yielded 500ms to 1,100ms medians for warm queries, but cold starts — dominated by metadata fetching — took 14 to 20 seconds. For comparison, BigQuery clocked in around 2,800ms and Athena around 4,200ms per query on the same data.

### Hive Partitioning Details

Enabling `hive_partitioning=true` tells DuckDB to interpret directory structures as partition columns. This works well, but there is a notable regression in version 1.5.0: the engine now discovers all files matching a glob pattern before applying partition filters, rather than pruning during discovery. On an S3 bucket with 122 partition files where only 39 match your filter, all 122 receive HTTP requests for footer reads. Setting `s3_allow_recursive_globbing=false` restores the older, more efficient behavior.

## CSV vs. Parquet: When to Use Which

The choice between formats often comes down to the stage of your pipeline. CSV is universal. Every tool reads it, every system exports it, and DuckDB's sniffer makes ad-hoc querying nearly frictionless. But CSV files carry inherent costs: they must be scanned sequentially row by row, there is no way to skip columns or row groups, and type information must be inferred rather than read from metadata.

Parquet files carry their schema, compression, and statistics with them. For repeated analytical queries, the difference is substantial — column pruning alone can reduce the data read by 10x or more on a table with dozens of columns. Writing results out to Parquet with `COPY ... TO ... (FORMAT parquet, COMPRESSION zstd)` also tends to produce files 3-5x smaller than gzipped CSV.

One practical gotcha: DuckDB writes HUGEINT values as DOUBLE when producing Parquet, which loses precision for very large integers. Casting to `DECIMAL(38,0)` before writing preserves the full value.

For most analytical workflows, the pattern is clear: ingest raw CSV once, convert to Parquet for ongoing analysis. DuckDB makes both halves of that process straightforward — and fast enough that the conversion step rarely feels like a burden.
