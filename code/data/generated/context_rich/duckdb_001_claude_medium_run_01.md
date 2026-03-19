# Getting Started with the DuckDB Python Client

If you work with data in Python, chances are you have bumped into situations where pandas starts to feel sluggish—wide joins across multiple CSVs, aggregations over millions of rows, or validation pipelines that eat through your laptop's RAM. DuckDB offers a compelling alternative: an embedded analytical database that runs inside your Python process, requires zero configuration, and speaks fluent SQL against files sitting on your local disk.

This post walks through the fundamentals of using DuckDB from Python, from installation through querying DataFrames and files, so you can decide whether it belongs in your data toolkit.

## Installation

Getting DuckDB into a Python environment takes a single pip command:


pip install duckdb


There are no external services to configure, no daemon processes, and no credentials to manage. The entire database engine ships as a compiled extension bundled into the Python package.

## Creating a Connection

Everything begins with a connection object. For exploratory analysis you can work entirely in memory:


import duckdb

conn = duckdb.connect()


If you need results to persist between sessions, pass a file path instead:


conn = duckdb.connect("my_analysis.duckdb")


A read-only flag is available when you want to guarantee that no accidental writes modify the database:


conn = duckdb.connect("my_analysis.duckdb", read_only=True)


DuckDB also exposes a default, module-level connection. Functions like `duckdb.sql()` and `duckdb.query()` use it behind the scenes, which is convenient for one-off scripts but less suitable for applications that manage multiple databases concurrently.

## Running SQL

With a connection in hand, the `execute` method accepts any SQL statement:


conn.execute("CREATE TABLE measurements (sensor_id INTEGER, reading DOUBLE)")
conn.execute("INSERT INTO measurements VALUES (1, 23.5), (2, 18.7)")
result = conn.execute("SELECT * FROM measurements").fetchall()


Parameterized queries use positional placeholders to keep user-supplied values out of the SQL string:


conn.execute("INSERT INTO measurements VALUES (?, ?)", [3, 21.0])


For bulk loading, `executemany` accepts an iterable of parameter tuples—handy when you already have rows in memory.

## Getting Results Out

DuckDB gives you several ways to materialize query results depending on what you plan to do next.

`fetchall()` and `fetchone()` return plain Python tuples, which is fine for small result sets or row-at-a-time processing. When your downstream code expects a pandas DataFrame, call `fetchdf()` directly on the query result:


df = conn.execute("SELECT * FROM measurements WHERE reading > 20").fetchdf()


There is also `fetchnumpy()`, which returns dictionary-keyed masked NumPy arrays. The masking handles NULL values more cleanly than pandas' approach of promoting integer columns to float whenever a missing value appears.

## Querying Pandas DataFrames with SQL

One of DuckDB's most practical features is its ability to treat an existing pandas DataFrame as a SQL table without copying the data into the database first. You register a DataFrame under a name:


import pandas as pd

sales = pd.DataFrame({
    "product": ["widget", "gadget", "widget", "gadget"],
    "revenue": [100, 250, 150, 300]
})

conn.register("sales", sales)
conn.execute("SELECT product, SUM(revenue) FROM sales GROUP BY product").fetchdf()


This means you can combine SQL tables and DataFrames in the same query, joining an in-database dimension table against an in-memory DataFrame loaded from an API response, for example.

## Querying Files Directly

DuckDB can read CSV, Parquet, and JSON files straight from a `SELECT` statement without any explicit loading step:


result = duckdb.sql("SELECT * FROM 'transactions_2024.csv' LIMIT 10")


Glob patterns let you treat a folder of files as a single table:


result = duckdb.sql("SELECT * FROM 'logs_*.csv'")


The built-in CSV parser infers column types automatically. For Parquet files, DuckDB pushes predicates and column selections down into the reader, meaning it only touches the data it actually needs—a significant efficiency gain over loading an entire file into a DataFrame first.

## The Relation API

Beyond raw SQL, DuckDB provides a programmatic interface called the Relation API. A relation wraps a lazy query plan that you build up through method calls:


rel = conn.table("measurements")
heavy_readings = rel.filter("reading > 20").project("sensor_id, reading").order("reading")


Operations like `filter`, `project`, `order`, `limit`, `aggregate`, `join`, `union`, and `distinct` can be chained together. Nothing executes until you materialize the result with `.fetchdf()`, `.fetchall()`, or `.execute()`. You can also create relations directly from DataFrames and CSV files:


rel = duckdb.from_csv_auto("sensor_data.csv")
summary = rel.aggregate("AVG(reading)", "sensor_id")


The Relation API is useful when you want to construct queries dynamically—say, building up filters from user selections in a dashboard—without resorting to string concatenation.

## Concurrency Considerations

DuckDB allows multiple cursors from a single connection, enabling concurrent read queries within one process:


cursor_a = conn.cursor()
cursor_b = conn.cursor()


However, be cautious with concurrent writes. Earlier versions of DuckDB had stability issues when multiple threads performed conflicting update operations through separate cursors on the same connection. Recent releases (v1.4.0 and later) resolved several of these problems, but a single-writer pattern remains the safest default for production workloads.

## Memory Awareness

Because DuckDB runs inside your process, it shares your application's memory budget. It uses efficient columnar compression and streaming execution, so many workloads fit comfortably in RAM. Still, certain operations—heavily partitioned exports to Parquet, very wide cross joins—can spike memory usage in surprising ways.

If you are writing partitioned data to storage, consider iterating over partition values and exporting each subset individually rather than issuing a single partitioned `COPY` command. This keeps memory predictable at the cost of a few more lines of code.

## When DuckDB Fits Well

DuckDB shines for local analytical queries: ad-hoc exploration of CSV and Parquet files, data validation pipelines, feature engineering in ML workflows, and anywhere you want SQL without the overhead of a server. Community benchmarks on moderate datasets (tens of gigabytes of Parquet) show sub-second response times on consumer hardware, often outperforming cloud warehouses for the same workload.

It is less suited for high-concurrency transactional workloads or scenarios where dozens of users need simultaneous write access. Think of it as SQLite's analytical counterpart: lightweight, embedded, and remarkably capable within its design niche.

If your current workflow involves reading CSVs into pandas, reshaping them, and running grouped aggregations, try rewriting one of those steps in DuckDB. The combination of familiar SQL, direct file access, and seamless DataFrame interoperability makes it one of the lowest-friction database tools available to Python developers today.
