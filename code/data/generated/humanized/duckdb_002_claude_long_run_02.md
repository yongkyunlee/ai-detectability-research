# Importing CSV and Parquet Files in DuckDB

DuckDB gets a lot of love for how easily it pulls in CSV and Parquet files. One line of SQL and you're querying data from a local disk, an S3 bucket, or a public HTTP endpoint. It genuinely feels like magic the first time you try it. But there's a lot happening under the hood, and understanding the mechanics will save you from some frustrating gotchas I've run into (and seen others run into) when file imports go sideways.

## CSV Import: The Sniffer and Its Limits

DuckDB's CSV import relies on an automatic detection system called the CSV sniffer. When you run something like `FROM read_csv('sales.csv')`, it doesn't just split on commas and pray. The sniffer goes through several phases: dialect detection, type detection, type refinement, header detection, and type replacement. It figures out the delimiter (comma, tab, pipe, whatever), the quote and escape characters, whether there's a header row, and what types each column should be.

By default, the sniffer examines the first 20,480 rows. This works fine most of the time.

Here's where it gets tricky, though. Say your CSV has 20,000 rows of clean text and then one row with a quoted field containing an embedded comma. The sniffer already decided the file doesn't use quoting, because it never saw any in its sample. When it hits that quoted field later, it treats the embedded comma as a delimiter and throws an error about too many columns. I've seen this bite people more than once. The fix is simple: pass `quote='"'` explicitly or set `sample_size=-1` to force a full-file scan during sniffing. Scanning the whole file is slower, but for files where weird formatting hides past the sample window, it's the safest bet.

There's also a companion function called `sniff_csv` that lets you inspect what the sniffer detected without loading any data. It returns the detected delimiter, quote character, escape character, newline style, whether it found a header, and a typed column listing. The really nice touch is that it generates a complete `read_csv` call with all detected parameters hardcoded, so you can paste it into your queries for fully deterministic parsing. For production pipelines where you don't want to rely on auto-detection every run, this is genuinely useful.

## CSV Reader Options in Depth

The `read_csv` function exposes a ton of parameters. The `delim` (or `sep`) parameter accepts strings up to four bytes, meaning DuckDB can handle multi-character delimiters. That sounds obscure, but it comes up with certain legacy data formats. The `quote` and `escape` characters are each limited to a single byte, and DuckDB enforces that the delimiter, quote, and escape characters don't overlap in ambiguous ways.

For dates and timestamps, you can pass format strings through `dateformat` and `timestampformat`. The auto-type detection considers a ranked list of candidate types, from the most specific (SQLNULL, BOOLEAN) down to the most general (VARCHAR). You can customize this list with `auto_type_candidates` if you want the sniffer to consider INTEGER but not DOUBLE, for example. The `columns` parameter lets you specify both column names and types upfront, bypassing type detection entirely; `names` provides column names without constraining types. And `all_varchar=true` is your escape hatch when you just need data loaded and want to handle type conversion yourself.

Two parameters are worth calling out for production use. The `ignore_errors` flag tells DuckDB to silently skip rows that fail to parse. Dangerous in some contexts, essential in others. If you want to know which rows failed and why, `store_rejects=true` writes problematic rows into a separate rejects table instead of dropping them silently. Pair that with `rejects_limit` to cap how many errors get collected before the query aborts.

## Parallel CSV Scanning

DuckDB parallelizes CSV reads by default. The engine divides the file into chunks and hands them to different threads, each using a state machine to track whether the scanner is inside a quoted field, at a line boundary, or mid-value. This is why it can ingest large CSVs substantially faster than single-threaded readers.

The `buffer_size` parameter controls chunk size. It interacts with `max_line_size`, which defaults to 2 MB. If you've got CSV files with extremely long lines (some scientific or genomic datasets do), you may need to bump both. One constraint: `buffer_size` must always be at least as large as `max_line_size`, since a single buffer needs to hold at least one complete row.

Compressed files (gzip or zstd) are more constrained here, since compressed streams generally can't be split at arbitrary points. DuckDB handles this by resetting its buffer manager when it needs to re-read portions of compressed files.

## Parquet Import: Metadata-Driven Efficiency

Parquet is a completely different animal. CSV is text that must be parsed character by character; Parquet is a binary columnar format with rich metadata baked right in. Each file contains a footer with schema information, row group boundaries, and column statistics like min/max values and null counts. DuckDB uses all of it.

When you run `FROM read_parquet('data.parquet')`, it first reads the file footer to understand the schema and row group layout. Then column pruning kicks in: if you select three columns from a 90-column file, the other 87 never get read from disk. Predicate pushdown goes further, skipping entire row groups whose statistics prove they can't contain matching rows. If your WHERE clause filters on a column whose minimum value in a row group is 500 and you're asking for values less than 100, that whole row group gets skipped.

The performance difference at scale is enormous. Benchmarks on 20 GB of ZSTD-compressed Parquet show DuckDB on local storage hitting median query times around 280 to 880 milliseconds depending on thread count, compared to 2.7 seconds for BigQuery and 4.2 seconds for Athena on the same queries. That speed comes from vectorized execution, local disk access, and aggressive metadata-driven pruning working together.

