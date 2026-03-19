# Importing CSV and Parquet Files in DuckDB

DuckDB makes file import feel lighter than in most databases because the first step is often not a load command at all. For both CSV and Parquet, you can point a query at a file path and start working immediately:

```sql
SELECT * FROM 'events.csv';
SELECT * FROM 'events.parquet';
```

DuckDB separates querying external files from materializing native tables. You can analyze files in place, then persist them later with `CREATE TABLE AS SELECT` or `COPY ... FROM`. CSV requires much more discovery work than Parquet.

## CSV import is really a schema discovery problem

When you reference a `.csv` file directly, DuckDB routes that through its CSV reader with autodetection enabled. Under the hood, that means it is trying to infer the dialect and the schema before it scans the data for real. The sniffer is looking for the delimiter, quote and escape characters, newline style, comment character, whether the file has a header, and the likely type of each column. It also tries to identify date and timestamp formats.

A very practical tool here is `sniff_csv()`:

```sql
FROM sniff_csv('events.csv');
```

This does more than report guesses. It returns the detected settings and builds a ready-to-run `read_csv(..., auto_detect=false, ...)` statement with explicit options and explicit column types. That gives you a clean path from ad hoc exploration to a stable ingestion query.

Sampling is the first trade-off to understand. The test suite includes sparse CSV examples where a tiny `sample_size` causes a numeric column to be classified as `VARCHAR`, while a larger sample or `sample_size=-1` finds the intended `DOUBLE`. If your files have rare non-null values, late-appearing columns, or mixed quality, inference quality depends directly on how much of the file DuckDB inspects.

For predictable ingestion, explicit schemas are still the safest option:

```sql
FROM read_csv(
  'lineitem.csv',
  auto_detect = false,
  delim = '|',
  header = false,
  columns = {
    'l_orderkey': 'BIGINT',
    'l_partkey': 'BIGINT',
    'l_shipdate': 'DATE'
  }
);
```

This avoids repeated sniffing and removes ambiguity around dates, timestamps, and numerics.

DuckDB also exposes escape hatches for ugly CSV. The reader supports `all_varchar` when you want parsing without type commitment, `strict_mode=false` for non-standard quoting and escaping, `ignore_errors=true` when you prefer to skip bad rows, `null_padding=true` for ragged rows, and reject-table options when you want to preserve failures for inspection instead of silently dropping them. Issue reports around malformed trailers and multi-file reads show why these knobs exist.

## Multiple CSV files: decide whether names matter

DuckDB is strong at scanning globs and file lists as a single relation:

```sql
SELECT * FROM 'logs_*.csv';
```

That is the happy path when all files share one schema. In the default mode, DuckDB effectively anchors on the first file’s schema and expects the rest to be compatible. If later files add columns or rename them, you can get ignored data or outright errors.

`union_by_name=true` changes the model. Instead of aligning files by column position, DuckDB aligns them by header names, widens types where needed, and fills missing columns with `NULL`.

There are two caveats. First, schema discovery gets harder, because DuckDB may need to sniff more than one file before it can decide on a unified schema. The codebase and error messages both point to `files_to_sniff` as an important control here. If the default sniff window misses a rare schema variant, increasing `files_to_sniff` or setting it to `-1` can fix the mismatch. Second, `union_by_name` is powerful, but it still benefits from cleaner inputs or more explicit reader settings.

For lineage and partition-aware ingestion, DuckDB can also add virtual columns. `filename=true` exposes the source file path. On hive-style layouts like `part=a/date=2024-01-01/file.csv`, `hive_partitioning=true` turns path segments into typed columns.

## Parquet import is simpler because the file already knows its schema

Parquet is the cleaner story. DuckDB can read Parquet through direct file references or through `read_parquet` and `parquet_scan`:

```sql
SELECT * FROM 'events.parquet';
SELECT * FROM read_parquet('events.parquet');
```

Here the file format does most of the work. Column names and physical types come from Parquet metadata, so there is no dialect sniffing and far less guesswork. That makes Parquet imports easier to automate and usually faster to plan.

Materialization is straightforward when you need it:

```sql
CREATE TABLE events AS
SELECT * FROM 'events.parquet';

COPY events_copy FROM 'events.parquet';
```

DuckDB also handles multi-file Parquet imports well. You can scan globs, unify files with different column orders, and enable `union_by_name=true` when schemas evolve across partitions or time windows. Virtual columns are available here too: `filename` exposes the source path, and `file_index` identifies which file in a multi-file scan produced each row.

Parquet’s bigger advantage is execution-time efficiency. The test suite shows projection pushdown and filter pushdown working on ordinary predicates. If you only select two columns, DuckDB can avoid pulling the rest. If you filter on a column with usable statistics, it can often skip work early.

But Parquet performance still depends on query shape. One reproduced issue shows that DuckDB will not push down filters built from expressions that can raise errors, such as `sqrt(column_0) < ...`. In practice, simple predicates on raw columns are the best fit for external Parquet scans.

Remote Parquet adds another layer: file discovery. Issue discussions around hive-partitioned Parquet on S3 show that pruning can be sensitive to globbing behavior and to how partition predicates are expressed. The practical lesson is simple: keep partition filters explicit, keep join predicates complete, and treat path-based partitioning as part of performance design.

DuckDB’s main idea is that import does not need to be a one-way gate. CSV and Parquet files can stay external until you have a reason to internalize them. CSV gives you flexibility but asks for more discipline around inference. Parquet gives you a cleaner, metadata-driven path and usually better scan performance.
