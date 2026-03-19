# Importing CSV and Parquet Files in DuckDB

DuckDB has earned a reputation as something of a Swiss Army knife for analytical data work. One of the features that draws people to it most quickly is how painlessly it ingests common file formats — particularly CSV and Parquet. Whether your data lives on a local disk, an S3 bucket, or a public HTTP endpoint, DuckDB can generally start querying it with a single line of SQL. But there is a lot going on beneath that simplicity, and understanding the mechanics of file import will help you get better performance and avoid some well-known pitfalls.

## CSV Import: The Sniffer and Its Limits

At the heart of DuckDB's CSV import lies a sophisticated automatic detection system called the CSV sniffer. When you run a query like `FROM read_csv('sales.csv')`, DuckDB does not simply split on commas and hope for the best. Instead, the sniffer runs through several distinct phases: dialect detection, type detection, type refinement, header detection, and finally type replacement. It figures out the delimiter (comma, tab, pipe, or something else), the quote and escape characters, whether a header row exists, and what data types each column should have.

The sniffer examines a sample of the file — by default, the first 20,480 rows — to make these decisions. This works well for the vast majority of files, but it creates a specific failure mode that has bitten more than a few users. If your CSV file has 20,000 rows of straightforward text data and then a single row containing a quoted field with an embedded comma, the sniffer may decide the file does not use quoting at all. When it later encounters that quoted field, it treats the embedded comma as a delimiter and throws an error about finding too many columns. The fix is straightforward: either pass `quote='"'` explicitly or set `sample_size=-1` to force DuckDB to scan the entire file during sniffing. The tradeoff with scanning the whole file is that sniffing takes longer, but for files where rare formatting quirks hide past the sample window, it is the safest option.

DuckDB provides a companion function called `sniff_csv` that lets you inspect what the sniffer detected without actually loading the data. It returns the detected delimiter, quote character, escape character, newline style, whether a header was found, and a typed column listing. It even generates a complete `read_csv` call with all detected parameters hardcoded, which you can paste into your queries for fully deterministic parsing. This is especially useful in production pipelines where you want to lock down the CSV interpretation and not rely on auto-detection for every run.

## CSV Reader Options in Depth

The `read_csv` function exposes a large number of parameters that give you fine-grained control over parsing. The `delim` (or `sep`) parameter accepts strings up to four bytes, which means DuckDB can handle multi-character delimiters — a feature that comes up with certain legacy data formats. The `quote` and `escape` characters are each limited to a single byte, and DuckDB enforces that the delimiter, quote, and escape characters do not overlap in ambiguous ways.

For date and timestamp handling, you can pass format strings through `dateformat` and `timestampformat`. The auto-type detection system considers a ranked list of candidate types, from the most specific (SQLNULL, BOOLEAN) down to the most general (VARCHAR). You can customize this list with `auto_type_candidates` if, for instance, you want the sniffer to consider INTEGER as a candidate but not DOUBLE.

The `columns` parameter allows you to specify both column names and types upfront, which bypasses the type detection phase entirely. The `names` parameter lets you provide column names without constraining types. And `all_varchar=true` is the escape hatch for when you just need to get data loaded and handle type conversion yourself.

Two parameters deserve special attention for production use. The `ignore_errors` flag tells DuckDB to silently skip rows that fail to parse, which is dangerous in some contexts but essential in others. If you want to know which rows failed and why, `store_rejects=true` writes problematic rows into a separate rejects table rather than dropping them silently. This pairs well with `rejects_limit` to cap how many errors get collected before the query aborts.

## Parallel CSV Scanning

By default, DuckDB attempts to parallelize CSV reads. The engine divides the file into chunks and assigns them to different threads, each using a state machine to track parsing context — whether the scanner is inside a quoted field, at a line boundary, or mid-value. This parallelism is why DuckDB can ingest large CSV files substantially faster than single-threaded readers.

The `buffer_size` parameter controls how large each chunk is. It interacts with `max_line_size`, which defaults to 2 MB. If you have CSV files with extremely long lines (some scientific or genomic datasets do), you may need to increase both. The constraint is that `buffer_size` must always be at least as large as `max_line_size`, since a single buffer needs to be able to hold at least one complete row.

For compressed CSV files (gzip or zstd), parallelism is more constrained since compressed streams generally cannot be split at arbitrary points. DuckDB handles this by resetting its buffer manager when it needs to re-read portions of compressed files.

## Parquet Import: Metadata-Driven Efficiency

Parquet files are a different beast entirely. Where CSV is a text format that must be parsed character by character, Parquet is a binary columnar format with rich metadata baked in. Each Parquet file contains a footer with schema information, row group boundaries, and column statistics (min/max values, null counts). DuckDB exploits all of this.

When you run `FROM read_parquet('data.parquet')`, DuckDB first reads the file footer to understand the schema and row group layout. It then uses column pruning to read only the columns your query actually references — if you select three columns from a 90-column Parquet file, the other 87 columns are never read from disk. It also uses predicate pushdown to skip entire row groups whose statistics prove they cannot contain matching rows. If your WHERE clause filters on a column whose minimum value in a row group is 500 and you are asking for values less than 100, that entire row group is skipped.

