# Getting Started with DuckDB's Python Client

If you spend any meaningful time wrangling CSV exports, Parquet files, or pandas DataFrames, you have probably heard someone mention DuckDB. It is an embedded analytical database—think SQLite, but built from the ground up for columnar, read-heavy workloads instead of row-level transactions. The Python client makes it particularly appealing for data engineers, analysts, and scientists who want to run fast SQL queries without setting up a server, managing connections pools, or spinning up a warehouse.

This guide walks you through installation, core usage patterns, and the handful of integration points that make DuckDB feel like a natural extension of the Python data stack.

## Why an Embedded Analytical Database?

Traditional analytical databases like Snowflake or BigQuery are powerful, but they carry operational overhead: network round trips, credential management, billing configurations, cold-start latency. For exploratory analysis, prototyping, or batch processing on a single machine, that overhead can feel disproportionate to the task at hand.

DuckDB runs inside your process. There is no separate server to launch. You import a library, open a connection, and execute SQL. The entire engine ships as a single installable package—around 16 MB for the CLI, even smaller when embedded. Despite that compact footprint, the columnar storage format and vectorized execution engine handle analytical queries on datasets in the tens-of-gigabytes range without breaking a sweat on modern hardware.

The trade-off is straightforward: DuckDB is not designed for concurrent transactional workloads or serving thousands of simultaneous users. It shines when one process (or a small number of threads within one process) needs to crunch through data quickly.

## Installation

Getting started takes a single pip command:

```
pip install duckdb
```

That pulls down a self-contained wheel with no external dependencies. No C library to link against, no system packages to install. It works on Linux, macOS, and Windows across Python 3.8 and later.

Verify the installation:

```python
import duckdb
print(duckdb.__version__)
```

You should see the version string printed without errors. That is the entire setup process.

## Connecting and Running Queries

The entry point is `duckdb.connect()`. Called without arguments, it creates an in-memory database that lives for the duration of your Python session. Pass a file path to persist data to disk.

```python
import duckdb

# In-memory (temporary)
conn = duckdb.connect()

# Persistent, backed by a file
conn = duckdb.connect("my_analysis.duckdb")
```

With a connection in hand, you can execute SQL directly:

```python
conn.execute("CREATE TABLE measurements (sensor_id INTEGER, reading DOUBLE, ts TIMESTAMP)")
conn.execute("INSERT INTO measurements VALUES (1, 23.5, '2025-06-15 08:00:00')")
conn.execute("INSERT INTO measurements VALUES (2, 19.8, '2025-06-15 08:01:00')")

result = conn.execute("SELECT sensor_id, AVG(reading) FROM measurements GROUP BY sensor_id")
print(result.fetchall())
```

DuckDB's Python client follows the PEP 249 (DB-API 2.0) interface, so if you have used `sqlite3` or `psycopg2`, the patterns will feel familiar. You can call `conn.cursor()` to get a cursor object, though it is not strictly necessary—executing directly on the connection works identically.

### Parameterized Queries

To avoid SQL injection and handle dynamic values cleanly, pass parameters as a list with `?` placeholders:

```python
conn.execute(
    "INSERT INTO measurements VALUES (?, ?, ?)",
    [3, 21.2, "2025-06-15 08:02:00"]
)
```

For bulk operations, `executemany()` accepts a list of parameter tuples:

```python
rows = [
    (4, 18.7, "2025-06-15 08:03:00"),
    (5, 22.1, "2025-06-15 08:04:00"),
    (6, 20.9, "2025-06-15 08:05:00"),
]
conn.executemany("INSERT INTO measurements VALUES (?, ?, ?)", rows)
```

## Fetching Results

DuckDB gives you several ways to pull results out of a query, each suited to different downstream needs:

```python
result = conn.execute("SELECT * FROM measurements WHERE reading > 20")

# Plain Python lists
result.fetchall()    # list of tuples
result.fetchone()    # single tuple

# Pandas DataFrame
result.fetchdf()

# NumPy arrays (masked, so NULLs are handled properly)
result.fetchnumpy()
```

The `fetchdf()` method is probably the one you will reach for most often. It hands you a pandas DataFrame that you can immediately plot, reshape, or feed into scikit-learn. The `fetchnumpy()` variant returns masked arrays, which can be useful when you want to avoid the overhead of a full DataFrame for purely numerical work.

## Querying Files Directly

Here is where DuckDB starts to feel genuinely different from other databases. You can point SQL at raw files—CSV, Parquet, JSON—and query them without any import step:

