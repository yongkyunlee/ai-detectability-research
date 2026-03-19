# Importing CSV and Parquet Files in DuckDB

Data pipelines live or die by how easily they ingest files. DuckDB has become a go-to tool for analysts and engineers who want to query flat files without spinning up a server, and its CSV and Parquet import capabilities are a big part of why. This post walks through how both formats work in DuckDB, the configuration knobs that matter, and the gotchas you should know about before pointing it at production data.

## CSV Import with read_csv

The simplest way to query a CSV in DuckDB is also the most direct:

```sql
SELECT * FROM read_csv('sales_data.csv');
```

Behind this one-liner, DuckDB runs an automatic sniffer that examines a sample of rows to detect the delimiter, quote character, escape character, whether a header row exists, and the data types of each column. By default, the sniffer inspects the first 20,480 rows. For most well-formed files, this is enough. For messy real-world data, it sometimes isn't.

### When Auto-Detection Falls Short

Consider a CSV where 20,000 rows have unquoted text fields, and then row 20,502 contains a value like `"Beth, Bens. Co."` — quoted because of the embedded comma. The sniffer sees 20,480 rows with no quoting, concludes the file doesn't use quotes, and later chokes when it encounters the quoted field. The error message suggests the row has too many columns, which is technically true from the sniffer's perspective but unhelpful if you don't know what went wrong.

There are two fixes. The explicit approach is to tell DuckDB the file uses quoting: `quote = '"'`. The brute-force approach is to set `sample_size = -1`, which forces the sniffer to scan the entire file before deciding on dialect parameters. The second option is slower but handles edge cases where problematic rows appear late in the file.

### Key Parameters

The `read_csv` function accepts a wide set of named parameters for situations where auto-detection isn't sufficient:

- **`sep` or `delim`**: Override the detected delimiter. DuckDB allows delimiters up to 4 bytes, so pipe-delimited or tab-delimited files work without issue.
- **`header`**: Force header detection on or off.
- **`all_varchar`**: Read every column as text, deferring type conversion to your SQL logic.
- **`ignore_errors`**: Skip malformed rows instead of failing the query. Pair with `store_rejects` if you need to audit which rows were dropped.
- **`null_padding`**: Fill in NULL values for rows that have fewer columns than expected.
- **`dateformat` / `timestampformat`**: Specify custom parsing formats for temporal columns.
- **`compression`**: Supports gzip and zstd compressed CSVs out of the box.
- **`parallel`**: Enabled by default; DuckDB can split CSV reading across threads for faster ingestion.

If you want to see exactly what the sniffer decided, the `sniff_csv()` function returns the detected parameters as a result set — useful for debugging before committing to a particular configuration.

## Parquet Import with read_parquet

Parquet is a columnar binary format, and DuckDB handles it natively through a built-in extension. Reading Parquet is straightforward:

```sql
SELECT * FROM read_parquet('transactions.parquet');
```

Because Parquet files carry their own schema metadata, there's no sniffing step. DuckDB reads the file footer to get column names, types, and row group statistics, then uses that information to optimize the query.

### Why Parquet Is Usually Faster

Three features make Parquet queries significantly faster than their CSV equivalents:

1. **Column pruning**: DuckDB only reads the columns referenced in your query. A `SELECT amount, date FROM ...` on a 50-column Parquet file reads just two columns of data.
2. **Predicate pushdown**: `WHERE` clauses can be evaluated against row group statistics stored in the file footer. If a row group's maximum value for a column is below your filter threshold, the entire group is skipped without reading any data.
3. **No parsing overhead**: Binary data doesn't need the character-by-character parsing that CSV requires.

Community benchmarks on roughly 20 GB of ZSTD-compressed financial Parquet data show DuckDB delivering sub-second median query times on local storage — around 284 ms with a 32-thread configuration, and roughly 881 ms with 8 threads. Those numbers are 3 to 10 times faster than cloud query engines like BigQuery or Athena running against the same data.

### Hive Partitioning

DuckDB can read directories of Parquet files organized in the Hive partition layout, where directory names encode column values:

```sql
SELECT * FROM read_parquet('s3://bucket/data/year=*/month=*/data.parquet')
WHERE year = 2025 AND month = 3;
```

The engine recognizes `year` and `month` as partition columns derived from the directory structure and prunes files at the planning stage, meaning it never opens Parquet files from partitions that don't match your filter.

One thing to watch: in version 1.5.0, a change to hierarchical S3 globbing caused a regression where all partition files were discovered before filters were applied. This meant extra HTTP requests to read footers of files that would ultimately be discarded. The workaround is `SET s3_allow_recursive_globbing = false;` and the team is actively addressing it.

### Multi-File and Glob Patterns

Both `read_csv` and `read_parquet` accept glob patterns (`*.parquet`, `data/**/*.csv`), making it natural to query entire directories of files as a single logical table. Combined with `union_by_name`, DuckDB can handle files with slightly different schemas by matching columns by name rather than position.

## Remote Files and S3

DuckDB can query CSV and Parquet files directly from HTTP URLs and S3-compatible storage. For Parquet, the first query against a remote file has a noticeable cold start — typically 14 to 20 seconds — because DuckDB must fetch the file footer over the network. Subsequent queries are fast because metadata is cached locally.

One asymmetry worth noting: as of recent versions, Parquet files accessed over HTTP are cached in DuckDB's external file cache, but CSV files are not. If you're repeatedly querying the same remote CSV, you'll pay the full download cost each time. For recurring queries against remote data, converting to Parquet first is almost always worth it.

## Choosing Between CSV and Parquet

The decision usually comes down to where you are in the data lifecycle. CSV works well for initial exploration, one-off imports, and receiving data from systems that only produce text. Parquet is the better choice for anything that will be queried more than once, needs to perform well at scale, or is stored remotely.

DuckDB makes the transition easy. You can convert a CSV to Parquet in a single statement:

```sql
COPY (SELECT * FROM read_csv('input.csv')) TO 'output.parquet' (FORMAT PARQUET, CODEC 'ZSTD');
```

For validation workflows — checking null counts, verifying type constraints, running range checks — DuckDB can replace pandas-based pipelines while using a fraction of the memory, since it processes data in streaming batches rather than loading entire files into RAM.

## Final Thoughts

DuckDB's file import story is one of its strongest features. CSV auto-detection handles most common cases with zero configuration, and when it doesn't, the fix is usually a single explicit parameter. Parquet support is fast, memory-efficient, and tightly integrated with the query optimizer. The main things to watch for are sniffer limitations on unusual CSVs, cold-start latency on remote Parquet files, and partition pruning behavior on S3 in newer releases. Know those edges, and the import path is remarkably smooth.
