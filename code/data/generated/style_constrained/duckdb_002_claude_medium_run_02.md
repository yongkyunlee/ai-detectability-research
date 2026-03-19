# Importing CSV and Parquet Files in DuckDB

Most data pipelines start with the same boring step: getting flat files into something queryable. DuckDB makes this almost absurdly simple. But the simplicity hides real engineering decisions you should understand before pointing it at production data.

## CSV: Auto-Detection That Mostly Works

Reading a CSV in DuckDB requires exactly one line of SQL:

```sql
SELECT * FROM 'myfile.csv';
```

That's it. DuckDB's sniffer inspects the first 2,048 rows by default. It auto-detects the delimiter, quote character, escape character, newline type, whether a header row exists, and the data types for every column. The type detection walks a specificity ladder—starting at `SQLNULL` at the top and falling through `BOOLEAN`, `TIME`, `DATE`, `TIMESTAMP`, `TIMESTAMP_TZ`, `BIGINT`, `DOUBLE`, and finally `VARCHAR` as the catch-all. The system tries the most specific type first and relaxes until something fits.

This works well for clean, uniform files. It doesn't work well when your data is messy in ways that only show up past the sample window. Issue #21000 in the DuckDB repository documents a case where a quoted field containing a comma first appears at row 20,502—well beyond the 2,048-row sniff. The sniffer never sees a quote character, doesn't detect it, and the parser chokes when it finally encounters one. The error message is blunt: `CSV Error on Line: 20502, Expected Number of Columns: 2 Found: 3`. Every other major CSV reader—pandas, Polars, R's `data.table`—handles this scenario correctly by default.

The fix is straightforward but manual. You can pass `sample_size = -1` to force a full-file scan during detection, or explicitly specify `quote = '"'` when you know your data uses standard quoting. I prefer the explicit route. Auto-detection is great for exploration, but for repeatable pipelines, pin your schema and dialect options. You won't regret it.

DuckDB also supports `ignore_errors = true` and `store_rejects = true`, which let you push malformed rows into a rejects table instead of failing the whole read. The `null_padding` option will pad short rows with NULLs rather than throwing. These are useful for initial data profiling, less so for production loads where you want strict validation. The parallel scanner is on by default and works across a single file, which is a nice touch for large CSVs on multi-core machines.

## Parquet: Where DuckDB Really Shines

Parquet reads follow the same pattern:

```sql
SELECT * FROM 'myfile.parquet';
```

But the internals are different in important ways. Parquet files carry their schema, so there's no sniffing step. They also carry row-group-level statistics—min/max values per column—which DuckDB uses for predicate pushdown. If your `WHERE` clause eliminates an entire row group based on its statistics, DuckDB skips reading it entirely. This is where Parquet earns its keep on analytical workloads.

A benchmark comparing DuckDB against BigQuery and Athena on roughly 20 GB of ZSTD-compressed Parquet data showed DuckDB local hitting a warm median of 284 ms with 32 threads and 64 GB of RAM. BigQuery clocked 2,775 ms. Athena came in at 4,211 ms. DuckDB was 3 to 10 times faster than the cloud platforms, running on a single AMD EPYC 9224 node. The scaling curve is clean too—doubling threads and memory roughly halves latency, from 4,971 ms at 4 threads down to 995 ms at 32 threads for wide scan queries.

And the writer side has good options. Snappy is the default compression codec, but ZSTD, GZIP, Brotli, and LZ4 are all available. You can control `row_group_size`, enable Bloom filters (on by default with a 1% false positive ratio), and toggle dictionary compression limits. Writing `PARQUET_VERSION V2` gives you data page V2 headers if your downstream tools support them.

## Hive Partitioning: Powerful, With Caveats

DuckDB reads hive-partitioned datasets out of the box:

```sql
SELECT * FROM read_parquet('s3://bucket/year=*/month=*/*.parquet',
  hive_partitioning = true);
```

You can specify partition column types with `hive_types` to avoid incorrect inference. Version 1.5.0 introduced file-level Dynamic Partition Pruning for local files, which lets DuckDB skip entire files based on partition key filters without reading any file metadata. That's a meaningful improvement for local datasets with thousands of partitions.

But v1.5.0 also introduced regressions in this area. Issue #21347 documents a case where v1.4.4 discovered exactly 39 matching files for a filtered query, while v1.5.0 discovered all 122 files first, then pruned to 39—issuing unnecessary HTTP GET requests along the way. A separate issue (#21348) showed a `QUALIFY ROW_NUMBER() OVER (...) = 1` query jumping from 81 S3 requests in v1.4.4 to 4,214 in v1.5.0, tripling wall-clock time. The workaround for the first is `SET s3_allow_recursive_globbing = false;` and for the second, `SET disabled_optimizers='top_n_window_elimination';`.

So if you're running hive-partitioned queries against S3, test your query patterns after upgrading.

## The Trade-Off Worth Knowing

CSV is simpler to produce and debug. You can open it in any text editor. But Parquet gives you columnar storage, embedded statistics, compression, and schema enforcement—all of which translate directly to faster analytical queries and less room for type-related surprises. For anything beyond a quick one-off exploration, Parquet is the better input format. The DuckDB benchmarks bear this out: column pruning and row-group skipping simply aren't possible with CSV, and on 20 GB datasets the performance gap is enormous.

We've been using DuckDB as a lightweight validation layer for files landing in S3—null counts, type checks, range validation, regex pattern matching—and it handles that role well without the memory overhead of loading everything into pandas. The `read_csv` and `read_parquet` functions are the entry point for almost every workflow we build. Know their defaults, know their limits, and you'll save yourself hours of debugging.