```python
# Query a CSV file as if it were a table
result = conn.execute("SELECT * FROM 'sensor_data.csv' WHERE reading > 20")
print(result.fetchdf())

# Query a Parquet file
result = conn.execute("SELECT sensor_id, COUNT(*) FROM 'archive.parquet' GROUP BY sensor_id")
```

DuckDB automatically infers the schema from the file: column names from headers, data types from sampled values. For CSVs with unusual delimiters or quoting, you can use `read_csv()` with explicit options, but the automatic detection handles the common cases well.

Glob patterns let you treat a directory of files as a single table:

```python
# Read all CSVs matching the pattern
result = conn.execute("SELECT * FROM 'logs_2025_*.csv'")
```

If those files have slightly different schemas—say, one has an extra column added midway through the year—the `union_by_name` option aligns columns by name rather than position, filling in NULLs where a column is absent.

## Working with Pandas

The pandas integration goes both directions. You already saw `fetchdf()` for pulling results into DataFrames. Going the other way, you can query an existing DataFrame directly in SQL:

```python
import pandas as pd

orders = pd.DataFrame({
    "order_id": [101, 102, 103],
    "amount": [59.99, 124.50, 33.00],
    "region": ["west", "east", "west"]
})

# Reference the DataFrame variable name directly in SQL
result = conn.execute("SELECT region, SUM(amount) as total FROM orders GROUP BY region")
print(result.fetchdf())
```

DuckDB resolves the variable name `orders` from the local Python scope. No registration, no import—just write the variable name in your query. For cases where you want more control, `conn.register("my_view", df)` explicitly creates a named virtual table backed by the DataFrame.

One thing to watch out for when building tables from DataFrames: if you use `INSERT INTO some_table SELECT * FROM df`, column ordering depends on the table definition, not the DataFrame. This can silently produce wrong results if the column orders differ. The safer pattern is `CREATE TABLE some_table AS SELECT * FROM df`, which preserves the DataFrame's column names and ordering, or explicitly listing columns in the INSERT statement.

## The Relation API

Beyond raw SQL, DuckDB offers a programmatic query builder called the Relation API. Relations are lazily evaluated—nothing executes until you actually request the data:

```python
rel = conn.sql("SELECT * FROM measurements")

# Chain operations
filtered = rel.filter("reading > 20").project("sensor_id, reading").order("reading DESC").limit(5)

# Execute and fetch
print(filtered.fetchdf())
```

You can also construct relations from DataFrames or CSV files:

```python
rel = duckdb.from_csv_auto("sensor_data.csv")
summary = rel.aggregate("sensor_id, AVG(reading) AS avg_reading").order("avg_reading")
```

Relations compose well. You can join two relations, union them, or pass them as subqueries. The lazy evaluation means DuckDB's optimizer sees the entire pipeline before it runs, which can result in better query plans than issuing individual SQL statements.

## Practical Tips

**In-memory vs. persistent connections.** For one-off scripts and notebooks, in-memory databases keep things simple. Switch to a file-backed database when you want to avoid re-importing data on every run or when your dataset is larger than available RAM (DuckDB will spill to disk).

**Memory behavior.** DuckDB uses a memory allocator that holds onto freed pages rather than returning them to the operating system immediately. If you are monitoring RSS in a long-running process, you might notice memory usage plateaus rather than drops after a large query finishes. This is expected allocator behavior—those pages get reused by subsequent queries without incurring allocation overhead.

**Thread safety.** A single connection should not be shared across threads making concurrent writes. For read-heavy parallelism within one process, DuckDB handles that internally during query execution. If you need multiple threads writing, use separate connections or serialize access.

**Notebook workflows.** DuckDB pairs naturally with Jupyter. A dedicated DuckDB kernel for Jupyter exists if you want native SQL cells, but the standard Python kernel with `conn.execute()` calls works well. Wrapping queries in `fetchdf()` gives you the DataFrame rendering that notebooks display nicely by default.

## Where to Go Next

Once you are comfortable with the basics, a few directions open up. DuckDB can query Parquet files stored in S3 directly, which makes it viable as a lightweight query layer over cloud data lakes. Extensions add support for additional formats and integrations—the spatial extension for geospatial data, the httpfs extension for remote files, and several others.

For anything beyond single-machine analytical workloads—high-concurrency serving, sub-millisecond transactional writes, or multi-terabyte datasets that exceed what one node can handle—you will want to look at dedicated systems built for those patterns. DuckDB does not try to be everything. It targets the analytical sweet spot on a single machine and does that job remarkably well.

The Python client is the shortest path from zero to running SQL against your data. Install the package, open a connection, and start writing queries. The gap between having data in a file and having answers from that data shrinks to a handful of lines.
