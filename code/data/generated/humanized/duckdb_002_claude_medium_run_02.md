# Importing CSV and Parquet Files in DuckDB

Data pipelines live or die by how easily they ingest files. DuckDB has become a go-to tool for analysts and engineers who want to query flat files without spinning up a server, and its CSV and Parquet import capabilities are a big reason why. This post walks through how both formats work in DuckDB, what configuration knobs matter, and the gotchas you should know about before pointing it at production data.

## CSV Import with read_csv

The simplest way to query a CSV in DuckDB is also the most direct:


SELECT * FROM read_csv('sales_data.csv');


Behind this one-liner, DuckDB runs an automatic sniffer that examines a sample of rows to detect the delimiter, quote character, escape character, whether a header row exists, and the data types of each column. By default it inspects the first 20,480 rows. For most well-formed files, that's enough. For messy real-world data, it sometimes isn't.

### When Auto-Detection Falls Short

Picture a CSV where 20,000 rows have unquoted text fields, and then row 20,502 contains a value like `"Beth, Bens. Co."`, quoted because of the embedded comma. The sniffer sees 20,480 rows with no quoting, concludes the file doesn't use quotes, and later chokes when it encounters that quoted field. The error message says the row has too many columns. Technically true from the sniffer's perspective, but pretty unhelpful if you don't know what went wrong.

Two fixes here. You can be explicit and tell DuckDB the file uses quoting: `quote = '"'`. Or you can go brute-force and set `sample_size = -1`, which scans the entire file before deciding on dialect parameters. The second option is slower but handles edge cases where problematic rows show up late in the file.

### Key Parameters

The `read_csv` function takes a wide set of named parameters for situations where auto-detection doesn't cut it. The `sep` or `delim` parameter overrides the detected delimiter, and DuckDB allows delimiters up to 4 bytes, so pipe-delimited or tab-delimited files work fine. You can force header detection on or off with `header`, or read every column as text using `all_varchar` to defer type conversion to your SQL logic.

Dealing with messy data? The `ignore_errors` parameter skips malformed rows instead of failing the query; pair it with `store_rejects` if you need to audit which rows were dropped. There's `null_padding` to fill in NULL values when rows have fewer columns than expected, `dateformat` and `timestampformat` for custom parsing of temporal columns, and `compression` for gzip and zstd compressed CSVs out of the box. Parallel reading is enabled by default, meaning DuckDB can split CSV ingestion across threads.

One handy trick: `sniff_csv()` returns the detected parameters as a result set. I've found it useful for debugging before committing to a particular configuration.

## Parquet Import with read_parquet

Parquet is a columnar binary format, and DuckDB handles it natively through a built-in extension. Reading it is straightforward:


SELECT * FROM read_parquet('transactions.parquet');


Because Parquet files carry their own schema metadata, there's no sniffing step. DuckDB reads the file footer to get column names, types, and row group statistics, then uses that information to plan the query.

### Why Parquet Is Usually Faster

Three things make Parquet queries significantly faster than their CSV equivalents.

First, column pruning. DuckDB only reads the columns referenced in your query. A `SELECT amount, date FROM ...` on a 50-column Parquet file reads just two columns of data. Second, predicate pushdown: `WHERE` clauses can be evaluated against row group statistics stored in the file footer, so if a row group's maximum value for a column is below your filter threshold, the entire group gets skipped without reading any data. Third, there's no parsing overhead. Binary data doesn't need the character-by-character parsing that CSV requires.

Community benchmarks on roughly 20 GB of ZSTD-compressed financial Parquet data show DuckDB delivering sub-second median query times on local storage, around 284 ms with a 32-thread configuration and roughly 881 ms with 8 threads. Those numbers are 3 to 10 times faster than cloud query engines like BigQuery or Athena running against the same data. Honestly, that surprised me.

### Hive Partitioning

DuckDB can read directories of Parquet files organized in the Hive partition layout, where directory names encode column values:


SELECT * FROM read_parquet('s3://bucket/data/year=*/month=*/data.parquet')
WHERE year = 2025 AND month = 3;


The engine recognizes `year` and `month` as partition columns derived from the directory structure and prunes files at the planning stage. It never opens Parquet files from partitions that don't match your filter.

One thing to watch: in version 1.5.0, a change to hierarchical S3 globbing caused a regression where all partition files were discovered before filters were applied. Extra HTTP requests to read footers of files that would ultimately be discarded. The workaround is `SET s3_allow_recursive_globbing = false;` and the team is actively addressing it.

### Multi-File and Glob Patterns

Both `read_csv` and `read_parquet` accept glob patterns (`*.parquet`, `data/**/*.csv`), making it natural to query entire directories of files as a single logical table. Combined with `union_by_name`, DuckDB can handle files with slightly different schemas by matching columns by name rather than position.

## Remote Files and S3

DuckDB can query CSV and Parquet files directly from HTTP URLs and S3-compatible storage. For Parquet, the first query against a remote file has a noticeable cold start, typically 14 to 20 seconds, because DuckDB must fetch the file footer over the network. Subsequent queries are fast since metadata gets cached locally.

There's an asymmetry worth knowing about here. As of recent versions, Parquet files accessed over HTTP are cached in DuckDB's external file cache, but CSV files are not. If you're repeatedly querying the same remote CSV, you'll pay the full download cost each time. For recurring queries against remote data, converting to Parquet first is almost always worth it.

## Choosing Between CSV and Parquet

This usually comes down to where you are in the data lifecycle. CSV works well for initial exploration, one-off imports, and receiving data from systems that only produce text. Parquet is the better choice for anything queried more than once, anything that needs to perform well at scale, or data stored remotely.

DuckDB makes the transition easy. You can convert a CSV to Parquet in a single statement:


COPY (SELECT * FROM read_csv('input.csv')) TO 'output.parquet' (FORMAT PARQUET, CODEC 'ZSTD');


For validation workflows (checking null counts, verifying type constraints, running range checks) DuckDB can replace pandas-based pipelines while using a fraction of the memory, since it processes data in streaming batches rather than loading entire files into RAM.

## Final Thoughts

DuckDB's file import story is, from what I can tell, one of its strongest features. CSV auto-detection handles most common cases with zero configuration, and when it doesn't, the fix is usually a single explicit parameter. Parquet support is fast, memory-efficient, and tightly integrated with the query optimizer. The main things to watch for are sniffer limitations on unusual CSVs, cold-start latency on remote Parquet files, and partition pruning behavior on S3 in newer releases. Know those edges and you won't have many problems.
