# Getting Started with DuckDB's Python Client

If you've spent any real time wrangling CSV exports, Parquet files, or pandas DataFrames, you've probably heard someone mention DuckDB. Think of it like SQLite, but built for columnar, read-heavy analytical workloads instead of row-level transactions. The Python client is what makes it especially appealing for data engineers, analysts, and scientists who want fast SQL queries without setting up a server, managing connection pools, or spinning up a warehouse.

This guide walks you through installation, core usage patterns, and the integration points that make DuckDB feel like a natural extension of the Python data stack.

## Why an Embedded Analytical Database?

Analytical databases like Snowflake or BigQuery are powerful, but they carry operational overhead: network round trips, credential management, billing configurations, cold-start latency. For exploratory analysis or batch processing on a single machine, that overhead can feel disproportionate.

DuckDB runs inside your process. No separate server to launch. You import a library, open a connection, and execute SQL. The entire engine ships as a single installable package (around 16 MB for the CLI, even smaller when embedded), yet the columnar storage format and vectorized execution engine handle analytical queries on datasets in the tens-of-gigabytes range without breaking a sweat on modern hardware.

The trade-off is straightforward: it's not designed for concurrent transactional workloads or serving thousands of simultaneous users. It shines when one process, or a small number of threads within that process, needs to crunch through data quickly.

## Installation

One pip command:


pip install duckdb


That pulls down a self-contained wheel with no external dependencies. No C library to link against, no system packages to install. Works on Linux, macOS, and Windows across Python 3.8 and later.

Verify it:


import duckdb
print(duckdb.__version__)


You should see the version string printed without errors. That's the entire setup.

## Connecting and Running Queries

The entry point is `duckdb.connect()`. Called without arguments, it creates an in-memory database that lives for the duration of your Python session. Pass a file path to persist data to disk.


import duckdb

# In-memory (temporary)
conn = duckdb.connect()

# Persistent, backed by a file
conn = duckdb.connect("my_analysis.duckdb")


With a connection in hand, you can execute SQL directly:


conn.execute("CREATE TABLE measurements (sensor_id INTEGER, reading DOUBLE, ts TIMESTAMP)")
conn.execute("INSERT INTO measurements VALUES (1, 23.5, '2025-06-15 08:00:00')")
conn.execute("INSERT INTO measurements VALUES (2, 19.8, '2025-06-15 08:01:00')")

result = conn.execute("SELECT sensor_id, AVG(reading) FROM measurements GROUP BY sensor_id")
print(result.fetchall())


The Python client follows PEP 249 (DB-API 2.0), so if you've used `sqlite3` or `psycopg2`, the patterns will feel familiar. You can call `conn.cursor()` to get a cursor object, though it isn't strictly necessary; executing directly on the connection works the same way.

### Parameterized Queries

To avoid SQL injection and handle dynamic values cleanly, pass parameters as a list with `?` placeholders:


conn.execute(
    "INSERT INTO measurements VALUES (?, ?, ?)",
    [3, 21.2, "2025-06-15 08:02:00"]
)


For bulk operations, `executemany()` accepts a list of parameter tuples:


rows = [
    (4, 18.7, "2025-06-15 08:03:00"),
    (5, 22.1, "2025-06-15 08:04:00"),
    (6, 20.9, "2025-06-15 08:05:00"),
]
conn.executemany("INSERT INTO measurements VALUES (?, ?, ?)", rows)


## Fetching Results

