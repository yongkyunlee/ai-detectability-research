# Importing CSV and Parquet Files in DuckDB: What You Actually Need to Know

DuckDB makes file imports look trivial. One line of SQL, and you're querying a CSV or Parquet file as if it were a table. But that simplicity hides a sophisticated engine with real trade-offs, sharp edges, and configuration knobs that matter once your data grows beyond toy datasets. We've been running DuckDB against production-scale workloads, and here's what we've learned about getting data in.

## The Basics Are Genuinely Simple

Reading a file requires almost nothing:


SELECT * FROM 'myfile.csv';
SELECT * FROM 'myfile.parquet';


That's it. DuckDB auto-detects the format, infers the schema, and starts scanning. You can also use the explicit function forms - `read_csv()` and `read_parquet()` - which give you access to the full configuration surface. And you can glob across hundreds of files with a wildcard pattern like `SELECT * FROM 'data/*.parquet'` without writing a single line of orchestration code.

So the happy path is dead simple. The interesting part is everything else.

## CSV: The Sniffer Is Smart, Until It Isn't

DuckDB's CSV reader ships with an auto-detection system that samples the first 20,480 rows of your file. It infers the delimiter, quote character, escape character, header presence, date formats, and column types. For most well-formed files, this works flawlessly.

But sampling has an inherent limitation. If your file contains a quoted field with an embedded comma, and that field only appears after row 20,480, the sniffer won't detect that quoting is in use. The parser then encounters what it thinks is an extra column and throws: `Invalid Input Error: CSV Error on Line: 20502 ... Expected Number of Columns: 2 Found: 3`. This is documented in issue #21000 against DuckDB v1.4.4 and remains open. Pandas, Polars, and R's readr all handle this correctly with their defaults, so it's a real gap.

The fix is straightforward. Pass `quote = '"'` explicitly, or increase the sample size. Setting `sample_size = -1` forces a full-file scan for detection, which trades startup latency for correctness on tricky files. We've found that specifying quote and delimiter explicitly is a better habit than relying on auto-detection for production pipelines. Auto-detect is great for exploration; explicit parameters are better for anything that runs unattended.

The full set of CSV options is extensive. You can control `sep`, `header`, `skip`, `dateformat`, `timestampformat`, `compression`, `encoding`, `null_padding`, `ignore_errors`, `strict_mode`, and many more. One option worth knowing about is `store_rejects`, which captures malformed rows in a separate table instead of halting the entire import. That's invaluable when you're ingesting messy real-world CSVs and need to audit failures without losing the good data.

And if your files have inconsistent schemas across partitions - different columns, different orderings - the `union_by_name` parameter merges them by column name rather than position. This works across both CSV and Parquet files and saves a surprising amount of glue code.

## Parquet: Faster, Typed, but Not Without Gotchas

Parquet is the better choice for analytical workloads. The columnar layout means DuckDB can skip entire columns it doesn't need, push predicates into row group statistics, and avoid the parsing overhead of text-based formats entirely. A benchmark comparing DuckDB against BigQuery and Athena on 20GB of ZSTD-compressed Parquet data showed DuckDB achieving a warm median query time of 284ms on an XL configuration (32 threads, 64GB RAM), compared to 2,775ms for BigQuery and 4,211ms for Athena. Those numbers come from 57 queries across financial time-series data stored in 161 Parquet files.

Reading Parquet files is zero-configuration by default. DuckDB reads the file footer, extracts the schema and row group metadata, and begins scanning. The reader supports Snappy, GZIP, ZSTD, Brotli, and LZ4 compression codecs. It handles encryption, bloom filters, and GeoParquet geometry columns. The `binary_as_string` option controls whether binary columns are treated as strings, and `file_row_number` adds a virtual column with the row's ordinal position.

Writing Parquet has more knobs. The default compression is Snappy, which prioritizes speed over compression ratio. ZSTD generally offers a better balance for storage-bound workloads. You can set `row_group_size` to control how many rows land in each row group - smaller groups improve predicate pushdown granularity but increase metadata overhead. The internal benchmarks test three configurations: 5,000 rows (small), 200,000 rows (medium), and 1,000,000 rows (large) per row group. A typical production write looks something like:


COPY (SELECT * FROM source_table) TO 'output.parquet' (
    FORMAT 'parquet',
    COMPRESSION 'ZSTD',
    ROW_GROUP_SIZE 100000
);


For hive-partitioned output, you can add `PARTITION_BY (year, month)` and `OVERWRITE_OR_IGNORE`. But be careful with deeply nested partition hierarchies - an issue documented in #21370 shows that three levels of partitioning can produce an unexpected number of output files unless you add an explicit `ORDER BY` on the partition columns.

One type-level gotcha to be aware of: HUGEINT columns lose precision when written to Parquet. DuckDB maps HUGEINT to DOUBLE internally during the write, so a value like `999999999999999999999999999999` becomes `1e+30`. The workaround is to cast to `DECIMAL(38,0)` before writing. This is tracked in issue #21180 and applies to v1.4.4 and later.

## Remote Files: S3, R2, and the Cold Start Problem

DuckDB can read CSV and Parquet files directly from S3, GCS, and S3-compatible stores like Cloudflare R2. This is powerful but comes with performance characteristics you need to understand.

Cold starts are severe. The same benchmark that showed 284ms warm median on local Parquet showed 14.3 seconds for the first query against R2. That's the cost of fetching Parquet file footers, schema information, and row group metadata across the network before any actual data scanning begins. Subsequent queries drop to 496ms because the metadata is cached. So if your workload is bursty or interactive, expect that first query to feel slow.

Window functions are particularly painful over remote storage. They require multiple passes over the data, and each pass means additional network round trips. The benchmark showed DuckDB+R2 taking 12,187ms for window function queries versus 947ms locally - a 13x penalty. Table scans and aggregations, by contrast, only see a 2x overhead because they stream data sequentially.

DuckDB 1.5.0 introduced some rough edges with remote Parquet. A regression caused `CREATE VIEW` over hive-partitioned S3 data to go from 420ms to over a minute when using explicit partition wildcards like `airline_id=*`. The workaround is to use recursive globs (`**/*.parquet`) or set `s3_allow_recursive_globbing = false`. There's also a false-positive ETag mismatch bug where the same hash is compared in quoted versus unquoted form, causing `HTTP Error: ETag on reading file ... was initially X and now it returned "X"`. Setting `unsafe_disable_etag_checks = true` suppresses this, though it weakens consistency guarantees.

CSV files over remote storage have their own issue. As of v1.4.4, CSVs aren't cached in the external file cache even when `enable_external_file_cache` is set to true. Every query re-downloads the entire file. The root cause is a missing caching mode flag in `csv_file_handle.cpp`. This is fixed in later builds but worth knowing if you're on an older version. For remote data, Parquet is simpler and faster - the columnar format means DuckDB only fetches the columns it needs, while CSV requires downloading the whole file every time.

## The Trade-Off: CSV vs. Parquet

CSV is simpler to produce, human-readable, and universally supported. But Parquet gives you columnar storage, embedded type information, predicate pushdown via row group statistics, and dramatically better performance on analytical queries. The benchmark data makes the case clearly: DuckDB scanning local Parquet at 208ms for table scans versus the overhead of parsing equivalent CSV text. If your pipeline produces both and you get to choose, use Parquet for anything that will be queried more than once.

But CSV still wins for one-off data exchanges, debugging, and interop with systems that don't speak Parquet. And DuckDB's CSV sniffer, despite its sample-size limitation, handles the vast majority of real-world files correctly. The key is knowing where the edges are - and for CSV, that means being explicit about quoting and delimiters in production code.

## Practical Recommendations

If you're setting up a new data pipeline with DuckDB, a few things will save you headaches.

- Use `read_parquet()` with explicit column selection (`SELECT col1, col2 FROM read_parquet(...)`) to take advantage of column pruning, especially over remote storage.
- For CSV imports in production, always specify `quote`, `sep`, and `header` explicitly rather than relying on auto-detection.
- When writing partitioned Parquet, add `ORDER BY` on your partition columns to get deterministic file output.
- For remote storage, prefer Cloudflare R2 over S3 if egress costs matter - at 1,000 queries per day scanning 5GB each, S3 egress runs $13,500/month versus $0 on R2.
- Pin your DuckDB version in CI. The v1.4.4 to v1.5.0 upgrade introduced at least four regressions affecting Parquet reading, including crashes on `INSERT OR IGNORE` with composite primary keys (issue #21254, fixed in PR #21270).

DuckDB 1.5.0, released on March 9, 2026, brought the new VARIANT and GEOMETRY types along with the `duckdb-cli` PyPI package for running the CLI via `uv run -w duckdb-cli duckdb`. These are meaningful additions, but the early v1.5.0 Parquet bugs suggest waiting for a patch release if stability matters more than new features for your use case.

The engine is excellent. The file import story is one of its strongest features. Just don't mistake simple syntax for simple behavior - understand your data, be explicit about your options, and test your upgrade paths.