## Reading Parquet from Remote Storage

The `httpfs` extension lets DuckDB read Parquet files directly from S3, GCS, or HTTP endpoints. Your data stays in cloud object storage and DuckDB queries it in place, no loading step needed. But remote access introduces some wrinkles that don't apply locally.

The first query against a remote Parquet file takes a cold start hit because DuckDB has to fetch the file footer and metadata over the network. In benchmarks, this cold start on Cloudflare R2 reached 14 to 20 seconds, compared to sub-second locally. Subsequent queries benefit from cached metadata and run much faster.

Hive-partitioned datasets add another layer. When data sits in directory structures like `year=2024/month=3/data.parquet`, DuckDB can use directory names to prune which files it even opens. Honestly, though, the interaction between glob expansion and partition pruning has been a moving target. In version 1.5.0, a change to hierarchical S3 glob expansion caused DuckDB to discover all files matching a glob pattern before applying partition filters, rather than pruning during discovery. For datasets with many partitions, this meant extra HTTP requests to read footers for files that would ultimately be filtered out. The workaround was to set `s3_allow_recursive_globbing=false`.

Wide-schema Parquet files on S3 also interact poorly with certain query optimizer rewrites. A common pattern, `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) = 1`, gets rewritten by the optimizer into an aggregate-based plan that may scan the remote files twice. On local disk you'd barely notice. On S3, where each column chunk read may be a separate HTTP range request, a 90-column file can generate thousands of small requests. Wrapping the scan in a `MATERIALIZED` CTE forces a single pass and avoids that problem.

## Glob Patterns and Multi-File Reads

Both `read_csv` and `read_parquet` accept glob patterns, so `read_parquet('data/*.parquet')` scans all matching files as if they were a single table. The `union_by_name` option handles schema evolution across files: if some files have a column that others lack, missing values get filled with NULLs. This is handy when files are generated over time and the schema gains new columns.

You can also pass a list of files directly: `read_csv(['jan.csv', 'feb.csv', 'mar.csv'])`. The `filename` parameter adds a column showing which source file each row came from, which I've found invaluable for debugging data quality issues.

For CSVs with heterogeneous formatting across a glob, the `files_to_sniff` parameter controls how many files get sampled during auto-detection. The default of 10 is usually enough, but I think bumping it higher is worth it if your files aren't uniform.

## Replacement Scans: Query Files Like Tables

This might be my favorite convenience feature. If you reference a name in the FROM clause that isn't a registered table, DuckDB checks whether it looks like a file path. If the name ends in `.csv`, `.tsv`, or `.parquet` (accounting for compression extensions like `.gz` or `.zst`), it automatically wraps it in the appropriate `read_csv_auto` or `read_parquet` call. So `SELECT * FROM 'sales.csv'` just works. No function call needed.

Compressed files work too. A file named `data.csv.gz` is recognized as gzip-compressed CSV and decompressed on the fly. Zstd-compressed Parquet (`.parquet.zst`) requires the parquet extension to be loaded, but DuckDB will try to auto-load it.

## CSV vs. Parquet: When to Use Which

CSV's strength is universality. Every tool reads and writes it, diffs are human-readable in version control, and non-technical users can open it in a spreadsheet. The downsides are performance (no columnar pruning, no row group skipping, no embedded statistics) and ambiguity (quoting conventions, delimiter choice, encoding issues, and null representation all need to be agreed upon between writer and reader).

Parquet's strength is performance and self-description. The schema, types, and compression are all embedded in the file; columnar storage means analytical queries touching a few columns out of many run dramatically faster; ZSTD compression gives good ratios with fast decompression. The tradeoff is that Parquet files are opaque binary (you can't open them in a text editor) and not every tool supports them natively.

For pipelines built around DuckDB, a common approach is to ingest messy CSV from external sources using `read_csv` with appropriate options, then write cleaned data to Parquet with `COPY ... TO ... (FORMAT PARQUET, COMPRESSION ZSTD)` for all downstream consumption. You pay the CSV parsing cost once and get Parquet's efficient storage and query performance from there on out.

## Practical Advice

If you're validating large CSV or Parquet files on S3, DuckDB can replace a pandas-based pipeline with much lower memory consumption. It streams data through rather than materializing entire DataFrames, and querying S3 directly means you skip the step of downloading files to local disk.

When working with remote Parquet files, keep an eye on how many HTTP requests your queries generate. Run `EXPLAIN ANALYZE` to see request counts, and consider materializing intermediate results to avoid redundant remote scans.

For CSVs with rare formatting anomalies, `sniff_csv` is your best diagnostic tool. Run it first, inspect what it detected, then lock down the parameters in your `read_csv` call.

And if you're moving data between formats, DuckDB makes it almost trivially easy: `COPY (FROM 'input.csv') TO 'output.parquet' (FORMAT PARQUET)`. One line. The sniffer, type detection, columnar encoding, and compression all happen automatically.