DuckDB gives you several ways to pull results out of a query. The most basic are `fetchall()`, which returns a list of tuples, and `fetchone()` for grabbing a single tuple. If you want a pandas DataFrame (and honestly, that's what I reach for most often), there's `fetchdf()`. For purely numerical work where you'd rather skip the DataFrame overhead, `fetchnumpy()` returns masked NumPy arrays that handle NULLs properly.


result = conn.execute("SELECT * FROM measurements WHERE reading > 20")

# Plain Python lists
result.fetchall()    # list of tuples
result.fetchone()    # single tuple

# Pandas DataFrame
result.fetchdf()

# NumPy arrays (masked, so NULLs are handled properly)
result.fetchnumpy()


## Querying Files Directly

Here's where things get interesting. You can point SQL at raw files (CSV, Parquet, JSON) and query them without any import step:


# Query a CSV file as if it were a table
result = conn.execute("SELECT * FROM 'sensor_data.csv' WHERE reading > 20")
print(result.fetchdf())

# Query a Parquet file
result = conn.execute("SELECT sensor_id, COUNT(*) FROM 'archive.parquet' GROUP BY sensor_id")


Schema inference happens automatically: column names from headers, data types from sampled values. For CSVs with unusual delimiters or quoting, you can use `read_csv()` with explicit options, but the automatic detection handles common cases well.

Glob patterns let you treat a directory of files as a single table:


# Read all CSVs matching the pattern
result = conn.execute("SELECT * FROM 'logs_2025_*.csv'")


If those files have slightly different schemas (say, one picked up an extra column midway through the year), the `union_by_name` option aligns columns by name rather than position, filling in NULLs where a column is absent.

## Working with Pandas

The pandas integration goes both directions. You already saw `fetchdf()` for pulling results into DataFrames. Going the other way, you can query an existing DataFrame directly in SQL:


import pandas as pd

orders = pd.DataFrame({
    "order_id": [101, 102, 103],
    "amount": [59.99, 124.50, 33.00],
    "region": ["west", "east", "west"]
})

# Reference the DataFrame variable name directly in SQL
result = conn.execute("SELECT region, SUM(amount) as total FROM orders GROUP BY region")
print(result.fetchdf())


DuckDB resolves the variable name `orders` from the local Python scope. No registration, no import step; just write the variable name in your query. For cases where you want more control, `conn.register("my_view", df)` explicitly creates a named virtual table backed by the DataFrame.

One gotcha worth knowing: if you use `INSERT INTO some_table SELECT * FROM df`, column ordering depends on the table definition, not the DataFrame. This can silently produce wrong results when column orders differ. The safer pattern is `CREATE TABLE some_table AS SELECT * FROM df`, which preserves the DataFrame's column names and ordering. Or just list your columns explicitly in the INSERT statement.

## The Relation API

Beyond raw SQL, there's a programmatic query builder called the Relation API. Relations are lazily evaluated, so nothing executes until you actually request the data:


rel = conn.sql("SELECT * FROM measurements")

# Chain operations
filtered = rel.filter("reading > 20").project("sensor_id, reading").order("reading DESC").limit(5)

# Execute and fetch
print(filtered.fetchdf())


You can also construct relations from DataFrames or CSV files:


rel = duckdb.from_csv_auto("sensor_data.csv")
summary = rel.aggregate("sensor_id, AVG(reading) AS avg_reading").order("avg_reading")


They compose well. Join two of them, union them, pass them as subqueries. Because evaluation is lazy, the optimizer sees the entire pipeline before running anything, which can produce better query plans than issuing individual SQL statements.

## Practical Tips

For one-off scripts and notebooks, in-memory databases keep things simple. Switch to a file-backed database when you want to avoid re-importing data on every run or when your dataset is larger than available RAM (DuckDB will spill to disk).

Something that caught me off guard: the memory allocator holds onto freed pages rather than returning them to the OS immediately. If you're monitoring RSS in a long-running process, you might notice memory usage plateaus rather than drops after a large query finishes. Don't panic. Those pages get reused by subsequent queries without extra allocation overhead.

On thread safety, a single connection shouldn't be shared across threads making concurrent writes. For read-heavy parallelism within one process, DuckDB handles that internally during query execution; if you need multiple threads writing, use separate connections or serialize access.

It pairs naturally with Jupyter, too. A dedicated DuckDB kernel exists if you want native SQL cells, but the standard Python kernel with `conn.execute()` calls works fine. Wrapping queries in `fetchdf()` gives you the DataFrame rendering that notebooks display nicely by default.

## Where to Go Next

Once you're comfortable with the basics, a few directions open up. DuckDB can query Parquet files stored in S3 directly, which makes it viable as a lightweight query layer over cloud data lakes. Extensions add support for extra formats and integrations: the spatial extension for geospatial data, the httpfs extension for remote files, and several others.

For anything beyond single-machine analytical workloads (high-concurrency serving, sub-millisecond transactional writes, multi-terabyte datasets that exceed what one node can handle), you'll want dedicated systems built for those patterns. It doesn't try to be everything; it targets the analytical sweet spot on a single machine and, from what I can tell, does that job very well.

The Python client is the shortest path from zero to running SQL against your data. Install the package, open a connection, start writing queries. That's it.
