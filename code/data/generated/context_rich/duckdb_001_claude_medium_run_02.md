# Getting Started with the DuckDB Python Client

Analysts and engineers who spend their time loading CSVs into Pandas, watching memory climb, and then rewriting everything in SQL on a remote warehouse should take a close look at DuckDB. It brings a full-featured analytical query engine into your Python process with zero infrastructure. No server. No Docker container. No credentials file. Just `pip install duckdb` and you are running columnar queries on your laptop.

## Why DuckDB Exists

SQLite proved that embedding a database directly inside an application could be wildly useful. But SQLite targets transactional workloads — row-level inserts, updates, and lookups. Analytical queries that scan millions of rows and compute aggregations are not its strength. DuckDB fills that gap. It stores data in columns rather than rows and processes values in vectorized batches that exploit modern CPU cache hierarchies. The outcome is that aggregation-heavy queries finish in a fraction of the time you might expect from an embedded library.

Because the engine lives inside your Python process, there is no serialization overhead when moving data between your application and the database. A query result can become a Pandas DataFrame or a NumPy array with minimal copying.

## Installing and Connecting

Installation is a single command:

```bash
pip install duckdb
```

There are no native dependencies to compile and no external services to start. The package ships a self-contained binary for each supported platform.

To open a connection:

```python
import duckdb

# Fully in-memory — everything vanishes when the process ends
conn = duckdb.connect()

# Backed by a file — your tables persist across sessions
conn = duckdb.connect("analytics.duckdb")
```

The connection object is your gateway to everything. It follows Python's DB-API 2.0 closely enough that existing muscle memory carries over.

## Running Queries

The `execute` method accepts SQL strings and returns a result object you can fetch from in several formats:

```python
conn.execute("CREATE TABLE events (user_id INTEGER, action VARCHAR, ts TIMESTAMP)")
conn.execute("INSERT INTO events VALUES (1, 'click', '2024-06-01 09:15:00')")
conn.execute("INSERT INTO events VALUES (?, ?, ?)", [2, 'purchase', '2024-06-01 10:30:00'])

# Fetch as Python tuples
rows = conn.execute("SELECT * FROM events").fetchall()

# Fetch directly as a Pandas DataFrame
df = conn.execute("SELECT action, COUNT(*) AS cnt FROM events GROUP BY action").fetchdf()

# Fetch as NumPy masked arrays — cleaner NULL handling
arrays = conn.execute("SELECT * FROM events").fetchnumpy()
```

For batch inserts, `executemany` accepts a list of parameter lists, which avoids writing a loop around single-row inserts:

```python
conn.executemany("INSERT INTO events VALUES (?, ?, ?)", [
    [3, 'click', '2024-06-01 11:00:00'],
    [4, 'signup', '2024-06-01 11:05:00'],
])
```

## Querying Pandas DataFrames Directly

Perhaps the most immediately useful feature: DuckDB can query Pandas DataFrames as though they are tables, without any explicit import step. It reads the DataFrame's underlying memory buffers directly.

```python
import pandas as pd

orders = pd.DataFrame({
    "customer": ["Alice", "Bob", "Alice", "Carol"],
    "amount": [50, 120, 30, 90]
})

result = duckdb.sql("""
    SELECT customer, SUM(amount) AS total_spent
    FROM orders
    GROUP BY customer
    ORDER BY total_spent DESC
""").fetchdf()
```

DuckDB resolves the name `orders` by looking it up in the calling scope's local variables. This feels almost magical the first time you see it. For cases where you want more explicit control, `conn.register("my_table", df)` binds a DataFrame to a specific name within a connection.

One subtlety worth noting: if you use `INSERT INTO ... SELECT * FROM registered_view`, column ordering follows position, not name. When columns in the DataFrame and the target table are in different orders, values can end up in the wrong columns silently. Specifying column names in both the INSERT and SELECT clauses avoids this entirely.

## Reading Files Without Importing

DuckDB queries CSV, Parquet, and JSON files in place. You do not need to load them into a table first:

```python
# CSV with automatic type detection
conn.execute("SELECT * FROM 'sales_2024.csv' WHERE region = 'West'").fetchdf()

# Multiple Parquet files via glob
conn.execute("SELECT * FROM 'logs/year=2024/month=*/*.parquet'").fetchdf()

# JSON lines
conn.execute("SELECT * FROM read_json_auto('events.jsonl')").fetchdf()
```

Glob support is especially handy when your data arrives as hundreds of daily export files. A single query unifies them all. For Parquet files, DuckDB pushes predicates and column selections down into the reader, so it only decompresses the data it actually needs. On wide tables with dozens of columns, this can cut I/O by an order of magnitude.

## The Relational API

Beyond raw SQL, DuckDB offers a chainable API for building queries programmatically. Operations are lazy — nothing executes until you explicitly ask for results:

```python
rel = conn.from_csv_auto("measurements.csv")
summary = (
    rel
    .filter("temperature > 30")
    .aggregate("station_id, AVG(temperature) AS avg_temp")
    .order("avg_temp DESC")
    .limit(10)
)
print(summary.fetchdf())
```

This style works well in library code where query structure depends on runtime parameters, and chaining avoids the messy string concatenation that plagues dynamic SQL construction.

## Practical Considerations

**Single-writer concurrency.** DuckDB permits multiple concurrent readers but only one writer. It is not designed for workloads where several threads or processes write simultaneously. For that, a client-server database remains the right tool.

**File size after deletes.** Deleting rows from a persistent database does not shrink the underlying file. Freed space is reused internally but not returned to the filesystem. In pipelines that frequently delete and reinsert data, the file can grow over time. Periodically exporting to Parquet and recreating the database is a reliable workaround.

**Memory after large queries.** DuckDB's allocator holds onto freed memory for potential reuse rather than returning it to the OS immediately. Monitoring tools may report higher resident memory than the data truly requires. This is expected behavior, not a leak, but it can cause confusion in memory-constrained environments.

## Where to Go Next

Once the basics feel comfortable, explore DuckDB's window functions, recursive CTEs, and nested types like structs and arrays for semi-structured data. The extension ecosystem adds capabilities for spatial queries, full-text search, and remote object storage access on S3 or GCS. A dedicated Jupyter kernel even lets you write DuckDB SQL in notebook cells without Python wrapper code.

For data work that lives in the uncomfortable middle ground — too large for Pandas, too small to justify a warehouse — DuckDB is a remarkably capable option. Try pointing it at a CSV file you already have and run a few aggregations. The speed alone usually makes the case.
