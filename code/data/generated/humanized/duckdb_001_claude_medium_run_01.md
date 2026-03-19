# Getting Started with the DuckDB Python Client

If you work with data in Python, you've probably hit the wall where pandas just gets slow. Wide joins across a pile of CSVs, aggregations over millions of rows, validation pipelines that eat your laptop's RAM. DuckDB gives you a way out: it's an embedded analytical database that runs inside your Python process, needs zero configuration, and can query files sitting on your local disk with plain SQL.

This post covers the basics of using it from Python, from installation through querying DataFrames and files, so you can figure out if it belongs in your workflow.

## Installation

One pip command:

```bash
pip install duckdb
```

No external services to configure. No daemon processes, no credentials. The whole database engine ships as a compiled extension bundled into the Python package, which honestly still surprises me given how much it can do.

## Creating a Connection

Everything starts with a connection object. For exploratory analysis you can work entirely in memory:

```python
import duckdb

conn = duckdb.connect()
```

Need results to stick around between sessions? Pass a file path instead:

```python
conn = duckdb.connect("my_analysis.duckdb")
```

There's also a read-only flag for when you want to make sure no accidental writes touch the database:

```python
conn = duckdb.connect("my_analysis.duckdb", read_only=True)
```

DuckDB exposes a default module-level connection too. Functions like `duckdb.sql()` and `duckdb.query()` use it behind the scenes. Convenient for throwaway scripts, but not great if you're managing multiple databases at once.

## Running SQL

With a connection in hand, `execute` takes any SQL statement:

```python
conn.execute("CREATE TABLE measurements (sensor_id INTEGER, reading DOUBLE)")
conn.execute("INSERT INTO measurements VALUES (1, 23.5), (2, 18.7)")
result = conn.execute("SELECT * FROM measurements").fetchall()
```

Parameterized queries use positional placeholders to keep user-supplied values out of the SQL string:

```python
conn.execute("INSERT INTO measurements VALUES (?, ?)", [3, 21.0])
```

For bulk loading, `executemany` accepts an iterable of parameter tuples, which is handy when you already have rows sitting in memory.

## Getting Results Out

There are several ways to pull query results depending on what you need next. `fetchall()` and `fetchone()` return plain Python tuples; fine for small result sets or row-at-a-time processing. When your downstream code expects a pandas DataFrame, call `fetchdf()` directly on the query result:

```python
df = conn.execute("SELECT * FROM measurements WHERE reading > 20").fetchdf()
```

Then there's `fetchnumpy()`, which returns dictionary-keyed masked NumPy arrays. The masking handles NULL values more cleanly than the pandas approach of promoting integer columns to float whenever a missing value shows up. I think this is underappreciated, from what I can tell most people don't even know it exists.

## Querying Pandas DataFrames with SQL

One of my favorite features: you can treat an existing pandas DataFrame as a SQL table without copying data into the database first. Just register it under a name:

```python
import pandas as pd

sales = pd.DataFrame({
    "product": ["widget", "gadget", "widget", "gadget"],
    "revenue": [100, 250, 150, 300]
})

conn.register("sales", sales)
conn.execute("SELECT product, SUM(revenue) FROM sales GROUP BY product").fetchdf()
```

This means you can combine SQL tables and DataFrames in the same query. Say you have a dimension table in the database and an in-memory DataFrame loaded from an API response; you can join them directly.

## Querying Files Directly

DuckDB reads CSV, Parquet, and JSON files straight from a `SELECT` statement. No explicit loading step needed:

```python
result = duckdb.sql("SELECT * FROM 'transactions_2024.csv' LIMIT 10")
```

Glob patterns let you treat a folder of files as one table:

```python
result = duckdb.sql("SELECT * FROM 'logs_*.csv'")
```

The built-in CSV parser infers column types automatically. For Parquet files, it pushes predicates and column selections down into the reader, so it only touches the data it actually needs. That's a real efficiency win over loading an entire file into a DataFrame first.

## The Relation API

Beyond raw SQL, there's a programmatic interface called the Relation API. A relation wraps a lazy query plan that you build up through method calls:

```python
rel = conn.table("measurements")
heavy_readings = rel.filter("reading > 20").project("sensor_id, reading").order("reading")
```

You can chain operations like `filter`, `project`, `order`, `limit`, `aggregate`, `join`, `union`, and `distinct`. Nothing executes until you materialize the result with `.fetchdf()`, `.fetchall()`, or `.execute()`. You can also create relations directly from DataFrames and CSV files:

```python
rel = duckdb.from_csv_auto("sensor_data.csv")
summary = rel.aggregate("AVG(reading)", "sensor_id")
```

This API is useful when you want to build queries dynamically (say, constructing filters from user selections in a dashboard) without resorting to string concatenation.

## Concurrency Considerations

You can open multiple cursors from a single connection, which enables concurrent read queries within one process:

```python
cursor_a = conn.cursor()
cursor_b = conn.cursor()
```

Be careful with concurrent writes though. Earlier versions had stability issues when multiple threads did conflicting updates through separate cursors on the same connection. Recent releases (v1.4.0 and later) fixed several of those problems, but sticking with a single-writer pattern is still the safest default for production workloads.

## Memory Awareness

Because DuckDB runs inside your process, it shares your application's memory budget. It uses efficient columnar compression and streaming execution, so many workloads fit comfortably in RAM.

That said, certain operations can spike memory in ways you won't expect. Heavily partitioned Parquet exports and very wide cross joins are the usual culprits. If you're writing partitioned data to storage, consider iterating over partition values and exporting each subset individually rather than issuing a single partitioned `COPY` command. Costs you a few more lines of code but keeps memory predictable.

## When DuckDB Fits Well

It shines for local analytical queries: ad-hoc exploration of CSV and Parquet files, data validation pipelines, feature engineering in ML workflows, anywhere you want SQL without the overhead of a server. Community benchmarks on moderate datasets (tens of gigabytes of Parquet) show sub-second response times on consumer hardware, often beating cloud warehouses for the same workload.

It's not great for high-concurrency transactional workloads or scenarios where dozens of users need simultaneous write access. Think of it as SQLite's analytical counterpart: lightweight, embedded, and really capable within its design niche.

If your current workflow involves reading CSVs into pandas, reshaping them, and running grouped aggregations, try rewriting one of those steps with DuckDB. The docs don't make it obvious how little friction is involved, but the combination of familiar SQL, direct file access, and easy DataFrame interop makes it worth the ten minutes to try.
