# Importing CSV and Parquet Files in DuckDB

DuckDB treats flat files as first-class citizens. You can point `read_csv` or `read_parquet` at a local path, an S3 URL, or even a glob pattern and start querying immediately—no `CREATE TABLE`, no loader scripts, no separate import step. That simplicity is the reason I keep reaching for it, but the two formats behave differently enough that picking the right one (and configuring it correctly) matters more than most people realize.

## CSV: Easy Until It Isn't

The `read_csv` function does automatic dialect detection. Delimiter, quoting character, header presence, date format—DuckDB's sniffer figures these out so you don't have to. For most files, `FROM read_csv('data.csv')` just works.

But the sniffer has a limit. By default it inspects the first 20,480 rows (`sample_size=20480`). If your file is well-behaved for the first twenty thousand rows and then introduces quoting on row 20,502, DuckDB won't detect it. This is a real issue reported against v1.4.4: a CSV where every row was unquoted except one field containing `"Beth, Bens. Co."` deep in the file. The sniffer decided no quoting was in use, then choked on the embedded comma with `Expected Number of Columns: 2 Found: 3`. Pandas, Polars, data.table, and readr all handled the same file correctly with default settings.

Two workarounds exist. You can pass `quote = '"'` explicitly, or set `sample_size = -1` to force a full-file scan. The explicit quote is simpler and faster, but `sample_size = -1` covers you when you don't know the file's quirks in advance. We've adopted a team convention: if we don't control the CSV producer, we always pass an explicit quote character. Scanning the entire file for dialect detection on a 500MB CSV is not cheap.

Beyond sniffing, `read_csv` exposes a handful of useful parameters. `union_by_name=true` merges multiple CSVs with different schemas by column name rather than position. `ignore_errors=true` skips malformed rows instead of failing. `all_varchar` forces every column to VARCHAR when you want to defer type coercion. And `strict_mode=false` relaxes standard compliance checking. These knobs give you enough control for messy real-world data, though you'll want to combine them carefully—`union_by_name` with malformed headers can trigger internal errors if the files are truly pathological.

One gap worth knowing: as of v1.4.4, remote CSVs on S3 aren't cached in DuckDB's external file cache. Parquet and JSON readers cache remote files properly, but the CSV reader was missing the `CachingMode::CACHE_REMOTE_ONLY` flag. Every query re-downloads the entire CSV. A fix was submitted, but if you're querying the same remote CSV repeatedly, you'll want to verify your version includes it.

## Parquet: The Performance Default

Parquet is where DuckDB really shines. The columnar format lets DuckDB apply column pruning (read only the columns your query references), predicate pushdown (apply WHERE filters at the storage layer), and row group statistics (skip entire chunks of data using min/max metadata). These aren't just theoretical—they translate directly into less I/O and faster queries.

A community benchmark against 20GB of ZSTD-compressed Parquet data tells the story clearly. DuckDB on local SSD with 8 threads and 16GB RAM hit an 881ms warm median across 57 queries. Bumping to 32 threads and 64GB dropped that to 284ms. BigQuery needed 2,775ms for the same workload. Athena needed 4,211ms. DuckDB was 3–10x faster, and that's on commodity hardware—an AMD EPYC with a SATA SSD, not anything exotic.

The `read_parquet` function supports hive-partitioned data through the `hive_partitioning` and `hive_types` parameters. So a query like `read_parquet('s3://bucket/data/year=*/month=*/*.parquet', hive_partitioning=true, hive_types={'year': USMALLINT, 'month': USMALLINT})` discovers partition columns from the directory structure and casts them to specific types. This works well, though v1.5.0 introduced a regression where explicit partition naming in glob patterns caused dramatic slowdowns—a `CREATE VIEW` that took 420ms in v1.4.4 ballooned to over 61 seconds. The workaround is `SET s3_allow_recursive_globbing = false` or switching to `**` glob patterns instead of explicit `partition_name=*` paths. A fix shipped in the httpfs extension.

Remote Parquet has one significant downside: cold starts. That same benchmark showed 14–20 seconds of overhead on first query when reading from Cloudflare R2, because DuckDB needs to fetch Parquet metadata (file footers, schema, row group info) over the network before it can plan the query. Subsequent queries drop back to ~1 second since metadata gets cached. If your workload is sporadic, this cold start dominates.

## Choosing Between Them

CSV is simpler to produce and human-readable. You can `git diff` a CSV. Parquet gives you compression, column pruning, and dramatically better performance at scale—284ms versus whatever it costs to full-scan a CSV of equivalent size. The trade-off is straightforward: CSV is easier to work with for small, ad-hoc datasets where readability and toolchain simplicity matter; Parquet is the right default once your data exceeds a few hundred megabytes or you're querying it repeatedly.

For teams moving off pandas-based validation pipelines, DuckDB's ability to query S3 directly without loading everything into memory is the real win. A pandas DataFrame materializes the entire file in RAM. DuckDB streams through it. That difference compounds fast when your CSVs grow past what fits in memory.

Both formats support glob patterns (`read_csv('logs_*.csv')`, `read_parquet('data/**/*.parquet')`), both support `union_by_name` for heterogeneous schemas, and both work against remote storage. The execution characteristics are just different enough that the format choice should be deliberate. Don't default to CSV out of habit when your data pipeline would benefit from columnar storage. And don't reach for Parquet when a 50-row config file would be more maintainable as a plain text CSV.

DuckDB makes both paths easy. The important thing is knowing where each one breaks down.
