# Getting Started with the DuckDB Python Client

If you spend your days wrangling CSV exports, joining Parquet files, or pushing Pandas to its memory limits, DuckDB deserves a hard look. It's an embedded analytical database that runs inside your Python process with no server required, and it routinely outperforms cloud query engines on medium-sized datasets. This post walks through installation, core usage patterns, and the practical details that matter once you move past toy examples.

## What DuckDB Actually Is

Most databases run as a separate process. You start a server, open a network connection, send queries over a wire protocol. DuckDB takes the opposite approach: it's an in-process library, similar in spirit to SQLite but engineered for analytical workloads rather than transactional ones. When you call `import duckdb` in Python, the entire query engine loads into your application's memory space. No daemon to manage. No port to configure. No authentication layer to set up.

Under the hood, it uses a columnar storage format and a vectorized execution engine. Instead of processing rows one at a time, it operates on batches of values that fit snugly in CPU caches. The practical result is that analytical queries (aggregations, window functions, large scans) run dramatically faster than you'd expect from a library you installed with pip.

## Installation

Getting started takes one line:


pip install duckdb


The package is self-contained. There are no system-level dependencies, no compiled extensions to chase down, no database server to provision. It supports Python 3.7+, though 3.9 or later is recommended if you want proper type hints and modern language features.

## Your First Queries

DuckDB exposes a connection object that acts as the entry point to everything. You can run it entirely in memory or back it with a file for persistence between sessions.


import duckdb

# In-memory database - disappears when the process exits
conn = duckdb.connect()

# Persistent database - state survives restarts
conn = duckdb.connect("my_analysis.duckdb")


From there, the interface follows Python's DB-API 2.0 conventions closely enough to feel familiar:


conn.execute("CREATE TABLE readings (sensor_id INTEGER, ts TIMESTAMP, value DOUBLE)")
conn.execute("INSERT INTO readings VALUES (1, '2024-01-15 08:30:00', 23.4)")
conn.execute("INSERT INTO readings VALUES (1, '2024-01-15 09:00:00', 24.1)")

results = conn.execute("SELECT sensor_id, AVG(value) FROM readings GROUP BY sensor_id").fetchall()
print(results)


The `fetchall()` method returns plain Python tuples, but that's rarely the most convenient format for analytical work. You've also got `fetchdf()` to hand you a Pandas DataFrame directly, and `fetchnumpy()` for NumPy masked arrays with proper NULL handling.

## Three Ways to Work

The Python client supports three distinct programming styles, and understanding the differences saves confusion later.

**Direct SQL execution** is the most straightforward. You write SQL strings, pass them to `execute()`, and fetch results. This is the right choice when your queries are self-contained and you want full control over the SQL dialect.

**The Relational API** offers a chainable, lazy interface for building queries programmatically:


rel = conn.from_csv_auto("sensor_data.csv")
result = rel.filter("value > 20").aggregate("sensor_id, AVG(value) AS avg_val").execute().fetchdf()


Operations like `filter()`, `project()`, and `aggregate()` build up a query plan without executing it. Nothing actually runs until you call `execute()` or a terminal method like `fetchdf()`. This deferred evaluation lets DuckDB optimize the full query before touching any data.

**Module-level shorthand functions** skip the explicit connection for quick one-off operations:


import duckdb

# Query a Pandas DataFrame with SQL, no connection needed
result = duckdb.query("SELECT * FROM my_df WHERE score > 90")


These use a shared default connection behind the scenes. They're convenient for notebooks and exploratory analysis, but the explicit connection approach scales better for production code.

## Querying Pandas DataFrames with SQL

One of DuckDB's strongest features is its ability to query Pandas DataFrames as if they were database tables. No data copying involved; it reads the DataFrame's underlying memory buffers directly.


import pandas as pd
import duckdb

sales = pd.DataFrame({
    "region": ["East", "West", "East", "West", "East"],
    "product": ["A", "A", "B", "B", "A"],
    "revenue": [100, 150, 200, 80, 120]
})

result = duckdb.query("""
    SELECT region, product, SUM(revenue) as total
    FROM sales
    GROUP BY region, product
    ORDER BY total DESC
""").fetchdf()


Notice that DuckDB picks up the variable name `sales` automatically and makes it available as a table reference in SQL. Honestly, this surprised me the first time I saw it. For more control, you can register DataFrames explicitly:


conn = duckdb.connect()
conn.register("monthly_sales", sales)
conn.execute("SELECT * FROM monthly_sales WHERE revenue > 100").fetchdf()


This integration works with Polars as well, supporting both eager and lazy evaluation modes. If your pipeline already uses Polars for its performance advantages, DuckDB slots in without friction.

## Working with Files Directly

