# Importing CSV and Parquet Files in DuckDB

DuckDB makes file imports absurdly simple. You point it at a file, and it figures out the rest. But underneath that simplicity sits a surprisingly sophisticated set of machinery - a multi-phase CSV sniffer, a columnar Parquet reader with predicate pushdown, and enough configuration knobs to handle the messy files that real-world data pipelines inevitably produce. We've been using DuckDB across several internal services, and I want to walk through how its import capabilities actually work, where the edges are, and how to think about choosing between CSV and Parquet as your interchange format.

## The Shortest Path: Just Reference the File

DuckDB's README captures the core idea in two lines of SQL:

```sql
SELECT * FROM 'myfile.csv';
SELECT * FROM 'myfile.parquet';
```

That's it. No `CREATE EXTERNAL TABLE`, no schema definition, no loader configuration. DuckDB resolves the file format from the extension and runs auto-detection. For quick exploration or ad-hoc analysis, this is hard to beat.

So why does the source code contain thousands of lines dedicated to CSV and Parquet reading? Because real data is ugly, and defaults only get you so far.

## CSV: Auto-Detection and the Sniffer

The CSV reader in DuckDB revolves around a component called the CSV Sniffer, implemented in `src/execution/operator/csv_scanner/sniffer/csv_sniffer.cpp`. The sniffer runs a multi-phase detection pipeline: dialect detection first (delimiter, quote character, escape character, comment character), then header detection, then type detection for each column. It does all of this by sampling the first portion of the file and scoring candidate configurations against each other.

The default delimiter candidates are `,`, `|`, `;`, and `\t`. Quote/escape combinations include double-quote with double-quote escape, single-quote variants, and backslash escapes - nine combinations in total are tested. Comment character detection checks for `#` as well as no comment character at all. The sniffer picks the combination that produces the most consistent column counts across sampled rows.

This works remarkably well for clean data. I've seen it correctly identify pipe-delimited files with single-quote escaping on the first try. But the sniffer isn't magic. If your CSV has a footer - say a metadata line appended after the data rows - things can go sideways. Issue #21248 on the DuckDB repo documents a case where two CSV files with inconsistent footer styles, combined with `union_by_name=true`, triggered an internal error in version 1.4.4. The bug was reproduced on both v1.4 and v1.5.

When auto-detection isn't enough, `read_csv` exposes a comprehensive set of named parameters. The function signature in the source code registers over 30 options: `sep`, `delim`, `quote`, `escape`, `nullstr`, `header`, `auto_detect`, `sample_size`, `skip`, `ignore_errors`, `store_rejects`, `null_padding`, `encoding`, `strict_mode`, `comment`, `dateformat`, `timestampformat`, `decimal_separator`, `parallel`, and more. We don't need to memorize these, but a few deserve special attention.

The `sample_size` parameter controls how many rows the sniffer reads during type detection. It defaults to `STANDARD_VECTOR_SIZE` chunks (2048 rows per chunk). Setting it to `-1` forces the sniffer to read the entire file before deciding on types - slower, but essential when your data has type variations that don't appear in the first few thousand rows.

The `store_rejects` parameter is one I wish more tools had. Instead of silently dropping malformed rows or halting on the first error, DuckDB can route rejected rows to a separate table for later inspection. You can combine `ignore_errors=true` with `store_rejects=true` to get a full import of the parseable rows plus a diagnostic table of everything that failed. That's a powerful pattern for pipelines where you don't control the upstream data quality.

There's also `sniff_csv`, a dedicated table function that runs only the sniffer and returns its findings as a result set - delimiter, quote character, escape character, newline type, whether a header was detected, the inferred column names and types, and even the date/timestamp format strings. It's useful for debugging why a particular file isn't parsing the way you'd expect. One caveat: `sniff_csv` currently doesn't support multi-file inputs. Calling it with a glob pattern that matches more than one file will throw a `NotImplementedException`.

DuckDB's CSV scanner also supports character encoding beyond UTF-8 through a pluggable encoder system. If the `encodings` extension is installed and loaded, you can pass `encoding='latin-1'` or similar to `read_csv`. Without the extension, attempting a non-UTF-8 encoding produces a helpful error message suggesting the install command.

## Parquet: Columnar Efficiency with Rich Metadata

Parquet import follows a different philosophy. Where CSV requires guessing (delimiters, types, headers), Parquet files carry their schema, compression codec, and row group statistics in the file metadata itself. DuckDB's Parquet reader is implemented as an extension in `extension/parquet/`, and it ships as a core extension - you don't need to install anything extra.

The reader supports several compression codecs: Snappy (the default for writes), GZIP, ZSTD, Brotli, and LZ4_RAW. When writing Parquet files, the default codec is Snappy, but ZSTD is increasingly popular for its better compression ratios. A community benchmark testing DuckDB against BigQuery and Athena on 20GB of ZSTD-compressed Parquet data showed DuckDB local achieving a warm median query time of 284ms with 32 threads - compared to 2,775ms for BigQuery and 4,211ms for Athena. The benchmark used 161 Parquet files across six tables, with 57 queries covering scans, aggregations, joins, and window functions.

Those numbers are impressive but come with context. DuckDB was running on local SSD storage (Samsung 870 EVO, AMD EPYC 9224, 64GB RAM), while BigQuery and Athena were serverless cloud platforms. The comparison is more about showing what's possible with local compute than declaring a winner. And the same benchmark revealed that DuckDB over remote storage (Cloudflare R2) had cold start overhead of 14-20 seconds - the time to fetch Parquet metadata (file footers, schema, row group info) over the network. Subsequent queries dropped back to around 496ms because metadata was cached.

