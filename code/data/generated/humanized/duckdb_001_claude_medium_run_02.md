# Getting Started with the DuckDB Python Client

If you've been loading CSVs into Pandas, watching memory creep up, and then rewriting everything in SQL on a remote warehouse, take a look at DuckDB. It brings a full analytical query engine into your Python process with zero infrastructure. No server. No Docker container. No credentials file. Just `pip install duckdb` and you're running columnar queries on your laptop.

## Why DuckDB Exists

SQLite proved that embedding a database inside an application could be wildly useful. But it targets transactional workloads: row-level inserts, updates, lookups. Analytical queries that scan millions of rows and compute aggregations? Not its strength.

DuckDB fills that gap. It stores data in columns rather than rows, processing values in vectorized batches that take advantage of modern CPU cache hierarchies. Aggregation-heavy queries finish in a fraction of the time you'd expect from an embedded library. And because the engine lives inside your Python process, there's no serialization overhead when moving data between your application and the database; a query result can become a Pandas DataFrame or a NumPy array with minimal copying.

## Installing and Connecting

Installation is a single command:

```bash
pip install duckdb
```

No native dependencies to compile, no external services to start. The package ships a self-contained binary for each supported platform.

To open a connection:

```python
import duckdb

# In-memory: everything vanishes when the process ends
conn = duckdb.connect()

# File-backed: tables persist across sessions
conn = duckdb.connect("analytics.duckdb")
```

The connection object is your entry point to everything. It follows Python's DB-API 2.0 closely enough that existing muscle memory carries over.

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

# Fetch as NumPy masked arrays for cleaner NULL handling
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

This might be my favorite feature. DuckDB can query Pandas DataFrames as though they're tables, with no explicit import step. It reads the DataFrame's underlying memory buffers directly.

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

DuckDB resolves the name `orders` by looking it up in the calling scope's local variables. Honestly, it feels almost magical the first time you see it. If you want more explicit control, `conn.register("my_table", df)` binds a DataFrame to a specific name within a connection.

One subtlety worth knowing: if you use `INSERT INTO ... SELECT * FROM registered_view`, column ordering follows position, not name. Columns in the DataFrame and the target table might be in different orders, and values can end up in the wrong place silently. Specifying column names in both the INSERT and SELECT clauses avoids this.

## Reading Files Without Importing

DuckDB queries CSV, Parquet, and JSON files in place. You don't need to load them into a table first:

```python
# CSV with automatic type detection
conn.execute("SELECT * FROM 'sales_2024.csv' WHERE region = 'West'").fetchdf()

# Multiple Parquet files via glob
conn.execute("SELECT * FROM 'logs/year=2024/month=*/*.parquet'").fetchdf()

# JSON lines
conn.execute("SELECT * FROM read_json_auto('events.jsonl')").fetchdf()
```

Glob support is especially handy when your data arrives as hundreds of daily export files; a single query unifies them all. For Parquet specifically, DuckDB pushes predicates and column selections down into the reader, so it only decompresses what it actually needs. On wide tables with dozens of columns, this can cut I/O by an order of magnitude.

## The Relational API

Beyond raw SQL, DuckDB offers a chainable API for building queries programmatically. Operations are lazy, so nothing executes until you explicitly ask for results:

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

This style works well in library code where query structure depends on runtime parameters. Chaining avoids the messy string concatenation that plagues dynamic SQL construction, which I think is reason enough to reach for it.

## Practical Considerations

DuckDB permits multiple concurrent readers but only one writer. It's not built for workloads where several threads or processes write simultaneously, so for that scenario a client-server database is still the right call.

Here's something that caught me off guard. Deleting rows from a persistent database doesn't shrink the underlying file; freed space gets reused internally but never returned to the filesystem. In pipelines that frequently delete and reinsert data, the file just keeps growing. The usual workaround is exporting to Parquet periodically and recreating the database from scratch.

The allocator also holds onto freed memory for reuse rather than returning it to the OS right away. Monitoring tools may report higher resident memory than your data truly requires. Not a leak. Just expected behavior, though it can cause confusion if you're in a memory-constrained environment.

## Where to Go Next

Once the basics feel comfortable, try DuckDB's window functions, recursive CTEs, and nested types like structs and arrays for semi-structured data. The extension ecosystem adds spatial queries, full-text search, and remote object storage access on S3 or GCS. There's even a dedicated Jupyter kernel that lets you write SQL in notebook cells without Python wrapper code.

For data work in the uncomfortable middle ground (too large for Pandas, too small to justify a warehouse) I've found this to be a pretty capable option. Point it at a CSV you already have and run a few aggregations. The speed alone usually makes the case.
