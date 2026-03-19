# Getting Started with the DuckDB Python Client

DuckDB just hit version 1.5.0. If you haven't tried it from Python yet, now's a good time. The Python client gives you an embedded analytical database that runs inside your process - no server, no daemon, no configuration files. Just `pip install duckdb` and you're running SQL.

I want to walk through what the client actually looks like in practice, where it shines, and where you'll want to be careful.

## The Basics: Connect and Query

The entry point is `duckdb.connect()`. Call it with no arguments and you get an in-memory database. Pass it a filename and you get persistence on disk.


import duckdb

conn = duckdb.connect()  # in-memory
conn = duckdb.connect("my_analysis.duckdb")  # persistent


From there, it's standard SQL execution. The API follows PEP 249 loosely - you can create a cursor with `conn.cursor()` if you want, but it's fully redundant. The connection object itself handles everything.


conn.execute("CREATE TABLE test_table (i INTEGER, j STRING)")
conn.execute("INSERT INTO test_table VALUES (?, ?)", [2, 'two'])
conn.executemany("INSERT INTO test_table VALUES (?, ?)", [[3, 'three'], [4, 'four']])


Parameterized queries work as you'd expect. So does `executemany()` for bulk inserts. Nothing surprising here - and that's the point.

## Fetching Results

This is where DuckDB starts to feel different from SQLite or Postgres client libraries. You don't just get rows back. You get multiple output formats depending on what you need downstream.


result = conn.execute("SELECT * FROM test_table")
result.fetchall()      # list of tuples
result.fetchdf()       # pandas DataFrame
result.fetchnumpy()    # dict of masked numpy arrays


The `fetchdf()` call is the one most people reach for. It hands you a pandas DataFrame directly, with no intermediate conversion step on your side. And `fetchnumpy()` is cleaner than `fetchdf()` when you're dealing with NULLs, since numpy masked arrays handle missing values more gracefully than pandas in certain numerical contexts.

## Querying Pandas DataFrames with SQL

Here's the feature that hooks people. You can point DuckDB at an existing pandas DataFrame and query it with SQL - no loading, no import, no ETL step.


import pandas as pd

test_df = pd.DataFrame({"i": [1, 2, 3, 4], "j": ["one", "two", "three", "four"]})
conn.register("test_df", test_df)
print(conn.execute("SELECT j FROM test_df WHERE i > 1").fetchdf())


We've all been there: you have a DataFrame, you need a grouped aggregation with a window function, and the pandas syntax is getting gnarly. SQL is just better for that kind of work. DuckDB lets you stay in SQL without leaving your Python process or copying data to an external database.

And it's fast. A community benchmark on 20 GB of Parquet data showed DuckDB on local storage hitting a warm median query time of 284 ms on an XL configuration (32 threads, 64 GB RAM), compared to 2,775 ms for BigQuery and 4,211 ms for Athena on the same queries. That's 3–10x faster for analytical workloads running on a single machine.

## The Relational API

Beyond raw SQL, DuckDB offers a relational API that lets you build queries programmatically. Think of it as a lazy query builder.


rel = conn.from_df(test_df)
rel.filter('i > 1').project('i + 1, j').order('j').limit(2)


Each call returns a new relation object. Nothing executes until you call `.execute()`, `.fetchdf()`, or `.df()`. You can chain operations, inspect column names and types, and compose queries without concatenating SQL strings.

There's also `duckdb.from_csv_auto()` for reading CSV files directly into a relation, which skips the pandas-loading-into-memory step entirely. For large CSV or Parquet validation pipelines - the kind where pandas chokes on memory - this matters a lot.

## Reading Files Directly

DuckDB reads Parquet, CSV, and JSON files natively. No extra libraries required.


SELECT * FROM 'myfile.csv';
SELECT * FROM 'myfile.parquet';


You can do this from the Python client just as easily with `conn.execute()`. The CSV parser auto-detects types, and glob patterns work for reading multiple files at once. If those files don't share the same schema, `union_by_name` handles the alignment. This is the kind of ergonomic touch that makes DuckDB pleasant for ad-hoc data work.

## Threading: Know the Rules

DuckDB supports multiple threads, but the model has constraints worth understanding up front. The documented approach is to create a separate cursor per thread via `conn.cursor()`. Each cursor gets its own transaction context.

But be aware of the edges. A now-fixed bug in version 1.3.0 caused segfaults when two threads ran concurrent `INSERT ... ON CONFLICT DO UPDATE` operations through separate cursors on the same connection. The crash happened during transaction rollback inside the ART (Adaptive Radix Tree) index code. This was resolved by version 1.4.3, but it illustrates something important: DuckDB's concurrency story is still maturing. If you're doing concurrent writes, stay on the latest stable release and test your specific patterns.

For read-heavy, single-writer workloads, DuckDB is solid. For high-concurrency read/write scenarios with frequent updates, you'll hit MVCC limitations. Community discussions have noted that DuckDB's concurrency model isn't designed for heavy parallel writes on the same records.

## Disk Space: An Open Gotcha

One thing to watch with persistent databases: dropping a table or deleting rows doesn't immediately shrink the `.duckdb` file. DuckDB uses free lists internally - dropped blocks get marked for reuse rather than reclaimed. `VACUUM` doesn't currently resolve this, and `CHECKPOINT` won't help either. This is a known open issue (GitHub issue #14124, open since September 2024). The problem compounds when ART indexes are involved - one user reported a 1,500-row table with a UNIQUE constraint whose database file grew to 1.2 GB over 24 hours of updates.

The practical workaround is exporting the database and reimporting it into a fresh file. That's ugly, but it works. If you're using DuckDB as a persistent store with frequent deletes and updates, understand this trade-off going in. DuckDB is simpler than running a Postgres instance for local analytics, but Postgres gives you proper VACUUM and space reclamation out of the box.

## Where This Fits

DuckDB's Python client is best suited for analytical workloads on a single machine: data exploration, ETL scripts, validation pipelines, embedding analytics into applications. The ability to query Parquet files on S3, run SQL on pandas DataFrames, and return results as Arrow or numpy arrays makes it a genuine Swiss army knife for data work.

Don't treat it as a general-purpose application database. Don't expect high-concurrency write throughput. And if you're persisting data with frequent mutations, keep the disk space behavior in mind.

But for the analytical path - reading files, transforming data, running aggregations - the Python client is about as frictionless as it gets. Install it, connect, write SQL. That's the whole setup.