DuckDB reads common file formats without importing data into tables first. This alone eliminates a surprising amount of boilerplate in data pipelines.


# Read a single CSV
conn.execute("SELECT * FROM 'measurements.csv' WHERE site = 'A'").fetchdf()

# Read all Parquet files matching a pattern
conn.execute("SELECT * FROM 'data/year=2024/*.parquet'").fetchdf()

# Query JSON lines
conn.execute("SELECT * FROM read_json_auto('events.jsonl')").fetchdf()


Glob patterns are particularly powerful here. If you have hundreds of CSV files following a naming convention, a single query can treat them as one logical table. Schema inference happens automatically, header detection works out of the box, and type coercion handles minor format differences across files.

For Parquet files, DuckDB applies column pruning and predicate pushdown. If your query only touches three columns out of fifty, it reads only those three from disk. If your WHERE clause filters on a column with Parquet statistics, entire row groups get skipped without decompression. On large datasets, these optimizations turn minutes into seconds. I think this is where DuckDB's design really shines compared to loading everything into a DataFrame first.

It also supports querying files in remote object storage. You can point queries at S3, Google Cloud Storage, or Cloudflare R2 buckets and DuckDB handles the HTTP range requests transparently. The first query against a remote source incurs a cold-start penalty while metadata is fetched and cached, but subsequent queries run at near-local speeds.

## SQL Features Worth Knowing

DuckDB implements a rich SQL dialect that goes well beyond basic SELECT statements. A few capabilities stand out for analytical Python work.

**Window functions** work as expected and perform well even on large result sets:


conn.execute("""
    SELECT sensor_id, ts, value,
           AVG(value) OVER (PARTITION BY sensor_id ORDER BY ts
                            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) as rolling_avg
    FROM readings
""").fetchdf()


**Common Table Expressions** chain naturally for multi-step transformations, and DuckDB handles deeply nested CTEs without the performance cliff you might see in other embedded databases.

**Advanced types** like arrays, structs, and maps let you model semi-structured data without flattening everything into flat tables. JSON columns can be queried with dot notation and bracket indexing, which simplifies working with API responses or log data.

## Things to Watch Out For

DuckDB is remarkably polished for its age, but a few rough edges are worth knowing before you commit to it in production.

**Concurrency limitations.** DuckDB allows multiple readers but only one writer at a time. It's not designed for workloads where many threads or processes write concurrently. If you need high-concurrency transactional writes, PostgreSQL is a better fit.

**Database file growth.** When you delete rows from a persistent database, the file doesn't shrink. Space occupied by deleted data isn't always reclaimed by `VACUUM` or `CHECKPOINT`, particularly when primary key or unique indexes are involved. For append-heavy analytical workflows this rarely matters, but if your pipeline does frequent upserts, keep an eye on file sizes. The pragmatic workaround is to periodically export and reimport.

**Memory behavior.** DuckDB's memory allocator (jemalloc on Linux, mimalloc elsewhere) doesn't immediately return freed memory to the OS. Resident memory may appear higher than expected after large queries complete. This is standard behavior for high-performance allocators and not a leak, but it can be surprising if you're monitoring process memory in a long-running service.

**Threading considerations.** Older versions had stability issues when multiple cursors on the same connection performed concurrent operations. These problems were addressed in version 1.4 and later, so if you're running something earlier and encountering segfaults, upgrading is the simplest fix.

## When DuckDB Fits and When It Doesn't

DuckDB excels at local analytical queries over medium-sized data, roughly the range from a few megabytes to tens of gigabytes. It's ideal for data exploration in notebooks, for replacing memory-constrained Pandas pipelines, and for embedding analytics directly in applications without infrastructure overhead.

Community benchmarks show it completing analytical queries three to ten times faster than managed cloud services like BigQuery or Athena on datasets in the single-digit to low-double-digit gigabyte range. And you pay zero per-query costs.

It's less suitable when you need distributed query processing across hundreds of gigabytes, when your workload is primarily transactional, or when many concurrent writers need to hit the same database. For those scenarios, purpose-built distributed or transactional databases remain the right choice.

## What Comes Next

Once you're comfortable with the basics, the ecosystem around DuckDB opens up. MotherDuck provides a managed serverless layer if you want to share databases across machines. The community maintains extensions for spatial data, full-text search, and additional file format support. There's even a dedicated Jupyter kernel that lets you write SQL cells natively without Python wrapper code.

The combination of trivial installation, strong Python integration, and analytical performance that punches well above its weight class makes DuckDB one of the most practical tools I've added to my workflow in recent years. Start with `pip install duckdb` and a CSV file you already have lying around. From what I can tell, you'll be surprised how quickly it changes the way you work with data.
