# Getting Started with the DuckDB Python Client

DuckDB is fast. That sounds like marketing copy, but the benchmarks back it up: on 20GB of Parquet data, DuckDB on a local machine hit a warm median of 284ms per query with 32 threads and 64GB RAM, compared to 2,775ms for BigQuery and 4,211ms for Athena on the same dataset. We're talking 3-10x faster than managed cloud platforms, running on commodity hardware, with zero infrastructure to manage.

So why should you care about the Python client specifically? Because `pip install duckdb` is all you need to start querying CSV files, Parquet files, and even pandas DataFrames directly from Python. No server process. No config files. No Docker containers. Just a library that embeds a full analytical database engine in your Python process.

## Installation and First Connection

One command gets you going:

```
pip install duckdb
```

Then open a connection:

```python
import duckdb

conn = duckdb.connect()
```

That's an in-memory database. If you want persistence, pass a filename: `duckdb.connect("my_analysis.db")`. The file-based approach gives you durability between sessions, but in-memory is where most people start. And for quick one-off queries, you don't even need an explicit connection - DuckDB provides module-level functions like `duckdb.sql()` that use a default in-memory connection behind the scenes.

## The SQL Interface

The Python client follows PEP 249 loosely. You can call `conn.cursor()` to get a cursor object, but it's fully redundant - `conn.execute()` works just fine on its own. I'd skip the cursor entirely unless you have code that expects that interface.

Running queries looks exactly like you'd expect:

```python
conn.execute("CREATE TABLE test_table (i INTEGER, j STRING)")
conn.execute("INSERT INTO test_table VALUES (1, 'one')")
conn.execute("INSERT INTO test_table VALUES (?, ?)", [2, 'two'])
```

Parameterized queries use `?` placeholders. For batch inserts, `executemany()` accepts a list of parameter lists:

```python
conn.executemany("INSERT INTO test_table VALUES (?, ?)", [[3, 'three'], [4, 'four']])
```

Fetching results gives you options. `fetchall()` returns plain tuples. `fetchdf()` hands you a pandas DataFrame. `fetchnumpy()` gives masked NumPy arrays, which handle NULLs more cleanly than pandas does for numeric columns.

## Querying Pandas DataFrames with SQL

This is the feature that hooks people. DuckDB can see your local Python variables and query them directly as if they were tables:

```python
import pandas as pd

test_df = pd.DataFrame({"i": [1, 2, 3, 4], "j": ["one", "two", "three", "four"]})
result = conn.execute("SELECT j FROM test_df WHERE i > 1").fetchdf()
```

No intermediate steps. No exporting to CSV, no creating temporary tables. DuckDB reaches into your local namespace and treats the DataFrame as a scannable relation. You can also explicitly register a DataFrame as a named view with `conn.register("my_view", df)`, which is useful when you want a stable name to reference across multiple queries.

One gotcha to know: when you use `INSERT INTO table SELECT * FROM dataframe`, column matching happens by position, not by name. If your DataFrame has columns `foo` and `bar` but your table defines them as `bar` then `foo`, the values get silently swapped. Use explicit column lists - `INSERT INTO table (foo, bar) SELECT foo, bar FROM dataframe` - or create the table directly with `CREATE TABLE items AS SELECT * FROM df` to let DuckDB infer the schema.

## The Relation API

Beyond raw SQL, DuckDB offers a programmatic query builder called the Relation API. Relations are lazily evaluated chains of relational operators. You build up a pipeline, and nothing executes until you call `.execute()`, `.df()`, or `.fetchall()`.

```python
rel = conn.from_df(test_df)
result = rel.filter('i > 1').project('i + 1, j').order('j').limit(2).df()
```

Each method returns a new relation, so chaining is natural. You can also create relations from CSV files with `duckdb.from_csv_auto(path)` or from existing tables with `conn.table("table_name")`. Relations expose metadata too: `.columns` gives column names, `.types` gives their types, `.alias` gives the relation's name.

The Relation API is simpler than SQL for exploratory work, but SQL gives you the full power of DuckDB's dialect - window functions, CTEs, correlated subqueries. The relation approach is simpler for simple pipelines, but SQL gives you everything.

## Concurrency: Know the Limits

DuckDB is an analytical database designed for single-process, read-heavy workloads. It's not a server. Multiple threads can read concurrently using separate cursors from the same connection, and the documentation advises using `conn.cursor()` for thread-local access. But concurrent writes are another story.

A reported issue showed that two threads doing `INSERT ... ON CONFLICT DO UPDATE` through separate cursors could crash with a segfault in DuckDB v1.3.0. The fix landed by v1.4.3 LTS via improvements to the ART (Adaptive Radix Tree) indexing, but the underlying reality remains: DuckDB's MVCC model isn't built for high-concurrency write workloads. If your use case requires parallel reads and updates on the same records, you'll want a different tool. DuckDB excels when you read a lot and write in batches.

## Working with Files Directly

DuckDB's ability to query files without loading them first is a standout feature. From the SQL interface you can reference CSV and Parquet files directly in your FROM clause, and the engine handles parsing, type inference, and columnar scanning. Glob patterns work too - `SELECT * FROM 'data_20*.csv'` reads hundreds of files as one table. And if files don't share the same schema, `union_by_name` reconciles the differences.

This makes DuckDB a strong replacement for pandas in data validation pipelines. Teams that hit memory limits loading large CSVs into DataFrames find that DuckDB can query those same files with a fraction of the RAM, because it processes data in batches using its vectorized execution engine rather than materializing the entire dataset.

## What to Watch Out For

DuckDB v1.5.0 shipped in March 2026, and like any major release, the issue tracker lit up. Memory allocated by DuckDB doesn't get immediately returned to the OS - the allocator pools freed memory for reuse, which looks like a leak in monitoring but is expected behavior. If you're embedding DuckDB in a long-running process, be aware that RSS will stay elevated even after large queries finish.

Also note that some configuration options you'd expect to pass through `duckdb.connect()` aren't available there yet. The `compress` option for in-memory databases, introduced in v1.4.0, can only be enabled via a two-step `ATTACH ... (COMPRESS)` pattern, not directly through the connection config dict. The DuckDB team has acknowledged this as a limitation they plan to address.

## Who Should Use This

DuckDB's Python client is the right choice when you need to run analytical SQL on local data - Parquet files, CSVs, DataFrames - without spinning up infrastructure. It's a terrible fit for serving concurrent web requests. But for ETL scripts, data validation, exploratory analysis, and embedded analytics, it's become a default tool for good reason. Install it, point it at your data, and write SQL. That's the whole getting-started guide.