These optimizations make an enormous difference at scale. Benchmarks on 20 GB of ZSTD-compressed Parquet data show DuckDB on local storage achieving median query times around 280–880 milliseconds depending on thread count, compared to 2.7 seconds for BigQuery and 4.2 seconds for Athena on the same queries. The speed advantage comes from the combination of vectorized execution, local disk access, and aggressive metadata-driven pruning.

## Reading Parquet from Remote Storage

DuckDB can read Parquet files directly from S3, GCS, or HTTP endpoints using the `httpfs` extension. This opens up a powerful workflow where data stays in cloud object storage and DuckDB queries it in place without a loading step. However, remote Parquet access introduces considerations that do not apply locally.

The first query against a remote Parquet file incurs a cold start penalty because DuckDB must fetch the file footer and metadata over the network. In benchmarks, this cold start for DuckDB querying Parquet on Cloudflare R2 reached 14–20 seconds, compared to sub-second cold starts for local storage. Subsequent queries benefit from cached metadata and run much faster.

Hive-partitioned Parquet datasets introduce additional complexity. When your data is organized into directory structures like `year=2024/month=3/data.parquet`, DuckDB can use the directory names to prune which files it even opens. However, the interaction between glob expansion and partition pruning has been an area of active development. In version 1.5.0, a change to hierarchical S3 glob expansion caused DuckDB to discover all files matching a glob pattern before applying partition filters, rather than pruning during discovery. For datasets with many partitions, this resulted in extra HTTP requests to read Parquet footers for files that would ultimately be filtered out. The workaround in that version was to set `s3_allow_recursive_globbing=false`.

Wide-schema Parquet files on S3 also interact poorly with certain query optimizer rewrites. A common pattern — `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) = 1` — gets rewritten by the optimizer into an aggregate-based plan that may scan the remote files twice. On local disk this is barely noticeable, but on S3, where each column chunk read may be a separate HTTP range request, a 90-column file can generate thousands of small requests. Wrapping the scan in a `MATERIALIZED` CTE forces a single pass.

## Glob Patterns and Multi-File Reads

Both `read_csv` and `read_parquet` accept glob patterns, so `read_parquet('data/*.parquet')` scans all matching files as if they were a single table. The `union_by_name` option handles schema evolution across files — if some files have a column that others lack, the missing values are filled with NULLs. This is particularly useful when files are generated over time and the schema gains new columns.

DuckDB also supports reading multiple files by passing a list: `read_csv(['jan.csv', 'feb.csv', 'mar.csv'])`. The `filename` parameter adds a column showing which source file each row came from, which is invaluable for debugging data quality issues.

For CSV files, the `files_to_sniff` parameter controls how many files from a glob pattern are sampled during auto-detection. The default of 10 is usually sufficient, but heterogeneous datasets may need a higher value.

## Replacement Scans: Query Files Like Tables

One of DuckDB's most convenient features is replacement scanning. If you reference a name in the FROM clause that is not a registered table, DuckDB checks whether it looks like a file path. If the name ends in `.csv`, `.tsv`, or `.parquet` (accounting for compression extensions like `.gz` or `.zst`), DuckDB automatically wraps it in the appropriate `read_csv_auto` or `read_parquet` call. This means `SELECT * FROM 'sales.csv'` just works — no function call needed.

This extends to compressed files as well. A file named `data.csv.gz` is recognized as a gzip-compressed CSV and decompressed on the fly. Zstd-compressed Parquet (`.parquet.zst`) requires the parquet extension to be loaded, but DuckDB will attempt to auto-load it.

## CSV vs. Parquet: When to Use Which

CSV's advantage is universality. Every tool can read and write it, diffs are human-readable in version control, and non-technical users can open it in a spreadsheet. The drawbacks are performance (no columnar pruning, no row group skipping, no embedded statistics) and ambiguity (quoting conventions, delimiter choice, encoding issues, and null representation all need to be negotiated between writer and reader).

Parquet's advantage is performance and self-description. The schema, types, and compression are all embedded in the file. Columnar storage means analytical queries that touch a few columns out of many are dramatically faster. ZSTD compression provides good ratios with fast decompression. The drawbacks are that Parquet files are opaque binary — you cannot open them in a text editor — and not every tool supports them natively.

For pipelines that DuckDB anchors, a common pattern is to ingest messy CSV from external sources using `read_csv` with appropriate options, then write cleaned data to Parquet with `COPY ... TO ... (FORMAT PARQUET, COMPRESSION ZSTD)` for all downstream consumption. This lets you pay the CSV parsing cost once and benefit from Parquet's efficient storage and query performance thereafter.

## Practical Advice

A few tips drawn from real-world usage and community experience:

If you are validating large CSV or Parquet files on S3, DuckDB can replace a pandas-based pipeline with much lower memory consumption. DuckDB streams data through rather than materializing entire DataFrames, and its ability to query S3 directly means you avoid downloading files to local disk.

When working with remote Parquet files, keep an eye on how many HTTP requests your queries generate. Use `EXPLAIN ANALYZE` to see request counts, and consider materializing intermediate results to avoid redundant remote scans.

For CSV files with rare formatting anomalies, `sniff_csv` is your diagnostic tool. Run it first, inspect what was detected, and then lock down the parameters in your `read_csv` call.

And finally, if you are moving data between formats, DuckDB makes it almost trivially easy: `COPY (FROM 'input.csv') TO 'output.parquet' (FORMAT PARQUET)`. One line, and the CSV sniffer, type detection, columnar encoding, and compression all happen automatically.