Row group size matters. DuckDB's benchmark suite includes tests for importing 100 million rows from Parquet files with small row groups (5,000 rows each) versus large row groups (1,000,000 rows each). Larger row groups reduce per-group overhead and allow more efficient vectorized processing, but they also mean coarser-grained predicate pushdown. Small row groups let DuckDB skip more data when filtering on columns with good statistics - min/max values stored per row group. The default row group size for writes is defined by `DEFAULT_ROW_GROUP_SIZE` in the source. Choosing between small and large row groups is simpler than it sounds: if your queries are predominantly filtered scans, lean toward smaller row groups; if they're full-table aggregations, larger groups reduce overhead.

Hive-style partitioning is supported for both reading and writing Parquet. You can write partitioned data with `PARTITION_BY` in a `COPY` statement and read it back with automatic hive partition detection. But there's a gotcha with deeply nested partitions: issue #21370 documents a case where partitioning by three keys (year, month, store_bucket) across ~19.7 million rows produced 6,418 files instead of the expected 28, some of them empty. The workaround, confirmed by DuckDB core developer Mytherin, is to explicitly `ORDER BY` the partition keys in the `SELECT` before the `COPY`. This is a known issue, not a bug per se, but it catches people off guard.

The Parquet extension also supports bloom filters (enabled by default for writes with a 1% false positive rate), dictionary compression with configurable size limits, field IDs for Iceberg compatibility, encryption configuration, V1 and V2 Parquet format versions, GeoParquet geometry encoding, and VARIANT type shredding - a DuckDB 1.5.0 feature. The `parquet_version` option accepts `V1` or `V2`, where V2 enables delta encoding and other more efficient page-level encodings.

## CSV vs. Parquet: The Trade-Off

CSV is simpler but Parquet gives you more. That's the one-sentence version, but the details matter for choosing correctly.

CSV files are human-readable, universally supported, and trivially generated by almost any system. DuckDB's auto-detection sniffer makes them nearly zero-effort to query. But they carry no schema, no column statistics, and no compression metadata. Every query requires a full scan - there's nothing to prune against. And type inference, however good, is inference. A column that looks like integers for the first 10,000 rows might contain a decimal on row 10,001, and unless your `sample_size` catches it, you'll get a cast error downstream.

Parquet files are self-describing. They carry column types, encoding metadata, row group statistics, and optional bloom filters. DuckDB can use these to skip entire row groups during filtered queries (predicate pushdown), read only the columns your query references (column pruning), and apply compression-aware I/O. The benchmark data bears this out: Athena scanning ZSTD Parquet files scanned 277GB total for 57 queries while BigQuery scanned 1,140GB for the same queries, largely due to differences in how aggressively they apply column pruning and predicate pushdown.

The practical trade-off: use CSV when you need interoperability with systems that don't speak Parquet, when the data is small enough that scanning doesn't matter, or when human readability is a requirement. Use Parquet for anything that persists, anything over a few hundred megabytes, or anything that will be queried repeatedly. And if you're already generating Parquet with ZSTD compression, DuckDB will read it extremely efficiently without any special configuration.

## Multi-File Reads and Glob Patterns

Both `read_csv` and `read_parquet` accept glob patterns, so `SELECT * FROM 'data/*.parquet'` reads all matching files as if they were a single table. The `union_by_name` option handles the case where files don't share the same schema - columns are merged by name, with NULLs filling in where a file doesn't have a particular column. This is enormously useful for datasets that evolve over time, where new columns get added in later files.

DuckDB also surfaces a `filename` column that you can request to track which file each row originated from. For Parquet, there's additionally `file_row_number` to get the row's position within its source file. These metadata columns make debugging data quality issues much more tractable when you're reading from hundreds of files.

## Watching for File Locking

One edge worth mentioning: DuckDB can hold file handles open longer than you'd expect. Issue #18304 documents a case where reading a Parquet file through the Julia client blocked the file from being overwritten or deleted, even after closing the DuckDB connection and running garbage collection. The workaround was to fully close the connection that performed the read before opening a new connection for the overwrite. The CLI didn't exhibit this behavior - it appears to be client-binding-specific. But it's the kind of thing that bites you in ETL pipelines where you read, transform, and write back to the same file path.

## Practical Recommendations

Start with the simplest possible query - `SELECT * FROM 'file.csv'` or `SELECT * FROM 'file.parquet'` - and only add options when something breaks. Use `sniff_csv` to debug CSV parsing issues before reaching for manual configuration. Prefer `store_rejects=true` over `ignore_errors` alone so you can audit what was dropped. For Parquet writes, consider ZSTD over the Snappy default if storage size matters more than write speed. And always test with representative data volumes; the sniffer's behavior on a 100-row sample may not reflect what happens at scale.

DuckDB's file import is one of those features that seems trivial until you need it to handle real-world messiness. The engineering underneath - from the state-machine-based CSV parser to the metadata-aware Parquet reader - is solid and getting better with each release. Version 1.5.0 shipped in March 2026 with new features like VARIANT types and geometry support, and the CSV and Parquet infrastructure continues to be actively developed. For most backend data workflows, it's genuinely the quickest path from file to queryable table I've found.
